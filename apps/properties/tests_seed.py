"""Cohérence des données de démonstration fabriquées par `seed_data`."""

import io

from django.core.management import call_command
from django.test import TestCase

from apps.accreditation.infrastructure.models import AccreditationFile


class SeedDataConsistencyTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Les tests tournent avec DEBUG=False : seed_data exige --force dans ce cas (protection de la production).
        call_command("seed_data", force=True, stdout=io.StringIO())

    def test_certified_files_were_submitted_before_being_certified(self):
        certified = AccreditationFile.objects.filter(certified_at__isnull=False)
        self.assertGreater(certified.count(), 0)
        for f in certified:
            self.assertLess(f.submitted_at, f.certified_at, f"{f.property.reference} : certifié avant d'être déposé")
            delay = (f.certified_at - f.submitted_at).days
            self.assertTrue(1 <= delay <= 30, f"{f.property.reference} : délai de {delay} jours peu réaliste")
