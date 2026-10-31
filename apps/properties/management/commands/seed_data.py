from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils.text import slugify

from apps.users.infrastructure.models import UserRole, ProjectObjective, ProjectTimeframe
from apps.properties.infrastructure.models import (
    Property, PropertyImage, PropertyType, PropertyTypology,
    PropertyGoal, PropertyStatus, VerificationStatus,
    DevelopmentProject, ProjectLot
)
from apps.crm.infrastructure.models import (
    Lead, LeadSource, PipelineStage, LeadTemperature,
    PropertyInquiry, VisitRequest, VisitRequestType, VisitRequestStatus, CRMInteraction
)
from apps.crm.domain.scoring_service import LeadScoringDomainService

User = get_user_model()

class Command(BaseCommand):
    help = "Peuple la base de données PostgreSQL avec des données dynamiques et réalistes du marché ivoirien pour THIEBBRO IMMO."

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("🌱 Initialisation des données dynamiques dans PostgreSQL..."))

        # 1. Utilisateurs & Conseillers
        admin_user, _ = User.objects.get_or_create(
            email='admin@thiebbro.ci',
            defaults={
                'first_name': 'Administrateur',
                'last_name': 'THIEBBRO',
                'phone_number': '+225 0700000001',
                'role': UserRole.ADMIN,
                'is_staff': True,
                'is_superuser': True
            }
        )
        admin_user.set_password('admin1234')
        admin_user.save()

        agent_koffi, _ = User.objects.get_or_create(
            email='koffi.agent@thiebbro.ci',
            defaults={
                'first_name': 'Koffi',
                'last_name': 'N\'Guessan',
                'phone_number': '+225 0707112233',
                'role': UserRole.AGENT,
                'is_staff': True
            }
        )
        agent_koffi.set_password('agent1234')
        agent_koffi.save()

        agent_aminata, _ = User.objects.get_or_create(
            email='aminata.agent@thiebbro.ci',
            defaults={
                'first_name': 'Aminata',
                'last_name': 'Touré',
                'phone_number': '+225 0505445566',
                'role': UserRole.AGENT,
                'is_staff': True
            }
        )
        agent_aminata.set_password('agent1234')
        agent_aminata.save()

        client_diaspora, _ = User.objects.get_or_create(
            email='soro.paris@gmail.com',
            defaults={
                'first_name': 'Sekou',
                'last_name': 'Soro',
                'phone_number': '+33 6 12 34 56 78',
                'country_of_residence': 'France',
                'is_diaspora': True,
                'role': UserRole.INVESTISSEUR,
                'project_objective': ProjectObjective.INVESTIR,
                'project_budget': Decimal('90000000'),
                'project_down_payment': Decimal('25000000'),
                'project_zone': 'Cocody & Bingerville',
                'project_timeframe': ProjectTimeframe.MOIS_0_3
            }
        )
        client_diaspora.set_password('client1234')
        client_diaspora.save()

        self.stdout.write(self.style.SUCCESS("✓ Utilisateurs & Conseillers créés"))

        # 2. Programmes Immobiliers Neufs (Écrans 20 & 24)
        proj_etoile, _ = DevelopmentProject.objects.get_or_create(
            name="L'Étoile d'Abatta",
            defaults={
                'slug': 'l-etoile-d-abatta',
                'developer_name': 'Kader & Partners Immobilier',
                'commune': 'Cocody',
                'neighborhood': 'Abatta',
                'description': 'Complexe résidentiel moderne composé d\'appartements de haut standing avec vue sur la lagune, piscine et sécurité 24h/24.',
                'total_lots_count': 64,
                'delivery_date': 'T4 2026',
                'starting_price': Decimal('65000000'),
                'is_featured': True
            }
        )

        # Création des lots pour L'Étoile d'Abatta
        lots_data = [
            ("Lot 101", PropertyTypology.F3, "Bâtiment A", 1, Decimal('85.00'), Decimal('66000000'), PropertyStatus.DISPONIBLE),
            ("Lot 102", PropertyTypology.F4, "Bâtiment A", 1, Decimal('110.00'), Decimal('85000000'), PropertyStatus.RESERVE),
            ("Lot 201", PropertyTypology.F3, "Bâtiment A", 2, Decimal('85.00'), Decimal('68000000'), PropertyStatus.DISPONIBLE),
            ("Lot 202", PropertyTypology.F4, "Bâtiment A", 2, Decimal('115.00'), Decimal('89000000'), PropertyStatus.OPTION),
            ("Lot 301", PropertyTypology.F5, "Bâtiment B", 3, Decimal('145.00'), Decimal('120000000'), PropertyStatus.DISPONIBLE),
        ]
        for num, typ, bat, etage, surf, prix, stat in lots_data:
            ProjectLot.objects.get_or_create(
                project=proj_etoile,
                lot_number=num,
                defaults={
                    'typology': typ,
                    'building_name': bat,
                    'floor': etage,
                    'surface_sqm': surf,
                    'price': prix,
                    'status': stat
                }
            )

        proj_bingerville, _ = DevelopmentProject.objects.get_or_create(
            name="Les Villas Serenes de Bingerville",
            defaults={
                'slug': 'les-villas-serenes-de-bingerville',
                'developer_name': 'Promoteur Bâtir CI',
                'commune': 'Bingerville',
                'neighborhood': 'Feh Kessé',
                'description': 'Ensemble de villas duplex contemporaines sécurisées en bordure de la voie principale avec club-house et espaces verts.',
                'total_lots_count': 32,
                'delivery_date': 'T2 2027',
                'starting_price': Decimal('95000000'),
                'is_featured': True
            }
        )

        self.stdout.write(self.style.SUCCESS("✓ Programmes Neufs et Lots créés"))

        # 3. Biens Immobiliers Individuels
        properties_catalog = [
            {
                'reference': 'THI-2026-001',
                'title': 'Appartement F3 Moderne avec Vue Dégagée',
                'property_type': PropertyType.APPARTEMENT,
                'typology': PropertyTypology.F3,
                'target_goal': PropertyGoal.MIXTE,
                'commune': 'Cocody',
                'neighborhood': 'Abatta',
                'price': Decimal('66000000'),
                'recommended_down_payment': Decimal('15000000'),
                'estimated_monthly_rent': Decimal('450000'),
                'estimated_yield_rate': Decimal('8.18'),
                'investment_score': 88,
                'surface_sqm': Decimal('82.00'),
                'rooms_count': 3,
                'bedrooms_count': 2,
                'bathrooms_count': 2,
                'has_parking': True,
                'has_security': True,
                'has_elevator': True,
                'is_featured': True,
                'is_selected_investment': True,
                'verification_status': VerificationStatus.VERIFICATION_RENFORCEE,
                'assigned_agent': agent_koffi,
                'development_project': proj_etoile,
                'description': "Superbe appartement F3 situé à Cocody Abatta dans un immeuble récent et sécurisé. Finitions soignées, cuisine équipée, balcon spacieux. Idéal pour résidence principale ou fort rendement locatif."
            },
            {
                'reference': 'THI-2026-002',
                'title': 'Villa Duplex 5 Pièces avec Jardin Privatif',
                'property_type': PropertyType.VILLA,
                'typology': PropertyTypology.F5,
                'target_goal': PropertyGoal.HABITATION,
                'commune': 'Bingerville',
                'neighborhood': 'Feh Kessé',
                'price': Decimal('115000000'),
                'recommended_down_payment': Decimal('25000000'),
                'estimated_monthly_rent': Decimal('750000'),
                'estimated_yield_rate': Decimal('7.83'),
                'investment_score': 82,
                'surface_sqm': Decimal('260.00'),
                'rooms_count': 5,
                'bedrooms_count': 4,
                'bathrooms_count': 4,
                'has_parking': True,
                'has_security': True,
                'has_swimming_pool': True,
                'has_green_space': True,
                'is_featured': True,
                'is_selected_investment': False,
                'verification_status': VerificationStatus.VERIFIE,
                'assigned_agent': agent_aminata,
                'development_project': proj_bingerville,
                'description': "Magnifique villa duplex moderne à Bingerville. Séjour lumineux double hauteur, suite parentale avec dressing, dépendance autonome, garage 2 véhicules et jardin arboré."
            },
            {
                'reference': 'THI-2026-003',
                'title': 'Résidence Meublée Rentable Zone 4',
                'property_type': PropertyType.RESIDENCE_MEUBLEE,
                'typology': PropertyTypology.F2,
                'target_goal': PropertyGoal.INVESTISSEMENT,
                'commune': 'Marcory',
                'neighborhood': 'Zone 4C',
                'price': Decimal('85000000'),
                'recommended_down_payment': Decimal('20000000'),
                'estimated_monthly_rent': Decimal('850000'),
                'estimated_yield_rate': Decimal('12.00'),
                'investment_score': 95,
                'surface_sqm': Decimal('65.00'),
                'rooms_count': 2,
                'bedrooms_count': 1,
                'bathrooms_count': 1,
                'has_parking': True,
                'has_security': True,
                'has_generator': True,
                'is_featured': False,
                'is_selected_investment': True,
                'verification_status': VerificationStatus.VERIFICATION_RENFORCEE,
                'assigned_agent': agent_koffi,
                'description': "Investissement clé en main à Marcory Zone 4. Appartement meublé design avec gestion locative assurée (taux d'occupation moyen de 85% à l'année). Rentabilité nette exceptionnelle."
            },
            {
                'reference': 'THI-2026-004',
                'title': 'Terrain Clôturé avec ACD en Bordure de Voie',
                'property_type': PropertyType.TERRAIN,
                'typology': PropertyTypology.AUTRE,
                'target_goal': PropertyGoal.INVESTISSEMENT,
                'commune': 'Grand-Bassam',
                'neighborhood': 'Moossou',
                'price': Decimal('42000000'),
                'recommended_down_payment': Decimal('42000000'),
                'investment_score': 80,
                'surface_sqm': Decimal('600.00'),
                'rooms_count': 0,
                'bedrooms_count': 0,
                'bathrooms_count': 0,
                'is_featured': True,
                'is_selected_investment': True,
                'verification_status': VerificationStatus.VERIFICATION_RENFORCEE,
                'assigned_agent': agent_aminata,
                'description': "Parcelle de 600 m² prête à bâtir avec Arrêté de Concession Définitive (ACD) certifié au Ministère de la Construction. Zone en forte plus-value immobilière."
            },
            {
                'reference': 'THI-2026-005',
                'title': 'Immeuble R+3 de 8 Appartements Rentable',
                'property_type': PropertyType.IMMEUBLE,
                'typology': PropertyTypology.AUTRE,
                'target_goal': PropertyGoal.INVESTISSEMENT,
                'commune': 'Cocody',
                'neighborhood': 'Angré 8e Tranche',
                'price': Decimal('320000000'),
                'recommended_down_payment': Decimal('80000000'),
                'estimated_monthly_rent': Decimal('2800000'),
                'estimated_yield_rate': Decimal('10.50'),
                'investment_score': 92,
                'surface_sqm': Decimal('750.00'),
                'rooms_count': 24,
                'bedrooms_count': 16,
                'bathrooms_count': 16,
                'has_parking': True,
                'has_security': True,
                'has_generator': True,
                'is_featured': False,
                'is_selected_investment': True,
                'verification_status': VerificationStatus.VERIFIE,
                'assigned_agent': agent_koffi,
                'description': "Immeuble de rapport entièrement loué générant 2,8 millions FCFA de revenus mensuels stables. Compteurs SODECI/CIE individuels, titre foncier validé."
            },
            {
                'reference': 'THI-2026-006',
                'title': 'Duplex Moderne 4 Pièces Riviera Palmeraie',
                'property_type': PropertyType.DUPLEX,
                'typology': PropertyTypology.F4,
                'target_goal': PropertyGoal.HABITATION,
                'commune': 'Cocody',
                'neighborhood': 'Riviera Palmeraie',
                'price': Decimal('98000000'),
                'recommended_down_payment': Decimal('20000000'),
                'estimated_monthly_rent': Decimal('650000'),
                'estimated_yield_rate': Decimal('7.95'),
                'investment_score': 84,
                'surface_sqm': Decimal('195.00'),
                'rooms_count': 4,
                'bedrooms_count': 3,
                'bathrooms_count': 3,
                'has_parking': True,
                'has_security': True,
                'is_featured': True,
                'is_selected_investment': False,
                'verification_status': VerificationStatus.VERIFIE,
                'assigned_agent': agent_aminata,
                'description': "Belle villa duplex dans une cité fermée et sécurisée à la Riviera Palmeraie. Proche des commerces, écoles internationales et voie rapide."
            }
        ]

        created_props = []
        for prop_data in properties_catalog:
            ref = prop_data.pop('reference')
            title = prop_data['title']
            slug = slugify(f"{ref}-{title}")[:250]
            prop, _ = Property.objects.get_or_create(
                reference=ref,
                defaults={'slug': slug, **prop_data}
            )
            created_props.append(prop)

        self.stdout.write(self.style.SUCCESS(f"✓ {len(created_props)} Biens Immobiliers créés dans le catalogue"))

        # 4. Leads CRM & Pipeline Kanban (Écran 26)
        leads_data = [
            {
                'full_name': 'Dr. Jean-Marc Kouamé',
                'phone_number': '+225 0708990011',
                'whatsapp_number': '+225 0708990011',
                'email': 'jm.kouame@yahoo.fr',
                'budget': Decimal('120000000'),
                'down_payment': Decimal('30000000'),
                'objective': 'Habiter',
                'preferred_zone': 'Bingerville / Feh Kessé',
                'property_type': 'Villa Duplex',
                'timeframe': '0-3 mois',
                'stage': PipelineStage.RDV,
                'source': LeadSource.TROUVER_MON_BIEN,
                'consulted_property': created_props[1], # Villa Bingerville
                'assigned_agent': agent_aminata,
                'is_diaspora': False
            },
            {
                'full_name': 'Fatou Diallo (Diaspora Canada)',
                'phone_number': '+1 514 555 0199',
                'whatsapp_number': '+1 514 555 0199',
                'email': 'fatou.diallo@gmail.com',
                'budget': Decimal('85000000'),
                'down_payment': Decimal('25000000'),
                'objective': 'Investir',
                'preferred_zone': 'Marcory Zone 4',
                'property_type': 'Résidence Meublée',
                'timeframe': 'Immédiatement',
                'stage': PipelineStage.PROPOSITION,
                'source': LeadSource.ESPACE_DIASPORA,
                'consulted_property': created_props[2], # Meublé Zone 4
                'assigned_agent': agent_koffi,
                'is_diaspora': True,
                'country_of_residence': 'Canada'
            },
            {
                'full_name': 'Moussa Koné',
                'phone_number': '+225 0102030405',
                'whatsapp_number': '+225 0102030405',
                'email': 'kone.moussa@gmail.com',
                'budget': Decimal('66000000'),
                'down_payment': Decimal('15000000'),
                'objective': 'Habiter',
                'preferred_zone': 'Cocody Abatta',
                'property_type': 'Appartement F3',
                'timeframe': '3-6 mois',
                'stage': PipelineStage.QUALIFIE,
                'source': LeadSource.WHATSAPP,
                'consulted_property': created_props[0], # F3 Abatta
                'assigned_agent': agent_koffi,
                'is_diaspora': False
            },
            {
                'full_name': 'Sarah Bamba',
                'phone_number': '+225 0709887766',
                'budget': Decimal('45000000'),
                'down_payment': Decimal('45000000'),
                'objective': 'Investir',
                'preferred_zone': 'Grand-Bassam',
                'property_type': 'Terrain',
                'timeframe': 'Immédiatement',
                'stage': PipelineStage.NEGOCIATION,
                'source': LeadSource.DEMANDE_INFO,
                'consulted_property': created_props[3], # Terrain Bassam
                'assigned_agent': agent_aminata,
                'is_diaspora': False
            }
        ]

        for lead_item in leads_data:
            phone = lead_item.pop('phone_number')
            lead, _ = Lead.objects.get_or_create(
                phone_number=phone,
                defaults=lead_item
            )
            # Calcul du score dynamique
            score, temp = LeadScoringDomainService.calculate_score(
                has_confirmed_budget=bool(lead.budget),
                has_confirmed_down_payment=bool(lead.down_payment and lead.down_payment > 0),
                timeframe_under_3_months=True,
                has_identified_property=bool(lead.consulted_property),
                has_visit_request=lead.stage in [PipelineStage.RDV, PipelineStage.VISITE, PipelineStage.PROPOSITION],
                has_recent_interaction=True
            )
            lead.score = score
            lead.temperature = temp
            lead.save()

            # Interaction associée
            CRMInteraction.objects.get_or_create(
                lead=lead,
                interaction_type='SEED_LOG',
                defaults={'details': f'Lead initialisé à l\'étape {lead.get_stage_display()} (Score: {score})'}
            )

        self.stdout.write(self.style.SUCCESS("✓ Pipeline Kanban CRM et Prospects peuplés"))

        # 5. Demandes de visites & Inquiries
        VisitRequest.objects.get_or_create(
            property=created_props[1], # Villa Bingerville
            scheduled_date='2026-10-10',
            scheduled_time='10:30:00',
            defaults={
                'lead': Lead.objects.get(phone_number='+225 0708990011'),
                'user': client_diaspora,
                'visit_type': VisitRequestType.PHYSIQUE,
                'status': VisitRequestStatus.CONFIRMEE,
                'notes': 'Client intéressé par une livraison rapide.'
            }
        )

        VisitRequest.objects.get_or_create(
            property=created_props[2], # Meublé Zone 4
            scheduled_date='2026-10-12',
            scheduled_time='15:00:00',
            defaults={
                'lead': Lead.objects.get(phone_number='+1 514 555 0199'),
                'visit_type': VisitRequestType.VISIO,
                'status': VisitRequestStatus.EN_ATTENTE,
                'notes': 'Visite vidéo Zoom / WhatsApp pour la diaspora au Canada.'
            }
        )

        self.stdout.write(self.style.SUCCESS("🎉 Toutes les données dynamiques sont injectées avec succès dans PostgreSQL !"))
