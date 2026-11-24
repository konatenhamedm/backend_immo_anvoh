"""Mesure et acquisition : canal d'origine des prospects, événements, vente datée, ROI par canal."""

from datetime import date, timedelta
from decimal import Decimal

from django.core.cache import cache
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.analytics.application import reporting
from apps.analytics.domain import events as ev
from apps.analytics.domain.events import clean_properties
from apps.analytics.infrastructure.models import AnalyticsEvent, ChannelSpend
from apps.crm.infrastructure.models import Lead
from apps.properties.infrastructure.models import Property, PropertyStatus
from apps.users.infrastructure.models import User, UserRole

PASSWORD = "Un-Mot2Passe-Solide"


def make_user(email, role=UserRole.PARTICULIER):
    return User.objects.create_user(email=email, password=PASSWORD, first_name="T", last_name="N", phone_number="+2250700000000", role=role)


def make_property(**extra):
    data = dict(title="Villa", description="d", property_type="VILLA", price=Decimal("50000000"), commune="Cocody", neighborhood="Angré", surface_sqm=Decimal("90"), status=PropertyStatus.DISPONIBLE)
    data.update(extra)
    return Property.objects.create(**data)


class AttributionTests(TestCase):
    """Le canal d'origine est enregistré à la création du prospect, une fois pour toutes."""

    def setUp(self):
        cache.clear()  # quota des formulaires publics partagé entre les tests
        self.prop = make_property()

    def _inquiry(self, phone, attribution=None):
        body = {"property_id": str(self.prop.id), "full_name": "Awa", "phone_number": phone, "objective": "Investir"}
        if attribution is not None:
            body["attribution"] = attribution
        return APIClient().post("/api/v1/crm/inquiries/", body, format="json")

    def test_channel_and_utm_are_saved_on_the_new_lead(self):
        r = self._inquiry("0707070707", {"channel": "FACEBOOK", "utm_source": "facebook", "utm_medium": "paid", "utm_campaign": "lancement-nov", "landing_path": "/diaspora"})
        self.assertEqual(r.status_code, 201)
        lead = Lead.objects.get(id=r.data["lead_id"])
        self.assertEqual((lead.acquisition_channel, lead.utm_source, lead.utm_medium, lead.utm_campaign, lead.landing_path), ("FACEBOOK", "facebook", "paid", "lancement-nov", "/diaspora"))

    def test_without_attribution_the_lead_comes_from_the_website(self):
        lead = Lead.objects.get(id=self._inquiry("0707070708").data["lead_id"])
        self.assertEqual(lead.acquisition_channel, "SITE_WEB")

    def test_first_touch_is_never_overwritten(self):
        self._inquiry("0707070709", {"channel": "GOOGLE"})
        self._inquiry("0707070709", {"channel": "FACEBOOK", "utm_source": "autre"})  # même téléphone, canal différent
        lead = Lead.objects.get(phone_number="+2250707070709")
        self.assertEqual((lead.acquisition_channel, lead.utm_source), ("GOOGLE", ""))

    def test_unknown_channel_is_rejected(self):
        self.assertEqual(self._inquiry("0707070710", {"channel": "TIKTOK"}).status_code, 400)

    def test_team_created_lead_can_carry_a_channel(self):
        admin = make_user("admin@test.ci", UserRole.ADMIN)
        c = APIClient()
        c.force_authenticate(admin)
        r = c.post("/api/v1/crm/leads/", {"full_name": "Salon", "phone_number": "0711111111", "acquisition_channel": "PARRAINAGE"}, format="json")
        self.assertEqual(r.status_code, 201)
        self.assertEqual(Lead.objects.get(phone_number="+2250711111111").acquisition_channel, "PARRAINAGE")


