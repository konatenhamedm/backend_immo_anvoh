from datetime import timedelta
from decimal import Decimal

from django.db.models import Count, DecimalField, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.interfaces.permissions import IsAdminRole
from apps.investments.domain import services
from apps.investments.infrastructure.models import (
    EntryKind, EntryStatus, InvestmentDocument, InvestmentPlan, PlanStatus, ScheduleEntry, Subscription, SubscriptionStatus,
)
from .schemas import InvestmentStatsSchema, MyInvestmentsSchema
from .serializers import (
    ConfirmPaymentSerializer, InvestmentDocumentSerializer, InvestmentPlanAdminSerializer, InvestmentPlanSerializer,
    RevenueEntrySerializer, ScheduleEntrySerializer, SubscribeSerializer, SubscriptionAdminUpdateSerializer,
    SubscriptionSerializer,
)

ZERO = Value(Decimal('0'), output_field=DecimalField(max_digits=16, decimal_places=2))


def _subs_qs():
    return Subscription.objects.select_related('plan', 'user').prefetch_related('entries', 'documents')


def _plans_with_stats():
    paid = Q(subscriptions__entries__status=EntryStatus.PAYE) & ~Q(subscriptions__entries__kind=EntryKind.REVENU)
    return InvestmentPlan.objects.annotate(
        subscribers=Count('subscriptions__user', filter=Q(subscriptions__status=SubscriptionStatus.ACTIVE), distinct=True),
        aum=Coalesce(Sum('subscriptions__entries__amount', filter=paid), ZERO),
    )


@extend_schema(tags=["Investissement"], summary="Plans d'investissement publiés")
class PlanListView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = InvestmentPlanSerializer
    pagination_class = None

    def get_queryset(self):
        return InvestmentPlan.objects.filter(status__in=[PlanStatus.OUVERT, PlanStatus.COMPLET])


@extend_schema(tags=["Investissement"], request=SubscribeSerializer, responses={201: SubscriptionSerializer},
               summary="Souscrire à un plan (crée l'échéancier, premier versement en attente de validation)")
class SubscribeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = SubscribeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data
        try:
            sub = services.subscribe(request.user, d['plan'], d['amount'], d['payment_method'], d.get('months'), d.get('payment_phone', ''))
        except services.SubscriptionError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(SubscriptionSerializer(_subs_qs().get(id=sub.id), context={'request': request}).data, status=status.HTTP_201_CREATED)


@extend_schema(tags=["Investissement"], summary="Mon portefeuille : synthèse, plans, échéancier et documents",
               responses={200: MyInvestmentsSchema})
class MyInvestmentsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        subs = list(_subs_qs().filter(user=request.user).exclude(status=SubscriptionStatus.ANNULEE))
        entries = sorted((e for s in subs for e in s.entries.all()), key=lambda e: e.due_date, reverse=True)
        today = timezone.localdate()
        invested = sum((services.paid_amount(s) for s in subs), Decimal('0'))
        estimated = sum(((s.estimated_value if s.estimated_value is not None else services.paid_amount(s)) for s in subs), Decimal('0'))
        income_year = sum((e.amount for e in entries if e.kind == EntryKind.REVENU and e.status == EntryStatus.RECU and e.due_date.year == today.year), Decimal('0'))
        upcoming = sorted((e for e in entries if e.kind != EntryKind.REVENU and e.status in (EntryStatus.A_VENIR, EntryStatus.EN_VALIDATION)), key=lambda e: e.due_date)
        # Échéancier affiché : passé récent + les 3 prochaines échéances.
        shown = [e for e in entries if e.due_date <= today + timedelta(days=45)][:12]
        docs = [d for s in subs for d in s.documents.all()]
        return Response({
            'summary': {
                'invested': invested,
                'estimated_value': estimated,
                'income_year': income_year,
                'next_due': ScheduleEntrySerializer(upcoming[0]).data if upcoming else None,
            },
            'subscriptions': SubscriptionSerializer(subs, many=True, context={'request': request}).data,
            'schedule': ScheduleEntrySerializer(shown, many=True).data,
            'documents': InvestmentDocumentSerializer(docs, many=True, context={'request': request}).data,
        })


@extend_schema(tags=["Back-office Investissement"])
class PlanAdminListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAdminRole]
    serializer_class = InvestmentPlanAdminSerializer
    pagination_class = None

    def get_queryset(self):
        return _plans_with_stats()


