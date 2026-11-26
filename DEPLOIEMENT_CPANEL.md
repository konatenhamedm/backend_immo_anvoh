# Déployer THIEBBRO IMMO sur un serveur cPanel (API + site)

Ce manuel décrit le déploiement complet sur un hébergement mutualisé cPanel (testé sur o2switch) :
**partie A : l'API Django** (cPanel « Setup Python App »), **partie B : le site** (cPanel « Setup Node.js App »). Compter 1 heure la première fois. Les intitulés des menus cPanel peuvent légèrement varier.

## Valeurs à adapter (exemple : celles utilisées pour le premier déploiement)
| Variable | Exemple | Votre valeur |
|---|---|---|
| `CPUSER` (identifiant cPanel) | `riil5934` | |
| Domaine de l'API | `thiebbro.maisonhautecouturerogerblon.com` | |
| Domaine du site | `frontthiebbro.maisonhautecouturerogerblon.com` | |

Dans la suite, `api.thiebbro.ci` désigne **le domaine de l'API** et `thiebbro_api` le dossier de l'application (le dossier peut porter le nom du domaine). Remplacez-les par vos valeurs.

# PARTIE A : l'API (backend)

## 0. Avant de commencer
- **Python 3.11** : c'est la version la plus récente proposée par o2switch dans *Setup Python App* (liste : 2.7, 3.3 … 3.11.18). Le projet y est **testé** (150 tests réussis en Python 3.11.18) : il utilise donc **Django 5.2 LTS**, compatible Python 3.10 à 3.13. Choisissez bien `3.11.18` : la valeur par défaut du menu est `2.7.18`, qui ne convient pas.
- Un **sous-domaine pour l'API**, par exemple `api.thiebbro.ci` (cPanel > *Domaines*, racine : `api.thiebbro.ci`), avec un certificat HTTPS (AutoSSL, automatique).
- Le code dans un dépôt Git (GitHub), ou une archive à téléverser.

## 1. Base de données MariaDB
o2switch fournit MariaDB 11.4 (pleinement supportée par Django 5.2). Son PostgreSQL (9.6) est trop ancien et le port 5432 vers l'extérieur est fermé : on utilise donc MariaDB.

1. cPanel > **Bases de données MySQL** : créer la base (`CPUSER_thiebbro`), puis un utilisateur avec un mot de passe fort, puis **ajouter l'utilisateur à la base** avec *tous les privilèges*.
2. Dans le `.env` : `DB_ENGINE=django.db.backends.mysql`, `DB_HOST=localhost`, `DB_PORT=3306`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`.

3. **Jeu de caractères (important)** : cPanel crée souvent la base en latin1/utf8 ancien, ce qui fait échouer les accents spéciaux et les flèches (`Incorrect string value`). Avant le premier `migrate`, dans **phpMyAdmin** : cliquer sur la base > onglet **Opérations** > *Collation* : choisir **`utf8mb4_unicode_ci`**, cocher *Changer la collation de toutes les tables*, valider. Si des tables existent déjà : les sélectionner toutes > *Supprimer* (DROP) avant, puis relancer `migrate`.

Le script de déploiement détecte ce moteur et installe `requirements-mysql.txt` (pilote PyMySQL, 100 % Python : `mysqlclient` ne s'installe pas sur le mutualisé car `gcc` y est interdit). Les tests passent à 150/150 sur MySQL.

## 2. Envoyer le code
Le plus simple : cPanel > **Git™ Version Control** > *Create Repository*, option *Clone a Repository* activée :
- **Clone URL** : `https://github.com/konatenhamedm/backend_immo_anvoh.git`
- **Repository Path** : `/home/CPUSER/thiebbro_api` (dossier **hors** de la racine web : le code ne doit pas être téléchargeable). Ici `CPUSER` = `riil5934`.
- **Repository Name** : `thiebbro_api`.

**Le dépôt est privé** : l'adresse HTTPS seule échouera. Utilisez une clé de déploiement (lecture seule) :
1. cPanel > **Accès SSH** (lien « Related Links » de la page Git) > *Gérer les clés SSH* > *Générer une nouvelle clé* (type RSA ou ED25519, **sans phrase secrète**, nom `github_deploy`), puis *Gérer* > **Authorize** pour cette clé.
2. Afficher la **clé publique** (*View/Download*) et la copier.
3. GitHub > dépôt `backend_immo_anvoh` > *Settings* > *Deploy keys* > *Add deploy key* : coller la clé, laisser *Allow write access* **décoché**.
4. Dans le formulaire cPanel, utiliser comme *Clone URL* : `git@github.com:konatenhamedm/backend_immo_anvoh.git` (au premier clonage, la connexion à `github.com` doit être acceptée : si cPanel affiche une erreur « Host key verification failed », ouvrez un terminal SSH et lancez une fois `ssh -T git@github.com`, répondre `yes`).

