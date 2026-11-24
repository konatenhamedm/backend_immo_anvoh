"""Garde-fou de sécurité : parcourt TOUTES les routes de l'API et vérifie qui peut les appeler.

Si une nouvelle route apparaît avec `AllowAny` (ou sans permission explicite), `test_only_declared_routes_are_public`
échoue : il faut alors soit la protéger, soit l'ajouter volontairement à PUBLIC_OPERATIONS ci-dessous.
"""

import re
import uuid

from django.core.cache import cache
from django.test import TestCase
from django.urls import get_resolver
from rest_framework.test import APIClient

from apps.users.infrastructure.models import User, UserRole

API_PREFIX = "api/v1/"
METHODS = ("get", "post", "put", "patch", "delete")
DUMMY = {"uuid": str(uuid.uuid4()), "int": "1", "slug": "x", "str": "x"}

# Opérations accessibles SANS connexion, par choix : (méthode, route).
PUBLIC_OPERATIONS = {
    # Authentification
    ("post", "auth/register/"),
    ("post", "auth/login/"),
    ("post", "auth/token/refresh/"),
    ("post", "auth/password/forgot/"),
    ("post", "auth/password/reset/"),
    ("post", "auth/code/request/"),
    ("post", "auth/code/verify/"),
    ("post", "auth/google/"),
    # Catalogue public
    ("get", "properties/home/"),
    ("get", "properties/search/"),
    ("get", "properties/meta/"),
    ("get", "properties/places/"),
    ("get", "properties/slugs/"),
    ("get", "properties/slug/<slug:slug>/"),
    ("get", "properties/<uuid:id>/"),
    ("get", "properties/invest/"),
    ("get", "properties/projects/"),
    ("get", "properties/projects/slug/<slug:slug>/"),
    ("get", "properties/projects/<uuid:id>/"),
    ("get", "properties/projects/<uuid:project_id>/lots/"),
    ("get", "properties/lots/<uuid:id>/"),
    # Référentiels publics
    ("get", "accreditation/notaries/"),
    ("get", "investments/plans/"),
    # Simulateurs
    ("post", "simulators/calculate-investment/"),
    ("post", "simulators/borrowing-capacity/"),
    # Formulaires de contact et de réservation (visiteurs non connectés)
    ("post", "crm/inquiries/"),
    ("post", "crm/whatsapp-click/"),
    ("post", "crm/find-my-property/"),
    ("post", "crm/diaspora-contact/"),
    # Mesure d'audience : événements envoyés par le navigateur (liste fermée, aucune donnée personnelle)
    ("post", "analytics/events/"),
    ("post", "crm/visits/schedule/"),
}

# Routes réservées à l'équipe, aux propriétaires ou aux notaires : un acheteur doit recevoir 403 sur toutes les méthodes.
RESTRICTED = re.compile(
    r"(^|/)admin/"
    r"|^auth/users/"
    r"|^crm/(pipeline|leads|visits/<uuid|inquiries/list|inquiries/<uuid)"
    r"|^crm/visits/$"
    r"|^crm/owner/"
    r"|^properties/owner/"
    r"|^rentals/owner/"
    r"|^accreditation/(queue|documents|owner)"
)

# Lecture publique, écriture réservée à l'équipe : un acheteur doit recevoir 403 sur les écritures.
STAFF_WRITE = {
    "properties/search/",
    "properties/<uuid:id>/",
    "properties/projects/",
    "properties/projects/<uuid:id>/",
    "properties/projects/<uuid:project_id>/lots/",
    "properties/lots/<uuid:id>/",
}


def _walk(patterns, prefix=""):
    for p in patterns:
        route = prefix + str(p.pattern)
        if hasattr(p, "url_patterns"):
            yield from _walk(p.url_patterns, route)
        else:
            yield route


def api_routes():
    return sorted(r[len(API_PREFIX) :] for r in _walk(get_resolver().url_patterns) if r.startswith(API_PREFIX))


def concrete(route):
    return "/" + API_PREFIX + re.sub(r"<(\w+):(\w+)>", lambda m: DUMMY[m.group(1)], route)


def call(client, method, route):
    return getattr(client, method)(concrete(route), {}, format="json").status_code


