"""
Scénarios de démonstration pour tourner des vidéos : chaque écran du site et du back-office a de quoi se montrer.

    python manage.py seed_demo_scenarios            # complète la base de démonstration (relançable)
    python manage.py seed_demo_scenarios --export   # puis réexporte fixtures/demo_data.json

À lancer APRÈS `load_demo_data` (ou `seed_data`) : la commande s'appuie sur les comptes et les biens de démonstration.
Toutes les dates sont RELATIVES à aujourd'hui (visites cette semaine, relances en retard, ventes des derniers mois…).

Elle REMPLACE les notifications, les relances, les événements de mesure et les dépenses marketing par un jeu cohérent :
les anciens (souvent des restes de tests) rendraient les statistiques et les cloches illisibles à l'écran.
Refuse de tourner quand DEBUG=False (sauf --force).
"""

import random
from datetime import time, timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.accreditation.domain import services as accreditation
from apps.accreditation.infrastructure.models import (
    AccreditationFile,
    AccreditationStatus,
    DocumentType,
    Notary,
    PropertyDocument,
)
from apps.analytics.domain import events as ev
from apps.analytics.infrastructure.models import AnalyticsEvent, ChannelSpend
from apps.crm.domain.lead_service import rescore
from apps.crm.infrastructure.models import (
    AlertFrequency,
    CRMInteraction,
    Lead,
    PipelineStage,
    PropertyInquiry,
    SearchAlert,
    VisitRequest,
    VisitRequestStatus,
    VisitRequestType,
)
from apps.notifications.domain import kinds
from apps.notifications.infrastructure.models import FollowUpStatus, FollowUpTask, Notification
from apps.properties.infrastructure.models import (
    DevelopmentProject,
    ProjectDocument,
    ProjectDocumentKind,
    Property,
    PropertyFavorite,
    PropertyStatus,
)

User = get_user_model()
PDF = b"%PDF-1.4\n1 0 obj<</Type/Catalog>>endobj\ntrailer<</Root 1 0 R>>\n%%EOF"

