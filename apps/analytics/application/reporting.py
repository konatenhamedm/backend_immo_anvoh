"""Calculs du tableau de bord d'acquisition : KPI de la spécification §31, entonnoir et ROI marketing par canal."""

from datetime import timedelta
from decimal import Decimal

from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone

from apps.analytics.domain import events as ev
from apps.analytics.infrastructure.models import AnalyticsEvent, ChannelSpend
from apps.crm.infrastructure.models import AcquisitionChannel, Lead, PipelineStage, VisitRequest

HOT = ("CHAUD", "TRES_CHAUD")


def _count(qs, name):
    return qs.filter(name=name).count()


def _active_users(events) -> int:
    """Utilisateurs actifs : navigateurs distincts, plus les comptes vus sans identifiant de navigateur."""
    browsers = events.exclude(anonymous_id="").values("anonymous_id").distinct().count()
    accounts = events.filter(anonymous_id="").exclude(user=None).values("user_id").distinct().count()
    return browsers + accounts


def _ratio(a, b):
    return round(a / b, 4) if b else None


def summary(days: int = 30) -> dict:
    now = timezone.now()
    start = now - timedelta(days=days)
    events = AnalyticsEvent.objects.filter(occurred_at__gte=start)
    leads = Lead.objects.filter(created_at__gte=start)

    counts = {name: _count(events, name) for name in sorted(ev.ALL_EVENTS)}
    viewed = events.filter(name=ev.PROPERTY_VIEW).values("properties__property").distinct().count()
    sessions = _count(events, ev.SESSION_START)
    leads_n = leads.count()
    sold_in_period = Lead.objects.filter(converted_at__gte=start)

    totals = {
        "downloads": counts[ev.APP_INSTALLED],
        "signups": counts[ev.SIGNUP],
        "active_users": _active_users(events),
        "sessions": sessions,
        "searches": counts[ev.SEARCH],
        "properties_viewed": counts[ev.PROPERTY_VIEW],
        "distinct_properties_viewed": viewed,
        "favorites": counts[ev.FAVORITE_ADD],
        "inquiries": counts[ev.INQUIRY],
        "whatsapp_clicks": counts[ev.WHATSAPP_CLICK],
        "visits_requested": counts[ev.VISIT_REQUESTED],
        "simulations": counts[ev.SIMULATION_CAPACITY] + counts[ev.SIMULATION_RENTABILITY],
        "leads": leads_n,
        "conversions": sold_in_period.count(),
        # KPI majeur : ventes dont le prospect est venu par la plateforme (tout canal identifié, hors « Autre »).
        "sales_generated_by_app": sold_in_period.exclude(acquisition_channel=AcquisitionChannel.AUTRE).count(),
    }

    funnel = [
        {"step": "Sessions", "count": sessions},
        {"step": "Recherches", "count": counts[ev.SEARCH]},
        {"step": "Biens consultés", "count": counts[ev.PROPERTY_VIEW]},
        {"step": "Leads", "count": leads_n},
        {"step": "Visites demandées", "count": counts[ev.VISIT_REQUESTED]},
        {"step": "Ventes", "count": totals["conversions"]},
    ]

    # Par canal : cohorte des prospects créés sur la période ; ventes = ceux qui sont (aujourd'hui) en étape VENTE.
    rows = (
        leads.values("acquisition_channel")
        .annotate(
            leads=Count("id"),
            qualified=Count("id", filter=Q(temperature__in=HOT)),
            with_visit=Count("id", filter=Q(visits__isnull=False), distinct=True),
            sales=Count("id", filter=Q(stage=PipelineStage.VENTE)),
        )
        .order_by("-leads")
    )
    first_month = start.date().replace(day=1)
    spend = {
        r["channel"]: r["total"]
        for r in ChannelSpend.objects.filter(month__gte=first_month, month__lte=now.date()).values("channel").annotate(total=Sum("amount"))
    }
    labels = dict(AcquisitionChannel.choices)
    by_channel = []
    for r in rows:
        ch = r["acquisition_channel"]
        cost = spend.get(ch, Decimal("0"))
        by_channel.append(
            {
                "channel": ch,
                "label": labels.get(ch, ch),
                "leads": r["leads"],
                "qualified": r["qualified"],
                "with_visit": r["with_visit"],
                "sales": r["sales"],
                "conversion_rate": _ratio(r["sales"], r["leads"]),
                "spend": cost,
                "cost_per_lead": round(cost / r["leads"], 2) if cost and r["leads"] else None,
                "cost_per_sale": round(cost / r["sales"], 2) if cost and r["sales"] else None,
            }
        )

    daily = {}
    for row in events.filter(name=ev.SESSION_START).annotate(d=TruncDate("occurred_at")).values("d").annotate(n=Count("id")):
        daily.setdefault(row["d"].isoformat(), {"date": row["d"].isoformat(), "sessions": 0, "leads": 0})["sessions"] = row["n"]
    for row in leads.annotate(d=TruncDate("created_at")).values("d").annotate(n=Count("id")):
        daily.setdefault(row["d"].isoformat(), {"date": row["d"].isoformat(), "sessions": 0, "leads": 0})["leads"] = row["n"]

    return {
        "period": {"days": days, "from": start.date().isoformat(), "to": now.date().isoformat()},
        "totals": totals,
        "funnel": funnel,
        "by_channel": by_channel,
        "daily": [daily[k] for k in sorted(daily)],
        "visits_in_db": VisitRequest.objects.filter(created_at__gte=start).count(),
    }
