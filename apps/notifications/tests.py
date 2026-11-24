"""Notifications : e-mail + application, attribution d'un conseiller, alertes de recherche, baisse de prix, relances."""

from datetime import date, timedelta
from decimal import Decimal
from io import StringIO

from django.core import mail
from django.core.cache import cache
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.crm.infrastructure.models import Lead, SearchAlert, VisitRequest, VisitRequestStatus
from apps.notifications.domain import kinds
from apps.notifications.infrastructure.models import FollowUpStatus, FollowUpTask, Notification
from apps.properties.infrastructure.models import Property, PropertyFavorite, PropertyStatus
from apps.users.infrastructure.models import User, UserRole

PASSWORD = "Un-Mot2Passe-Solide"


def make_user(email, role=UserRole.PARTICULIER, **extra):
    return User.objects.create_user(
        email=email, password=PASSWORD, first_name="Test", last_name="Nom", phone_number="+2250700000000", role=role, **extra
    )


def make_property(title="Villa Test", status=PropertyStatus.DISPONIBLE, **extra):
    data = dict(
        title=title,
        description="d",
        property_type="VILLA",
        transaction="VENTE",
        price=Decimal("60000000"),
        commune="Cocody",
        neighborhood="Abatta",
        surface_sqm=Decimal("100"),
        status=status,
    )
    data.update(extra)
    return Property.objects.create(**data)


def client_for(user):
    c = APIClient()
    c.force_authenticate(user)
    return c


class LeadNotificationTests(TestCase):
    """Une demande publique prévient le bon conseiller, par e-mail et dans l'application."""

    def setUp(self):
        cache.clear()  # le quota des formulaires publics (10/min) est partagé par tous les tests via le cache
        self.agent = make_user("agent@test.ci", UserRole.AGENT)
        self.admin = make_user("admin@test.ci", UserRole.ADMIN)
        self.prop = make_property(assigned_agent=self.agent)

    def _inquiry(self, phone="0707070707"):
        with self.captureOnCommitCallbacks(execute=True):
            return APIClient().post(
                "/api/v1/crm/inquiries/",
                {"property_id": str(self.prop.id), "full_name": "Awa Traoré", "phone_number": phone, "objective": "Investir"},
                format="json",
            )

    def test_inquiry_notifies_property_agent_in_app_and_by_email(self):
        self.assertEqual(self._inquiry().status_code, 201)
        n = Notification.objects.get(user=self.agent)
        self.assertEqual(n.kind, kinds.LEAD_NEW)
        self.assertIn("Awa Traoré", n.title)
        self.assertIn("/admin/crm?lead=", n.url)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["agent@test.ci"])
        self.assertIn("http://localhost:3100/admin/crm?lead=", mail.outbox[0].body)
        self.assertEqual(Notification.objects.filter(user=self.admin).count(), 0)  # l'admin n'est prévenu qu'à défaut de conseiller
        n.refresh_from_db()
        self.assertIsNotNone(n.emailed_at)

    def test_without_any_agent_admins_are_notified(self):
        self.prop.assigned_agent = None
        self.prop.save()
        self.agent.is_active = False
        self.agent.save()
        self._inquiry()
        self.assertEqual(Notification.objects.filter(user=self.admin, kind=kinds.LEAD_NEW).count(), 1)

    def test_lead_without_agent_gets_the_least_loaded_active_agent(self):
        self.prop.assigned_agent = None
        self.prop.save()
        busy = make_user("busy@test.ci", UserRole.AGENT)
        for i in range(2):
            Lead.objects.create(full_name=f"Déjà {i}", phone_number=f"+22505000000{i}", assigned_agent=busy)
        self._inquiry()
        self.assertEqual(Lead.objects.get(phone_number="+2250707070707").assigned_agent, self.agent)  # 0 prospect < 2

    def test_visit_request_notifies_agent_then_confirmation_notifies_visitor(self):
        visitor = make_user("client@test.ci")
        with self.captureOnCommitCallbacks(execute=True):
            r = client_for(visitor).post(
                "/api/v1/crm/visits/schedule/",
                {
                    "property_id": str(self.prop.id),
                    "full_name": "Client Test",
                    "phone_number": "0708080808",
                    "visit_type": "PHYSIQUE",
                    "scheduled_date": str(date.today() + timedelta(days=(5 - date.today().weekday()) % 7 + 7)),  # un samedi
                    "scheduled_time": "10:00",
                },
                format="json",
            )
        self.assertEqual(r.status_code, 201)
        self.assertTrue(Notification.objects.filter(user=self.agent, kind=kinds.VISIT_REQUESTED).exists())

        visit = VisitRequest.objects.get()
        with self.captureOnCommitCallbacks(execute=True):
            visit.status = VisitRequestStatus.CONFIRMEE
            visit.save()
            visit.save()  # un second enregistrement ne notifie pas deux fois
        n = Notification.objects.get(user=visitor, kind=kinds.VISIT_CONFIRMED)
        self.assertEqual(n.title, "Votre visite est confirmée pour samedi à 10h.")  # texte de la spécification
        self.assertEqual(Notification.objects.filter(user=visitor).count(), 1)

    def test_hot_find_my_property_lead_notifies_qualified_prospect(self):
        with self.captureOnCommitCallbacks(execute=True):
            r = APIClient().post(
                "/api/v1/crm/find-my-property/",
                {
                    "full_name": "Chaud Lead",
                    "phone_number": "0709090909",
                    "objective": "Investir",
                    "property_type": "Villa",
                    "preferred_zone": "Cocody",
                    "budget_range": "50-80 M",
                    "budget_amount": 80000000,
                    "down_payment": 20000000,
                    "timeframe": "0-3 mois",
                    "residence_location": "Côte d'Ivoire",
                },
                format="json",
            )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["temperature"], "CHAUD")
        kinds_sent = set(Notification.objects.filter(user=self.agent).values_list("kind", flat=True))
        self.assertEqual(kinds_sent, {kinds.LEAD_NEW, kinds.LEAD_QUALIFIED})

    def test_email_failure_never_breaks_the_request(self):
        from unittest import mock

        with mock.patch("apps.notifications.application.service.send_mail", side_effect=OSError("SMTP en panne")):
            with self.assertLogs("apps.notifications.application.service", level="ERROR"):
                r = self._inquiry()
        self.assertEqual(r.status_code, 201)
        n = Notification.objects.get(user=self.agent)
        self.assertIsNone(n.emailed_at)  # visible dans l'application, e-mail non parti


