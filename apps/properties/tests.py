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


class SearchFiltersTests(TestCase):
    """Écran 05 : disponibilité et tri par pertinence du moteur de recherche."""

    URL = "/api/v1/properties/search/"

    def setUp(self):
        from apps.properties.infrastructure.models import Property

        def make(title, commune, status, **extra):
            return Property.objects.create(
                title=title,
                description="d",
                property_type="VILLA",
                price=Decimal("50000000"),
                commune=commune,
                neighborhood="Angré",
                surface_sqm=Decimal("100"),
                status=status,
                **extra,
            )

        make("Villa Cocody", "Cocody", PropertyStatus.RESERVE)
        make("Terrain Cocody", "Cocody", PropertyStatus.DISPONIBLE)
        # Créé en dernier : « Cocody » n'apparaît que dans la commune, pas dans le titre.
        make("Villa à Bingerville", "Cocody", PropertyStatus.DISPONIBLE)

    def _titles(self, **params):
        r = APIClient().get(self.URL, params)
        self.assertEqual(r.status_code, 200)
        return [p["title"] for p in r.data["results"]]

    def test_availability_filter(self):
        self.assertEqual(self._titles(status="RESERVE"), ["Villa Cocody"])
        self.assertEqual(len(self._titles(status="DISPONIBLE")), 2)

    def test_relevance_puts_title_matches_before_place_matches(self):
        # Tri par défaut (le plus récent d'abord) : la correspondance par commune seule arrive en tête...
        self.assertEqual(self._titles(q="cocody")[0], "Villa à Bingerville")
        # ... la pertinence la relègue derrière les correspondances de titre.
        self.assertEqual(self._titles(q="cocody", ordering="relevance")[-1], "Villa à Bingerville")


class ProjectPublicApiTests(TestCase):
    """Fiche d'un programme par slug et liste allégée (page « Programmes » du site)."""

    def setUp(self):
        cache.clear()
        self.project = make_project("Résidence Slug", [PropertyStatus.DISPONIBLE, PropertyStatus.VENDU])

    def test_detail_by_slug_returns_lots(self):
        r = APIClient().get(f"/api/v1/properties/projects/slug/{self.project.slug}/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.data["lots"]), 2)

    def test_unknown_slug_is_404(self):
        self.assertEqual(APIClient().get("/api/v1/properties/projects/slug/inconnu/").status_code, 404)

    def test_summary_list_has_counts_but_no_lots(self):
        r = APIClient().get("/api/v1/properties/projects/?summary=1")
        self.assertEqual(r.status_code, 200)
        row = (r.data["results"] if isinstance(r.data, dict) else r.data)[0]
        self.assertNotIn("lots", row)
        self.assertEqual((row["lots_available"], row["lots_sold"]), (1, 1))


class MultiWordSearchTests(TestCase):
    """L'exemple de la spécification : l'utilisateur saisit « Cocody Abatta » (commune + quartier)."""

    URL = "/api/v1/properties/search/"

    def setUp(self):
        from apps.properties.infrastructure.models import Property

        def make(title, commune, quarter, kind, **extra):
            return Property.objects.create(
                title=title, description="d", property_type=kind, price=Decimal("50000000"), commune=commune,
                neighborhood=quarter, surface_sqm=Decimal("100"), status=PropertyStatus.DISPONIBLE, **extra,
            )

        make("Appartement lumineux", "Cocody", "Abatta", "APPARTEMENT", typology="F3")
        make("Villa avec piscine", "Cocody", "Angré", "VILLA", typology="F5")
        make("Terrain viabilisé", "Bingerville", "Akandjé", "TERRAIN")

    def _titles(self, q):
        r = APIClient().get(self.URL, {"q": q})
        self.assertEqual(r.status_code, 200)
        return sorted(p["title"] for p in r.data["results"])

    def test_commune_and_quarter_in_any_order(self):
        self.assertEqual(self._titles("Cocody Abatta"), ["Appartement lumineux"])
        self.assertEqual(self._titles("abatta cocody"), ["Appartement lumineux"])

    def test_type_word_and_place(self):
        self.assertEqual(self._titles("villa Cocody"), ["Villa avec piscine"])
        self.assertEqual(self._titles("villas cocody"), ["Villa avec piscine"])  # pluriel
        self.assertEqual(self._titles("terrain bingerville"), ["Terrain viabilisé"])
        self.assertEqual(self._titles("appart abatta"), ["Appartement lumineux"])  # début de mot

    def test_typology_and_every_word_must_match(self):
        self.assertEqual(self._titles("F3 Abatta"), ["Appartement lumineux"])
        self.assertEqual(self._titles("F5 Abatta"), [])  # F5 n'est pas à Abatta
        self.assertEqual(self._titles("Cocody Marcory"), [])

    def test_blank_query_and_many_words_are_harmless(self):
        self.assertEqual(len(self._titles("   ")), 3)
        self.assertEqual(self._titles("Cocody " * 40), sorted(["Appartement lumineux", "Villa avec piscine"]))


class SearchQueryCountTests(TestCase):
    """La recherche garde un nombre de requêtes constant : pas de requête par bien (spécification §35 : recherche < 3 s)."""

    def test_query_count_does_not_grow_with_results(self):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        from apps.properties.infrastructure.models import Property, PropertyImage

        def add(n):
            for i in range(n):
                p = Property.objects.create(
                    title=f"Bien {i}", description="d", property_type="VILLA", price=Decimal("50000000"),
                    commune="Cocody", neighborhood="Angré", surface_sqm=Decimal("100"), status=PropertyStatus.DISPONIBLE,
                )
                PropertyImage.objects.create(property=p, external_url="https://x/a.jpg", is_cover=True)
                PropertyImage.objects.create(property=p, external_url="https://x/b.jpg")

        def queries():
            with CaptureQueriesContext(connection) as ctx:
                r = APIClient().get("/api/v1/properties/search/?page_size=12")
            self.assertEqual(r.status_code, 200)
            return len(ctx.captured_queries)

        add(3)
        few = queries()
        add(20)
        many = queries()
        self.assertEqual(few, many)
        self.assertLessEqual(many, 5)
