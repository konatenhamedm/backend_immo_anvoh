"""
Données de démonstration complètes (catalogue, propriétaires, notaires, CRM, accréditations, investissements,
gestion locative, messagerie), alignées sur la maquette du site Next.js.

Sécurité :
- refuse de tourner quand DEBUG=False, sauf --force ;
- aucun mot de passe en dur : SEED_PASSWORD (variable d'environnement) ou mot de passe aléatoire affiché une fois.

Usage : python manage.py seed_data            (relançable : met à jour sans dupliquer)
"""
import os
import secrets
from datetime import date, time, timedelta
from decimal import Decimal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.users.infrastructure.models import UserRole, ProjectObjective, ProjectTimeframe, IdentityStatus
from apps.properties.infrastructure.models import (
    Property, PropertyImage, PropertyType, PropertyTypology, PropertyGoal, PropertyStatus, VerificationStatus,
    DevelopmentProject, ProjectLot, TransactionType, TitleDeedType,
)
from apps.crm.infrastructure.models import (
    Lead, LeadSource, PipelineStage, VisitRequest, VisitRequestType, VisitRequestStatus, CRMInteraction,
)
from apps.crm.domain.lead_service import rescore
from apps.accreditation.infrastructure.models import (
    Notary, AccreditationFile, AccreditationStatus, PropertyDocument, DocumentType,
)
from apps.investments.infrastructure.models import (
    InvestmentPlan, PlanRisk, PaymentMethod, ScheduleEntry, EntryKind, EntryStatus, Subscription,
)
from apps.investments.domain.services import subscribe, confirm_payment, add_months
from apps.rentals.infrastructure.models import Lease, RentPayment, RentStatus, OwnerPayout, PayoutStatus
from apps.messaging.infrastructure.models import Conversation, ConversationParticipant, Message

User = get_user_model()


def u(photo_id: str, w: int = 1600) -> str:
    return f"https://images.unsplash.com/{photo_id}?auto=format&fit=crop&w={w}&q=80"


IMG = {
    'villaPool': u("photo-1613490493576-7fde63acd811"), 'modernHouse': u("photo-1600596542815-ffad4c1539a9"),
    'houseFacade': u("photo-1600585154340-be6161a56a0c"), 'villaEvening': u("photo-1512917774080-9991f1c4c750"),
    'whiteHouse': u("photo-1564013799919-ab600027ffc6"), 'suburbHouse': u("photo-1580587771525-78b9dba3b914"),
    'livingRoom': u("photo-1502672260266-1c1ef2d93688"), 'apartment': u("photo-1522708323590-d24dbb6b0267"),
    'interior': u("photo-1560448204-e02f11c3d0e2"), 'kitchen': u("photo-1556909114-f6e7ad7d3136"),
    'bedroom': u("photo-1505693416388-ac5ce068fe85"), 'building': u("photo-1545324418-cc1a3fa10c00"),
    'land': u("photo-1500382017468-9049fed747ef"), 'skyline': u("photo-1486406146926-c627a92ad1ab"),
}
MATTERPORT_DEMO = "https://my.matterport.com/show/?m=SxQL3iGyoDo&play=1&qs=1"
FLAG_WORDS = {'gardiennage': 'has_security', 'sécurité': 'has_security', 'groupe électrogène': 'has_generator',
              'parking': 'has_parking', 'piscine': 'has_swimming_pool', 'ascenseur': 'has_elevator', 'jardin': 'has_green_space'}