(Alternative : rendre temporairement le dépôt public.)

## 3. Créer l'application Python
cPanel > **Setup Python App** > *Create Application* :
| Champ | Valeur |
|---|---|
| Python version | **3.11.18** (pas la 2.7.18 proposée par défaut) |
| Application root | `thiebbro_api` |
| Application URL | `api.thiebbro.ci` |
| Application startup file | `passenger_wsgi.py` |
| Application Entry point | `application` |

Après *Create*, cPanel affiche en haut de page une commande du type `source /home/CPUSER/virtualenv/thiebbro_api/3.11/bin/activate && cd /home/CPUSER/thiebbro_api` : **copiez-la**, elle sert à l'étape 5. (Si cPanel a créé son propre `passenger_wsgi.py`, remplacez-le par celui du dépôt.)

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
source /home/CPUSER/virtualenv/thiebbro_api/3.11/bin/activate && cd /home/CPUSER/thiebbro_api   # la commande copiée à l'étape 3
bash scripts/deploy_o2switch.sh      # dépendances, migrations, fichiers statiques, redémarrage
python manage.py createsuperuser     # votre compte administrateur
```
Puis dans *Setup Python App*, bouton **Restart**.

**Vérifier :** `https://api.thiebbro.ci/api/v1/properties/meta/` répond du JSON, `https://api.thiebbro.ci/api/docs/` affiche la documentation de l'API, `https://api.thiebbro.ci/admin/` s'ouvre avec le style de l'administration (sinon les fichiers statiques ne sont pas servis : revoir `STATIC_ROOT`).

## 6. Jouer les fixtures (base de démonstration)
```bash
python manage.py load_demo_data --force --password 'UnMotDePasseFortEtUnique'   # une seule fois, sur une base vide (--force n'efface rien)
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
cd /home/CPUSER/thiebbro_api && /home/CPUSER/virtualenv/thiebbro_api/3.11/bin/python manage.py create_followups
```

## 8. Autoriser le site (à faire une fois l'adresse du site connue)
Dans le `.env` de l'API, puis **Restart** de l'application Python :
```
CORS_ALLOWED_ORIGINS=https://frontthiebbro.maisonhautecouturerogerblon.com
FRONTEND_URL=https://frontthiebbro.maisonhautecouturerogerblon.com
```
(adresse exacte, avec `https://`, sans `/` final). Dans Google Cloud (identifiants OAuth « Web »), ajouter l'adresse du site aux **origines JavaScript autorisées** : sans cela, le bouton « Continuer avec Google » est refusé.

## 9. Mettre à jour plus tard (API)
```bash
source …/activate && cd ~/thiebbro_api
git pull && bash scripts/deploy_o2switch.sh
```

## 10. En cas de problème
| Symptôme | Piste |
|---|---|
| Page d'erreur 500 sans détail | Journal `stderr.log` dans le dossier de l'application, ou `~/logs/` (cPanel > *Erreurs*) |
| `ImproperlyConfigured: SECRET_KEY…` | `.env` absent, mal placé (il doit être à côté de `manage.py`) ou `SECRET_KEY` vide |
| Page blanche « Bad Request (400) » | `ALLOWED_HOSTS` ne contient pas exactement le domaine (sans `https://`, sans espace ni guillemets), ou l'application n'a pas été redémarrée. Vérifier : `python manage.py shell -c "from django.conf import settings; print(settings.ALLOWED_HOSTS)"`, puis `mkdir -p tmp && touch tmp/restart.txt` |
| `Incorrect string value … column` au chargement des données | Base en latin1/utf8 ancien : appliquer l'étape 1.3 (collation `utf8mb4_unicode_ci`), vider les tables, relancer `migrate` |
| `PostgreSQL 14 or later is required` | Le `.env` pointe vers la base PostgreSQL 9.6 du serveur : utiliser MariaDB (étape 1) |
| `Permission denied: 'gcc'` à l'installation | Normal sur mutualisé : le projet utilise PyMySQL (pur Python), lancer `bash scripts/deploy_o2switch.sh` qui installe `requirements-mysql.txt` |
| Le site public reçoit des erreurs CORS | `CORS_ALLOWED_ORIGINS` : adresse exacte avec `https://`, sans `/` final |
| Connexion à `/admin/` refusée (CSRF) | `CSRF_TRUSTED_ORIGINS=https://api.thiebbro.ci` |
| Images/PDF en 404 | `MEDIA_ROOT` hors de la racine web, ou fichiers non copiés (relancer `load_demo_data`) |
| `pip install` échoue | Application créée avec la mauvaise version de Python (il faut 3.10 à 3.13, idéalement 3.11.18) |
| E-mails non reçus | Tester avec `python manage.py shell -c "from django.core.mail import send_mail; send_mail('Test','Bonjour','no-reply@thiebbro.ci',['vous@exemple.com'])"` |


# PARTIE B : le site (frontend)

