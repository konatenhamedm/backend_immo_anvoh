"""Requêtes et fonctions partagées par les vues du module `properties` (aucune vue ici)."""

import math

from django.db.models import Case, Count, F, FloatField, IntegerField, Q, Value, When
from django.db.models.functions import ACos, Cast, Cos, Least, Radians, Sin
from rest_framework.exceptions import NotFound

from apps.properties.infrastructure.models import (
    PUBLIC_STATUSES,
    DevelopmentProject,
    Property,
    PropertyStatus,
    PropertyType,
    PropertyTypology,
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


MAX_SEARCH_WORDS = 6


def _search_words(q: str) -> list[str]:
    return [w for w in q.replace(",", " ").split() if w][:MAX_SEARCH_WORDS]


def _type_codes_for(word: str) -> list[str]:
    """« villa », « villas », « app » → codes de type de bien dont le libellé commence par ce mot (3 lettres au moins)."""
    w = word.lower()
    candidates = {w, w[:-1] if w.endswith("s") else w}
    if len(w) < 3:
        return []
    return [code for code, label in PropertyType.choices if any(label.lower().startswith(c) for c in candidates if len(c) >= 3)]


def _word_matches(word: str) -> Q:
    """Un mot de la recherche correspond au titre, au lieu, à la description, à la référence, au type ou à la typologie (F3…)."""
    cond = (
        Q(title__icontains=word)
        | Q(commune__icontains=word)
        | Q(neighborhood__icontains=word)
        | Q(description__icontains=word)
        | Q(reference__icontains=word)
    )
    codes = _type_codes_for(word)
    if codes:
        cond |= Q(property_type__in=codes)
    if word.upper() in PropertyTypology.values:
        cond |= Q(typology=word.upper())
    return cond


def _float(value, low=None, high=None):
    try:
        v = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(v) or math.isinf(v) or (low is not None and v < low) or (high is not None and v > high):
        return None
    return v


def distance_expression(lat: float, lng: float):
    """Distance en km (formule de Haversine, rayon terrestre 6 371 km) entre (lat, lng) et la position du bien."""
    lat0 = Radians(Value(lat, output_field=FloatField()))
    lng0 = Radians(Value(lng, output_field=FloatField()))
    # Les positions sont stockées en DECIMAL : on les convertit en flottants avant le calcul trigonométrique.
    plat = Radians(Cast(F("latitude"), FloatField()))
    plng = Radians(Cast(F("longitude"), FloatField()))
    cosine = Cos(lat0) * Cos(plat) * Cos(plng - lng0) + Sin(lat0) * Sin(plat)
    return 6371.0 * ACos(Least(Value(1.0, output_field=FloatField()), cosine))


def apply_geo_filters(qs, params):
    """
    Recherche géographique (spécification §6) :
    - lat, lng, radius_km : biens autour d'un point (autour de moi, autour d'un lieu) ; chaque bien reçoit distance_km ;
    - bbox=sud,ouest,nord,est : biens dans la zone visible d'une carte.
    Renvoie (queryset, near) : near vaut True quand le tri « distance » est possible.
    """
    lat, lng = _float(params.get("lat"), -90, 90), _float(params.get("lng"), -180, 180)
    radius = _float(params.get("radius_km"), 0.1, 200)
    near = lat is not None and lng is not None and radius is not None
    if near:
        dlat = radius / 111.0
        dlng = radius / (111.0 * max(math.cos(math.radians(lat)), 0.01))
        qs = (
            qs.exclude(latitude__isnull=True, longitude__isnull=True)
            .filter(latitude__gte=lat - dlat, latitude__lte=lat + dlat, longitude__gte=lng - dlng, longitude__lte=lng + dlng)  # pré-filtre
            .annotate(distance_km=distance_expression(lat, lng))
            .filter(distance_km__lte=radius)
        )
    box = str(params.get("bbox") or "").split(",")
    if len(box) == 4:
        s_, w_, n_, e_ = (_float(x) for x in box)
        if None not in (s_, w_, n_, e_) and -90 <= s_ <= n_ <= 90 and -180 <= w_ <= e_ <= 180:
            qs = qs.filter(latitude__gte=s_, latitude__lte=n_, longitude__gte=w_, longitude__lte=e_)
    return qs, near


def apply_search_filters(qs, params):
    q = (params.get("q") or "").strip()
    words = _search_words(q)
    # Recherche par MOTS : « Cocody Abatta » ou « villa Cocody » trouvent les biens qui correspondent à chaque mot
    # (commune, quartier, type…), et non la seule phrase exacte.
    for word in words:
        qs = qs.filter(_word_matches(word))
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
    qs, near = apply_geo_filters(qs, params)
    ordering = params.get("ordering", "-created_at")
    if ordering == "distance" and near:
        return qs.order_by("distance_km", "-created_at")
    if ordering == "relevance":
        # Pertinence : correspondance du texte cherché (titre > lieu > reste), puis mise en avant et score.
        if words:
            title_hit = Q()
            place_hit = Q()
            for w in words:
                title_hit |= Q(title__icontains=w)
                place_hit |= Q(commune__icontains=w) | Q(neighborhood__icontains=w)
            qs = qs.annotate(
                _rank=Case(
                    When(title_hit, then=Value(3)),
                    When(place_hit, then=Value(2)),
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
