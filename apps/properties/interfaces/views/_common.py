"""Requêtes et fonctions partagées par les vues du module `properties` (aucune vue ici)."""

from django.db.models import Case, Count, IntegerField, Q, Value, When
from rest_framework.exceptions import NotFound

from apps.properties.infrastructure.models import (
    PUBLIC_STATUSES,
    DevelopmentProject,
    Property,
    PropertyStatus,
    VerificationStatus,
)
from apps.users.interfaces.permissions import is_staff_or_agent

from ..serializers import (
    favorite_ids_for,
)


def cards_qs():
    return Property.objects.select_related("owner", "assigned_agent", "accreditation__notary").prefetch_related(
        "images"
    )


def public_qs():
    return cards_qs().filter(status__in=PUBLIC_STATUSES)


def project_summaries():
    """
    Programmes neufs avec leurs décomptes de lots, calculés par la base (un seul GROUP BY, aucun lot chargé).

    À utiliser avec DevelopmentProjectSummarySerializer. Pour la liste détaillée des lots, voir DevelopmentProjectSerializer.
    """
    return DevelopmentProject.objects.annotate(
        lots_sold=Count("lots", filter=Q(lots__status=PropertyStatus.VENDU)),
        lots_available=Count("lots", filter=Q(lots__status=PropertyStatus.DISPONIBLE)),
    )


def ctx(request):
    return {"request": request, "favorite_ids": favorite_ids_for(request)}


def can_manage(user, prop) -> bool:
    return is_staff_or_agent(user) or (user.is_authenticated and prop.owner_id == user.id)


def apply_search_filters(qs, params):
    q = params.get("q")
    if q:
        qs = qs.filter(
            Q(title__icontains=q)
            | Q(commune__icontains=q)
            | Q(neighborhood__icontains=q)
            | Q(description__icontains=q)
            | Q(reference__icontains=q)
        )
    for param, lookup in (
        ("commune", "commune__icontains"),
        ("neighborhood", "neighborhood__icontains"),
        ("type", "property_type"),
        ("typology", "typology"),
        ("target_goal", "target_goal"),
        ("transaction", "transaction"),
        ("min_price", "price__gte"),
        ("max_price", "price__lte"),
        ("min_surface", "surface_sqm__gte"),
        ("rooms_count", "rooms_count"),
        ("min_bedrooms", "bedrooms_count__gte"),
        ("status", "status"),  # disponibilité : DISPONIBLE | OPTION | RESERVE (déjà borné par public_qs)
    ):
        if params.get(param):
            qs = qs.filter(**{lookup: params[param]})
    if params.get("verified") in ("1", "true"):
        qs = qs.filter(verification_status__in=[VerificationStatus.VERIFIE, VerificationStatus.VERIFICATION_RENFORCEE])
    if params.get("has_tour") in ("1", "true"):
        qs = qs.exclude(virtual_tour_url__isnull=True).exclude(virtual_tour_url="")
    ordering = params.get("ordering", "-created_at")
    if ordering == "relevance":
        # Pertinence : correspondance du texte cherché (titre > lieu > reste), puis mise en avant et score.
        if q:
            qs = qs.annotate(
                _rank=Case(
                    When(title__icontains=q, then=Value(3)),
                    When(Q(commune__icontains=q) | Q(neighborhood__icontains=q), then=Value(2)),
                    default=Value(1),
                    output_field=IntegerField(),
                )
            )
            return qs.order_by("-_rank", "-is_featured", "-investment_score", "-created_at")
        return qs.order_by("-is_featured", "-investment_score", "-created_at")
    allowed = [
        "price",
        "-price",
        "created_at",
        "-created_at",
        "-estimated_yield_rate",
        "-investment_score",
        "-views_count",
    ]
    return qs.order_by(ordering if ordering in allowed else "-created_at")


def _visible_or_404(request, prop):
    if not prop.is_public and not can_manage(request.user, prop):
        raise NotFound("Bien introuvable")
    return prop


def owner_qs(user):
    return cards_qs().filter(owner=user).annotate(leads_count=Count("leads", distinct=True))
