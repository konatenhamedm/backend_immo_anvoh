# Thiebbro Immo — API (Django REST, Clean Architecture)

Plateforme PropTech immobilière et d'investissement (Côte d'Ivoire). Cette API alimente le site, les espaces connectés et le back-office du dépôt front `thiebbroimmobilier` (Next.js).

Django 6 · Django REST Framework · JWT (simplejwt) · PostgreSQL · drf-spectacular (OpenAPI).
Le détail des changements d'intégration avec le front est dans `CHANGEMENTS.md` ; le schéma de base de données dans `SCHEMA_BASE_DE_DONNEES.md`.

## Démarrer

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # puis adapter (base PostgreSQL, SECRET_KEY…)
createdb thiebbro_immo_db       # ou CREATE DATABASE thiebbro_immo_db;
python manage.py migrate
python manage.py seed_data      # données de démonstration (développement uniquement)
python manage.py runserver      # http://127.0.0.1:8000
```

- Documentation interactive : `/api/docs/` (Swagger), `/api/redoc/`, schéma brut `/api/schema/`.
- Django Admin : `/admin/`.
- Comptes de démo : mot de passe `SEED_PASSWORD` (sinon généré et affiché une fois). Le front propose des boutons « Comptes de démo » en développement.
- `seed_data` **refuse de s'exécuter si `DEBUG=False`** (sauf `--force`) pour ne pas polluer une base de production.

### Données de démonstration pour un testeur ou un autre développeur

Un développeur qui démarre le projet chez lui n'a besoin que de ceci (PostgreSQL installé) :

```bash
git clone … && git checkout feat/backoffice-integration
python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
cp .env.example .env                  # adapter DB_USER / DB_PASSWORD
createdb thiebbro_immo_db
python manage.py load_demo_data       # migrations + base de démonstration + pièces PDF
python manage.py runserver
```

Comptes de démo (mot de passe `Demo12345!`) : `admin@thiebbro.ci`, `aminata.agent@thiebbro.ci` (conseiller), `a.kone@notaire.ci` (notaire),
`k.yao@mail.ci` (propriétaire, avec baux), `awa.traore@mail.ci` (acheteuse), `soro.paris@gmail.com` (investisseur).

| Commande | Rôle |
| :--- | :--- |
| `python manage.py migrate` | met à jour la **structure** de la base (tables, colonnes, index) : à relancer après chaque `git pull` |
| `python manage.py load_demo_data` | migre, puis charge `fixtures/demo_data.json` et copie `fixtures/demo_media/` : met à jour les **données** |
| `python manage.py load_demo_data --no-migrate` | idem sans les migrations |
| `python manage.py export_demo_data` | régénère `fixtures/` depuis la base actuelle (voir avertissement ci-dessous) |
| `python manage.py seed_data` | alternative : FABRIQUE des données neuves, dates relatives à aujourd'hui |

- **Mise à jour sans danger** : chaque objet du fichier est créé ou *remplacé* s'il existe déjà (même identifiant) ; ce qui n'est pas dans le fichier est conservé. On peut relancer la commande à volonté.
- **`load_demo_data` ou `seed_data` ?** `load_demo_data` restitue à l'identique la base exportée (mêmes identifiants, mêmes dates : tout le monde voit les mêmes données). `seed_data` repart de zéro avec des dates récentes. Les deux refusent de s'exécuter si `DEBUG=False`.
- **Pourquoi des fixtures et pas une migration de données ?** Une migration s'exécute sur *toutes* les bases, production comprise : y mettre des comptes de démonstration serait dangereux. Les fixtures se chargent à la demande, seulement là où on le décide.
- ⚠ **`fixtures/` ne doit contenir que des données de démonstration** (comptes avec mots de passe hachés, e-mails, téléphones). Ne jamais exporter ni versionner une base contenant de vraies données de clients.
- Le chargement est vérifié par des tests (`apps/properties/tests_demo_data.py`) : aller-retour complet, idempotence, refus en production.

### Variables d'environnement (`.env.example`)

| Variable | Rôle | Défaut |
| :--- | :--- | :--- |
| `DEBUG` | Mode développement | `False` (mettre `True` en local) |
| `SECRET_KEY` | Clé Django | **obligatoire si `DEBUG=False`** |
| `ALLOWED_HOSTS` | Hôtes autorisés | `localhost,127.0.0.1` |
| `CORS_ALLOWED_ORIGINS` | Origines autorisées (site Next, back-office) | `http://localhost:3000,http://localhost:5173` |
| `DB_ENGINE` `DB_NAME` `DB_USER` `DB_PASSWORD` `DB_HOST` `DB_PORT` | Base de données | PostgreSQL local |
| `JWT_ACCESS_MINUTES` | Durée du jeton d'accès (le jeton de rafraîchissement dure 7 jours) | `60` |
| `SEED_PASSWORD` | Mot de passe des comptes de démo | généré |

