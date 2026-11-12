# 🏢 THIEBBRO IMMO - Backend API (Django Clean Architecture)

> **Plateforme PropTech Immobilière & Investissement (Côte d'Ivoire)**  
> Conçue pour alimenter une application web et mobile (Frontend TanStack / React).

---

## 🧭 Guide Rapide pour Développeur Symfony / Spring Boot / NestJS

Puisque tu maîtrises déjà **Symfony**, **Java Spring Boot** et **NestJS**, voici la table de correspondance immédiate pour prendre en main ce backend Django sans aucune friction :

| Concept | Symfony (PHP) | Spring Boot (Java) | NestJS (TS) | Django Clean Arch (Ce projet) |
| :--- | :--- | :--- | :--- | :--- |
| **CLI / Commandes** | `php bin/console ...` | `./mvnw ...` / `gradle` | `nest ...` / `npm run` | `python manage.py ...` |
| **Routage** | `routes.yaml` / Annotations | `@RequestMapping` | `@Controller('path')` | `urls.py` (`path()`, `include()`) |
| **Contrôleur HTTP** | `AbstractController` | `@RestController` | `@Controller` | DRF `APIView` / `GenericAPIView` dans `interfaces/views.py` |
| **Validation & DTO** | Symfony Form / Serializer | DTO + `@Valid` / Bean Validation | DTO + `class-validator` | `serializers.py` (`serializers.Serializer` / `ModelSerializer`) |
| **Cas d'Usage (Application)** | Command Handler / Service | `@Service` / UseCase | Service / Command Handler | `application/use_cases.py` |
| **Règles Métier Pures (Domain)** | Entités / Domain Services | Domain Model / `@DomainService` | Domain Entities / Services | `domain/entities.py` & `domain/services.py` |
| **ORM / Tables SQL** | Doctrine Entities (`#[ORM\Entity]`) | JPA `@Entity` / Hibernate | TypeORM `@Entity` / Prisma schema | `infrastructure/models.py` (`models.Model`) |
| **Abstraction Accès Données** | Doctrine Repository | Spring Data `JpaRepository` | Repository Pattern | `infrastructure/repositories.py` |
| **Migrations BD** | `doctrine:migrations:migrate` | Flyway / Liquibase | `prisma migrate` / `typeorm migration` | `python manage.py makemigrations` & `migrate` |
| **Back-Office Admin** | EasyAdmin / Sonata | Non inclus nativement | Non inclus nativement | **Django Admin natif** (`/admin/`, automatique et surpuissant) |
| **Documentation API** | NelmioApiDoc | Springdoc / Swagger UI | `@nestjs/swagger` | **drf-spectacular** (`/api/docs/`) |

---

## 🏛️ Structure Clean Architecture du Projet

Chaque domaine fonctionnel (Bounded Context DDD) est situé dans le dossier `apps/` et suit le découpage en 4 couches concentriques :

```text
backend-immobilier/
├── config/                     # Configuration globale du projet Django
│   ├── settings.py             # Configuration (DB, CORS, Apps, JWT/Auth, DRF)
│   ├── urls.py                 # Routage racine + Swagger UI (/api/docs/)
│   └── wsgi.py / asgi.py
│
├── apps/                       # Modules métier (Bounded Contexts)
│   ├── users/                  # Gestion des comptes (Particulier, Investisseur, Promoteur, Diaspora)
│   │   ├── domain/             # Règles et contrats métier utilisateurs
│   │   ├── application/        # Use cases d'inscription, validation profil
│   │   ├── infrastructure/     # Modèle User personnalisé (AbstractUser)
│   │   └── interfaces/         # Contrôleurs & DTOs
│   │
│   ├── properties/             # Catalogue des biens immobiliers & Fiches détaillées
│   │   ├── domain/             # Logique des biens, calcul de scoring
│   │   ├── application/        # Recherche avancée, filtre par critères
│   │   ├── infrastructure/     # Modèles Property, PropertyImage, Repositories
│   │   └── interfaces/         # Vues REST API & Serializers
│   │
│   ├── simulators/             # Simulateurs financiers (Règles métier pures)
│   │   ├── domain/             # Formules financières de rentabilité, mensualité, cash-flow
│   │   ├── application/        # Use cases : CalculateInvestmentYield, EstimateBorrowingCapacity
│   │   ├── infrastructure/     # Historique des simulations
│   │   └── interfaces/         # Endpoints DRF exposés au front TanStack
│   │
│   └── crm/                    # Pipeline commercial & Prospects
│       ├── domain/             # Pipeline d'acquisition (Nouveau -> Visite -> Vente)
│       ├── application/        # Traitement des leads (Trouvez-moi mon bien, WhatsApp)
│       ├── infrastructure/     # Modèles Lead, VisitRequest
│       └── interfaces/         # Endpoints de capture de leads et prise de RDV
│
├── .env                        # Variables d'environnement locales (PostgreSQL, CORS...)
├── requirements.txt            # Dépendances Python gelées
└── manage.py                   # Script CLI Django
```

---

## 🚀 Démarrage et Utilisation

### 1. Activer l'environnement virtuel Python

```bash
# Sur macOS / Linux
source .venv/bin/activate
```

### 2. Configurer la base de données PostgreSQL

Modifie le fichier `.env` avec tes identifiants locaux PostgreSQL :
```env
DB_ENGINE=django.db.backends.postgresql
DB_NAME=thiebbro_immo_db
DB_USER=mon_utilisateur_postgres
DB_PASSWORD=mon_mot_de_passe
DB_HOST=localhost
DB_PORT=5432
```

> **Astuce** : Crée la base de données une première fois sur ton serveur PostgreSQL :
> ```sql
> CREATE DATABASE thiebbro_immo_db;
> ```

### 3. Exécuter les migrations

```bash
python manage.py migrate
```

### 4. Créer un compte Administrateur

```bash
python manage.py createsuperuser
```

### 5. Lancer le serveur de développement

```bash
python manage.py runserver
```

L'API est alors disponible sur :
- **Swagger UI (Interactive API Docs)** : [http://127.0.0.1:8000/api/docs/](http://127.0.0.1:8000/api/docs/)
- **Documentation ReDoc** : [http://127.0.0.1:8000/api/redoc/](http://127.0.0.1:8000/api/redoc/)
- **Django Admin Back-Office** : [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

---

## 🧪 Tests Unitaires et Clean Architecture

Grâce au découplage de la Clean Architecture, la logique métier financière (`apps/simulators/domain/`) s'exécute sans base de données, à la vitesse de l'éclair :

```bash
python manage.py test apps.simulators
```

---

## 📱 Cartographie : Écrans Frontend vs Endpoints API Backend

| Écran Front-End | Intitulé / Rôle | Méthode & Endpoint API | Description |
| :--- | :--- | :--- | :--- |
| **Écran 03** | Inscription | `POST /api/v1/auth/register/` | Création compte + délivrance JWT |
| **Écran 03** | Connexion | `POST /api/v1/auth/login/` | Auth email/password -> JWT tokens |
| **Écran 04** | Accueil | `GET /api/v1/properties/home/` | Données agrégées : En vedette, récents, investissements, programmes |
| **Écran 05 & 06** | Recherche & Résultats | `GET /api/v1/properties/search/` | Filtres (Budget, type, commune, pièces, tri) |
| **Écran 07** | Fiche Bien | `GET /api/v1/properties/<uuid:id>/` | Détail complet, galerie, bloc rentabilité |
| **Écran 08** | Demande d'informations | `POST /api/v1/crm/inquiries/` | Crée le lead + associe le bien + log CRM |
| **Écran 09** | Clic WhatsApp | `POST /api/v1/crm/whatsapp-click/` | Loggue l'interaction commerciale CRM |
| **Écran 10** | Trouver mon bien (7 étapes) | `POST /api/v1/crm/find-my-property/` | Lead + Scoring automatique + Biens recommandés |
| **Écran 11** | Simulateur Capacité d'Achat | `POST /api/v1/simulators/borrowing-capacity/` | Calcul mensualité max & pouvoir d'achat |
| **Écran 12** | Calculateur Rentabilité | `POST /api/v1/simulators/calculate-investment/` | Rentabilité brute/nette, cash-flow, mensualité |
| **Écran 13** | Espace Investir | `GET /api/v1/properties/invest/` | Top rendement, meublés, terrains, programmes |
| **Écran 14** | Mes Favoris | `GET /api/v1/properties/favorites/`<br>`POST /api/v1/properties/favorites/<id>/toggle/` | Consultation et ajout/retrait favoris |
| **Écran 15** | Mes Demandes | `GET /api/v1/crm/my-requests/` | Inquiries, visites et état du projet |
| **Écran 16** | Prise de RDV / Visite | `POST /api/v1/crm/visits/schedule/` | Programme visite physique ou visio |
| **Écran 18** | Profil Utilisateur & Projet | `GET /api/v1/auth/profile/`<br>`PATCH /api/v1/auth/profile/` | Profil et informations "Mon Projet" |
| **Écran 20 & 24** | Programmes Neufs & Lots | `GET /api/v1/properties/projects/`<br>`GET /api/v1/properties/projects/<id>/` | Programmes avec lots (F3, 85m², dispo/réservé) |
| **Écran 26** | Back-office CRM Kanban | `GET /api/v1/crm/pipeline/kanban/` | Colonnes Kanban prospects avec scores |

---

## 🤝 Intégration avec le Frontend TanStack (Ton Collègue)

- **Swagger UI Interactive** : [http://127.0.0.1:8000/api/docs/](http://127.0.0.1:8000/api/docs/)
- **Documentation ReDoc** : [http://127.0.0.1:8000/api/redoc/](http://127.0.0.1:8000/api/redoc/)
- **Schéma OpenAPI 3 brut** : [http://127.0.0.1:8000/api/schema/](http://127.0.0.1:8000/api/schema/)
- **CORS activé** : Les origines Vite / TanStack (`localhost:5173`, `localhost:3000`) sont autorisées via `django-cors-headers`.
- **Génération automatique de code côté Front** : Ton collègue peut générer ses types TypeScript et requêtes TanStack Query avec `@hey-api/openapi-ts` ou `kubb`.

---

## 🔄 Mise à jour : API connectée au site Next.js (novembre 2026)

### Sécurité (changements importants)
- **Toutes les routes exigent une connexion par défaut.** Les routes publiques (catalogue, fiche, simulateurs, formulaires de contact) le déclarent explicitement.
- **Permissions par rôle** (`apps/users/interfaces/permissions.py`) : administrateur, équipe (admin + conseiller), propriétaire, notaire.
- **Rôle verrouillé** : l'inscription n'accepte que `PARTICULIER`, `INVESTISSEUR` ou `PROPRIETAIRE` ; le profil ne permet plus de changer de rôle. Seul un administrateur attribue `AGENT`, `NOTAIRE` ou `ADMIN`.
- `DEBUG` désactivé par défaut, `SECRET_KEY` obligatoire en production, CORS limité aux origines déclarées, limitation de débit (120 req/min anonyme, 600 connecté), mots de passe validés par Django (8 caractères minimum).
- `seed_data` refuse de tourner avec `DEBUG=False` (sauf `--force`) et n'écrit plus aucun mot de passe en dur.

### Nouveaux domaines (`apps/`)
| App | Rôle | Routes principales |
| :--- | :--- | :--- |
| `accreditation` | Notaires partenaires, dossier de vérification par bien (4 étapes), pièces justificatives, certification ou refus | `/api/v1/accreditation/notaries/`, `owner/files/`, `owner/properties/<id>/documents/`, `queue/`, `queue/<id>/` (assign, advance, certify, refuse), `documents/<id>/` |
| `messaging` | Conversations acheteur ↔ propriétaire / conseiller / notaire, non-lus | `/api/v1/messaging/conversations/`, `conversations/<id>/messages/`, `unread-count/` |
| `investments` | Plans, souscriptions, échéancier (mensualités, versements, revenus reversés), documents | `/api/v1/investments/plans/`, `subscriptions/`, `me/`, `admin/plans/`, `admin/stats/`, `admin/subscriptions/`, `admin/entries/<id>/confirm/` |
| `rentals` | Gestion locative : baux, loyers encaissés, versements aux propriétaires | `/api/v1/rentals/owner/summary/`, `admin/leases/`, `admin/payments/`, `admin/payouts/` |

### Ajouts aux domaines existants
- **Biens** : propriétaire, vente ou location, type de titre, vues, équipements libres, photos par URL externe, demande et planification de scan 3D. Référence et slug générés automatiquement. Fiche par slug (`/properties/slug/<slug>/`), espace propriétaire (`/properties/owner/`, `owner/dashboard/`), photos (`/properties/<id>/images/`), catalogue back-office (`/properties/admin/properties/`), référentiels (`/properties/meta/`).
- **CRM** : téléphones normalisés et dédoublonnés, score cumulatif (ne baisse plus), étapes qui n'avancent que vers l'avant, plus de lead « Inconnu » pour les clics WhatsApp anonymes, visites dans le passé refusées. Nouveaux : tableau de bord admin, saisie manuelle de prospect, notes, visites côté propriétaire, annulation par le client, alertes de recherche (`/crm/alerts/`).
- **Comptes** : vérification d'identité (dépôt de pièce), préférences de notification, changement de mot de passe (`/auth/profile/password/`), gestion des comptes par l'admin (filtres, statut, rôle).

### Paiements
Aucun prestataire de paiement n'est branché. Une souscription crée l'échéancier ; le premier versement reste « en attente de validation » jusqu'à sa confirmation par l'équipe (`admin/entries/<id>/confirm/`, bouton « Valider le paiement » dans le back-office). Le branchement d'un prestataire (CinetPay, Paydunya…) remplacera cette confirmation par un webhook.

### Démarrage rapide en local (SQLite)
```bash
python -m venv .venv && .venv/Scripts/pip install -r requirements.txt   # Windows (sous macOS/Linux : .venv/bin/…)
export DB_ENGINE=django.db.backends.sqlite3 DEBUG=True SEED_PASSWORD='un-mot-de-passe-de-demo'
python manage.py migrate
python manage.py seed_data      # 12 biens, propriétaires, notaires, CRM, plans, gestion locative, messages
python manage.py runserver
python manage.py test apps      # 22 tests
```
Comptes de démonstration (mot de passe = `SEED_PASSWORD`) : `admin@thiebbro.ci` (admin), `koffi.agent@thiebbro.ci` (conseiller), `k.yao@mail.ci` (propriétaire), `awa.traore@mail.ci` (acheteuse), `a.kone@notaire.ci` (notaire).

### admin-web
Le back-office Vite a désormais un écran de connexion (réservé à l'équipe) : l'API n'accepte plus d'appels anonymes. L'URL de l'API se règle avec `VITE_API_URL`. Le site Next.js contient un back-office plus complet (`/admin`) : `admin-web` peut être retiré à terme.