# Catalogue aligné sur la maquette du front (src/lib/data.ts).
CATALOG = [
    dict(ref="THI-2026-006", slug="duplex-moderne-riviera-palmeraie", title="Duplex moderne 4 pièces Riviera Palmeraie", type="DUPLEX", tx="VENTE", price=98_000_000, commune="Cocody", quartier="Riviera Palmeraie", surface=195, rooms=4, bedrooms=3, baths=3, images=['modernHouse', 'livingRoom', 'kitchen', 'bedroom'], cert="VERIFIE", deed="TITRE_FONCIER", tour=True, yield_=7.95, score=84, views=1284, owner="kouadio", notary="kone", featured=True, typology="F4", goal="HABITATION", agent="aminata", rent=650_000,
         desc="Duplex lumineux en résidence sécurisée, à deux pas du carrefour Palmeraie. Séjour double hauteur, cuisine équipée ouverte, trois suites parentales et une terrasse panoramique. Livré avec titre foncier individuel.",
         amenities=["Gardiennage 24/7", "Groupe électrogène", "Climatisation", "Parking 2 places", "Cuisine équipée", "Terrasse"]),
    dict(ref="THI-2026-005", slug="immeuble-r3-angre-8e-tranche", title="Immeuble R+3 de 8 appartements rentables", type="IMMEUBLE", tx="VENTE", price=320_000_000, commune="Cocody", quartier="Angré 8e Tranche", surface=750, rooms=24, bedrooms=16, baths=16, images=['building', 'apartment', 'interior'], cert="VERIFIE", deed="TITRE_FONCIER", tour=True, yield_=10.5, score=92, views=932, owner="sci", notary="bamba", featured=True, typology="AUTRE", goal="INVESTISSEMENT", agent="koffi", rent=2_800_000, selected=True,
         desc="Immeuble de rapport entièrement loué : 8 appartements F3 avec baux en cours. Revenus locatifs bruts de 2,8 M FCFA par mois. Idéal pour un investisseur cherchant un rendement immédiat.",
         amenities=["Entièrement loué", "Compteurs individuels", "Forage", "Parking 8 places", "Ascenseur"]),
    dict(ref="THI-2026-004", slug="terrain-cloture-acd-grand-bassam", title="Terrain clôturé avec ACD en bordure de voie", type="TERRAIN", tx="VENTE", price=42_000_000, commune="Grand-Bassam", quartier="Mooussou", surface=600, rooms=0, bedrooms=0, baths=0, images=['land'], cert="VERIFICATION_RENFORCEE", deed="ACD", tour=False, yield_=None, score=80, views=611, owner="adjoua", notary="kone", typology="AUTRE", goal="INVESTISSEMENT", agent="aminata", selected=True,
         desc="Parcelle de 600 m² entièrement clôturée, en bordure de voie bitumée. Arrêté de Concession Définitive vérifié auprès du cadastre. Zone en forte valorisation à 5 minutes de la plage.",
         amenities=["Clôturé", "Voie bitumée", "Eau & électricité à proximité", "Bornage effectué"]),
    dict(ref="THI-2026-003", slug="residence-meublee-zone-4", title="Résidence meublée rentable Zone 4", type="RESIDENCE_MEUBLEE", tx="VENTE", price=85_000_000, commune="Marcory", quartier="Zone 4C", surface=65, rooms=2, bedrooms=1, baths=1, images=['interior', 'bedroom', 'kitchen'], cert="VERIFICATION_RENFORCEE", deed="CERTIFICAT_PROPRIETE", tour=True, yield_=12, score=95, views=1540, owner="kouadio", notary="bamba", featured=True, typology="F2", goal="INVESTISSEMENT", agent="koffi", rent=850_000, selected=True,
         desc="Appartement meublé haut standing en location courte durée, taux d'occupation de 82 %. Gestion locative clé en main disponible. Quartier prisé des expatriés.",
         amenities=["Meublé", "Piscine", "Salle de sport", "Fibre optique", "Gestion locative"]),
    dict(ref="THI-2026-002", slug="villa-duplex-jardin-bingerville", title="Villa duplex 5 pièces avec jardin privatif", type="VILLA", tx="VENTE", price=115_000_000, commune="Bingerville", quartier="Feh Kessé", surface=260, rooms=5, bedrooms=4, baths=4, images=['villaEvening', 'livingRoom', 'kitchen', 'bedroom'], cert="VERIFIE", deed="TITRE_FONCIER", tour=True, yield_=7.83, score=82, views=1102, owner="kouadio", notary="kone", typology="F5", goal="HABITATION", agent="aminata", rent=750_000, project="bingerville",
         desc="Villa contemporaine sur 500 m² de terrain avec jardin arboré. Quatre chambres dont une suite au rez-de-chaussée, bureau, buanderie et dépendance pour le personnel.",
         amenities=["Jardin", "Dépendance", "Gardiennage", "Climatisation", "Parking 3 places"]),
    dict(ref="THI-2026-001", slug="appartement-f3-vue-degagee-abatta", title="Appartement F3 moderne avec vue dégagée", type="APPARTEMENT", tx="VENTE", price=66_000_000, commune="Cocody", quartier="Abatta", surface=82, rooms=3, bedrooms=2, baths=2, images=['apartment', 'livingRoom', 'bedroom'], cert="VERIFICATION_RENFORCEE", deed="LETTRE_ATTRIBUTION", tour=False, yield_=8.18, score=88, views=704, owner="ibrahim", notary="bamba", typology="F3", goal="MIXTE", agent="koffi", rent=450_000, project="etoile",
         desc="F3 au 4e étage avec balcon et vue dégagée sur la lagune. Résidence récente avec ascenseur, à proximité des écoles et du nouveau centre commercial.",
         amenities=["Balcon", "Ascenseur", "Vue lagune", "Parking"]),
    dict(ref="THI-2026-007", slug="villa-basse-piscine-assinie", title="Villa basse pieds dans l'eau avec piscine", type="VILLA", tx="LOCATION", price=1_800_000, commune="Assinie", quartier="Assouindé", surface=320, rooms=6, bedrooms=5, baths=5, images=['villaPool', 'livingRoom', 'bedroom'], cert="VERIFIE", deed="TITRE_FONCIER", tour=True, yield_=None, score=90, views=2210, owner="marie", notary="kone", featured=True, typology="F5", goal="LOCATION", agent="aminata",
         desc="Villa d'exception en front de lagune, piscine à débordement, ponton privé. Location mensuelle meublée, personnel de maison inclus.",
         amenities=["Piscine", "Ponton privé", "Meublé", "Personnel inclus", "Wi-Fi"]),
    dict(ref="THI-2026-008", slug="maison-4-pieces-yopougon", title="Maison 4 pièces rénovée avec cour", type="MAISON", tx="LOCATION", price=350_000, commune="Yopougon", quartier="Niangon Nord", surface=140, rooms=4, bedrooms=3, baths=2, images=['suburbHouse', 'kitchen'], cert="EN_COURS", deed="ACD", tour=False, yield_=None, score=71, views=486, owner="kouadio", notary="ouattara", typology="F4", goal="LOCATION", agent="koffi", scan=True,
         desc="Maison entièrement rénovée avec grande cour carrelée, proche des commodités. Disponible immédiatement, caution de 2 mois.",
         amenities=["Cour", "Rénovée", "Compteur individuel"]),
    dict(ref="THI-2026-009", slug="appartement-f4-plateau", title="Appartement F4 de standing au Plateau", type="APPARTEMENT", tx="LOCATION", price=950_000, commune="Plateau", quartier="Boulevard Clozel", surface=128, rooms=4, bedrooms=3, baths=2, images=['livingRoom', 'interior', 'bedroom'], cert="VERIFIE", deed="CERTIFICAT_PROPRIETE", tour=True, yield_=None, score=86, views=812, owner="sci", notary="bamba", typology="F4", goal="LOCATION", agent="koffi",
         desc="Appartement traversant au cœur du quartier des affaires, vue sur la baie de Cocody. Idéal pour cadres et diplomates.",
         amenities=["Vue baie", "Concierge", "Groupe électrogène", "Parking sécurisé"]),
    dict(ref="THI-2026-010", slug="terrain-lotissement-songon", title="Lot de terrain 500 m² dans lotissement viabilisé", type="TERRAIN", tx="VENTE", price=18_500_000, commune="Songon", quartier="Songon Kassemblé", surface=500, rooms=0, bedrooms=0, baths=0, images=['land'], cert="EN_COURS", deed="LETTRE_ATTRIBUTION", tour=False, yield_=None, score=74, views=390, owner="adjoua", notary="kone", typology="AUTRE", goal="INVESTISSEMENT", agent="aminata",
         desc="Lot dans un lotissement approuvé, voiries tracées, électrification en cours. Paiement échelonné possible sur 24 mois.",
         amenities=["Lotissement approuvé", "Paiement échelonné", "Voirie tracée"]),
    dict(ref="THI-2026-011", slug="villa-contemporaine-riviera-golf", title="Villa contemporaine 6 pièces Riviera Golf", type="VILLA", tx="VENTE", price=285_000_000, commune="Cocody", quartier="Riviera Golf", surface=410, rooms=6, bedrooms=5, baths=6, images=['houseFacade', 'livingRoom', 'kitchen', 'bedroom'], cert="VERIFIE", deed="TITRE_FONCIER", tour=True, yield_=6.4, score=89, views=1876, owner="marie", notary="kone", featured=True, typology="F5", goal="HABITATION", agent="aminata", rent=1_500_000,
         desc="Architecture contemporaine en bordure du golf, piscine, domotique, cinq suites. Prestations haut de gamme et matériaux importés.",
         amenities=["Piscine", "Domotique", "Vue golf", "Cave", "Parking 4 places"]),
    dict(ref="THI-2026-012", slug="maison-familiale-bingerville", title="Maison familiale 5 pièces proche du lycée", type="MAISON", tx="VENTE", price=72_000_000, commune="Bingerville", quartier="Akandjé", surface=210, rooms=5, bedrooms=4, baths=3, images=['whiteHouse', 'livingRoom'], cert="VERIFIE", deed="ACD", tour=False, yield_=7.1, score=79, views=544, owner="kouadio", notary="bamba", typology="F5", goal="HABITATION", agent="koffi", rent=425_000,
         desc="Maison de plain-pied sur 450 m², quartier calme et résidentiel. Proche écoles, marché et transport.",
         amenities=["Plain-pied", "Jardin", "Garage", "Forage"]),
]