## Modules (`apps/`)

Chaque module suit la même organisation : `domain/` (règles métier pures), `infrastructure/` (modèles), `interfaces/` (serializers, vues, urls, permissions).

**Vues par public.** Les modules volumineux (`crm`, `properties`) ont un **paquet** `interfaces/views/` avec un fichier par public ; les modules courts gardent un seul `views.py`. Les `urls.py` importent toujours `from .views import …` (le `__init__.py` ré-exporte les vues).

| Fichier | Public |
| :--- | :--- |
| `public*.py`, `catalog.py`, `projects.py` | visiteurs (lecture ouverte, écriture équipe pour les programmes) |
| `buyer.py`, `favorites.py` | utilisateur connecté (acheteur) |
| `owner.py`, `images.py` | propriétaire |
| `admin_*.py`, `admin.py` | équipe (conseillers et administrateurs) |
| `_common.py` | requêtes et fonctions partagées (aucune vue) |

Règle : découper un module dès qu'il dépasse ~250 lignes ou 3 publics.

| Module | Rôle | Préfixe |
| :--- | :--- | :--- |
| `users` | Comptes, rôles, profil, vérification d'identité, gestion admin | `/api/v1/auth/` |
| `properties` | Catalogue, fiches, photos, favoris, programmes neufs et lots, espace propriétaire, catalogue admin | `/api/v1/properties/` |
| `crm` | Prospects, kanban, demandes d'informations, visites, alertes, recherche globale, tableau de bord | `/api/v1/crm/` |
| `accreditation` | Vérification notariale des biens : dossiers, pièces, notaires partenaires | `/api/v1/accreditation/` |
| `investments` | Plans, souscriptions, échéancier, revenus, documents | `/api/v1/investments/` |
| `rentals` | Gestion locative : baux, loyers encaissés, reversements aux propriétaires | `/api/v1/rentals/` |
| `messaging` | Conversations et messages, compteur de non-lus | `/api/v1/messaging/` |
| `simulators` | Rentabilité et capacité d'emprunt (publics) | `/api/v1/simulators/` |
| `analytics` | Mesure d'audience, canal d'acquisition des prospects, ROI marketing par canal | `/api/v1/analytics/` |
| `notifications` | Notifications (application + e-mail), attribution d'un conseiller, tâches de relance | `/api/v1/notifications/` |

### Médias, programmes et performance

- **Photos** : à l'envoi, chaque photo est redressée (EXIF), réduite à 1 600 px, recompressée en JPEG (≈ 6 Mo → 200-400 Ko) et dotée d'une miniature de 480 px
  (`cover_thumb` sur les cartes, `thumbnail_url` sur la galerie). Limites : 15 Mo, 50 millions de pixels ; une photo de petite taille n'est jamais agrandie ; les images
  externes (URL) ne sont pas modifiées. Les photos déjà enregistrées avant cette version n'ont pas de miniature (le site retombe sur l'image complète).
