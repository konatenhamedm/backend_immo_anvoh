from decimal import Decimal

from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.interfaces.permissions import IsAdminRole, IsOwnerRole
from apps.investments.domain.services import add_months
from apps.rentals.infrastructure.models import Lease, OwnerPayout, PayoutStatus, RentPayment, RentStatus
from .serializers import LeaseSerializer, OwnerPayoutSerializer, RentPaymentSerializer

MONTHS_FR = ['Janv.', 'Févr.', 'Mars', 'Avr.', 'Mai', 'Juin', 'Juil.', 'Août', 'Sept.', 'Oct.', 'Nov.', 'Déc.']


def _net(payment: RentPayment) -> Decimal:
    """Loyer encaissé, net des honoraires de gestion."""
    return payment.amount * (Decimal('100') - payment.lease.management_fee_rate) / Decimal('100')


@extend_schema(tags=["Gestion locative"], summary="Revenus & performance du propriétaire connecté")
class OwnerRentalSummaryView(APIView):
    permission_classes = [IsOwnerRole]

    def get(self, request):
        today = timezone.localdate()
        this_month = today.replace(day=1)
        leases = list(Lease.objects.filter(property__owner=request.user, is_active=True).select_related('property').prefetch_related('property__images'))
        payments = list(RentPayment.objects.filter(lease__property__owner=request.user, status=RentStatus.PAYE).select_related('lease'))

        by_month = {}
        for p in payments:
            by_month[p.period] = by_month.get(p.period, Decimal('0')) + _net(p)
        months = [add_months(this_month, -i) for i in range(5, -1, -1)]
        current = by_month.get(this_month, Decimal('0'))
        previous = by_month.get(add_months(this_month, -1), Decimal('0'))

        month_statuses = dict(RentPayment.objects.filter(lease__in=leases, period=this_month).values_list('lease_id', 'status'))
        payouts = OwnerPayout.objects.filter(owner=request.user)
        next_payout = payouts.filter(status=PayoutStatus.PROGRAMME, payout_date__gte=today).order_by('payout_date').first()

        def lease_row(lease):
            p = lease.property
            cover = next((i for i in p.images.all() if i.is_cover), None) or next(iter(p.images.all()), None)
            month_status = month_statuses.get(lease.id)
            return {
                'lease_id': str(lease.id),
                'property': {'id': str(p.id), 'reference': p.reference, 'title': p.title, 'slug': p.slug, 'commune': p.commune,
                             'neighborhood': p.neighborhood, 'cover_image': cover.url(request) if cover else None},
                'tenant': lease.tenant_label,
                'monthly_rent': lease.monthly_rent,
                'occupancy_rate': lease.occupancy_rate,
                # Pas de loyer enregistré pour le mois en cours : « en retard » passé le 5, sinon « à venir ».
                'current_status': month_status or (RentStatus.EN_RETARD if today.day > 5 else 'A_VENIR'),
            }

        return Response({
            'month_label': f"{MONTHS_FR[this_month.month - 1]} {this_month.year}",
            'month_revenue': current,
            'month_delta_pct': round(float((current - previous) / previous * 100), 1) if previous else None,
            'year_total': sum((v for k, v in by_month.items() if k.year == today.year), Decimal('0')),
            'occupancy_rate': round(sum(l.occupancy_rate for l in leases) / len(leases)) if leases else None,
            'next_payout': OwnerPayoutSerializer(next_payout).data if next_payout else None,
            'monthly': [{'month': MONTHS_FR[m.month - 1], 'value': round(float(by_month.get(m, 0)) / 1_000_000, 2)} for m in months],
            'payouts': OwnerPayoutSerializer(payouts.filter(status=PayoutStatus.VERSE)[:5], many=True).data,
            'leases': [lease_row(l) for l in leases],
        })


@extend_schema(tags=["Back-office Gestion locative"])
class LeaseAdminListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAdminRole]
    serializer_class = LeaseSerializer
    queryset = Lease.objects.select_related('property')


@extend_schema(tags=["Back-office Gestion locative"])
class LeaseAdminDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAdminRole]
    serializer_class = LeaseSerializer
    queryset = Lease.objects.select_related('property')
    lookup_field = 'id'


@extend_schema(tags=["Back-office Gestion locative"], summary="Loyers encaissés (enregistrement mensuel)")
class RentPaymentAdminListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAdminRole]
    serializer_class = RentPaymentSerializer
    queryset = RentPayment.objects.select_related('lease')


@extend_schema(tags=["Back-office Gestion locative"], summary="Versements aux propriétaires")
class PayoutAdminListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAdminRole]
    serializer_class = OwnerPayoutSerializer
    queryset = OwnerPayout.objects.all()


@extend_schema(tags=["Back-office Gestion locative"])
class PayoutAdminDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAdminRole]
    serializer_class = OwnerPayoutSerializer
    queryset = OwnerPayout.objects.all()
    lookup_field = 'id'
