"""
Exporte la base ACTUELLE en « fixture » (équivalent des fixtures Doctrine), à donner à un développeur ou testeur.

    python manage.py export_demo_data            # écrit fixtures/demo_data.json + fixtures/demo_media/

Contenu : toutes les tables métier (comptes, biens, programmes, prospects, investissements, gestion locative…) ET les
fichiers médias qu'elles référencent (pièces PDF, etc.). Sont exclus : sessions, permissions (recréées par Django),
journal de l'admin Django.

⚠ N'exporter QUE des données de démonstration : le fichier contient les comptes avec leurs mots de passe hachés,
e-mails et téléphones. Ne jamais exporter ni versionner une base contenant de vraies données de clients.

Se recharge avec : python manage.py load_demo_data
"""

import shutil
from pathlib import Path

from django.apps import apps
from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import models

EXCLUDED = ["contenttypes", "auth.permission", "sessions", "admin.logentry"]


def default_dir() -> Path:
    return Path(settings.BASE_DIR) / "fixtures"


class Command(BaseCommand):
    help = "Exporte la base actuelle (données + fichiers médias référencés) vers fixtures/ pour un autre environnement."

    def add_arguments(self, parser):
        parser.add_argument("--dir", default=None, help="Dossier de sortie (défaut : fixtures/ à la racine du projet).")

    def handle(self, *args, **options):
        out = Path(options["dir"]) if options["dir"] else default_dir()
        out.mkdir(parents=True, exist_ok=True)
        data_file = out / "demo_data.json"

        # Natural keys : les références (ex. permissions d'un utilisateur) restent valables dans une autre base.
        call_command(
            "dumpdata",
            natural_foreign=True,
            natural_primary=True,
            indent=2,
            exclude=EXCLUDED,
            output=str(data_file),
        )

        media_out = out / "demo_media"
        if media_out.exists():
            shutil.rmtree(media_out)
        copied = missing = 0
        media_root = Path(settings.MEDIA_ROOT)
        for model in apps.get_models():
            file_fields = [f.name for f in model._meta.get_fields() if isinstance(f, models.FileField)]
            if not file_fields:
                continue
            for name in file_fields:
                for relative in model.objects.exclude(**{name: ""}).values_list(name, flat=True).distinct():
                    if not relative:
                        continue
                    source = media_root / relative
                    if not source.is_file():
                        missing += 1
                        continue
                    target = media_out / relative
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, target)
                    copied += 1

        self.stdout.write(self.style.SUCCESS(f"Données : {data_file} ({data_file.stat().st_size // 1024} Ko)"))
        self.stdout.write(self.style.SUCCESS(f"Médias  : {copied} fichier(s) référencé(s) copié(s) dans {media_out}"))
        if missing:
            self.stdout.write(
                self.style.WARNING(f"{missing} fichier(s) référencé(s) introuvable(s) dans {media_root} (ignorés).")
            )
        self.stdout.write(
            self.style.WARNING(
                "Rappel : uniquement des données de démonstration (mots de passe hachés, e-mails, téléphones)."
            )
        )