# Prospects de démonstration : (nom, téléphone, canal, source, étape, objectif, budget, apport, délai, zone,
#   conseiller, bien (référence), créé il y a N jours, vendu il y a N jours, pays)
LEADS = [
    (
        "Aïcha Diomandé",
        "+2250799000001",
        "FACEBOOK",
        "SITE_WEB",
        "NOUVEAU",
        "Habiter",
        45_000_000,
        5_000_000,
        "6 mois",
        "Cocody",
        "aminata",
        "THI-2026-012",
        1,
        None,
        None,
    ),
    (
        "Boris Zadi",
        "+2250799000002",
        "GOOGLE",
        "SIMULATEUR",
        "NOUVEAU",
        "Investir",
        120_000_000,
        30_000_000,
        "3 mois",
        "Marcory",
        None,
        "THI-2026-003",
        2,
        None,
        None,
    ),
    (
        "Clarisse N'Dri",
        "+2250799000003",
        "INSTAGRAM",
        "DEMANDE_INFO",
        "CONTACTE",
        "Louer",
        600_000,
        None,
        "1 mois",
        "Plateau",
        "koffi",
        "THI-2026-009",
        4,
        None,
        None,
    ),
    (
        "Didier Kouadio",
        "+2250799000004",
        "SITE_WEB",
        "TROUVER_MON_BIEN",
        "QUALIFIE",
        "Habiter",
        75_000_000,
        15_000_000,
        "2 mois",
        "Bingerville",
        "aminata",
        "THI-2026-011",
        6,
        None,
        None,
    ),
    (
        "Estelle Gbané",
        "+33612000005",
        "FACEBOOK",
        "ESPACE_DIASPORA",
        "QUALIFIE",
        "Investir",
        90_000_000,
        40_000_000,
        "3 mois",
        "Cocody",
        "koffi",
        "THI-2026-002",
        8,
        None,
        "France",
    ),
    (
        "Franck Ouédraogo",
        "+2250799000006",
        "WHATSAPP",
        "WHATSAPP",
        "RDV",
        "Habiter",
        66_000_000,
        20_000_000,
        "1 mois",
        "Abatta",
        "aminata",
        "THI-2026-001",
        10,
        None,
        None,
    ),
    (
        "Grâce Aka",
        "+14385000007",
        "LINKEDIN",
        "ESPACE_DIASPORA",
        "VISITE",
        "Investir",
        150_000_000,
        60_000_000,
        "4 mois",
        "Riviera",
        "koffi",
        "THI-2026-006",
        12,
        None,
        "Canada",
    ),
    (
        "Hugues Tano",
        "+2250799000008",
        "PARRAINAGE",
        "SITE_WEB",
        "PROPOSITION",
        "Habiter",
        285_000_000,
        80_000_000,
        "2 mois",
        "Riviera Golf",
        "aminata",
        "THI-2026-011",
        15,
        None,
        None,
    ),
    (
        "Inès Koffi",
        "+2250799000009",
        "GOOGLE",
        "SITE_WEB",
        "NEGOCIATION",
        "Investir",
        85_000_000,
        25_000_000,
        "1 mois",
        "Marcory",
        "koffi",
        "THI-2026-003",
        18,
        None,
        None,
    ),
    (
        "Jacques Amani",
        "+2250799000010",
        "CAMPAGNE",
        "APPLICATION",
        "RESERVATION",
        "Habiter",
        72_000_000,
        22_000_000,
        "1 mois",
        "Bingerville",
        "aminata",
        "THI-2026-012",
        22,
        None,
        None,
    ),
    (
        "Karim Sidibé",
        "+2250799000011",
        "SITE_WEB",
        "SITE_WEB",
        "VENTE",
        "Habiter",
        66_000_000,
        20_000_000,
        "1 mois",
        "Abatta",
        "aminata",
        "THI-2026-001",
        60,
        8,
        None,
    ),
    (
        "Laure Bakayoko",
        "+2250799000012",
        "GOOGLE",
        "SIMULATEUR",
        "VENTE",
        "Investir",
        98_000_000,
        30_000_000,
        "2 mois",
        "Riviera",
        "koffi",
        "THI-2026-006",
        75,
        24,
        None,
    ),
    (
        "Mamadou Cissé",
        "+2250799000013",
        "FACEBOOK",
        "DEMANDE_INFO",
        "VENTE",
        "Investir",
        42_000_000,
        10_000_000,
        "2 mois",
        "Grand-Bassam",
        "koffi",
        "THI-2026-004",
        95,
        41,
        None,
    ),
    (
        "Nadège Traoré",
        "+33699000014",
        "FACEBOOK",
        "ESPACE_DIASPORA",
        "VENTE",
        "Habiter",
        320_000_000,
        120_000_000,
        "3 mois",
        "Cocody",
        "aminata",
        "THI-2026-005",
        110,
        58,
        "France",
    ),
    (
        "Olivier Yao",
        "+2250799000015",
        "WHATSAPP",
        "WHATSAPP",
        "PERDU",
        "Habiter",
        30_000_000,
        None,
        "6 mois",
        "Yopougon",
        "koffi",
        None,
        30,
        None,
        None,
    ),
    (
        "Priscilla Kra",
        "+2250799000016",
        "INSTAGRAM",
        "SITE_WEB",
        "PERDU",
        "Louer",
        400_000,
        None,
        "1 mois",
        "Plateau",
        "aminata",
        None,
        40,
        None,
        None,
    ),
]

# Source du prospect → canal d'acquisition des prospects déjà présents sans canal.
SOURCE_TO_CHANNEL = {
    "APPLICATION": "APPLICATION",
    "SITE_WEB": "SITE_WEB",
    "WHATSAPP": "WHATSAPP",
    "TROUVER_MON_BIEN": "SITE_WEB",
    "ESPACE_DIASPORA": "FACEBOOK",
    "SIMULATEUR": "GOOGLE",
    "DEMANDE_INFO": "INSTAGRAM",
    "VISITE": "SITE_WEB",
}

PROJECT_SCHEDULES = [
    (
        [
            ("Réservation", 10),
            ("Signature du contrat", 20),
            ("Achèvement des fondations", 20),
            ("Gros œuvre terminé", 25),
            ("Livraison", 25),
        ],
        "Paiement par virement ou chèque de banque. Les frais de notaire sont à la charge de l'acquéreur.",
    ),
    (
        [("Réservation", 15), ("Signature de l'acte", 35), ("Hors d'eau, hors d'air", 30), ("Remise des clés", 20)],
        "Un échéancier personnalisé est possible pour la diaspora : contactez votre conseiller.",
    ),
    ([("Réservation", 20), ("Contrat de vente", 30), ("Mi-chantier", 30), ("Livraison", 20)], ""),
]


