"""
Règles métier des souscriptions.

- Plan avec paiement échelonné : N mensualités sans intérêt (12 à 36), la première est due à la souscription.
- Sinon : un versement unique.
- Le premier versement reste « en attente de validation » tant que le paiement n'est pas confirmé
  (aucun prestataire de paiement n'est branché : la confirmation est faite par l'équipe, ou plus tard par webhook).
- La souscription devient active au premier paiement confirmé.
"""
import math
from datetime import date
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.investments.infrastructure.models import (
    EntryKind, EntryStatus, InvestmentPlan, PlanStatus, ScheduleEntry, Subscription, SubscriptionStatus,
)

MIN_MONTHS, MAX_MONTHS = 12, 36


class SubscriptionError(Exception):
    pass


def add_months(d: date, months: int) -> date:
    m = d.month - 1 + months
    year, month = d.year + m // 12, m % 12 + 1
    days = [31, 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    return date(year, month, min(d.day, days[month - 1]))


def monthly_amount(amount: Decimal, months: int) -> Decimal:
    """Mensualité arrondie au millier supérieur (comme l'affiche le parcours de souscription)."""
    return Decimal(math.ceil(float(amount) / months / 1000) * 1000)


@transaction.atomic
def subscribe(user, plan: InvestmentPlan, amount: Decimal, payment_method: str, months: int | None = None,
              payment_phone: str = '') -> Subscription:
    if plan.status != PlanStatus.OUVERT:
        raise SubscriptionError("Ce plan n'est pas ouvert à la souscription.")
    if amount < plan.min_ticket:
        raise SubscriptionError(f"Montant minimum : {plan.min_ticket:,.0f} FCFA.".replace(',', ' '))
    if plan.allows_instalments:
        months = months or 24
        if not MIN_MONTHS <= months <= MAX_MONTHS:
            raise SubscriptionError(f"Choisissez entre {MIN_MONTHS} et {MAX_MONTHS} mensualités.")
    else:
        months = None

    sub = Subscription.objects.create(
        user=user, plan=plan, amount=amount, months=months, payment_method=payment_method,
        payment_phone=payment_phone, accepted_terms_at=timezone.now(),
    )
    today = timezone.localdate()
    if months:
        monthly = monthly_amount(amount, months)
        ScheduleEntry.objects.bulk_create([
            ScheduleEntry(
                subscription=sub, kind=EntryKind.MENSUALITE, label=f"Mensualité {i + 1}/{months} — {plan.name}",
                due_date=add_months(today, i), amount=monthly,
                status=EntryStatus.EN_VALIDATION if i == 0 else EntryStatus.A_VENIR,
            )
            for i in range(months)
        ])
    else:
        ScheduleEntry.objects.create(
            subscription=sub, kind=EntryKind.VERSEMENT, label=f"Versement — {plan.name}",
            due_date=today, amount=amount, status=EntryStatus.EN_VALIDATION,
        )
    return sub


@transaction.atomic
def confirm_payment(entry: ScheduleEntry, reference: str = '') -> ScheduleEntry:
    """Valide le paiement d'une échéance (versement ou mensualité) et active la souscription au premier paiement."""
    if entry.kind == EntryKind.REVENU:
        raise SubscriptionError("Un revenu reversé ne se valide pas comme un paiement.")
    if entry.status == EntryStatus.PAYE:
        return entry
    entry.status = EntryStatus.PAYE
    entry.payment_reference = reference
    entry.settled_at = timezone.now()
    entry.save()

    sub = entry.subscription
    if sub.status == SubscriptionStatus.EN_ATTENTE:
        sub.status = SubscriptionStatus.ACTIVE
        sub.activated_at = timezone.now()
        sub.save(update_fields=['status', 'activated_at'])
    elif not sub.entries.exclude(kind=EntryKind.REVENU).exclude(status=EntryStatus.PAYE).exists() and sub.plan.allows_instalments:
        sub.status = SubscriptionStatus.TERMINEE
        sub.save(update_fields=['status'])
    return entry


def paid_amount(sub: Subscription) -> Decimal:
    return sum((e.amount for e in sub.entries.all() if e.kind != EntryKind.REVENU and e.status == EntryStatus.PAYE), Decimal('0'))