class ApiSurfaceTests(TestCase):
    def setUp(self):
        cache.clear()  # les quotas par scope sont comptés dans le cache : repartir de zéro

    def test_routes_are_discovered(self):
        # Si l'analyse des routes casse, les autres tests passeraient à vide.
        self.assertGreater(len(api_routes()), 60)

    def test_only_declared_routes_are_public(self):
        anon = APIClient()
        leaks = []
        for route in api_routes():
            cache.clear()  # compteur de quota partagé entre les formulaires publics
            for method in METHODS:
                status = call(anon, method, route)
                if (method, route) in PUBLIC_OPERATIONS:
                    self.assertNotIn(status, (401, 403), f"{method.upper()} {route} devrait rester public ({status})")
                elif status not in (401, 403, 405):
                    leaks.append(f"{method.upper()} {route} -> {status}")
        self.assertEqual(leaks, [], "Routes accessibles sans connexion et non déclarées publiques")

    def test_public_allowlist_has_no_dead_entries(self):
        routes = set(api_routes())
        dead = sorted(op for op in PUBLIC_OPERATIONS if op[1] not in routes)
        self.assertEqual(dead, [], "PUBLIC_OPERATIONS référence des routes qui n'existent plus")

    def test_buyer_is_locked_out_of_restricted_routes(self):
        buyer = APIClient()
        buyer.force_authenticate(
            User.objects.create_user(
                email="acheteur@test.ci",
                password="Un-Mot2Passe-Solide",
                first_name="A",
                last_name="B",
                phone_number="+2250700000000",
                role=UserRole.PARTICULIER,
            )
        )
        restricted = [r for r in api_routes() if RESTRICTED.search(r)]
        self.assertGreater(len(restricted), 20)
        leaks = []
        for route in restricted:
            cache.clear()
            for method in METHODS:
                status = call(buyer, method, route)
                if status not in (403, 405):
                    leaks.append(f"{method.upper()} {route} -> {status}")
        self.assertEqual(leaks, [], "Un acheteur accède à des routes réservées")

    def test_buyer_cannot_write_staff_managed_resources(self):
        buyer = APIClient()
        buyer.force_authenticate(
            User.objects.create_user(
                email="acheteur2@test.ci",
                password="Un-Mot2Passe-Solide",
                first_name="A",
                last_name="B",
                phone_number="+2250700000001",
                role=UserRole.PARTICULIER,
            )
        )
        leaks = []
        for route in sorted(STAFF_WRITE):
            cache.clear()
            for method in ("post", "put", "patch", "delete"):
                status = call(buyer, method, route)
                if status not in (403, 405):
                    leaks.append(f"{method.upper()} {route} -> {status}")
        self.assertEqual(leaks, [], "Un acheteur peut écrire sur une ressource gérée par l'équipe")


class ThrottlingTests(TestCase):
    """Les formulaires publics et la connexion ont un quota propre (anti-spam, anti-force brute)."""

    def setUp(self):
        cache.clear()

    def tearDown(self):
        cache.clear()  # ne pas laisser de compteur saturé aux autres tests

    def _hammer(self, path, body, attempts):
        client = APIClient()
        return [client.post(f"/api/v1/{path}", body, format="json").status_code for _ in range(attempts)]

    def test_login_is_limited(self):
        codes = self._hammer("auth/login/", {"email": "x@test.ci", "password": "faux"}, 22)
        self.assertEqual(codes[:20], [401] * 20)
        self.assertEqual(set(codes[20:]), {429})

    def test_public_forms_are_limited(self):
        for path in (
            "crm/inquiries/",
            "crm/whatsapp-click/",
            "crm/find-my-property/",
            "crm/diaspora-contact/",
            "crm/visits/schedule/",
        ):
            cache.clear()
            codes = self._hammer(path, {}, 12)
            self.assertNotIn(429, codes[:10], path)
            self.assertEqual(set(codes[10:]), {429}, f"{path} : le 11e envoi doit être refusé")

    def test_read_endpoints_are_not_affected(self):
        client = APIClient()
        self.assertTrue(all(client.get("/api/v1/properties/home/").status_code == 200 for _ in range(15)))
