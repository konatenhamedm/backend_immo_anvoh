"""Tests d'intégration des parcours ajoutés : sécurité, publication propriétaire, accréditation, CRM, investissement, messagerie."""
from datetime import timedelta
from decimal import Decimal

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.users.infrastructure.models import User, UserRole
from apps.properties.infrastructure.models import Property, PropertyStatus, VerificationStatus
from apps.crm.infrastructure.models import Lead, PipelineStage
from apps.accreditation.infrastructure.models import Notary
from apps.investments.infrastructure.models import InvestmentPlan, EntryStatus

PASSWORD = 'Un-Mot2Passe-Solide'


def make_user(email, role=UserRole.PARTICULIER, **extra):
    return User.objects.create_user(email=email, password=PASSWORD, first_name='Test', last_name=email.split('@')[0],
                                    phone_number='+2250700000000', role=role, **extra)


def client_for(user=None):
    c = APIClient()
    if user:
        c.force_authenticate(user)
    return c


def make_property(**kw):
    defaults = dict(title='Villa test', description='Desc', property_type='VILLA', price=Decimal('50000000'),
                    commune='Cocody', neighborhood='Angré', surface_sqm=Decimal('200'), status=PropertyStatus.DISPONIBLE)
    defaults.update(kw)
    return Property.objects.create(**defaults)


class SecurityTests(TestCase):
    def test_anonymous_cannot_manage_users_or_properties(self):
        anon = client_for()
        self.assertEqual(anon.get('/api/v1/auth/users/').status_code, 401)
        self.assertEqual(anon.get('/api/v1/crm/pipeline/kanban/').status_code, 401)
        prop = make_property()
        self.assertEqual(anon.delete(f'/api/v1/properties/{prop.id}/').status_code, 401)
        self.assertEqual(anon.post('/api/v1/properties/search/', {'title': 'x'}).status_code, 401)

    def test_register_cannot_self_assign_admin(self):
        r = client_for().post('/api/v1/auth/register/', {
            'email': 'pirate@test.ci', 'password': PASSWORD, 'first_name': 'P', 'last_name': 'X', 'phone_number': '0707070707', 'role': 'ADMIN',
        }, format='json')
        self.assertEqual(r.status_code, 400)
        self.assertFalse(User.objects.filter(email='pirate@test.ci').exists())

    def test_profile_role_is_read_only(self):
        user = make_user('client@test.ci')
        client_for(user).patch('/api/v1/auth/profile/', {'role': 'ADMIN'}, format='json')
        user.refresh_from_db()
        self.assertEqual(user.role, UserRole.PARTICULIER)

    def test_buyer_cannot_open_back_office(self):
        user = make_user('buyer@test.ci')
        self.assertEqual(client_for(user).get('/api/v1/auth/users/').status_code, 403)
        self.assertEqual(client_for(user).get('/api/v1/crm/admin/dashboard/').status_code, 403)

    def test_simulators_stay_public(self):
        r = client_for().post('/api/v1/simulators/borrowing-capacity/', {
            'monthly_income': 1500000, 'existing_monthly_debts': 0, 'down_payment': 10000000,
            'annual_interest_rate': 7.5, 'loan_duration_years': 15,
        }, format='json')
        self.assertNotIn(r.status_code, (401, 403))


