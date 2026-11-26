"""
Point d'entrée de l'application pour Passenger (cPanel « Setup Python App », o2switch).

Passenger cherche une variable `application` dans ce fichier : on réutilise celle de Django.
Les variables d'environnement (SECRET_KEY, base de données…) viennent du fichier `.env` à côté de `manage.py`,
lu par config/settings.py.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

from config.wsgi import application  # noqa: E402,F401