class ServerEventTests(TestCase):
    def setUp(self):
        cache.clear()
        self.prop = make_property()

    def test_conversion_events_are_recorded_with_their_channel(self):
        c = APIClient()
        att = {"channel": "INSTAGRAM"}
        c.post("/api/v1/crm/inquiries/", {"property_id": str(self.prop.id), "full_name": "A", "phone_number": "0712121212", "objective": "Habiter", "attribution": att}, format="json")
        c.post("/api/v1/crm/whatsapp-click/", {"property_id": str(self.prop.id), "attribution": att}, format="json")  # anonyme : pas de prospect
        c.post("/api/v1/crm/visits/schedule/", {"property_id": str(self.prop.id), "full_name": "A", "phone_number": "0712121212", "scheduled_date": str(date.today() + timedelta(days=2)), "scheduled_time": "10:00", "attribution": att}, format="json")
        names = {e.name: e.channel for e in AnalyticsEvent.objects.all()}
        self.assertEqual(names, {ev.LEAD_CREATED: "INSTAGRAM", ev.INQUIRY: "INSTAGRAM", ev.WHATSAPP_CLICK: "INSTAGRAM", ev.VISIT_REQUESTED: "INSTAGRAM"})
        self.assertEqual(AnalyticsEvent.objects.filter(name=ev.LEAD_CREATED).count(), 1)  # une seule création, pas une par appel

    def test_favorite_added_is_recorded_but_not_removal(self):
        user = make_user("c@test.ci")
        c = APIClient()
        c.force_authenticate(user)
        c.post(f"/api/v1/properties/favorites/{self.prop.id}/toggle/")
        c.post(f"/api/v1/properties/favorites/{self.prop.id}/toggle/")  # retrait
        self.assertEqual(AnalyticsEvent.objects.filter(name=ev.FAVORITE_ADD).count(), 1)

    def test_sale_gets_a_date_and_an_event_once(self):
        lead = Lead.objects.create(full_name="Acheteur", phone_number="+2250713131313", acquisition_channel="GOOGLE")
        self.assertIsNone(lead.converted_at)
        lead.stage = "VENTE"
        lead.save()
        lead.refresh_from_db()
        self.assertIsNotNone(lead.converted_at)
        lead.save()  # un enregistrement de plus ne compte pas une seconde vente
        self.assertEqual(AnalyticsEvent.objects.filter(name=ev.SALE, channel="GOOGLE").count(), 1)
        lead.stage = "NEGOCIATION"  # vente annulée par l'équipe
        lead.save()
        lead.refresh_from_db()
        self.assertIsNone(lead.converted_at)


class IngestTests(TestCase):
    URL = "/api/v1/analytics/events/"
    ANON = "b7f3c2a1-1111-2222-3333-444455556666"

    def setUp(self):
        cache.clear()

    def _post(self, events, anon=None, client=None):
        return (client or APIClient()).post(self.URL, {"anonymous_id": anon or self.ANON, "events": events}, format="json")

    def test_accepts_client_events_without_login(self):
        r = self._post([{"name": "SESSION_START", "path": "/"}, {"name": "SEARCH", "path": "/biens", "properties": {"q": "Cocody", "results": 12}}])
        self.assertEqual(r.status_code, 204)
        self.assertEqual(AnalyticsEvent.objects.count(), 2)
        e = AnalyticsEvent.objects.get(name="SEARCH")
        self.assertEqual((e.anonymous_id, e.properties), (self.ANON, {"q": "Cocody", "results": 12}))

    def test_server_only_and_unknown_events_are_refused(self):
        for name in ("SALE", "LEAD_CREATED", "FAVORITE_ADD", "N_IMPORTE_QUOI"):
            self.assertEqual(self._post([{"name": name}]).status_code, 400, name)
        self.assertEqual(AnalyticsEvent.objects.count(), 0)  # impossible de gonfler les ventes depuis le navigateur

    def test_personal_data_is_dropped(self):
        self._post([{"name": "SEARCH", "properties": {"q": "villa", "email": "x@y.ci", "phone": "0707", "full_name": "Awa", "message": "salut", "nested": {"a": 1}}}])
        self.assertEqual(AnalyticsEvent.objects.get().properties, {"q": "villa"})
        self.assertEqual(clean_properties({"password": "x", "ok": True}), {"ok": True})
        self.assertEqual(len(clean_properties({f"k{i}": i for i in range(50)})), 12)
        self.assertEqual(len(clean_properties({"long": "x" * 500})["long"]), 120)

    def test_batch_limits_and_anonymous_id_format(self):
        self.assertEqual(self._post([{"name": "SEARCH"}] * 21).status_code, 400)
        self.assertEqual(self._post([]).status_code, 400)
        self.assertEqual(self._post([{"name": "SEARCH"}], anon="court").status_code, 400)

    def test_logged_in_user_is_attached(self):
        user = make_user("c@test.ci")
        c = APIClient()
        c.force_authenticate(user)
        self._post([{"name": "SIGNUP", "channel": "SITE_WEB"}], client=c)
        self.assertEqual(AnalyticsEvent.objects.get().user, user)

    def test_throttled(self):
        from django.core.cache import cache

        cache.clear()
        codes = [self._post([{"name": "SEARCH"}]).status_code for _ in range(250)]
        self.assertIn(429, codes)
        cache.clear()