@extend_schema(tags=["Back-office Investissement"])
class PlanAdminDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAdminRole]
    serializer_class = InvestmentPlanAdminSerializer
    lookup_field = 'id'

    def get_queryset(self):
        return _plans_with_stats()


@extend_schema(tags=["Back-office Investissement"], summary="Indicateurs : encours, souscripteurs, souscriptions du mois",
               responses={200: InvestmentStatsSchema})
class InvestmentStatsView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        today = timezone.localdate()
        paid = ScheduleEntry.objects.filter(status=EntryStatus.PAYE).exclude(kind=EntryKind.REVENU)
        return Response({
            'aum': paid.aggregate(t=Coalesce(Sum('amount'), ZERO))['t'],
            'subscribers': Subscription.objects.filter(status=SubscriptionStatus.ACTIVE).values('user').distinct().count(),
            'subscriptions_this_month': Subscription.objects.filter(created_at__year=today.year, created_at__month=today.month).count(),
            'pending_payments': ScheduleEntry.objects.filter(status=EntryStatus.EN_VALIDATION).count(),
            'income_paid_year': ScheduleEntry.objects.filter(kind=EntryKind.REVENU, status=EntryStatus.RECU, due_date__year=today.year)
                                .aggregate(t=Coalesce(Sum('amount'), ZERO))['t'],
        })


@extend_schema(tags=["Back-office Investissement"], summary="Souscriptions (?status=)")
class SubscriptionAdminListView(generics.ListAPIView):
    permission_classes = [IsAdminRole]
    serializer_class = SubscriptionSerializer

    def get_queryset(self):
        qs = _subs_qs()
        if self.request.query_params.get('status'):
            qs = qs.filter(status=self.request.query_params['status'])
        return qs


@extend_schema(tags=["Back-office Investissement"], summary="Affecter un actif, réévaluer, annuler")
class SubscriptionAdminDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAdminRole]
    lookup_field = 'id'

    def get_queryset(self):
        return _subs_qs()

    def get_serializer_class(self):
        return SubscriptionSerializer if self.request.method == 'GET' else SubscriptionAdminUpdateSerializer


@extend_schema(tags=["Back-office Investissement"], request=ConfirmPaymentSerializer, responses={200: ScheduleEntrySerializer},
               summary="Valider le paiement d'une échéance (en attendant le branchement d'un prestataire de paiement)")
class ConfirmPaymentView(APIView):
    permission_classes = [IsAdminRole]

    def post(self, request, id):
        entry = get_object_or_404(ScheduleEntry.objects.select_related('subscription__plan'), id=id)
        serializer = ConfirmPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            services.confirm_payment(entry, serializer.validated_data['reference'])
        except services.SubscriptionError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(ScheduleEntrySerializer(entry).data)


@extend_schema(tags=["Back-office Investissement"], request=RevenueEntrySerializer, responses={201: ScheduleEntrySerializer},
               summary="Enregistrer un revenu reversé au souscripteur (loyer, plus-value)")
class RevenueEntryCreateView(APIView):
    permission_classes = [IsAdminRole]

    def post(self, request, id):
        sub = get_object_or_404(Subscription, id=id)
        serializer = RevenueEntrySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data
        entry = ScheduleEntry.objects.create(
            subscription=sub, kind=EntryKind.REVENU, label=d['label'], due_date=d['due_date'], amount=d['amount'],
            status=EntryStatus.RECU if d['received'] else EntryStatus.PROGRAMME,
            settled_at=timezone.now() if d['received'] else None,
        )
        return Response(ScheduleEntrySerializer(entry).data, status=status.HTTP_201_CREATED)


@extend_schema(tags=["Back-office Investissement"], summary="Déposer un document pour le souscripteur (multipart : title, file)",
               request={'multipart/form-data': {'type': 'object', 'required': ['title', 'file'], 'properties': {'title': {'type': 'string'}, 'file': {'type': 'string', 'format': 'binary'}}}},
               responses={201: InvestmentDocumentSerializer})
class InvestmentDocumentUploadView(APIView):
    permission_classes = [IsAdminRole]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, id):
        sub = get_object_or_404(Subscription, id=id)
        title, file = request.data.get('title'), request.FILES.get('file')
        if not title or not file:
            return Response({'detail': 'Titre et fichier requis.'}, status=status.HTTP_400_BAD_REQUEST)
        doc = InvestmentDocument.objects.create(subscription=sub, title=title, file=file)
        return Response(InvestmentDocumentSerializer(doc, context={'request': request}).data, status=status.HTTP_201_CREATED)
