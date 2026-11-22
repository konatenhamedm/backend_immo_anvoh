"""Recherche globale de l'en-tête du back-office."""

from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIClient

from apps.crm.infrastructure.models import Lead
from apps.properties.infrastructure.models import Property, PropertyStatus
from apps.users.infrastructure.models import User, UserRole

PASSWORD = "Un-Mot2Passe-Solide"


def make_user(email, role, first="Test"):
    return User.objects.create_user(
        email=email, password=PASSWORD, first_name=first, last_name="Nom", phone_number="+2250700000000", role=role
    )


def client_for(user):
    c = APIClient()
    c.force_authenticate(user)
    return c


class GlobalSearchTests(TestCase):
    URL = "/api/v1/crm/admin/search/"

    def setUp(self):
        self.admin = make_user("admin@test.ci", UserRole.ADMIN)
        self.agent = make_user("agent@test.ci", UserRole.AGENT)
        Property.objects.create(
            title="Villa Zéphyr",
            description="d",
            property_type="VILLA",
            price=Decimal("1"),
            commune="Cocody",
            neighborhood="Angré",
            surface_sqm=Decimal("100"),
            status=PropertyStatus.DISPONIBLE,
        )
        Property.objects.create(
            title="Zéphyr archivée",
            description="d",
            property_type="VILLA",
            price=Decimal("1"),
            commune="Cocody",
            neighborhood="Angré",
            surface_sqm=Decimal("100"),
            status=PropertyStatus.ARCHIVE,
        )
        Lead.objects.create(full_name="Zéphyrine Koffi", phone_number="+2250101010101")

    def test_finds_properties_leads_and_users_for_admin(self):
        r = client_for(self.admin).get(self.URL, {"q": "zéph"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual([p["title"] for p in r.data["properties"]], ["Villa Zéphyr"], "les biens archivés sont exclus")
        self.assertEqual([l["full_name"] for l in r.data["leads"]], ["Zéphyrine Koffi"])
        self.assertEqual(r.data["users"], [])
        users = client_for(self.admin).get(self.URL, {"q": "agent@test"})
        self.assertEqual([u["email"] for u in users.data["users"]], ["agent@test.ci"])

    def test_agent_never_sees_user_accounts(self):
        r = client_for(self.agent).get(self.URL, {"q": "agent@test"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["users"], [])

    def test_short_queries_return_nothing(self):
        r = client_for(self.admin).get(self.URL, {"q": "z"})
        self.assertEqual(r.data, {"properties": [], "leads": [], "users": []})

    def test_closed_to_non_team_roles(self):
        for role in (UserRole.PARTICULIER, UserRole.PROPRIETAIRE, UserRole.NOTAIRE):
            self.assertEqual(
                client_for(make_user(f"{role}@test.ci", role)).get(self.URL, {"q": "zéph"}).status_code, 403
            )
        self.assertEqual(APIClient().get(self.URL, {"q": "zéph"}).status_code, 401)