- **Programmes** : `payment_schedule` (échéancier en %, 100 % au plus) et `payment_notes` ; plans et documents (`POST /properties/projects/<id>/documents/`,
  PDF/JPG/PNG/WebP, 20 Mo ; `DELETE /properties/projects/documents/<id>/`), listés dans la fiche programme.
- **Recherche** : `q` fonctionne **par mots** (« Cocody Abatta », « villa Cocody », « F3 Abatta » : chaque mot doit correspondre au titre, au lieu, au type, à la typologie, à la
  description ou à la référence). Mesuré sur 5 000 biens publiés : 20 à 60 ms par recherche (objectif de la spécification : moins de 3 s) ; un test garde le nombre de requêtes constant.
  Limite connue : la recherche distingue les accents (« Résidence » ≠ « Residence »).

### Géolocalisation et carte (spécification §6)

- **Recherche géographique** : `GET /properties/search/?lat=&lng=&radius_km=` (biens autour d'un point, `distance_km` renvoyée, `ordering=distance`) et `bbox=sud,ouest,nord,est`
  (zone d'une carte). Distance de Haversine calculée en base ; paramètres invalides ignorés, jamais une erreur.
- **Vie privée des positions** : l'API publique n'expose que des coordonnées **arrondies à 2 décimales (≈ 1 km)** : le site promet « adresse exacte communiquée après rendez-vous ».
  Seuls l'équipe et le propriétaire du bien reçoivent la position exacte. Les distances sont calculées sur les positions exactes côté serveur.
- **Lieux** : `GET /properties/places/` liste communes et quartiers avec leur position centrale (moyenne des biens publiés) et leur nombre de biens ; sert à « autour d'un lieu » et aux quartiers voisins.
- **Données de démonstration** : `python manage.py set_demo_coordinates` renseigne des positions **approximatives** (centres de communes d'Abidjan) pour les biens sans position, afin de montrer la carte.
  Ce sont des ordres de grandeur, pas des mesures : en production, l'équipe saisit la vraie position de chaque bien. Refuse de s'exécuter si `DEBUG=False`.

### Notifications et relances

Le module `notifications` prévient **l'équipe** (conseiller du prospect, sinon du bien, sinon administrateurs) d'un nouveau prospect, d'une
demande d'information ou de visite, d'un prospect qualifié (score ≥ 70), d'une relance à faire ; et **le client** d'un nouveau bien
correspondant à une alerte de recherche, d'une baisse de prix d'un favori, d'une visite confirmée. Chaque notification est visible dans
l'application (`GET /api/v1/notifications/`) et envoyée par e-mail ; l'e-mail n'est jamais bloquant (une panne SMTP n'empêche pas la demande).
Les préférences du profil (`notifications_enabled`, `notification_preferences`) sont respectées pour les notifications client.
Les prospects sans conseiller en reçoivent un automatiquement (celui qui a le moins de prospects ouverts).

- **E-mail** : en développement, les messages s'affichent dans la console du serveur. En production, renseigner `EMAIL_HOST`, `EMAIL_HOST_USER`,
  `EMAIL_HOST_PASSWORD`, `DEFAULT_FROM_EMAIL` et `FRONTEND_URL` (voir `.env.example`).
- **Relances** : planifier **chaque jour** `python manage.py create_followups` (cron). Il crée une tâche pour chaque prospect sans activité depuis
  N jours (réglage « Relance après » du back-office, 3 par défaut ; ou `--days N`) et prévient son conseiller. `--dry-run` affiche sans écrire.
  Liste et clôture : `GET /api/v1/notifications/followups/`, `POST …/followups/<id>/done/`.
- **Aucun envoi** pendant `seed_data`, `load_demo_data`, `loaddata`… (pas de messages fictifs en masse).
- Autres canaux (SMS, WhatsApp, push Firebase) : ajouter une fonction à `CHANNELS` dans `apps/notifications/application/service.py`.
- Pas encore : résumés quotidien et hebdomadaire des alertes (seules les alertes « immédiates » sont envoyées).

### Mesure et acquisition

Le module `analytics` répond à la spécification §29 (sources des leads, ROI par canal) et §31 (KPI).

- **Canal d'origine du prospect** : `Lead.acquisition_channel` (Application, Site Web, WhatsApp, Facebook, Instagram, LinkedIn, Google, Parrainage,
  Campagne publicitaire, Autre) + `utm_source`, `utm_medium`, `utm_campaign`, `referral_code`, `landing_path`. Le site envoie un objet `attribution` avec chaque formulaire public ;
  il n'est enregistré qu'à la **création** du prospect (premier contact). Sans `attribution`, le canal est « Site Web » ; un prospect saisi à la main par l'équipe peut recevoir un canal
  (`acquisition_channel` dans `POST /crm/leads/`), sinon « Autre ». `Lead.source` reste ce que le prospect a fait (formulaire) ; le canal est d'où il est venu.
- **Événements** : le navigateur envoie par lots (`POST /analytics/events/`, public, 20 au plus, limité à 240 requêtes/min) une **liste fermée** : sessions, recherches, biens
  consultés, inscriptions, installations, simulations. Les événements de **conversion** (prospect créé, demande, clic WhatsApp, visite demandée, favori, vente) sont enregistrés
  **par le serveur uniquement** : ils ne peuvent pas être gonflés depuis le navigateur. Aucune donnée personnelle (e-mail, téléphone, nom… sont supprimés), pas de mesure pendant `seed_data`.
- **Vente datée** : passer un prospect en étape « Vente » enregistre `converted_at` et l'événement `SALE` (une seule fois) ; le retirer de cette étape annule la date.
- **Tableau de bord** : `GET /api/v1/analytics/summary/?days=30` (administrateurs) : KPI, entonnoir, par canal (prospects, qualifiés, avec visite, ventes, taux de conversion, coût par prospect
  et par vente), série quotidienne. **KPI majeur** : `sales_generated_by_app` = ventes de la période dont le prospect est arrivé par un canal identifié (hors « Autre »).
- **ROI** : saisir les dépenses dans l'admin Django (« Dépenses marketing » : canal, mois, montant) ; le coût par prospect et par vente en découle.

### Convention d'URL

Chaque module expose, selon le public visé : des routes ouvertes (`/<module>/…`), des routes de l'utilisateur connecté (`…/me/`, `…/my-…/`), des routes propriétaire (`…/owner/…`) et des routes d'équipe (`…/admin/…`). Les routes anciennes qui ne suivent pas ce schéma sont conservées pour le front actuel.

## Sécurité

- **Toute route exige une connexion** (`DEFAULT_PERMISSION_CLASSES = IsAuthenticated`). Les routes publiques le déclarent explicitement.
- **Rôles** : `PARTICULIER`, `INVESTISSEUR`, `PROPRIETAIRE`, `PROMOTEUR`, `AGENT` (conseiller), `NOTAIRE`, `ADMIN`. Permissions centralisées dans `apps/users/interfaces/permissions.py` :

  | Permission | Qui passe |
  | :--- | :--- |
  | `IsAdminRole` | Administrateurs (rôle `ADMIN`, ou superutilisateur Django) |
  | `IsStaffOrAgent` | Administrateurs et conseillers |
  | `IsOwnerRole` | Propriétaires et promoteurs (et l'administrateur, sous mandat) |
  | `IsNotaryOrAdmin` | Notaires partenaires et équipe |
  | `ReadOnlyOr(perm)` | Lecture pour tous, écriture avec la permission donnée |

  Le drapeau Django `is_staff` (accès au site `/admin/` de Django) **ne donne aucun droit d'administrateur sur l'API** : seul le rôle `ADMIN` (ou `is_superuser`) le fait. Un conseiller `is_staff` reste un conseiller (`is_admin()` dans `permissions.py`, verrouillé par `apps/users/tests_permissions.py`).
- **Inscription** : seuls les rôles grand public sont acceptés ; le rôle d'un profil est en lecture seule.
- **Quotas** (`DEFAULT_THROTTLE_RATES`) : 120/min anonyme, 600/min connecté ; `auth` 20/min (connexion, inscription, changement de mot de passe) ; `public_forms` 10/min partagé entre les 4 formulaires publics. Déclarer `throttle_scope = '…'` avec `ScopedThrottleMixin` (`apps/users/interfaces/throttling.py`) pour une nouvelle route sensible.
- **Pagination** : `?page_size=` jusqu'à 100 (défaut 12).
- **En production** : cookies sécurisés, en-têtes de sécurité, réponses JSON uniquement.

## Formatage du code (Ruff)

Le code Python est formaté et analysé avec **Ruff** (configuration dans `pyproject.toml` : 120 caractères, guillemets doubles, imports triés). **Tout le dépôt est formaté** ; la CI refuse un code non formaté (`ruff format --check` et `ruff check`).

```bash
pip install -r requirements-dev.txt
ruff format .                 # reformate (équivalent de PHP-CS-Fixer)
ruff check .                  # signale les problèmes ; ajouter --fix pour corriger l'automatique
```

Dans VS Code : installer l'extension **Ruff** (`charliermarsh.ruff`), puis activer « Format on Save » pour Python. Le dépôt étant entièrement formaté, le formatage à l'enregistrement ne produit plus de bruit : laisser « Format on Save » activé. Les `models.py` ré-exportent volontairement les modèles de `infrastructure/` (exception `F401` dans `pyproject.toml`) : ne pas y supprimer d'imports « inutilisés ».

## Tests

```bash
python manage.py test apps         # 39 tests, base PostgreSQL de test créée à la volée
```

À noter : `apps/users/tests_api_surface.py` **parcourt toutes les routes** et échoue si une route devient publique sans être déclarée dans `PUBLIC_OPERATIONS`, ou si un acheteur accède à une route réservée.

Recette automatisée contre l'API qui tourne (données de démo) :

```bash
python3 scripts/recette_api.py     # ~68 contrôles : connexions, droits par rôle, parcours acheteur/propriétaire/notaire, messagerie
```

## OpenAPI et front

Le schéma est complet : `python manage.py spectacular --file openapi.yaml` ne doit produire **ni erreur ni avertissement** (la CI le vérifie).

- Un `@extend_schema(responses=…)` est requis pour toute vue `APIView` (voir les `schemas.py` de chaque module pour les réponses agrégées).
- Un champ calculé (`SerializerMethodField`) porte un type via `@extend_schema_field` ou une annotation de retour.
- `config/openapi.py` marque comme obligatoires les champs des réponses (une réponse les contient toujours) ; les énumérations ont des noms explicites (`ENUM_NAME_OVERRIDES` dans `settings.py`).
- Côté front, `npm run api:types` génère les types TypeScript depuis ce schéma.

## Base de données

Index ajoutés sur les champs filtrés ou triés (statut, commune, type, étape et téléphone du prospect, date des visites…). Pour tout nouveau filtre fréquent : `indexes = [...]` dans le `Meta` du modèle, puis `makemigrations`. Les écrans de liste doivent charger leurs relations d'un coup (`select_related` / `prefetch_related` ; voir `cards_qs()` dans `properties` et `PROPERTY_CARD_RELATED` dans `crm`).

## Back-office

Le back-office est désormais **dans le front Next.js** (`/admin`). Le dossier `admin-web/` (Vite + TanStack) est l'ancienne application, conservée comme référence le temps de la recette ; elle n'est plus maintenue et ne fonctionne plus telle quelle (l'API exige maintenant une connexion avec rafraîchissement du jeton).