class Command(BaseCommand):
    help = "Peuple la base avec des données de démonstration complètes et cohérentes avec le site."

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true', help="Autorise l'exécution avec DEBUG=False (jamais en production réelle).")

    @transaction.atomic
    def handle(self, *args, **options):
        if not settings.DEBUG and not options['force']:
            raise CommandError("Données de démonstration refusées avec DEBUG=False. Relancez avec --force si c'est volontaire.")
        password = os.getenv('SEED_PASSWORD') or secrets.token_urlsafe(10)
        self.today = timezone.localdate()

        users = self._users(password)
        notaries = self._notaries(users)
        projects = self._projects()
        props = self._catalog(users, projects)
        self._accreditations(props, notaries)
        leads = self._crm(users, props)
        self._visits(users, props, leads)
        self._plans_and_subscriptions(users)
        self._rentals(users, props)
        self._messages(users, props)

        self.stdout.write(self.style.SUCCESS("Données de démonstration injectées."))
        if not os.getenv('SEED_PASSWORD'):
            self.stdout.write(self.style.WARNING(f"Mot de passe des comptes de démonstration (affiché une seule fois) : {password}"))
        self.stdout.write("Comptes : " + ", ".join(sorted(u.email for u in users.values())))

    # ------------------------------------------------------------------
    def _user(self, key_email, password, **fields):
        user, _ = User.objects.update_or_create(email=key_email, defaults=fields)
        user.set_password(password)
        user.save()
        return user

    def _users(self, pw):
        ci = "Côte d'Ivoire"
        return {
            'admin': self._user('admin@thiebbro.ci', pw, first_name='Admin', last_name='Super', phone_number='+2250700000001', role=UserRole.ADMIN, is_staff=True, is_superuser=True),
            'koffi': self._user('koffi.agent@thiebbro.ci', pw, first_name='Moussa', last_name='Koffi', phone_number='+2250707112233', role=UserRole.AGENT),
            'aminata': self._user('aminata.agent@thiebbro.ci', pw, first_name='Aminata', last_name='Touré', phone_number='+2250505445566', role=UserRole.AGENT),
            'kouadio': self._user('k.yao@mail.ci', pw, first_name='Kouadio', last_name='Yao', phone_number='+2250708112244', role=UserRole.PROPRIETAIRE, identity_status=IdentityStatus.VERIFIE),
            'adjoua': self._user('adjoua.kouassi@mail.ci', pw, first_name='Adjoua', last_name='Kouassi', phone_number='+2250709223355', role=UserRole.PROPRIETAIRE, identity_status=IdentityStatus.VERIFIE),
            'marie': self._user('ml.ehui@mail.ci', pw, first_name='Marie-Laure', last_name='Ehui', phone_number='+2250101334466', role=UserRole.PROPRIETAIRE, identity_status=IdentityStatus.VERIFIE),
            'ibrahim': self._user('i.diallo@mail.ci', pw, first_name='Ibrahim', last_name='Diallo', phone_number='+2250102445577', role=UserRole.PROPRIETAIRE, identity_status=IdentityStatus.EN_ATTENTE),
            'sci': self._user('contact@sci-roniers.ci', pw, first_name='SCI', last_name='Les Rôniers', phone_number='+2252720556688', role=UserRole.PROMOTEUR, identity_status=IdentityStatus.VERIFIE),
            'awa': self._user('awa.traore@mail.ci', pw, first_name='Awa', last_name='Traoré', phone_number='+2250707556699', role=UserRole.PARTICULIER, country_of_residence=ci,
                              project_objective=ProjectObjective.HABITER, project_budget=Decimal('120000000'), project_down_payment=Decimal('30000000'),
                              project_zone='Bingerville, Cocody', project_timeframe=ProjectTimeframe.MOIS_0_3, identity_status=IdentityStatus.VERIFIE),
            'sekou': self._user('soro.paris@gmail.com', pw, first_name='Sekou', last_name='Soro', phone_number='+33612345678', role=UserRole.INVESTISSEUR, country_of_residence='France', is_diaspora=True,
                               project_objective=ProjectObjective.INVESTIR, project_budget=Decimal('90000000'), project_down_payment=Decimal('25000000'), project_zone='Cocody & Bingerville'),
            'paul': self._user('p.kacou@mail.ci', pw, first_name='Paul', last_name='Kacou', phone_number='+2250708667700', role=UserRole.PARTICULIER, is_active=False),
            'kone': self._user('a.kone@notaire.ci', pw, first_name='Aya', last_name='Koné', phone_number='+2252722441100', role=UserRole.NOTAIRE),
            'bamba': self._user('s.bamba@notaire.ci', pw, first_name='Serge', last_name='Bamba', phone_number='+2252720331100', role=UserRole.NOTAIRE),
            'ouattara': self._user('f.ouattara@notaire.ci', pw, first_name='Fatou', last_name='Ouattara', phone_number='+2252721221100', role=UserRole.NOTAIRE),
        }

    def _notaries(self, users):
        data = {'kone': ("Me Aya Koné", "Étude Koné & Associés", "Cocody"),
                'bamba': ("Me Serge Bamba", "Office notarial du Plateau", "Plateau"),
                'ouattara': ("Me Fatou Ouattara", "Cabinet Ouattara", "Marcory")}
        out = {}
        for key, (name, office, city) in data.items():
            out[key], _ = Notary.objects.update_or_create(user=users[key], defaults={'full_name': name, 'office': office, 'city': city, 'email': users[key].email})
        return out

    def _projects(self):
        specs = [
            ('etoile', "L'Étoile d'Abatta", 'Kader & Partners Immobilier', 'Cocody', 'Abatta', 64, 22, 'T4 2026', 65_000_000, 74, IMG['skyline'],
             "Complexe résidentiel moderne d'appartements de haut standing avec vue sur la lagune, piscine et sécurité 24h/24."),
            ('bingerville', "Les Villas Sereines de Bingerville", 'Promoteur Bâtir CI', 'Bingerville', 'Feh Kessé', 32, 9, 'T2 2027', 95_000_000, 41, IMG['villaEvening'],
             "Villas duplex contemporaines sécurisées avec club-house et espaces verts."),
            ('cocotiers', "Résidence Les Cocotiers", 'Thiebbro Développement', 'Bingerville', 'Abatta Village', 48, 31, 'T2 2027', 38_000_000, 62, IMG['building'],
             "Appartements F2 à F4 en VEFA, livrés avec cuisine équipée et parking."),
            ('lagune', "Cité Lagune Bleue", 'Groupe Ivoire Habitat', 'Grand-Bassam', 'Mondoukou', 120, 54, 'T4 2027', 24_500_000, 35, IMG['skyline'],
             "Logements économiques et intermédiaires à 10 minutes de la plage, paiement échelonné."),
            ('akandje', "Les Jardins d'Akandjé", 'Akandjé Promotion', 'Bingerville', 'Akandjé', 36, 33, 'T1 2027', 55_000_000, 88, IMG['whiteHouse'],
             "Villas jumelées dans un parc arboré, à proximité du lycée et du marché."),
        ]
        out = {}
        for key, name, dev, commune, hood, units, sold, delivery, start, progress, cover, desc in specs:
            p, _ = DevelopmentProject.objects.update_or_create(name=name, defaults=dict(
                developer_name=dev, commune=commune, neighborhood=hood, description=desc, total_lots_count=units,
                delivery_date=delivery, starting_price=Decimal(start), construction_progress=progress,
                cover_image_url=cover, is_featured=key in ('etoile', 'cocotiers', 'akandje')))
            if p.lots.count() != units:
                p.lots.all().delete()
                typologies = [PropertyTypology.F2, PropertyTypology.F3, PropertyTypology.F4]
                ProjectLot.objects.bulk_create([
                    ProjectLot(project=p, lot_number=f"Lot {100 + i}", typology=typologies[i % 3], building_name=f"Bât. {'ABC'[i % 3]}",
                               floor=i % 5, surface_sqm=Decimal(55 + (i % 3) * 25), price=Decimal(start + (i % 3) * 12_000_000),
                               status=PropertyStatus.VENDU if i < sold else (PropertyStatus.RESERVE if i < sold + 2 else PropertyStatus.DISPONIBLE))
                    for i in range(units)
                ])
            out[key] = p
        return out

    def _catalog(self, users, projects):
        agents = {'koffi': users['koffi'], 'aminata': users['aminata']}
        out = {}
        for i, s in enumerate(CATALOG):
            flags = {f: False for f in set(FLAG_WORDS.values())}
            extra = []
            for a in s['amenities']:
                field = next((f for word, f in FLAG_WORDS.items() if word in a.lower()), None)
                if field:
                    flags[field] = True
                else:
                    extra.append(a)
            pending = s['cert'] == 'EN_COURS'
            prop, _ = Property.objects.update_or_create(reference=s['ref'], defaults=dict(
                slug=s['slug'], title=s['title'], description=s['desc'], property_type=s['type'], transaction=s['tx'],
                title_deed=s['deed'], typology=s['typology'], target_goal=s['goal'],
                status=PropertyStatus.EN_ATTENTE if pending else PropertyStatus.DISPONIBLE,
                verification_status=VerificationStatus.EN_ATTENTE if pending else s['cert'],
                is_featured=s.get('featured', False), is_selected_investment=s.get('selected', False),
                price=Decimal(s['price']), recommended_down_payment=Decimal(int(s['price'] * 0.2)) if s['tx'] == 'VENTE' else None,
                estimated_monthly_rent=Decimal(s['rent']) if s.get('rent') else None,
                estimated_yield_rate=Decimal(str(s['yield_'])) if s['yield_'] else None, investment_score=s['score'],
                commune=s['commune'], neighborhood=s['quartier'], surface_sqm=Decimal(s['surface']),
                rooms_count=s['rooms'], bedrooms_count=s['bedrooms'], bathrooms_count=s['baths'],
                amenities_extra=extra, virtual_tour_url=MATTERPORT_DEMO if s['tour'] else None,
                tour_scan_requested=s.get('scan', False), views_count=s['views'],
                owner=users[s['owner']], assigned_agent=agents[s['agent']],
                development_project=projects.get(s.get('project')), **flags,
            ))
            # Date d'ajout étalée pour un tri « plus récents » réaliste.
            Property.objects.filter(pk=prop.pk).update(created_at=timezone.now() - timedelta(days=len(CATALOG) - i))
            prop.images.all().delete()
            PropertyImage.objects.bulk_create([PropertyImage(property=prop, external_url=IMG[k], is_cover=j == 0, order=j) for j, k in enumerate(s['images'])])
            out[s['ref']] = prop
        return out

    def _accreditations(self, props, notaries):
        spec_by_ref = {s['ref']: s for s in CATALOG}
        pdf = b"%PDF-1.4\n% document de demonstration Thiebbro\n"
        for ref, prop in props.items():
            s = spec_by_ref[ref]
            certified = s['cert'] != 'EN_COURS'
            step = 3 if certified else (2 if ref == 'THI-2026-008' else 1)
            file, _ = AccreditationFile.objects.update_or_create(property=prop, defaults=dict(
                notary=notaries[s['notary']], step=step,
                status=AccreditationStatus.CERTIFIE if certified else AccreditationStatus.EN_COURS,
                certification_level=s['cert'] if certified else '', refusal_reason='',
                certified_at=timezone.now() - timedelta(days=20) if certified else None,
            ))
            docs = list(DocumentType) if certified else ([DocumentType.TITRE, DocumentType.IDENTITE] if ref == 'THI-2026-008' else [DocumentType.TITRE, DocumentType.IDENTITE, DocumentType.PLAN])
            prop.documents.all().delete()
            for d in docs:
                doc = PropertyDocument(property=prop, doc_type=d, status='VALIDE' if certified else 'DEPOSE')
                doc.file.save(f"{ref.lower()}-{d.value.lower()}.pdf", ContentFile(pdf), save=False)
                doc.save()

    def _crm(self, users, props):
        p = props
        specs = [
            ("Awa Traoré", users['awa'].phone_number, 'THI-2026-002', 120_000_000, PipelineStage.VISITE, LeadSource.SITE_WEB, 'aminata', users['awa'], '0-3 mois', 'Habiter'),
            ("Jean-Marc N'Guessan", '+15145550199', 'THI-2026-003', 90_000_000, PipelineStage.QUALIFIE, LeadSource.ESPACE_DIASPORA, 'koffi', None, 'Immédiatement', 'Investir'),
            ("Kevin Aka", '+2250102030406', 'THI-2026-011', 300_000_000, PipelineStage.PROPOSITION, LeadSource.APPLICATION, 'aminata', None, '0-3 mois', 'Habiter'),
            ("Fatim Coulibaly", '+2250709887766', 'THI-2026-005', 330_000_000, PipelineStage.RESERVATION, LeadSource.DEMANDE_INFO, 'koffi', None, 'Immédiatement', 'Investir'),
            ("Paul Kacou", users['paul'].phone_number, 'THI-2026-004', 45_000_000, PipelineStage.NOUVEAU, LeadSource.WHATSAPP, None, users['paul'], '3-6 mois', 'Investir'),
            ("Mariam Sangaré", '+2250504332211', 'THI-2026-010', 20_000_000, PipelineStage.NOUVEAU, LeadSource.SITE_WEB, None, None, '6-12 mois', 'Investir'),
            ("Hervé Gnagne", '+2250708990012', 'THI-2026-006', 100_000_000, PipelineStage.VENTE, LeadSource.SITE_WEB, 'aminata', None, 'Immédiatement', 'Habiter'),
            ("Sandrine Yapi", '+2250101112233', 'THI-2026-009', 1_000_000, PipelineStage.QUALIFIE, LeadSource.SITE_WEB, 'koffi', None, '0-3 mois', 'Louer'),
            ("Sekou Soro", users['sekou'].phone_number, 'THI-2026-003', 90_000_000, PipelineStage.CONTACTE, LeadSource.SIMULATEUR, 'koffi', users['sekou'], '0-3 mois', 'Investir'),
        ]
        out = {}
        for name, phone, ref, budget, stage, source, agent, account, timeframe, objective in specs:
            lead, _ = Lead.objects.update_or_create(phone_number=phone, defaults=dict(
                full_name=name, user=account, consulted_property=p[ref], budget=Decimal(budget), down_payment=Decimal(int(budget * 0.25)),
                stage=stage, source=source, assigned_agent=users[agent] if agent else None, timeframe=timeframe,
                objective=objective, preferred_zone=p[ref].commune, property_type=p[ref].get_property_type_display(),
            ))
            rescore(lead)
            lead.save()
            CRMInteraction.objects.get_or_create(lead=lead, interaction_type='SEED', defaults={'details': f"Prospect intéressé par {ref} — étape {lead.get_stage_display()}"})
            out[name] = lead
        return out

    def _visits(self, users, props, leads):
        t = self.today
        specs = [
            ('THI-2026-002', "Awa Traoré", VisitRequestType.PHYSIQUE, t + timedelta(days=2), time(10, 30), VisitRequestStatus.CONFIRMEE, "Cliente intéressée par une livraison rapide."),
            ('THI-2026-003', "Jean-Marc N'Guessan", VisitRequestType.VISIO, t + timedelta(days=3), time(15, 0), VisitRequestStatus.EN_ATTENTE, "Visite vidéo pour la diaspora au Canada."),
            ('THI-2026-006', "Awa Traoré", VisitRequestType.PHYSIQUE, t + timedelta(days=5), time(9, 0), VisitRequestStatus.EN_ATTENTE, "Souhaite venir avec un architecte."),
            ('THI-2026-011', "Kevin Aka", VisitRequestType.VISITE_3D, t - timedelta(days=9), time(18, 0), VisitRequestStatus.EFFECTUEE, "Visite Matterport commentée par l'agent."),
            ('THI-2026-005', "Fatim Coulibaly", VisitRequestType.PHYSIQUE, t - timedelta(days=14), time(11, 0), VisitRequestStatus.ANNULEE, "Reportée à la demande de la cliente."),
            ('THI-2026-012', "Awa Traoré", VisitRequestType.PHYSIQUE, t + timedelta(days=8), time(16, 0), VisitRequestStatus.EN_ATTENTE, "Deuxième visite avec la famille."),
        ]
        for ref, lead_name, vtype, day, hour, st, note in specs:
            lead = leads[lead_name]
            VisitRequest.objects.update_or_create(property=props[ref], lead=lead, scheduled_date=day, defaults=dict(
                user=lead.user, visit_type=vtype, scheduled_time=hour, status=st, notes=note))

    def _plans_and_subscriptions(self, users):
        plans = [
            ('patrimoine', "Plan Patrimoine", "Constituez un capital foncier en payant par mensualités.", 150_000, "12 à 36 mois", "+18 % de plus-value estimée", PlanRisk.FAIBLE, True, False,
             ["Terrains avec ACD vérifié", "Paiement échelonné sans intérêt", "Bornage et suivi notarial inclus", "Revente assistée"]),
            ('rendement', "Plan Rendement Locatif", "Des revenus mensuels grâce à des biens déjà loués.", 5_000_000, "5 à 10 ans", "8 à 12 % brut / an", PlanRisk.MODERE, False, True,
             ["Biens loués à l'acquisition", "Gestion locative déléguée", "Reporting mensuel des loyers", "Assurance loyers impayés"]),
            ('diaspora', "Plan Diaspora", "Investissez au pays depuis l'étranger, en toute sécurité.", 2_500_000, "Sur mesure", "7 à 10 % brut / an", PlanRisk.MODERE, False, False,
             ["Visites vidéo et 3D Matterport", "Signature notariale à distance", "Compte séquestre sécurisé", "Conseiller dédié"]),
        ]
        objs = {}
        for order, (code, name, tagline, ticket, duration, target, risk, instal, highlight, features) in enumerate(plans):
            objs[code], _ = InvestmentPlan.objects.update_or_create(code=code, defaults=dict(
                name=name, tagline=tagline, min_ticket=Decimal(ticket), duration_label=duration, target_yield_label=target,
                risk=risk, allows_instalments=instal, highlight=highlight, features=features, order=order, status='OUVERT'))

        if not Subscription.objects.filter(user=users['awa']).exists():
            sub = subscribe(users['awa'], objs['patrimoine'], Decimal('18560000'), PaymentMethod.ORANGE, months=32, payment_phone=users['awa'].phone_number)
            sub.asset_label = "Lot 500 m² — Songon Kassemblé"
            sub.save(update_fields=['asset_label'])
            # Les 7 premières mensualités sont payées : on recale l'échéancier dans le passé.
            for i, entry in enumerate(sub.entries.order_by('due_date')):
                entry.due_date = add_months(self.today.replace(day=5), i - 7)
                entry.status = EntryStatus.A_VENIR
                entry.save(update_fields=['due_date', 'status'])
                if i < 7:
                    confirm_payment(entry, f"OM-{entry.due_date:%y%m}-{i + 1:03d}")
        if not Subscription.objects.filter(user=users['sekou']).exists():
            sub = subscribe(users['sekou'], objs['rendement'], Decimal('32000000'), PaymentMethod.TRANSFER)
            sub.asset_label = "Quote-part 10 % — Immeuble Angré"
            sub.estimated_value = Decimal('34600000')
            sub.save(update_fields=['asset_label', 'estimated_value'])
            confirm_payment(sub.entries.first(), "VIR-SEQ-0001")
            for m in range(1, 5):
                ScheduleEntry.objects.create(subscription=sub, kind=EntryKind.REVENU, label="Loyer reversé — Immeuble Angré",
                                             due_date=add_months(self.today.replace(day=1), -m), amount=Decimal('245000'), status=EntryStatus.RECU)
            ScheduleEntry.objects.create(subscription=sub, kind=EntryKind.REVENU, label="Loyer reversé — Immeuble Angré",
                                         due_date=add_months(self.today.replace(day=1), 1), amount=Decimal('245000'), status=EntryStatus.PROGRAMME)

    def _rentals(self, users, props):
        month = self.today.replace(day=1)
        specs = [('THI-2026-003', "Location courte durée", 850_000, 82), ('THI-2026-008', "M. Konan B.", 350_000, 100), ('THI-2026-002', "Famille Assi", 750_000, 100)]
        for ref, tenant, rent, occ in specs:
            lease, _ = Lease.objects.update_or_create(property=props[ref], tenant_label=tenant, defaults=dict(
                monthly_rent=Decimal(rent), occupancy_rate=occ, start_date=add_months(month, -10)))
            for i in range(6, -1, -1):
                period = add_months(month, -i)
                late = ref == 'THI-2026-008' and i == 0
                RentPayment.objects.update_or_create(lease=lease, period=period, defaults=dict(
                    amount=Decimal(0) if late else Decimal(int(rent * occ / 100 * (0.92 + 0.02 * ((6 - i) % 4)))),
                    status=RentStatus.EN_RETARD if late else RentStatus.PAYE, paid_at=None if late else period + timedelta(days=3)))
        owner = users['kouadio']
        OwnerPayout.objects.filter(owner=owner).delete()
        for i, amount in enumerate([1_690_000, 1_744_000, 1_802_000]):
            d = add_months(month, -(3 - i)).replace(day=5)
            OwnerPayout.objects.create(owner=owner, amount=Decimal(amount), reference=f"VIR-{d:%y%m}-00{31 + i * 4}", payout_date=d, status=PayoutStatus.VERSE)
        OwnerPayout.objects.create(owner=owner, amount=Decimal(1_800_000), payout_date=add_months(month, 1).replace(day=5), status=PayoutStatus.PROGRAMME)

    def _messages(self, users, props):
        threads = [
            (users['awa'], users['kouadio'], 'THI-2026-006', [(users['awa'], "Bonjour, le titre foncier est-il disponible ?"), (users['kouadio'], "Oui, le titre foncier est disponible pour consultation chez le notaire.")]),
            (users['awa'], users['koffi'], 'THI-2026-003', [(users['koffi'], "Je vous ai envoyé la simulation de rendement mise à jour.")]),
            (users['awa'], users['kone'], 'THI-2026-002', [(users['kone'], "Le compromis de vente est prêt pour relecture.")]),
        ]
        for a, b, ref, msgs in threads:
            prop = props[ref]
            conv = Conversation.objects.filter(property=prop, participants__user=a).filter(participants__user=b).first()
            if conv:
                continue
            conv = Conversation.objects.create(property=prop, subject=prop.title)
            ConversationParticipant.objects.create(conversation=conv, user=a)
            ConversationParticipant.objects.create(conversation=conv, user=b, last_read_at=timezone.now())
            for sender, body in msgs:
                Message.objects.create(conversation=conv, sender=sender, body=body)