class OwnerPublishingAndAccreditationTests(TestCase):
    def setUp(self):
        self.owner = make_user('owner@test.ci', UserRole.PROPRIETAIRE)
        self.admin = make_user('admin@test.ci', UserRole.ADMIN, is_staff=True)
        self.notary_user = make_user('notaire@test.ci', UserRole.NOTAIRE)
        self.notary = Notary.objects.create(user=self.notary_user, full_name='Me Test', office='Étude Test', city='Plateau')

    def _publish(self):
        r = client_for(self.owner).post('/api/v1/properties/owner/', {
            'title': 'Villa 5 pièces', 'description': 'Belle villa', 'property_type': 'VILLA', 'transaction': 'VENTE',
            'price': '135000000', 'commune': 'Cocody', 'neighborhood': 'Riviera 3', 'surface_sqm': '280', 'bedrooms_count': 4,
            'image_urls': ['https://images.unsplash.com/photo-1600585154340-be6161a56a0c'],
        }, format='json')
        self.assertEqual(r.status_code, 201, r.content)
        return Property.objects.get(id=r.json()['id'])

    def test_owner_listing_is_hidden_until_certified(self):
        prop = self._publish()
        self.assertEqual(prop.status, PropertyStatus.EN_ATTENTE)
        self.assertTrue(prop.reference.startswith('THI-'))
        self.assertEqual(client_for().get(f'/api/v1/properties/slug/{prop.slug}/').status_code, 404)
        self.assertEqual(client_for(self.owner).get(f'/api/v1/properties/slug/{prop.slug}/').status_code, 200)

        file = prop.accreditation
        admin = client_for(self.admin)
        self.assertEqual(admin.post(f'/api/v1/accreditation/queue/{file.id}/', {'action': 'certify'}, format='json').status_code, 400)  # pièces manquantes
        for doc in ('TITRE', 'IDENTITE', 'PLAN'):
            r = client_for(self.owner).post(f'/api/v1/accreditation/owner/properties/{prop.id}/documents/',
                                            {'doc_type': doc, 'file': SimpleUploadedFile(f'{doc}.pdf', b'%PDF-1.4', 'application/pdf')}, format='multipart')
            self.assertEqual(r.status_code, 201, r.content)
        self.assertEqual(admin.post(f'/api/v1/accreditation/queue/{file.id}/', {'action': 'assign', 'notary_id': str(self.notary.id)}, format='json').status_code, 200)

        # Le notaire assigné voit le dossier et le certifie : le bien est publié avec le badge.
        notary = client_for(self.notary_user)
        self.assertEqual(len(notary.get('/api/v1/accreditation/queue/').json()), 1)
        self.assertEqual(notary.post(f'/api/v1/accreditation/queue/{file.id}/', {'action': 'certify', 'level': 'VERIFICATION_RENFORCEE'}, format='json').status_code, 200)
        prop.refresh_from_db()
        self.assertEqual(prop.status, PropertyStatus.DISPONIBLE)
        self.assertEqual(prop.verification_status, VerificationStatus.VERIFICATION_RENFORCEE)
        self.assertEqual(client_for().get(f'/api/v1/properties/slug/{prop.slug}/').status_code, 200)

    def test_refusal_returns_listing_to_draft(self):
        prop = self._publish()
        r = client_for(self.admin).post(f'/api/v1/accreditation/queue/{prop.accreditation.id}/', {'action': 'refuse', 'reason': 'Titre illisible'}, format='json')
        self.assertEqual(r.status_code, 200)
        prop.refresh_from_db()
        self.assertEqual(prop.status, PropertyStatus.BROUILLON)
        self.assertEqual(prop.verification_status, VerificationStatus.REFUSE)

    def test_owner_cannot_edit_someone_elses_property(self):
        other = make_user('other@test.ci', UserRole.PROPRIETAIRE)
        prop = make_property(owner=other)
        self.assertEqual(client_for(self.owner).patch(f'/api/v1/properties/owner/{prop.id}/', {'price': '1'}, format='json').status_code, 404)


class CrmTests(TestCase):
    def setUp(self):
        self.prop = make_property()

    def test_anonymous_whatsapp_click_creates_no_catch_all_lead(self):
        r = client_for().post('/api/v1/crm/whatsapp-click/', {'property_id': str(self.prop.id)}, format='json')
        self.assertEqual(r.json()['status'], 'anonymous')
        self.assertEqual(Lead.objects.count(), 0)

    def test_phone_formats_are_deduplicated_and_stage_never_goes_back(self):
        day = (timezone.localdate() + timedelta(days=3)).isoformat()
        c = client_for()
        c.post('/api/v1/crm/visits/schedule/', {'property_id': str(self.prop.id), 'full_name': 'Awa', 'phone_number': '07 07 07 07 07',
                                                'scheduled_date': day, 'scheduled_time': '10:00'}, format='json')
        lead = Lead.objects.get()
        self.assertEqual(lead.phone_number, '+2250707070707')
        self.assertEqual(lead.stage, PipelineStage.RDV)
        score_after_visit = lead.score
        c.post('/api/v1/crm/inquiries/', {'property_id': str(self.prop.id), 'full_name': 'Awa', 'phone_number': '+225 07 07 07 07 07',
                                          'objective': 'Habiter'}, format='json')
        lead.refresh_from_db()
        self.assertEqual(Lead.objects.count(), 1)
        self.assertEqual(lead.stage, PipelineStage.RDV)
        self.assertGreaterEqual(lead.score, score_after_visit)

    def test_visit_in_the_past_is_rejected(self):
        r = client_for().post('/api/v1/crm/visits/schedule/', {'property_id': str(self.prop.id), 'full_name': 'A', 'phone_number': '0707070707',
                                                               'scheduled_date': '2020-01-01', 'scheduled_time': '10:00'}, format='json')
        self.assertEqual(r.status_code, 400)


