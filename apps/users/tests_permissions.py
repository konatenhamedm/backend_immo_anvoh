"""Qui est « administrateur » pour l'API : le rôle ADMIN (ou un superutilisateur), jamais le seul drapeau is_staff."""

from django.test import TestCase
from rest_framework.test import APIClient

from apps.users.infrastructure.models import User, UserRole
from apps.users.interfaces.permissions import is_admin, is_staff_or_agent

PASSWORD = "Un-Mot2Passe-Solide"
ADMIN_ONLY_ROUTE = "/api/v1/rentals/admin/leases/"  # IsAdminRole
TEAM_ROUTE = "/api/v1/crm/admin/dashboard/"  # IsStaffOrAgent


def make_user(email, role, **extra):
    return User.objects.create_user(
        email=email,
        password=PASSWORD,
        first_name="Test",
        last_name="Nom",
        phone_number="+2250700000000",
        role=role,
        **extra,
    )


def client_for(user):
    c = APIClient()
    c.force_authenticate(user)
    return c


class AdminMeansAdminRoleTests(TestCase):
    def test_staff_flag_does_not_make_an_agent_an_administrator(self):
        agent = make_user("agent@test.ci", UserRole.AGENT, is_staff=True)
        self.assertFalse(is_admin(agent))
        self.assertTrue(is_staff_or_agent(agent), "il reste un conseiller")
        self.assertEqual(client_for(agent).get(ADMIN_ONLY_ROUTE).status_code, 403)
        self.assertEqual(client_for(agent).get("/api/v1/auth/users/").status_code, 403)
        self.assertEqual(client_for(agent).get(TEAM_ROUTE).status_code, 200, "ses droits de conseiller sont intacts")
        self.assertFalse(client_for(agent).get("/api/v1/auth/profile/").data["is_admin"])

    def test_staff_flag_gives_nothing_to_other_roles(self):
        for role in (UserRole.PARTICULIER, UserRole.PROPRIETAIRE, UserRole.NOTAIRE):
            user = make_user(f"{role}@test.ci", role, is_staff=True)
            self.assertFalse(is_admin(user), role)
            self.assertEqual(client_for(user).get(ADMIN_ONLY_ROUTE).status_code, 403, role)

    def test_admin_role_works_without_the_staff_flag(self):
        admin = make_user("admin@test.ci", UserRole.ADMIN)
        self.assertFalse(admin.is_staff)
        self.assertTrue(is_admin(admin))
        self.assertEqual(client_for(admin).get(ADMIN_ONLY_ROUTE).status_code, 200)
        self.assertTrue(client_for(admin).get("/api/v1/auth/profile/").data["is_admin"])

    def test_superuser_is_administrator_even_without_the_role(self):
        root = make_user("root@test.ci", UserRole.PARTICULIER, is_superuser=True)
        self.assertTrue(is_admin(root))
        self.assertEqual(client_for(root).get(ADMIN_ONLY_ROUTE).status_code, 200)

    def test_createsuperuser_gives_the_admin_role(self):
        root = User.objects.create_superuser(email="su@test.ci", password=PASSWORD)
        self.assertEqual(root.role, UserRole.ADMIN)
        self.assertTrue(is_admin(root))

    def test_anonymous_is_not_administrator(self):
        self.assertFalse(is_admin(None))
        self.assertEqual(APIClient().get(ADMIN_ONLY_ROUTE).status_code, 401)

    def test_changing_a_role_through_the_api_keeps_staff_flag_consistent(self):
        admin = make_user("admin2@test.ci", UserRole.ADMIN)
        target = make_user("cible@test.ci", UserRole.AGENT)
        r = client_for(admin).patch(f"/api/v1/auth/users/{target.id}/", {"role": "ADMIN"}, format="json")
        self.assertEqual(r.status_code, 200)
        target.refresh_from_db()
        self.assertTrue(is_admin(target))
        r = client_for(admin).patch(f"/api/v1/auth/users/{target.id}/", {"role": "AGENT"}, format="json")
        target.refresh_from_db()
        self.assertFalse(is_admin(target), "rétrogradé : plus administrateur")
        self.assertFalse(target.is_staff)
