"""
Charge la base de démonstration exportée par `export_demo_data` : met à jour la base du développeur ou du testeur.

    python manage.py load_demo_data               # applique les migrations, charge les données, copie les médias
    python manage.py load_demo_data --no-migrate  # si le schéma est déjà à jour

Comportement « mise à jour » : chaque objet du fichier est créé, ou REMPLACÉ s'il existe déjà avec le même identifiant ;
les objets qui ne sont pas dans le fichier sont conservés. Relancer la commande est donc sans danger.

Différence avec `seed_data` : `seed_data` FABRIQUE des données neuves avec des dates relatives à aujourd'hui ;
`load_demo_data` restitue à l'identique la base exportée (mêmes identifiants, mêmes dates).

Comme seed_data, elle refuse de s'exécuter si DEBUG=False (sauf --force) pour ne pas polluer une base de production.
"""

import shutil
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

from .export_demo_data import default_dir


class Command(BaseCommand):
    help = "Charge fixtures/demo_data.json (et copie fixtures/demo_media/ dans MEDIA_ROOT) après avoir migré le schéma."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dir", default=None, help="Dossier contenant demo_data.json et demo_media/ (défaut : fixtures/)."
        )
        parser.add_argument(
            "--no-migrate", action="store_true", help="Ne pas appliquer les migrations avant le chargement."
        )
        parser.add_argument("--force", action="store_true", help="Autoriser l'exécution quand DEBUG=False.")

    def handle(self, *args, **options):
        if not settings.DEBUG and not options["force"]:
            raise CommandError("Refus : DEBUG=False (production ?). Utiliser --force si c'est volontaire.")
        folder = Path(options["dir"]) if options["dir"] else default_dir()
        data_file = folder / "demo_data.json"
        if not data_file.is_file():
            raise CommandError(f"Fichier introuvable : {data_file} (le générer avec export_demo_data).")

        if not options["no_migrate"]:
            self.stdout.write("Application des migrations…")
            call_command("migrate", interactive=False, verbosity=0)

        self.stdout.write(f"Chargement de {data_file.name}…")
        call_command("loaddata", str(data_file), verbosity=0)

        media_in = folder / "demo_media"
        copied = 0
        if media_in.is_dir():
            media_root = Path(settings.MEDIA_ROOT)
            for source in media_in.rglob("*"):
                if source.is_file():
                    target = media_root / source.relative_to(media_in)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, target)
                    copied += 1

        self.stdout.write(self.style.SUCCESS(f"Base de démonstration chargée ({copied} fichier(s) média copié(s))."))
        self.stdout.write("Comptes de démo : voir README (mot de passe d'origine de l'export, Demo12345! par défaut).")
