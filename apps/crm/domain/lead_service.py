"""
Règles métier des prospects (leads).

QUE CONTIENT CE FICHIER ?
-------------------------
Trois fonctions écrites POUR CE PROJET (ce ne sont pas des fonctions de Django ni de DRF) :

    find_or_create_lead(...)   retrouve un prospect par son téléphone, ou le crée    → ÉCRIT en base
    advance_stage(lead, ...)   fait avancer l'étape du pipeline, jamais en arrière   → en mémoire seulement
    rescore(lead)              recalcule le score et la température                  → en mémoire seulement

« En mémoire seulement » = la fonction modifie l'objet Python mais n'écrit RIEN en base : c'est à l'appelant
de faire lead.save() ensuite (comme avec Doctrine : modifier l'entité ne suffit pas, il faut un flush).

Pourquoi ici et pas dans les contrôleurs ? C'est le « domain service » (≈ un Service Symfony sans dépendance HTTP) :
la même règle sert au formulaire de contact, à WhatsApp, à la réservation de visite et à la saisie manuelle de
l'équipe, et elle peut être testée sans serveur.

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
from apps.crm.infrastructure.models import AcquisitionChannel, Lead, PipelineStage

# Ordre du pipeline commercial, du début à la fin. « PERDU » n'y figure pas : c'est une sortie, pas une étape.
# Sert à comparer deux étapes (STAGE_ORDER.index("RDV") > STAGE_ORDER.index("CONTACTE")) pour ne jamais reculer.
STAGE_ORDER = [
    PipelineStage.NOUVEAU,
    PipelineStage.CONTACTE,
    PipelineStage.QUALIFIE,
    PipelineStage.RDV,
    PipelineStage.VISITE,
    PipelineStage.PROPOSITION,
    PipelineStage.NEGOCIATION,
    PipelineStage.RESERVATION,
    PipelineStage.VENTE,
]
ATTRIBUTION_FIELDS = {"utm_source", "utm_medium", "utm_campaign", "referral_code", "landing_path"}
SHORT_TIMEFRAME_MARKERS = ("immédiat", "immediat", "0-3", "0_3", "0 à 3", "0 a 3", "moins de 3")


def normalize_phone(raw: str | None) -> str:
    """'07 07 07 07 07' → '+2250707070707' ; '+33 6 12…' → '+33612…' ; '' si vide."""
    raw = (raw or "").strip()
    digits = re.sub(r"\D", "", raw)
    if not digits:
        return ""
    if raw.startswith("+"):
        return "+" + digits
    if digits.startswith("00"):
        return "+" + digits[2:]
    if digits.startswith("225") and len(digits) == 13:
        return "+" + digits
    if len(digits) == 10:  # numéro ivoirien local (10 chiffres depuis 2021)
        return "+225" + digits
    return digits


# @transaction.atomic (natif Django) : tout ce que fait la fonction est dans UNE transaction SQL — si une erreur
# survient, rien n'est enregistré (≈ $em->wrapInTransaction()). Évite d'avoir un prospect à moitié écrit.
@transaction.atomic
def find_or_create_lead(
    *,
    phone: str | None,
    user=None,
    full_name: str = "",
    email: str = "",
    source: str,
    prop=None,
    extra: dict | None = None,
    attribution: dict | None = None,
) -> Lead | None:
    """
    Retrouve le prospect existant, ou en crée un nouveau. C'est le point d'entrée UNIQUE pour éviter les doublons.

    « find or create » = « chercher, sinon créer ». Elle est appelée par : le formulaire de demande d'informations,
    la réservation de visite, « Trouver mon bien », le clic WhatsApp et la saisie manuelle de l'équipe.

    Paramètres (tous nommés : on écrit find_or_create_lead(phone=..., source=...), c'est le sens du « * ») :
        phone      téléphone saisi (n'importe quel format) ; normalisé avant la recherche
        user       compte connecté s'il y en a un (permet de rattacher le prospect à son compte)
        full_name, email   informations saisies
        source     d'où vient le prospect (LeadSource : SITE_WEB, WHATSAPP, VISITE, AUTRE…)
        prop       bien consulté (objet Property) — assigne aussi le conseiller du bien s'il n'y en a pas
        extra      dictionnaire de champs en plus (budget, notes…), posés SEULEMENT s'ils sont renseignés
        attribution origine marketing {channel, utm_source, utm_medium, utm_campaign, referral_code, landing_path} :
                   enregistrée à la CRÉATION du prospect seulement (premier contact), jamais écrasée ensuite

    Retourne le Lead (déjà ENREGISTRÉ en base), ou None si le visiteur est impossible à identifier
    (ni téléphone, ni compte connecté) : on ne crée jamais de prospect « Inconnu ».

    Règle de recherche : 1) par téléphone normalisé, 2) sinon par compte utilisateur, 3) sinon on crée.
    S'il existe déjà, on le COMPLÈTE (e-mail, nom, compte…) sans écraser ce que l'équipe a qualifié.
    Un prospect « Perdu » qui se manifeste de nouveau repasse en « Nouveau ».
    """
    phone = normalize_phone(phone) or (normalize_phone(user.phone_number) if user else "")
    lead = None
    if phone:
        # select_for_update() : VERROUILLE la ligne le temps de la transaction. Si deux visiteurs envoient le même
        # numéro en même temps, le 2e attend le 1er au lieu de créer un doublon (≈ verrou pessimiste Doctrine).
        lead = Lead.objects.select_for_update().filter(phone_number=phone).order_by("created_at").first()
    if lead is None and user is not None:
        lead = Lead.objects.select_for_update().filter(user=user).order_by("created_at").first()
    if lead is None and not phone and user is None:
        return None

    is_new = False
    if lead is None:
        lead = Lead(
            phone_number=phone,
            user=user,
            source=source,
            full_name=full_name or (f"{user.first_name} {user.last_name}".strip() if user else "") or "Prospect",
            email=email or (user.email if user else ""),
        )
        for key, value in (attribution or {}).items():
            if key == "channel":
                lead.acquisition_channel = value or AcquisitionChannel.AUTRE
            elif key in ATTRIBUTION_FIELDS and value:
                setattr(lead, key, value)
        is_new = True
    else:
        # Compléter sans écraser ce que l'équipe a déjà qualifié.
        if user is not None and lead.user_id is None:
            lead.user = user
        if email and not lead.email:
            lead.email = email
        if full_name and lead.full_name in ("", "Prospect", "Visiteur WhatsApp"):
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
        if value not in (None, ""):
            setattr(lead, key, value)  # setattr(obj, "budget", 5) équivaut à obj.budget = 5 (nom de champ dynamique)
    assign_agent(lead)  # sans effet si le prospect a déjà un conseiller (celui du bien, ou choisi par l'équipe)
    # ENREGISTRE : INSERT si c'est un nouveau prospect, UPDATE de toutes les colonnes sinon.
    lead.save()
    if is_new:
        from apps.analytics.application.recorder import record  # import tardif : évite une dépendance circulaire
        from apps.analytics.domain.events import LEAD_CREATED

        record(LEAD_CREATED, user=user, channel=lead.acquisition_channel, properties={"source": lead.source})
    return lead


def assign_agent(lead: Lead) -> None:
    """
    Attribue un conseiller à un prospect qui n'en a pas (spécification §10 : « attribue un conseiller »).

    Choisit le conseiller actif qui a le MOINS de prospects ouverts (répartition équitable). N'écrit rien si le
    prospect a déjà un conseiller ou s'il n'existe aucun conseiller actif. N'enregistre pas : l'appelant fait lead.save().
    """
    if lead.assigned_agent_id is not None:
        return
    from django.db.models import Count, Q

    from apps.users.infrastructure.models import User, UserRole

    agent = (
        User.objects.filter(role=UserRole.AGENT, is_active=True)
        .annotate(open_leads=Count("assigned_crm_leads", filter=~Q(assigned_crm_leads__stage__in=["VENTE", "PERDU"])))
        .order_by("open_leads", "date_joined")
        .first()
    )
    if agent is not None:
        lead.assigned_agent = agent


def advance_stage(lead: Lead, target: str) -> None:
    """
    Place le prospect à l'étape `target` SEULEMENT si c'est plus avancé que son étape actuelle.

        advance_stage(lead, "RDV")   # lead en "CONTACTE"  → devient "RDV"
        advance_stage(lead, "RDV")   # lead en "VISITE"    → reste "VISITE" (on ne recule jamais)
        advance_stage(lead, "PERDU") # toujours accepté : « Perdu » est une sortie du pipeline

    Pourquoi : une demande de visite ne doit pas faire repasser en « RDV fixé » un prospect déjà en négociation.
    Ne retourne rien et n'écrit pas en base : modifie `lead.stage` en mémoire, l'appelant fait lead.save().
    Pour faire reculer volontairement un prospect, l'équipe le déplace à la main (écran kanban).
    """
    if target == PipelineStage.PERDU:
        lead.stage = target
        return
    current = STAGE_ORDER.index(lead.stage) if lead.stage in STAGE_ORDER else -1
    if STAGE_ORDER.index(target) > current:
        lead.stage = target


def rescore(lead: Lead) -> None:
    """
    Recalcule le SCORE (0–100) et la TEMPÉRATURE du prospect d'après ce que l'on sait de lui.

    Le calcul des points est dans LeadScoringDomainService.calculate_score (scoring_service.py) :
        budget confirmé +20 · apport confirmé +20 · délai < 3 mois +20 · bien identifié +15
        · demande de visite +15 · interaction récente (30 jours) +10   → plafonné à 100
        température : ≥ 90 TRES_CHAUD · ≥ 70 CHAUD · ≥ 40 TIEDE · sinon FROID

    Cette fonction se contente de RASSEMBLER les faits depuis le prospect (lecture), de les passer au calcul,
    puis de ranger le résultat dans lead.score et lead.temperature. Elle n'écrit PAS en base : appeler lead.save()
    (ou lead.save(update_fields=["score", "temperature"])) ensuite.

    Le score est « cumulatif » : il repart toujours des faits connus, il ne baisse donc pas à chaque action.
    À appeler après tout changement qui peut influer : budget, apport, visite demandée, bien consulté, étape…
    """
    timeframe = (lead.timeframe or "").lower()
    score, temperature = LeadScoringDomainService.calculate_score(
        has_confirmed_budget=bool(lead.budget),
        has_confirmed_down_payment=bool(lead.down_payment and lead.down_payment > 0),
        timeframe_under_3_months=any(m in timeframe for m in SHORT_TIMEFRAME_MARKERS),
        # lead.inquiries / lead.visits : relations inverses (≈ OneToMany Doctrine). .exists() = SELECT 1 … LIMIT 1,
        # une requête très légère qui répond seulement « y en a-t-il au moins un ? ».
        has_identified_property=bool(lead.consulted_property_id) or lead.inquiries.exists(),
        has_visit_request=lead.visits.exists(),
        has_recent_interaction=bool(lead.last_interaction_at and (timezone.now() - lead.last_interaction_at).days <= 30)
        or lead.pk is None,
    )
    lead.score, lead.temperature = score, temperature
