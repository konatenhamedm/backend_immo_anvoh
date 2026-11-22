"""Accueil et « Investir » : programmes neufs sans leurs lots (réponses allégées) ; la liste détaillée garde ses lots."""

from decimal import Decimal

from django.core.cache import cache
from django.test import TestCase
from rest_framework.test import APIClient

from apps.properties.infrastructure.models import DevelopmentProject, ProjectLot, PropertyStatus
from apps.users.infrastructure.models import User, UserRole


def make_project(name, statuses):
    project = DevelopmentProject.objects.create(
        name=name,
        developer_name="SCI Test",
        commune="Cocody",
        neighborhood="Angré",
        description="Programme de test",
        total_lots_count=len(statuses),
        starting_price=Decimal("30000000"),
    )
    for i, status in enumerate(statuses):
        ProjectLot.objects.create(
            project=project,
            lot_number=f"Lot {i + 1}",
            surface_sqm=Decimal("80"),
            price=Decimal("30000000"),
            status=status,
        )
    return project


class LighterProgramsTests(TestCase):
    def setUp(self):
        cache.clear()
        self.project = make_project(
            "Résidence Test",
            [PropertyStatus.VENDU] * 3
            + [PropertyStatus.DISPONIBLE] * 2
            + [PropertyStatus.RESERVE, PropertyStatus.OPTION],
        )

    def _programs(self, path):
        r = APIClient().get(path)
        self.assertEqual(r.status_code, 200)
        return r.data["development_projects"]

    def test_home_programs_have_counts_but_no_lot_list(self):
        (program,) = self._programs("/api/v1/properties/home/")
        self.assertNotIn("lots", program)
        self.assertNotIn("description", program)
        self.assertEqual(program["total_lots_count"], 7)
        self.assertEqual(program["lots_sold"], 3)
        self.assertEqual(program["lots_available"], 2, "réservés et en option ne sont pas « disponibles »")

    def test_invest_programs_are_light_too(self):
        (program,) = self._programs("/api/v1/properties/invest/")
        self.assertNotIn("lots", program)
        self.assertEqual((program["lots_sold"], program["lots_available"]), (3, 2))

    def test_counts_cost_a_single_query_whatever_the_number_of_lots(self):
        for i in range(5):
            make_project(f"Programme {i}", [PropertyStatus.DISPONIBLE] * 40)
        client = APIClient()
        client.get("/api/v1/properties/home/")  # chauffe
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        with CaptureQueriesContext(connection) as queries:
            client.get("/api/v1/properties/home/")
        lot_queries = [
            q
            for q in queries
            if "properties_projectlot" in q["sql"]
            and "GROUP BY" not in q["sql"].upper()
            and "COUNT" not in q["sql"].upper()
        ]
        self.assertEqual(lot_queries, [], "aucun lot n'est chargé un par un")

    def test_detailed_list_keeps_its_lots_for_the_back_office(self):
        admin = User.objects.create_user(
            email="admin@test.ci",
            password="Un-Mot2Passe-Solide",
            first_name="A",
            last_name="B",
            phone_number="+2250700000000",
            role=UserRole.ADMIN,
        )
        c = APIClient()
        c.force_authenticate(admin)
        r = c.get("/api/v1/properties/projects/")
        self.assertEqual(r.status_code, 200)
        program = r.data["results"][0]
        self.assertEqual(len(program["lots"]), 7)
        self.assertEqual(program["lots_sold"], 3)