class AlertAndPriceTests(TestCase):
    def setUp(self):
        self.user = make_user("client@test.ci")
        self.alert = SearchAlert.objects.create(user=self.user, commune="Cocody", transaction="VENTE", max_budget=Decimal("80000000"))

    def test_publishing_a_matching_property_notifies_the_alert_owner_once(self):
        draft = make_property("Brouillon", status=PropertyStatus.BROUILLON)
        self.assertEqual(Notification.objects.count(), 0)  # un brouillon n'est pas publié
        with self.captureOnCommitCallbacks(execute=True):
            draft.status = PropertyStatus.DISPONIBLE
            draft.save()
            draft.save()
        n = Notification.objects.get()
        self.assertEqual(n.kind, kinds.NEW_MATCH)
        self.assertEqual(n.title, "Nouveau bien disponible à Abatta Cocody.")
        self.assertEqual(n.url, f"/biens/{draft.slug}")
        self.alert.refresh_from_db()
        self.assertIsNotNone(self.alert.last_notified_at)
        self.assertEqual(len(mail.outbox), 1)

    def test_non_matching_property_does_not_notify(self):
        make_property("Trop cher", price=Decimal("200000000"))
        make_property("Autre commune", commune="Marcory")
        self.assertEqual(Notification.objects.count(), 0)

    def test_user_preferences_are_respected(self):
        self.user.notification_preferences = {"new_matches": False}
        self.user.save()
        make_property()
        self.assertEqual(Notification.objects.count(), 0)
        self.user.notification_preferences = {}
        self.user.notifications_enabled = False
        self.user.save()
        make_property("Deuxième")
        self.assertEqual(Notification.objects.count(), 0)

    def test_price_drop_notifies_users_who_favorited(self):
        prop = make_property(price=Decimal("90000000"))  # hors budget de l'alerte : seul le favori compte
        PropertyFavorite.objects.create(user=self.user, property=prop)
        Notification.objects.all().delete()
        prop.price = Decimal("85000000")
        prop.save()
        n = Notification.objects.get()
        self.assertEqual(n.kind, kinds.PRICE_DROP)
        self.assertIn("85 000 000", n.body)
        prop.price = Decimal("95000000")  # une hausse ne notifie pas
        prop.save()
        self.assertEqual(Notification.objects.count(), 1)

    def test_loading_commands_are_silent(self):
        from unittest import mock

        with mock.patch("sys.argv", ["manage.py", "load_demo_data"]):
            make_property("Chargement de démo")
        self.assertEqual(Notification.objects.count(), 0)