class SummaryTests(TestCase):
    def setUp(self):
        self.admin = make_user("admin@test.ci", UserRole.ADMIN)
        self.client_api = APIClient()
        self.client_api.force_authenticate(self.admin)

    def _event(self, name, anon="visitor-00-xxxx", channel="", **props):
        return AnalyticsEvent.objects.create(name=name, anonymous_id=anon, channel=channel, properties=props)

    def test_kpis_funnel_and_roi_by_channel(self):
        for i in range(4):
            self._event("SESSION_START", anon=f"visitor-{i % 3:02d}-xxxx")  # 3 navigateurs distincts, 4 sessions
        self._event("SEARCH")
        self._event("PROPERTY_VIEW", property="THI-1")
        self._event("PROPERTY_VIEW", property="THI-1")
        self._event("APP_INSTALLED")
        self._event("SIGNUP")
        # 4 prospects Facebook (1 vendu), 1 Google (non vendu), 1 saisi par l'équipe (vendu, hors app)
        for i in range(4):
            Lead.objects.create(full_name=f"FB{i}", phone_number=f"+2250720000{i:03d}", acquisition_channel="FACEBOOK", temperature="CHAUD" if i < 2 else "FROID")
        sold = Lead.objects.get(full_name="FB0")
        sold.stage = "VENTE"
        sold.save()
        Lead.objects.create(full_name="G0", phone_number="+2250730000000", acquisition_channel="GOOGLE")
        manual = Lead.objects.create(full_name="Manuel", phone_number="+2250740000000", acquisition_channel="AUTRE")
        manual.stage = "VENTE"
        manual.save()
        ChannelSpend.objects.create(channel="FACEBOOK", month=date.today().replace(day=1), amount=Decimal("200000"))

        s = reporting.summary(30)
        t = s["totals"]
        self.assertEqual((t["sessions"], t["active_users"], t["searches"], t["properties_viewed"], t["distinct_properties_viewed"]), (4, 3, 1, 2, 1))
        self.assertEqual((t["downloads"], t["signups"], t["leads"], t["conversions"]), (1, 1, 6, 2))
        self.assertEqual(t["sales_generated_by_app"], 1)  # la vente saisie à la main (canal « Autre ») n'est pas comptée
        fb = next(r for r in s["by_channel"] if r["channel"] == "FACEBOOK")
        self.assertEqual((fb["leads"], fb["qualified"], fb["sales"], fb["conversion_rate"]), (4, 2, 1, 0.25))
        self.assertEqual((fb["spend"], fb["cost_per_lead"], fb["cost_per_sale"]), (Decimal("200000"), Decimal("50000.00"), Decimal("200000.00")))
        google = next(r for r in s["by_channel"] if r["channel"] == "GOOGLE")
        self.assertEqual((google["leads"], google["sales"], google["cost_per_lead"], google["cost_per_sale"]), (1, 0, None, None))
        self.assertEqual([f["step"] for f in s["funnel"]], ["Sessions", "Recherches", "Biens consultés", "Leads", "Visites demandées", "Ventes"])
        self.assertTrue(s["daily"])

    def test_period_excludes_old_activity(self):
        old = self._event("SESSION_START")
        AnalyticsEvent.objects.filter(pk=old.pk).update(occurred_at=timezone.now() - timedelta(days=60))
        self.assertEqual(reporting.summary(30)["totals"]["sessions"], 0)
        self.assertEqual(reporting.summary(90)["totals"]["sessions"], 1)

    def test_api_is_for_administrators_only(self):
        self.assertEqual(self.client_api.get("/api/v1/analytics/summary/?days=7").data["period"]["days"], 7)
        self.assertEqual(self.client_api.get("/api/v1/analytics/summary/?days=abc").data["period"]["days"], 30)
        self.assertEqual(self.client_api.get("/api/v1/analytics/summary/?days=9999").data["period"]["days"], 365)
        for user in (make_user("agent@test.ci", UserRole.AGENT), make_user("buyer@test.ci")):
            c = APIClient()
            c.force_authenticate(user)
            self.assertEqual(c.get("/api/v1/analytics/summary/").status_code, 403, user.role)
        self.assertEqual(APIClient().get("/api/v1/analytics/summary/").status_code, 401)