def _at(days_ago: int, hour: int = 10, minute: int = 0):
    base = timezone.localtime() - timedelta(days=days_ago)
    return base.replace(hour=hour, minute=minute, second=0, microsecond=0)


class Command(BaseCommand):
    help = "Complète la base de démonstration avec des scénarios riches (relançable ; dates relatives à aujourd'hui)."

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true", help="Autoriser l'exécution quand DEBUG=False.")
        parser.add_argument("--export", action="store_true", help="Réexporter fixtures/demo_data.json à la fin.")
        parser.add_argument("--seed", type=int, default=2026, help="Graine du générateur de la mesure d'audience.")

    def handle(self, *args, **options):
        if not settings.DEBUG and not options["force"]:
            raise CommandError("Refus : DEBUG=False (production ?). Utiliser --force si c'est volontaire.")
        # Les e-mails de notification ne doivent pas partir pendant le remplissage.
        settings.NOTIFICATIONS_FORCE = False
        self.rng = random.Random(options["seed"])
        with transaction.atomic():
            self.users = {
                "aminata": User.objects.filter(email="aminata.agent@thiebbro.ci").first(),
                "koffi": User.objects.filter(email="koffi.agent@thiebbro.ci").first(),
                "admin": User.objects.filter(email="admin@thiebbro.ci").first(),
                "awa": User.objects.filter(email="awa.traore@mail.ci").first(),
                "paul": User.objects.filter(email="p.kacou@mail.ci").first(),
            }
            if not all(self.users.values()):
                raise CommandError("Comptes de démonstration absents : lancer d'abord `load_demo_data` ou `seed_data`.")
            self.props = {p.reference: p for p in Property.objects.all()}
            self.clean_test_leftovers()
            self.leads()
            self.inquiries()
            self.visits()
            self.followups()
            self.alerts_and_favorites()
            self.marketing()
            self.projects()
            self.accreditations()
            self.measurement()
            self.notifications()
        if options["export"]:
            call_command("export_demo_data")
        self.stdout.write(self.style.SUCCESS("Scénarios de démonstration prêts."))

    # ------------------------------------------------------------------ nettoyage

    def clean_test_leftovers(self):
        Property.objects.filter(title__icontains="E2E").delete()
        User.objects.filter(email__contains="e2e-").delete()
        Lead.objects.filter(full_name__icontains="E2E").delete()
        self.props = {p.reference: p for p in Property.objects.all()}

    # ------------------------------------------------------------------ CRM

    def leads(self):
        agents = {"aminata": self.users["aminata"], "koffi": self.users["koffi"], None: None}
        for (
            name,
            phone,
            channel,
            source,
            stage,
            objective,
            budget,
            down,
            timeframe,
            zone,
            agent,
            ref,
            created,
            sold,
            country,
        ) in LEADS:
            lead, _ = Lead.objects.get_or_create(phone_number=phone, defaults={"full_name": name})
            lead.full_name = name
            lead.acquisition_channel = channel
            lead.source = source
            lead.stage = stage
            lead.objective = objective
            lead.budget = budget
            lead.down_payment = down
            lead.timeframe = timeframe
            lead.preferred_zone = zone
            lead.assigned_agent = agents[agent]
            lead.consulted_property = self.props.get(ref)
            lead.country_of_residence = country or "Côte d'Ivoire"
            lead.is_diaspora = bool(country)
            lead.utm_source = {
                "FACEBOOK": "facebook",
                "GOOGLE": "google",
                "INSTAGRAM": "instagram",
                "LINKEDIN": "linkedin",
            }.get(channel, "")
            lead.utm_medium = "cpc" if channel in ("FACEBOOK", "GOOGLE", "INSTAGRAM", "LINKEDIN") else ""
            lead.utm_campaign = "lancement-riviera" if lead.utm_source else ""
            lead.landing_path = f"/biens/{lead.consulted_property.slug}" if lead.consulted_property else "/"
            lead.converted_at = _at(sold, 15) if sold else None
            rescore(lead)
            lead.save()
            # Dates relatives (auto_now_add / auto_now : on passe par update).
            Lead.objects.filter(pk=lead.pk).update(
                created_at=_at(created, 9), last_interaction_at=_at(max(created - 2, 0), 16)
            )
            if not lead.interactions.exists():
                for kind, text, back in [
                    ("INQUIRY", "Demande d'informations reçue.", created),
                    ("CALL", "Premier appel : projet confirmé.", max(created - 1, 0)),
                ]:
                    i = CRMInteraction.objects.create(lead=lead, interaction_type=kind, details=text)
                    CRMInteraction.objects.filter(pk=i.pk).update(created_at=_at(back, 11))
        # Prospects déjà présents sans canal d'acquisition : on le déduit de leur source.
        for lead in Lead.objects.filter(acquisition_channel="AUTRE"):
            mapped = SOURCE_TO_CHANNEL.get(lead.source)
            if mapped:
                Lead.objects.filter(pk=lead.pk).update(acquisition_channel=mapped)
        # Prospects antérieurs à ce jeu : on étale leurs dates de création pour que les courbes mensuelles aient du relief.
        mine = {row[1] for row in LEADS} | {"+2250707556699"}
        for i, lead in enumerate(Lead.objects.exclude(phone_number__in=mine).order_by("full_name")):
            Lead.objects.filter(pk=lead.pk).update(created_at=_at(4 + i * 6, 9))

    def inquiries(self):
        samples = [
            (
                "+2250799000001",
                "THI-2026-012",
                "Habiter",
                "Bonjour, la maison est-elle toujours disponible ? Peut-on négocier le prix ?",
                False,
                1,
            ),
            (
                "+2250799000002",
                "THI-2026-003",
                "Investir",
                "Quel est le loyer actuel de la résidence meublée ?",
                False,
                2,
            ),
            ("+2250799000003", "THI-2026-009", "Louer", "L'appartement accepte-t-il les animaux ?", False, 4),
            (
                "+2250799000004",
                "THI-2026-011",
                "Habiter",
                "Pouvez-vous m'envoyer le plan et le titre foncier ?",
                True,
                6,
            ),
            ("+33612000005", "THI-2026-002", "Investir", "Je vis en France : visite en visio possible ?", True, 8),
            ("+2250799000006", "THI-2026-001", "Habiter", "Disponible pour une visite samedi matin ?", True, 10),
        ]
        for phone, ref, objective, message, processed, ago in samples:
            lead, prop = Lead.objects.filter(phone_number=phone).first(), self.props.get(ref)
            if not lead or not prop:
                continue
            inquiry, _ = PropertyInquiry.objects.get_or_create(
                lead=lead, property=prop, defaults={"objective": objective}
            )
            inquiry.objective, inquiry.message, inquiry.is_processed = objective, message, processed
            inquiry.save()
            PropertyInquiry.objects.filter(pk=inquiry.pk).update(created_at=_at(ago, 14))

    def visits(self):
        today = timezone.localdate()
        # (téléphone, bien, type, statut, décalage en jours, heure)
        plan = [
            ("+2250799000006", "THI-2026-001", VisitRequestType.PHYSIQUE, VisitRequestStatus.CONFIRMEE, 0, time(15, 0)),
            (
                "+2250799000004",
                "THI-2026-011",
                VisitRequestType.PHYSIQUE,
                VisitRequestStatus.EN_ATTENTE,
                1,
                time(10, 30),
            ),
            ("+33612000005", "THI-2026-002", VisitRequestType.VISIO, VisitRequestStatus.CONFIRMEE, 2, time(18, 0)),
            (
                "+14385000007",
                "THI-2026-006",
                VisitRequestType.VISITE_3D,
                VisitRequestStatus.EN_ATTENTE,
                3,
                time(19, 30),
            ),
            ("+2250799000008", "THI-2026-011", VisitRequestType.PHYSIQUE, VisitRequestStatus.CONFIRMEE, 4, time(9, 0)),
            (
                "+2250799000009",
                "THI-2026-003",
                VisitRequestType.PHYSIQUE,
                VisitRequestStatus.EFFECTUEE,
                -3,
                time(11, 0),
            ),
            (
                "+2250799000010",
                "THI-2026-012",
                VisitRequestType.PHYSIQUE,
                VisitRequestStatus.EFFECTUEE,
                -6,
                time(16, 0),
            ),
            ("+2250799000003", "THI-2026-009", VisitRequestType.PHYSIQUE, VisitRequestStatus.ANNULEE, -2, time(14, 0)),
        ]
        for phone, ref, vtype, status, offset, at in plan:
            lead, prop = Lead.objects.filter(phone_number=phone).first(), self.props.get(ref)
            if not lead or not prop:
                continue
            when = today + timedelta(days=offset)
            visit, _ = VisitRequest.objects.get_or_create(
                lead=lead, property=prop, defaults={"scheduled_date": when, "scheduled_time": at}
            )
            visit.visit_type, visit.status, visit.scheduled_date, visit.scheduled_time = vtype, status, when, at
            visit.notes = "Demande créée depuis la fiche du bien." if status == VisitRequestStatus.EN_ATTENTE else ""
            visit.save()
        # Les visites de la cliente de démonstration (Awa) apparaissent dans « Mes demandes ».
        awa_lead, _ = Lead.objects.get_or_create(phone_number="+2250707556699", defaults={"full_name": "Awa Traoré"})
        awa_lead.user = self.users["awa"]
        awa_lead.full_name = "Awa Traoré"
        awa_lead.email = self.users["awa"].email
        awa_lead.stage = PipelineStage.RDV
        awa_lead.assigned_agent = self.users["aminata"]
        awa_lead.acquisition_channel = "SITE_WEB"
        awa_lead.source = "SITE_WEB"
        awa_lead.budget = 70_000_000
        rescore(awa_lead)
        awa_lead.save()
        for ref, status, offset, at in [
            ("THI-2026-012", VisitRequestStatus.CONFIRMEE, 2, time(11, 0)),
            ("THI-2026-001", VisitRequestStatus.EN_ATTENTE, 5, time(16, 30)),
        ]:
            prop = self.props.get(ref)
            if prop:
                v, _ = VisitRequest.objects.get_or_create(
                    lead=awa_lead,
                    property=prop,
                    defaults={"scheduled_date": today + timedelta(days=offset), "scheduled_time": at},
                )
                v.user, v.status, v.scheduled_date, v.scheduled_time = (
                    self.users["awa"],
                    status,
                    today + timedelta(days=offset),
                    at,
                )
                v.save()
        if prop := self.props.get("THI-2026-002"):
            inquiry, _ = PropertyInquiry.objects.get_or_create(
                lead=awa_lead, property=prop, defaults={"objective": "Habiter"}
            )
            inquiry.user, inquiry.message = self.users["awa"], "Je souhaite des précisions sur les charges de la villa."
            inquiry.save()

    def followups(self):
        FollowUpTask.objects.all().delete()
        today = timezone.localdate()
        items = [
            ("+2250799000003", "koffi", "Aucune activité depuis 4 jours", -2, FollowUpStatus.OUVERTE),
            ("+2250799000005", "aminata", "Envoyer la brochure du programme", -1, FollowUpStatus.OUVERTE),
            ("+2250799000002", "aminata", "Rappeler pour confirmer le budget", 0, FollowUpStatus.OUVERTE),
            ("+33612000005", "koffi", "Proposer une visite en visio ce week-end", 0, FollowUpStatus.OUVERTE),
            ("+2250799000008", "aminata", "Relancer après la visite", 2, FollowUpStatus.OUVERTE),
            ("+2250799000001", "aminata", "Premier contact téléphonique", 1, FollowUpStatus.OUVERTE),
            ("+2250799000006", "aminata", "Envoyer le contrat de réservation", -4, FollowUpStatus.FAITE),
            ("+2250799000009", "koffi", "Confirmer l'offre auprès du propriétaire", -3, FollowUpStatus.FAITE),
        ]
        for phone, agent, reason, offset, status in items:
            lead = Lead.objects.filter(phone_number=phone).first()
            if not lead:
                continue
            t = FollowUpTask.objects.create(
                lead=lead,
                assigned_to=self.users[agent],
                reason=reason,
                due_date=today + timedelta(days=offset),
                status=status,
            )
            if status == FollowUpStatus.FAITE:
                FollowUpTask.objects.filter(pk=t.pk).update(completed_at=_at(abs(offset), 12))

    # ------------------------------------------------------------------ client

    def alerts_and_favorites(self):
        awa, paul = self.users["awa"], self.users["paul"]
        for user, criteria in [
            (
                awa,
                dict(
                    transaction="VENTE",
                    property_type="VILLA",
                    commune="Cocody",
                    max_budget=300_000_000,
                    frequency=AlertFrequency.IMMEDIATE,
                ),
            ),
            (
                awa,
                dict(
                    transaction="LOCATION",
                    property_type="",
                    commune="Plateau",
                    max_budget=1_000_000,
                    frequency=AlertFrequency.IMMEDIATE,
                ),
            ),
            (
                paul,
                dict(
                    transaction="VENTE",
                    property_type="TERRAIN",
                    commune="Bingerville",
                    max_budget=60_000_000,
                    frequency=AlertFrequency.IMMEDIATE,
                ),
            ),
        ]:
            SearchAlert.objects.get_or_create(
                user=user, commune=criteria["commune"], transaction=criteria["transaction"], defaults=criteria
            )
        for user, refs in [
            (awa, ["THI-2026-012", "THI-2026-002", "THI-2026-011", "THI-2026-009", "THI-2026-007"]),
            (paul, ["THI-2026-004", "THI-2026-010", "THI-2026-005"]),
        ]:
            for ref in refs:
                if prop := self.props.get(ref):
                    PropertyFavorite.objects.get_or_create(user=user, property=prop)

    # ------------------------------------------------------------------ marketing et mesure

    def marketing(self):
        ChannelSpend.objects.all().delete()
        first = timezone.localdate().replace(day=1)
        budgets = {
            "FACEBOOK": 450_000,
            "GOOGLE": 600_000,
            "INSTAGRAM": 250_000,
            "LINKEDIN": 180_000,
            "CAMPAGNE": 300_000,
        }
        for months_back in range(0, 4):
            month = (first - timedelta(days=30 * months_back)).replace(day=1)
            for channel, amount in budgets.items():
                ChannelSpend.objects.update_or_create(
                    channel=channel,
                    month=month,
                    defaults={"amount": amount, "note": "Budget publicitaire (démonstration)"},
                )

    def measurement(self):
        """Sessions, recherches, vues… sur 60 jours, avec une courbe crédible (week-ends plus calmes, campagne récente)."""
        AnalyticsEvent.objects.all().delete()
        channels = ["SITE_WEB", "GOOGLE", "FACEBOOK", "INSTAGRAM", "WHATSAPP", "LINKEDIN", "AUTRE"]
        weights = [30, 22, 18, 10, 10, 4, 6]
        refs = list(self.props)
        batch, stamps = [], {}
        for ago in range(60, -1, -1):
            day = _at(ago, 0)
            weekend = day.weekday() >= 5
            growth = 1 + (60 - ago) / 60  # l'audience double sur deux mois
            sessions = int(self.rng.randint(35, 60) * growth * (0.6 if weekend else 1))
            for s in range(sessions):
                anon = f"demo-{ago}-{s}"
                channel = self.rng.choices(channels, weights)[0]
                at = day.replace(hour=self.rng.randint(7, 22), minute=self.rng.randint(0, 59))

                def add(name, path="/", props=None, user=None):
                    e = AnalyticsEvent(
                        name=name, anonymous_id=anon, channel=channel, path=path, properties=props or {}, user=user
                    )
                    batch.append(e)
                    stamps[e.pk] = at + timedelta(seconds=len(batch) % 600)

                add(ev.SESSION_START)
                if self.rng.random() < 0.7:
                    add(
                        ev.SEARCH,
                        "/biens",
                        {"q": self.rng.choice(["Cocody", "Bingerville", "Villa", "Terrain", "Marcory"])},
                    )
                for _ in range(self.rng.choice([0, 1, 1, 2, 3])):
                    add(ev.PROPERTY_VIEW, "/biens", {"property": self.rng.choice(refs)})
                r = self.rng.random()
                if r < 0.06:
                    add(ev.SIMULATION_CAPACITY, "/capacite-achat")
                elif r < 0.10:
                    add(ev.SIMULATION_RENTABILITY, "/investir/simulateur")
                if self.rng.random() < 0.05:
                    add(ev.FAVORITE_ADD)
                if self.rng.random() < 0.03:
                    add(ev.WHATSAPP_CLICK)
                if self.rng.random() < 0.025:
                    add(ev.SIGNUP)
                if self.rng.random() < 0.012:
                    add(ev.APP_INSTALLED)
        # Événements de conversion alignés sur les prospects réels.
        for lead in Lead.objects.all():
            e = AnalyticsEvent(
                name=ev.LEAD_CREATED, anonymous_id=f"lead-{lead.pk}", channel=lead.acquisition_channel, path="/"
            )
            batch.append(e)
            stamps[e.pk] = lead.created_at
            if lead.converted_at:
                e2 = AnalyticsEvent(
                    name=ev.SALE, anonymous_id=f"lead-{lead.pk}", channel=lead.acquisition_channel, path="/"
                )
                batch.append(e2)
                stamps[e2.pk] = lead.converted_at
        for visit in VisitRequest.objects.all():
            e = AnalyticsEvent(
                name=ev.VISIT_REQUESTED,
                anonymous_id=f"visit-{visit.pk}",
                channel=visit.lead.acquisition_channel,
                path="/",
            )
            batch.append(e)
            stamps[e.pk] = visit.created_at
        for inquiry in PropertyInquiry.objects.all():
            e = AnalyticsEvent(
                name=ev.INQUIRY, anonymous_id=f"inq-{inquiry.pk}", channel=inquiry.lead.acquisition_channel, path="/"
            )
            batch.append(e)
            stamps[e.pk] = inquiry.created_at
        AnalyticsEvent.objects.bulk_create(batch, batch_size=1000)
        by_time = {}
        for pk, when in stamps.items():
            by_time.setdefault(when, []).append(pk)
        for when, pks in by_time.items():
            AnalyticsEvent.objects.filter(pk__in=pks).update(occurred_at=when)

    # ------------------------------------------------------------------ programmes et accréditations

    def projects(self):
        for project, (schedule, notes) in zip(
            DevelopmentProject.objects.order_by("name"), PROJECT_SCHEDULES * 2, strict=False
        ):
            project.payment_schedule = [{"label": label, "percent": pct} for label, pct in schedule]
            project.payment_notes = notes
            project.save()
            if not project.documents.exists():
                for kind, title in [
                    (ProjectDocumentKind.PLAN, "Plan de masse"),
                    (ProjectDocumentKind.PLAN, "Plan type F3"),
                    (ProjectDocumentKind.DOCUMENT, "Brochure commerciale"),
                ]:
                    doc = ProjectDocument(project=project, kind=kind, title=title)
                    doc.file.save(f"{title.lower().replace(' ', '-')}.pdf", ContentFile(PDF), save=True)

    def accreditations(self):
        """Dossiers à tous les stades : pièces manquantes, contrôle en cours, refus motivé, brouillon du propriétaire."""
        owner = User.objects.filter(email="k.yao@mail.ci").first()
        notary = Notary.objects.filter(user__email="a.kone@notaire.ci").first() or Notary.objects.first()
        if not owner:
            return

        def prop(title, status, **extra):
            defaults = dict(
                description="Bien de démonstration créé pour illustrer le parcours d'accréditation.",
                property_type="VILLA",
                price=95_000_000,
                commune="Cocody",
                neighborhood="Angré",
                surface_sqm=180,
                owner=owner,
                status=status,
            )
            defaults.update(extra)
            p, _ = Property.objects.get_or_create(title=title, defaults=defaults)
            return p

        draft = prop("Villa 4 pièces à Angré (brouillon)", PropertyStatus.BROUILLON)
        draft.verification_status = "NON_VERIFIE"
        draft.save()

        missing = prop(
            "Appartement F4 Riviera 3 (pièces à compléter)",
            PropertyStatus.EN_ATTENTE,
            property_type="APPARTEMENT",
            price=120_000_000,
            neighborhood="Riviera 3",
            surface_sqm=140,
        )
        file = accreditation.ensure_file(missing)
        file.notary = notary
        file.save()
        if not missing.documents.exists():
            d = PropertyDocument(property=missing, doc_type=DocumentType.TITRE)
            d.file.save("titre-foncier.pdf", ContentFile(PDF), save=True)

        refused = prop(
            "Terrain 800 m² Songon (dossier refusé)",
            PropertyStatus.EN_ATTENTE,
            property_type="TERRAIN",
            price=40_000_000,
            neighborhood="Songon",
            surface_sqm=800,
        )
        file = accreditation.ensure_file(refused)
        file.notary = notary
        file.save()
        for t in (DocumentType.TITRE, DocumentType.IDENTITE, DocumentType.PLAN):
            if not refused.documents.filter(doc_type=t).exists():
                d = PropertyDocument(property=refused, doc_type=t)
                d.file.save(f"{t.lower()}.pdf", ContentFile(PDF), save=True)
        refused.documents.filter(doc_type=DocumentType.TITRE).update(
            status="REJETE", comment="Titre foncier illisible : merci de scanner à nouveau."
        )
        if AccreditationFile.objects.get(property=refused).status != AccreditationStatus.REFUSE:
            accreditation.refuse(
                AccreditationFile.objects.get(property=refused),
                "Titre foncier illisible : merci de déposer un scan net.",
            )

    # ------------------------------------------------------------------ notifications

    def notifications(self):
        Notification.objects.all().delete()
        awa, paul = self.users["awa"], self.users["paul"]

        def add(user, kind, title, body, url, ago_h, read=False):
            n = Notification.objects.create(
                user=user, kind=kind, title=title, body=body, url=url, emailed_at=timezone.now()
            )
            when = timezone.now() - timedelta(hours=ago_h)
            Notification.objects.filter(pk=n.pk).update(
                created_at=when, read_at=when + timedelta(hours=1) if read else None
            )

        add(
            awa,
            kinds.VISIT_CONFIRMED,
            "Visite confirmée",
            "Votre visite de la Maison familiale 5 pièces est confirmée dans 2 jours à 11 h.",
            "/espace/demandes",
            2,
        )
        add(
            awa,
            kinds.NEW_MATCH,
            "Nouveau bien pour votre recherche",
            "Villa contemporaine 6 pièces Riviera Golf correspond à votre alerte (Cocody, villa).",
            "/biens/villa-contemporaine-6-pieces-riviera-golf",
            20,
        )
        add(
            awa,
            kinds.PRICE_DROP,
            "Baisse de prix sur un favori",
            "Le prix de l'Appartement F4 de standing au Plateau a baissé.",
            "/espace/favoris",
            70,
            read=True,
        )
        add(
            paul,
            kinds.NEW_MATCH,
            "Nouveau terrain à Bingerville",
            "Un terrain de 500 m² correspond à votre alerte.",
            "/biens",
            5,
        )
        leads = {lead.phone_number: lead for lead in Lead.objects.all()}
        for agent, phone, kind, title, body, ago in [
            (
                "aminata",
                "+2250799000001",
                kinds.LEAD_NEW,
                "Nouveau prospect",
                "Aïcha Diomandé demande des informations sur la Maison familiale.",
                3,
            ),
            (
                "aminata",
                "+2250799000004",
                kinds.VISIT_REQUESTED,
                "Demande de visite",
                "Didier Kouadio souhaite visiter demain à 10 h 30.",
                6,
            ),
            (
                "aminata",
                "+2250799000006",
                kinds.LEAD_QUALIFIED,
                "Prospect qualifié",
                "Franck Ouédraogo est chaud : budget et apport confirmés.",
                28,
            ),
            (
                "aminata",
                "+2250799000005",
                kinds.FOLLOWUP_DUE,
                "Relance à effectuer",
                "Estelle Gbané : envoyer la brochure du programme.",
                30,
            ),
            (
                "koffi",
                "+2250799000002",
                kinds.LEAD_NEW,
                "Nouveau prospect",
                "Boris Zadi arrive du simulateur de rentabilité.",
                4,
            ),
            (
                "koffi",
                "+14385000007",
                kinds.VISIT_REQUESTED,
                "Demande de visite 3D",
                "Grâce Aka (Canada) demande une visite 3D guidée.",
                9,
            ),
            (
                "koffi",
                "+2250799000003",
                kinds.FOLLOWUP_DUE,
                "Relance en retard",
                "Clarisse N'Dri : aucune activité depuis 4 jours.",
                26,
            ),
        ]:
            lead = leads.get(phone)
            if lead:
                add(self.users[agent], kind, title, body, f"/admin/crm?lead={lead.pk}", ago)
        add(
            self.users["admin"],
            kinds.LEAD_NEW,
            "Nouveau prospect à assigner",
            "Boris Zadi n'a pas encore de conseiller.",
            "/admin/crm",
            4,
        )
