"""
Règles métier des prospects (leads).

Corrige les défauts de la première version :
- téléphone normalisé (+225…) avant tout dédoublonnage ;
- un clic WhatsApp anonyme sans numéro ne crée plus de lead fourre-tout « Inconnu » ;
- un lead existant est complété (compte, e-mail, conseiller) au lieu d'être ignoré ;
- le score est recalculé à partir des faits connus du lead (cumulatifs), il ne baisse plus à chaque action ;
- l'étape du pipeline n'avance que vers l'avant (sauf réactivation d'un lead perdu).
"""
import re

from django.db import transaction
from django.utils import timezone

from apps.crm.domain.scoring_service import LeadScoringDomainService
from apps.crm.infrastructure.models import Lead, PipelineStage

STAGE_ORDER = [
    PipelineStage.NOUVEAU, PipelineStage.CONTACTE, PipelineStage.QUALIFIE, PipelineStage.RDV, PipelineStage.VISITE,
    PipelineStage.PROPOSITION, PipelineStage.NEGOCIATION, PipelineStage.RESERVATION, PipelineStage.VENTE,
]
SHORT_TIMEFRAME_MARKERS = ('immédiat', 'immediat', '0-3', '0_3', '0 à 3', '0 a 3', 'moins de 3')


def normalize_phone(raw: str | None) -> str:
    """'07 07 07 07 07' → '+2250707070707' ; '+33 6 12…' → '+33612…' ; '' si vide."""
    raw = (raw or '').strip()
    digits = re.sub(r'\D', '', raw)
    if not digits:
        return ''
    if raw.startswith('+'):
        return '+' + digits
    if digits.startswith('00'):
        return '+' + digits[2:]
    if digits.startswith('225') and len(digits) == 13:
        return '+' + digits
    if len(digits) == 10:  # numéro ivoirien local (10 chiffres depuis 2021)
        return '+225' + digits
    return digits


@transaction.atomic
def find_or_create_lead(*, phone: str | None, user=None, full_name: str = '', email: str = '', source: str,
                        prop=None, extra: dict | None = None) -> Lead | None:
    """Retrouve le lead (par téléphone normalisé, sinon par compte) ou le crée. None si le visiteur est inidentifiable."""
    phone = normalize_phone(phone) or (normalize_phone(user.phone_number) if user else '')
    lead = None
    if phone:
        lead = Lead.objects.select_for_update().filter(phone_number=phone).order_by('created_at').first()
    if lead is None and user is not None:
        lead = Lead.objects.select_for_update().filter(user=user).order_by('created_at').first()
    if lead is None and not phone and user is None:
        return None

    if lead is None:
        lead = Lead(
            phone_number=phone, user=user, source=source,
            full_name=full_name or (f"{user.first_name} {user.last_name}".strip() if user else '') or 'Prospect',
            email=email or (user.email if user else ''),
        )
    else:
        # Compléter sans écraser ce que l'équipe a déjà qualifié.
        if user is not None and lead.user_id is None:
            lead.user = user
        if email and not lead.email:
            lead.email = email
        if full_name and lead.full_name in ('', 'Prospect', 'Visiteur WhatsApp'):
            lead.full_name = full_name
        if phone and not lead.phone_number:
            lead.phone_number = phone
        if lead.stage == PipelineStage.PERDU:
            lead.stage = PipelineStage.NOUVEAU  # le prospect revient : on le réactive
    if prop is not None:
        lead.consulted_property = prop
        if lead.assigned_agent_id is None and prop.assigned_agent_id:
            lead.assigned_agent_id = prop.assigned_agent_id
    for key, value in (extra or {}).items():
        if value not in (None, ''):
            setattr(lead, key, value)
    lead.save()
    return lead


def advance_stage(lead: Lead, target: str) -> None:
    """Fait avancer le lead jusqu'à `target` s'il n'y est pas déjà (jamais de retour en arrière)."""
    if target == PipelineStage.PERDU:
        lead.stage = target
        return
    current = STAGE_ORDER.index(lead.stage) if lead.stage in STAGE_ORDER else -1
    if STAGE_ORDER.index(target) > current:
        lead.stage = target


def rescore(lead: Lead) -> None:
    """Score d'intention calculé à partir de ce que l'on sait du prospect (cumulatif)."""
    timeframe = (lead.timeframe or '').lower()
    score, temperature = LeadScoringDomainService.calculate_score(
        has_confirmed_budget=bool(lead.budget),
        has_confirmed_down_payment=bool(lead.down_payment and lead.down_payment > 0),
        timeframe_under_3_months=any(m in timeframe for m in SHORT_TIMEFRAME_MARKERS),
        has_identified_property=bool(lead.consulted_property_id) or lead.inquiries.exists(),
        has_visit_request=lead.visits.exists(),
        has_recent_interaction=bool(lead.last_interaction_at and (timezone.now() - lead.last_interaction_at).days <= 30) or lead.pk is None,
    )
    lead.score, lead.temperature = score, temperature
