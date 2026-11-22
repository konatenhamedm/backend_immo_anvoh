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