Le site est une application Node (rendu serveur). Il est livré **déjà compilé** dans l'archive `thiebbro-front.zip` (dossier `release/` du projet `thiebbro-web`) : aucun outil de compilation n'est nécessaire sur le serveur.

## B1. Compiler (sur votre ordinateur, si l'adresse de l'API change)
Les adresses de production sont déjà dans `thiebbro-web/.env.production` :
```
VITE_API_URL=https://thiebbro.maisonhautecouturerogerblon.com/api/v1
VITE_SITE_URL=https://frontthiebbro.maisonhautecouturerogerblon.com
```
Pour un autre serveur : modifier ces deux lignes, puis :
```bash
cd thiebbro-web
npm install
npm run build
mkdir -p release && rm -f release/thiebbro-front.zip && zip -qr release/thiebbro-front.zip dist server.mjs app.cjs package.json package-lock.json
```
Les adresses sont **intégrées au code au moment de la compilation** : changer d'adresse oblige à recompiler. Compléter aussi dans `.env` (ou `.env.production`) avant de compiler : `VITE_WHATSAPP_NUMBER`, `VITE_CONTACT_PHONE`, `VITE_GOOGLE_CLIENT_ID` (même valeur que `GOOGLE_CLIENT_ID` de l'API) et les `VITE_COMPANY_*` des mentions légales.

## B2. Créer le sous-domaine du site
cPanel > **Domaines** > créer `frontthiebbro.maisonhautecouturerogerblon.com` (la racine de document peut rester par défaut) ; AutoSSL délivre le certificat HTTPS en quelques minutes.

## B3. Envoyer le site
1. cPanel > **Gestionnaire de fichiers** : créer le dossier `/home/CPUSER/thiebbro_front` (hors de la racine web).
2. Y téléverser `thiebbro-front.zip`, clic droit > **Extract**. On doit voir `dist/`, `server.mjs`, `app.cjs`, `package.json`, `package-lock.json`.

## B4. Créer l'application Node.js
cPanel > **Setup Node.js App** > *Create Application* :
| Champ | Valeur |
|---|---|
| Node.js version | la plus récente proposée, **20 minimum** |
| Application mode | Production |
| Application root | `thiebbro_front` |
| Application URL | `frontthiebbro.maisonhautecouturerogerblon.com` |
| Application startup file | `app.cjs` |

*Create*, puis copier la commande `source /home/CPUSER/nodevenv/thiebbro_front/…/bin/activate && cd /home/CPUSER/thiebbro_front` affichée en haut de la page.

## B5. Installer les dépendances et démarrer
Dans le **Terminal** cPanel :
```bash
source /home/CPUSER/nodevenv/thiebbro_front/20/bin/activate && cd /home/CPUSER/thiebbro_front   # la commande copiée à l'étape B4
npm install --omit=dev
```
(`--omit=dev` évite d'installer les outils de test, inutiles et très lourds.) Puis, dans *Setup Node.js App*, bouton **Restart**.

**Vérifier :** `https://frontthiebbro.maisonhautecouturerogerblon.com/` affiche l'accueil, `/robots.txt` et `/sitemap.xml` répondent, et la connexion avec un compte de démonstration fonctionne (sinon : étape A8, CORS).

## B6. Mettre à jour le site plus tard
Recompiler et refaire l'archive (B1), puis téléverser et extraire par-dessus l'ancienne (remplacer), **Restart**. Pas besoin de refaire `npm install` si `package.json` n'a pas changé.

## B7. Problèmes courants (site)
| Symptôme | Piste |
|---|---|
| Erreur 503 / page d'erreur Passenger | Journal dans le dossier de l'application ; vérifier la version de Node (20+), que `npm install --omit=dev` s'est bien terminé, que le fichier de démarrage est `app.cjs` |
| Le site s'affiche mais les listes sont vides / erreurs réseau | L'adresse de l'API compilée est fausse (`VITE_API_URL`) : corriger, recompiler. Ou CORS non autorisé côté API (A8) |
| « Continuer avec Google » refusé | Origine du site absente de Google Cloud ou `VITE_GOOGLE_CLIENT_ID` vide à la compilation |
| Ancien contenu après une mise à jour | Vider le cache du navigateur (le site installe un service worker) ; *Restart* de l'application |

## Points de vigilance
- **Sauvegardes** : activer les sauvegardes cPanel et exporter régulièrement la base (cPanel > phpMyAdmin > Exporter, ou `mysqldump`) ; sauvegarder `media/`.
- **Documents sensibles** : les pièces d'identité et titres fonciers déposés par les propriétaires sont stockés dans `media/`, donc accessibles par leur adresse exacte. Avant un lancement public, il faut les servir par une route protégée (contrôle d'accès) plutôt que directement : à prévoir.
- **Documentation de l'API** (`/api/docs/`) publique : à restreindre si vous ne voulez pas l'exposer.
