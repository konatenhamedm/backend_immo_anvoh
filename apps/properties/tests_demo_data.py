"""Export / chargement de la base de démonstration : aller-retour complet, y compris les 4 modules récents."""

import io
import json
import tempfile
from decimal import Decimal
from pathlib import Path

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from apps.accreditation.infrastructure.models import Notary
from apps.properties.infrastructure.models import Property, PropertyStatus
from apps.rentals.infrastructure.models import Lease
from apps.users.infrastructure.models import User, UserRole


class DemoDataRoundTripTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            email="proprio@test.ci",
            password="Un-Mot2Passe-Solide",
            first_name="Awa",
            last_name="Test",
            phone_number="+2250700000000",
            role=UserRole.PROPRIETAIRE,
        )
        self.prop = Property.objects.create(
            title="Villa de démonstration",
            description="d",
            property_type="VILLA",
            price=Decimal("50000000"),
            commune="Cocody",
            neighborhood="Angré",
            surface_sqm=Decimal("150"),
            status=PropertyStatus.DISPONIBLE,
            owner=self.owner,
        )
        Notary.objects.create(full_name="Me Test", office="Étude Test", city="Cocody")
        Lease.objects.create(
            property=self.prop, tenant_label="Famille Test", monthly_rent=Decimal("400000"), start_date="2026-01-01"
        )

    def _export(self, folder):
        call_command("export_demo_data", dir=folder, stdout=io.StringIO())
        return json.loads((Path(folder) / "demo_data.json").read_text())

    def test_export_includes_every_module_even_those_without_models_py_history(self):
        with tempfile.TemporaryDirectory() as folder:
            labels = {o["model"] for o in self._export(folder)}
        # accreditation, investments, messaging, rentals : oubliés par dumpdata tant qu'ils n'avaient pas de models.py
        self.assertIn("accreditation.notary", labels)
        self.assertIn("rentals.lease", labels)
        self.assertIn("properties.property", labels)
        self.assertIn("users.user", labels)
        self.assertFalse({"sessions.session", "contenttypes.contenttype", "auth.permission"} & labels)

    def test_round_trip_restores_data_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as folder:
            self._export(folder)
            Lease.objects.all().delete()
            Notary.objects.all().delete()
            Property.objects.all().delete()
            User.objects.all().delete()

            call_command("load_demo_data", dir=folder, no_migrate=True, force=True, stdout=io.StringIO())
            self.assertEqual(
                (User.objects.count(), Property.objects.count(), Notary.objects.count(), Lease.objects.count()),
                (1, 1, 1, 1),
            )
            self.assertTrue(User.objects.get(email="proprio@test.ci").check_password("Un-Mot2Passe-Solide"))

            # Mise à jour : une modification locale est remplacée par la version du fichier, sans doublon.
            Property.objects.update(title="MODIFIÉ")
            call_command("load_demo_data", dir=folder, no_migrate=True, force=True, stdout=io.StringIO())
            self.assertEqual(Property.objects.count(), 1)
            self.assertEqual(Property.objects.get().title, "Villa de démonstration")

    def test_load_refuses_without_force_when_debug_is_off(self):
        with tempfile.TemporaryDirectory() as folder:
            self._export(folder)
            # Les tests tournent avec DEBUG=False : sans --force la commande doit refuser (protection de la production).
            with self.assertRaises(CommandError):
                call_command("load_demo_data", dir=folder, no_migrate=True, stdout=io.StringIO())

    def test_load_fails_clearly_when_the_file_is_missing(self):
        with tempfile.TemporaryDirectory() as folder, self.assertRaises(CommandError):
            call_command("load_demo_data", dir=folder, no_migrate=True, force=True, stdout=io.StringIO())
