# Déployer le backend sur o2switch (cPanel)

Le backend est une application Django : sur cPanel elle tourne via **« Setup Python App »** (Passenger). Compter 45 minutes la première fois. `CPUSER` = votre identifiant cPanel ; `thiebbro.ci` = votre domaine (à adapter). Les intitulés des menus cPanel peuvent légèrement varier.

## 0. Avant de commencer
- **Python 3.12 ou plus** : Django 6.1 l'exige. Ouvrez *Setup Python App > Create application* et regardez la liste des versions. Si 3.12 n'y figure pas, demandez son activation au support o2switch (réponse rapide en général).
- Un **sous-domaine pour l'API**, par exemple `api.thiebbro.ci` (cPanel > *Domaines*, racine : `api.thiebbro.ci`), avec un certificat HTTPS (AutoSSL, automatique).
- Le code dans un dépôt Git (GitHub), ou une archive à téléverser.

## 1. Base de données PostgreSQL
cPanel > **Bases de données PostgreSQL** :
1. Créer la base `thiebbro` (devient `CPUSER_thiebbro`).
2. Créer un utilisateur avec un mot de passe fort (`CPUSER_thiebbro`).
3. L'ajouter à la base avec **tous les privilèges**.

## 2. Envoyer le code
Le plus simple : cPanel > **Git™ Version Control** > *Create* > cloner le dépôt dans `/home/CPUSER/thiebbro_api` (dossier **hors** de la racine web : le code ne doit pas être téléchargeable). Sinon, par SSH : `git clone <dépôt> ~/thiebbro_api`.

## 3. Créer l'application Python
cPanel > **Setup Python App** > *Create Application* :
| Champ | Valeur |
|---|---|
| Python version | 3.12 ou plus |
| Application root | `thiebbro_api` |
| Application URL | `api.thiebbro.ci` |
| Application startup file | `passenger_wsgi.py` |
| Application Entry point | `application` |

Après *Create*, cPanel affiche en haut de page une commande du type `source /home/CPUSER/virtualenv/thiebbro_api/3.12/bin/activate && cd /home/CPUSER/thiebbro_api` : **copiez-la**, elle sert à l'étape 5. (Si cPanel a créé son propre `passenger_wsgi.py`, remplacez-le par celui du dépôt.)

## 4. Configuration (`.env`)
Dans `~/thiebbro_api`, copier le modèle puis le remplir :
```bash
cp .env.production.example .env && chmod 600 .env
python3 -c "import secrets; print(secrets.token_urlsafe(64))"   # à coller dans SECRET_KEY
nano .env
```
À renseigner au minimum : `SECRET_KEY`, `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, `CSRF_TRUSTED_ORIGINS`, les `DB_*`, `STATIC_ROOT`, `MEDIA_ROOT`, les `EMAIL_*` (créez avant un compte *no-reply@thiebbro.ci* dans cPanel > *Comptes de messagerie*) et `FRONTEND_URL`.

> `STATIC_ROOT` et `MEDIA_ROOT` pointent **dans la racine web du sous-domaine** (`/home/CPUSER/api.thiebbro.ci/…`) : c'est ce qui permet au serveur web de distribuer directement les images, les PDF et les fichiers de l'administration Django, sans passer par Python.

## 5. Installer et démarrer (Terminal cPanel ou SSH)
```bash
source /home/CPUSER/virtualenv/thiebbro_api/3.12/bin/activate && cd /home/CPUSER/thiebbro_api   # la commande copiée à l'étape 3
bash scripts/deploy_o2switch.sh      # dépendances, migrations, fichiers statiques, redémarrage
python manage.py createsuperuser     # votre compte administrateur
```
Puis dans *Setup Python App*, bouton **Restart**.

**Vérifier :** `https://api.thiebbro.ci/api/v1/properties/meta/` répond du JSON, `https://api.thiebbro.ci/api/docs/` affiche la documentation de l'API, `https://api.thiebbro.ci/admin/` s'ouvre avec le style de l'administration (sinon les fichiers statiques ne sont pas servis : revoir `STATIC_ROOT`).

