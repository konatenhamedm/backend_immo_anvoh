#!/usr/bin/env bash
# Mise à jour du backend sur o2switch (cPanel). À lancer dans le Terminal cPanel, depuis le dossier de l'application :
#   source ~/virtualenv/<dossier-app>/<version>/bin/activate      (la commande exacte est affichée dans « Setup Python App »)
#   bash scripts/deploy_o2switch.sh
set -euo pipefail
cd "$(dirname "$0")/.."

echo "→ Dépendances"
pip install --upgrade pip >/dev/null
if grep -qs '^DB_ENGINE=django.db.backends.mysql' .env; then
  pip install -r requirements-mysql.txt   # base MySQL / MariaDB (pilote mysqlclient)
else
  pip install -r requirements.txt
fi

echo "→ Contrôle de la configuration"
python manage.py check --deploy || true

echo "→ Migrations"
python manage.py migrate --noinput

echo "→ Fichiers statiques"
python manage.py collectstatic --noinput

echo "→ Redémarrage de l'application (Passenger relit le code au prochain appel)"
mkdir -p tmp && touch tmp/restart.txt

echo "Terminé."