class InvestmentAndMessagingTests(TestCase):
    def setUp(self):
        self.buyer = make_user('buyer@test.ci')
        self.admin = make_user('admin@test.ci', UserRole.ADMIN, is_staff=True)
        self.plan = InvestmentPlan.objects.create(code='patrimoine', name='Plan Patrimoine', min_ticket=Decimal('150000'), allows_instalments=True)

    def test_subscription_schedule_and_activation(self):
        c = client_for(self.buyer)
        self.assertEqual(c.post('/api/v1/investments/subscriptions/', {'plan': 'patrimoine', 'amount': '100000', 'payment_method': 'WAVE',
                                                                     'payment_phone': '0707070707', 'accept_terms': True}, format='json').status_code, 400)
        r = c.post('/api/v1/investments/subscriptions/', {'plan': 'patrimoine', 'amount': '2400000', 'months': 24, 'payment_method': 'WAVE',
                                                          'payment_phone': '0707070707', 'accept_terms': True}, format='json')
        self.assertEqual(r.status_code, 201, r.content)
        self.assertEqual(r.json()['status'], 'EN_ATTENTE')
        entry_id = r.json()['next_entry']['id']
        self.assertEqual(r.json()['next_entry']['status'], EntryStatus.EN_VALIDATION)
        self.assertEqual(client_for(self.admin).post(f'/api/v1/investments/admin/entries/{entry_id}/confirm/', {}, format='json').status_code, 200)
        me = c.get('/api/v1/investments/me/').json()
        self.assertEqual(me['subscriptions'][0]['status'], 'ACTIVE')
        self.assertEqual(Decimal(me['summary']['invested']), Decimal('100000'))

    def test_buyer_can_message_owner_about_property_but_not_other_clients(self):
        owner = make_user('owner@test.ci', UserRole.PROPRIETAIRE)
        prop = make_property(owner=owner)
        c = client_for(self.buyer)
        r = c.post('/api/v1/messaging/conversations/', {'property_id': str(prop.id), 'body': 'Bonjour'}, format='json')
        self.assertEqual(r.status_code, 201, r.content)
        self.assertEqual(client_for(owner).get('/api/v1/messaging/unread-count/').json()['unread'], 1)
        stranger = make_user('stranger@test.ci')
        self.assertEqual(c.post('/api/v1/messaging/conversations/', {'recipient_id': stranger.id, 'body': 'Spam'}, format='json').status_code, 403)


class LatestEndpointsTests(TestCase):
    def setUp(self):
        self.buyer = make_user('buyer@test.ci')
        self.agent = make_user('agent@test.ci', UserRole.AGENT)

    def test_search_alerts_are_private_and_capped(self):
        c = client_for(self.buyer)
        r = c.post('/api/v1/crm/alerts/', {'transaction': 'VENTE', 'commune': 'Cocody', 'max_budget': '90000000', 'frequency': 'DAILY'}, format='json')
        self.assertEqual(r.status_code, 201, r.content)
        self.assertIn('Achat', r.json()['label'])
        other = client_for(make_user('other@test.ci'))
        self.assertEqual(other.get('/api/v1/crm/alerts/').json(), [])
        self.assertEqual(other.delete(f"/api/v1/crm/alerts/{r.json()['id']}/").status_code, 404)
        self.assertEqual(c.post('/api/v1/crm/alerts/', {'transaction': 'TROC'}, format='json').status_code, 400)

    def test_agent_creates_lead_once_per_phone(self):
        c = client_for(self.agent)
        body = {'full_name': 'Yao K.', 'phone_number': '07 08 09 10 11', 'source': 'AUTRE', 'assign_to_me': True}
        self.assertEqual(c.post('/api/v1/crm/leads/', body, format='json').status_code, 201)
        self.assertEqual(c.post('/api/v1/crm/leads/', {**body, 'phone_number': '+2250708091011'}, format='json').status_code, 201)
        self.assertEqual(Lead.objects.count(), 1)
        self.assertEqual(Lead.objects.get().assigned_agent, self.agent)
        self.assertEqual(client_for(self.buyer).post('/api/v1/crm/leads/', body, format='json').status_code, 403)

    def test_password_change_requires_current_password(self):
        c = client_for(self.buyer)
        self.assertEqual(c.post('/api/v1/auth/profile/password/', {'current_password': 'faux', 'new_password': 'Nouveau-Mot2Passe'}, format='json').status_code, 400)
        r = c.post('/api/v1/auth/profile/password/', {'current_password': PASSWORD, 'new_password': 'Nouveau-Mot2Passe'}, format='json')
        self.assertEqual(r.status_code, 200)
        self.assertIn('access', r.json())
        self.buyer.refresh_from_db()
        self.assertTrue(self.buyer.check_password('Nouveau-Mot2Passe'))

    def test_notification_preferences_are_validated(self):
        c = client_for(self.buyer)
        self.assertEqual(c.patch('/api/v1/auth/profile/', {'notification_preferences': {'newsletter': True}}, format='json').status_code, 200)
        self.assertEqual(c.patch('/api/v1/auth/profile/', {'notification_preferences': {'pirate': True}}, format='json').status_code, 400)

    def test_staff_schedules_a_3d_scan(self):
        prop = make_property(tour_scan_requested=True)
        r = client_for(self.agent).patch(f'/api/v1/properties/admin/properties/{prop.id}/', {'tour_scan_scheduled_at': (timezone.now() + timedelta(days=2)).isoformat(), 'tour_scan_technician': 'Tech A'}, format='json')
        self.assertEqual(r.status_code, 200, r.content)
        prop.refresh_from_db()
        self.assertEqual(prop.tour_scan_technician, 'Tech A')