## 6. Jouer les fixtures (base de démonstration)
```bash
python manage.py load_demo_data --force --password 'UnMotDePasseFortEtUnique'
python manage.py seed_demo_scenarios --force       # facultatif : prospects, visites, relances, statistiques à des dates récentes
```
- `--force` est obligatoire parce que l'application tourne avec `DEBUG=False`.
- `--password` est **obligatoire** hors développement : sans lui, les 16 comptes de démonstration (dont `admin@thiebbro.ci`, super-administrateur) garderaient le mot de passe public `Demo12345!`. Avec lui, tous les comptes chargés reçoivent le mot de passe choisi. La liste des comptes est dans `fixtures/demo_data.json` ; ceux que vous ne voulez pas, supprimez-les ensuite dans `/admin/`.
- La commande migre la base, charge `fixtures/demo_data.json` (≈ 12 800 objets), et copie les PDF de `fixtures/demo_media/` dans `MEDIA_ROOT`. Elle est relançable sans danger.
- Les photos des biens pointent vers des images Unsplash (aucun fichier à envoyer).
- **Pour un vrai site en production, ne chargez pas ces données** : créez seulement votre super-administrateur et saisissez vos biens. La base de démonstration sert aux présentations et aux recettes.

## 7. Tâche quotidienne (relances automatiques)
cPanel > **Tâches Cron** > une fois par jour, à 7 h :
```
cd /home/CPUSER/thiebbro_api && /home/CPUSER/virtualenv/thiebbro_api/3.12/bin/python manage.py create_followups
```

## 8. Brancher le site
- Dans le front, compiler avec `VITE_API_URL=https://api.thiebbro.ci/api/v1`.
- Dans Google Cloud (identifiants OAuth), ajouter l'adresse du site aux « origines JavaScript autorisées ».
- Le site (TanStack Start) est une application Node : sur cPanel, *Setup Node.js App*. À traiter à part.

## 9. Mettre à jour plus tard
```bash
source …/activate && cd ~/thiebbro_api
git pull && bash scripts/deploy_o2switch.sh
```

## 10. En cas de problème
| Symptôme | Piste |
|---|---|
| Page d'erreur 500 sans détail | Journal `stderr.log` dans le dossier de l'application, ou `~/logs/` (cPanel > *Erreurs*) |
| `ImproperlyConfigured: SECRET_KEY…` | `.env` absent, mal placé (il doit être à côté de `manage.py`) ou `SECRET_KEY` vide |
| `DisallowedHost` | `ALLOWED_HOSTS` ne contient pas le sous-domaine |
| Le site public reçoit des erreurs CORS | `CORS_ALLOWED_ORIGINS` : adresse exacte avec `https://`, sans `/` final |
| Connexion à `/admin/` refusée (CSRF) | `CSRF_TRUSTED_ORIGINS=https://api.thiebbro.ci` |
| Images/PDF en 404 | `MEDIA_ROOT` hors de la racine web, ou fichiers non copiés (relancer `load_demo_data`) |
| `pip install` échoue | Version de Python trop ancienne (3.12 minimum) |
| E-mails non reçus | Tester avec `python manage.py shell -c "from django.core.mail import send_mail; send_mail('Test','Bonjour','no-reply@thiebbro.ci',['vous@exemple.com'])"` |

## Points de vigilance
- **Sauvegardes** : activer les sauvegardes cPanel et faire un `pg_dump` régulier de la base ; sauvegarder `media/`.
- **Documents sensibles** : les pièces d'identité et titres fonciers déposés par les propriétaires sont stockés dans `media/`, donc accessibles par leur adresse exacte. Avant un lancement public, il faut les servir par une route protégée (contrôle d'accès) plutôt que directement : à prévoir.
- **Documentation de l'API** (`/api/docs/`) publique : à restreindre si vous ne voulez pas l'exposer.