class NotificationApiTests(TestCase):
    def setUp(self):
        self.me = make_user("me@test.ci")
        self.other = make_user("other@test.ci")
        from apps.notifications.application.service import notify

        self.a = notify(self.me, kinds.NEW_MATCH, "Première")
        self.b = notify(self.me, kinds.NEW_MATCH, "Deuxième")
        notify(self.other, kinds.NEW_MATCH, "Pour quelqu'un d'autre")

    def test_list_count_and_read(self):
        c = client_for(self.me)
        self.assertEqual(c.get("/api/v1/notifications/unread-count/").data["unread"], 2)
        titles = [n["title"] for n in c.get("/api/v1/notifications/").data["results"]]
        self.assertEqual(sorted(titles), ["Deuxième", "Première"])  # jamais celles des autres
        self.assertTrue(c.post(f"/api/v1/notifications/{self.a.id}/read/").data["is_read"])
        self.assertEqual(c.get("/api/v1/notifications/unread-count/").data["unread"], 1)
        self.assertEqual(len(c.get("/api/v1/notifications/?unread=1").data["results"]), 1)
        c.post("/api/v1/notifications/read-all/")
        self.assertEqual(c.get("/api/v1/notifications/unread-count/").data["unread"], 0)

    def test_cannot_read_someone_elses_notification(self):
        n = Notification.objects.get(user=self.other)
        self.assertEqual(client_for(self.me).post(f"/api/v1/notifications/{n.id}/read/").status_code, 404)

    def test_requires_login(self):
        self.assertEqual(APIClient().get("/api/v1/notifications/").status_code, 401)


class FollowUpTests(TestCase):
    def setUp(self):
        self.agent = make_user("agent@test.ci", UserRole.AGENT)
        self.admin = make_user("admin@test.ci", UserRole.ADMIN)
        self.lead = Lead.objects.create(full_name="Inactif", phone_number="+2250701010101", assigned_agent=self.agent)

    def _age(self, lead, days):
        # last_interaction_at est en auto_now : seul update() permet de le vieillir.
        Lead.objects.filter(pk=lead.pk).update(last_interaction_at=timezone.now() - timedelta(days=days))

    def _run(self, *args):
        out = StringIO()
        with self.captureOnCommitCallbacks(execute=True):
            call_command("create_followups", *args, stdout=out)
        return out.getvalue()

    def test_stale_lead_gets_one_task_and_its_agent_is_notified(self):
        self._age(self.lead, 5)
        self._run("--days", "3")
        task = FollowUpTask.objects.get()
        self.assertEqual((task.lead, task.assigned_to, task.status), (self.lead, self.agent, FollowUpStatus.OUVERTE))
        self.assertIn("3 jours", task.reason)
        self.assertEqual(Notification.objects.get(user=self.agent).kind, kinds.FOLLOWUP_DUE)
        self._run("--days", "3")  # deuxième passage : pas de doublon
        self.assertEqual(FollowUpTask.objects.count(), 1)

    def test_recent_closed_and_dry_run_are_left_alone(self):
        recent = Lead.objects.create(full_name="Récent", phone_number="+2250702020202")
        sold = Lead.objects.create(full_name="Vendu", phone_number="+2250703030303", stage="VENTE")
        lost = Lead.objects.create(full_name="Perdu", phone_number="+2250704040404", stage="PERDU")
        for lead in (recent,):
            self._age(lead, 1)
        for lead in (sold, lost):
            self._age(lead, 30)
        self._age(self.lead, 5)
        self._run("--days", "3", "--dry-run")
        self.assertEqual(FollowUpTask.objects.count(), 0)
        self._run("--days", "3")
        self.assertEqual(list(FollowUpTask.objects.values_list("lead__full_name", flat=True)), ["Inactif"])

    def test_done_task_allows_a_new_one_later(self):
        self._age(self.lead, 5)
        self._run("--days", "3")
        task = FollowUpTask.objects.get()
        r = client_for(self.agent).post(f"/api/v1/notifications/followups/{task.id}/done/")
        self.assertEqual(r.data["status"], "FAITE")
        self._age(self.lead, 5)
        self._run("--days", "3")
        self.assertEqual(FollowUpTask.objects.count(), 2)

    def test_api_agent_sees_own_admin_sees_all_buyer_is_refused(self):
        other_agent = make_user("agent2@test.ci", UserRole.AGENT)
        mine = FollowUpTask.objects.create(lead=self.lead, assigned_to=self.agent, reason="x", due_date=date.today())
        theirs_lead = Lead.objects.create(full_name="Autre", phone_number="+2250705050505", assigned_agent=other_agent)
        FollowUpTask.objects.create(lead=theirs_lead, assigned_to=other_agent, reason="y", due_date=date.today())
        self.assertEqual([t["id"] for t in client_for(self.agent).get("/api/v1/notifications/followups/").data["results"]], [str(mine.id)])
        self.assertEqual(len(client_for(self.admin).get("/api/v1/notifications/followups/").data["results"]), 2)
        self.assertEqual(client_for(make_user("buyer@test.ci")).get("/api/v1/notifications/followups/").status_code, 403)
        # Un conseiller ne peut pas clore la relance d'un collègue.
        theirs = FollowUpTask.objects.get(lead=theirs_lead)
        self.assertEqual(client_for(self.agent).post(f"/api/v1/notifications/followups/{theirs.id}/done/").status_code, 404)
