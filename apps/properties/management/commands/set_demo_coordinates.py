"""
Renseigne des positions GPS APPROXIMATIVES de démonstration pour les biens et programmes qui n'en ont pas.

Les coordonnées ci-dessous sont des ordres de grandeur du centre des communes d'Abidjan, pas des mesures : elles servent à
montrer la carte et la recherche « autour de moi » avec les données de démonstration. En production, l'équipe saisit
la vraie position de chaque bien (champs latitude / longitude, ou carte du formulaire de publication).

Ne modifie jamais un bien qui a déjà une position. Refuse de s'exécuter si DEBUG=False (sauf --force).
"""

import hashlib

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.properties.infrastructure.models import Property

# (latitude, longitude) approximatives : centre de la commune ou du quartier
PLACES = {
    "plateau": (5.320, -4.020),
    "cocody": (5.350, -3.985),
    "marcory": (5.300, -3.985),
    "yopougon": (5.340, -4.080),
    "bingerville": (5.355, -3.885),
    "grand-bassam": (5.200, -3.740),
    "assinie": (5.150, -3.300),
    "songon": (5.330, -4.260),
    "riviera golf": (5.340, -3.955),
    "abatta": (5.395, -3.905),
    "angré": (5.405, -3.985),
}


def jitter(key: str) -> tuple[float, float]:
    """Décalage stable (≈ ± 700 m) pour que deux biens d'un même quartier ne soient pas superposés."""
    h = hashlib.sha256(key.encode()).digest()
    return ((h[0] / 255 - 0.5) * 0.012, (h[1] / 255 - 0.5) * 0.012)


class Command(BaseCommand):
    help = "Positions GPS approximatives de démonstration pour les biens sans coordonnées."

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true", help="Autoriser hors DEBUG (déconseillé)")

    def handle(self, *args, force=False, **options):
        if not settings.DEBUG and not force:
            raise CommandError("Commande de démonstration : refusée quand DEBUG=False (utilisez --force si vous savez ce que vous faites).")
        done = skipped = 0
        for p in Property.objects.filter(latitude__isnull=True):
            base = PLACES.get((p.neighborhood or "").lower()) or PLACES.get((p.commune or "").lower())
            if base is None:
                skipped += 1
                continue
            dy, dx = jitter(str(p.pk))
            Property.objects.filter(pk=p.pk).update(latitude=round(base[0] + dy, 6), longitude=round(base[1] + dx, 6))
            done += 1
        self.stdout.write(self.style.SUCCESS(f"{done} bien(s) positionné(s) (approximativement), {skipped} sans lieu connu."))
