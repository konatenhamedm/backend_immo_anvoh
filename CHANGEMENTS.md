# Changements — intégration avec le site Next.js (novembre 2026)

Ce document décrit ce qui a changé dans l'API (commit `8bab094`) et pourquoi.

**L'objectif :** que le site `thiebbroimmov1` fonctionne entièrement sur cette API. Jusqu'ici, le site affichait des données de démonstration écrites en dur dans le code. Chaque écran du site a été relié à une route de l'API. Quand l'API n'avait pas ce qu'il fallait, la route ou le module a été créé ici.

Le document du site (`thiebbroimmov1/CHANGEMENTS.md`) décrit l'autre moitié du travail.

---

## 1. À faire après avoir récupéré le code

```bash
pip install -r requirements.txt
python manage.py migrate          # 4 nouveaux modules + nouvelles colonnes
python manage.py seed_data        # données de démonstration (développement uniquement)
python manage.py test apps.accreditation
```

**Variables d'environnement** (voir `.env.example`) :

| Variable | Rôle | Changement |
| :--- | :--- | :--- |
| `DEBUG` | Mode développement | **Vaut désormais `False` par défaut.** Mettre `DEBUG=True` en local. |
| `SECRET_KEY` | Clé Django | **Obligatoire quand `DEBUG=False`** : le serveur refuse de démarrer sans elle. |
| `JWT_ACCESS_MINUTES` | Durée du jeton d'accès | Nouveau, 60 min par défaut (avant : 24 h). |
| `SEED_PASSWORD` | Mot de passe des comptes de démo | Nouveau. Sans cette variable, un mot de passe aléatoire est généré et affiché une fois. |
| `CORS_ALLOWED_ORIGINS` | Origines autorisées | Plus d'ouverture totale en `DEBUG` : il faut déclarer l'URL du site et celle du back-office. |

---

## 2. Sécurité de l'API

**Pourquoi :** avant ce travail, toutes les routes étaient ouvertes. N'importe qui pouvait lister les utilisateurs, modifier un bien ou se créer un compte administrateur à l'inscription.

- **Toute route exige désormais une connexion** (`DEFAULT_PERMISSION_CLASSES = IsAuthenticated`). Les routes publiques (catalogue, fiche bien, simulateurs, notaires, demande de contact) le déclarent explicitement avec `AllowAny`.
- **Des permissions par rôle** sont centralisées dans `apps/users/interfaces/permissions.py` :

  | Permission | Qui passe |
  | :--- | :--- |
  | `IsAdminRole` | Administrateurs uniquement |
  | `IsStaffOrAgent` | Administrateurs et conseillers |
  | `IsOwnerRole` | Propriétaires et promoteurs |
  | `IsNotaryOrAdmin` | Notaires partenaires et équipe Thiebbro |
  | `ReadOnlyOr(perm)` | Lecture pour tous, écriture avec la permission donnée |

- **Inscription :** on ne peut plus choisir son rôle librement. Seuls les rôles « grand public » sont acceptés (`SELF_SERVICE_ROLES` : particulier, investisseur, propriétaire, promoteur). Le mot de passe passe par les validateurs Django.
- **Profil :** un utilisateur ne peut plus modifier son propre rôle (champ en lecture seule).
- **Limitation de débit :** 120 requêtes/min en anonyme, 600/min connecté.
- **Pagination unifiée** (`config/pagination.py`) : paramètre `page_size`, 100 maximum.
- **En production** : cookies sécurisés, en-têtes HTTP de sécurité, réponses JSON uniquement (pas d'interface navigable DRF).

---

## 3. Modules existants enrichis

### `users`

**Pourquoi :** le site a des écrans « Profil », « Vérification d'identité », « Changer de mot de passe », « Préférences de notification » et une gestion des utilisateurs côté admin.

- **Nouveau rôle :** `NOTAIRE`, pour les notaires partenaires qui vérifient les dossiers.
- **Nouveaux champs :**
  - `identity_status` et `identity_document` : pièce d'identité déposée, puis vérifiée.
  - `notification_preferences` (JSON).
- **Nouvelles routes :**
  - `profile/identity/` : dépôt de la pièce.
  - `profile/password/` : changement de mot de passe.
  - `users/` et `users/<id>/` : gestion admin, avec filtres par rôle et recherche.
- **Profil :** il renvoie `is_admin`. Le site l'utilise pour masquer aux conseillers les écrans réservés aux administrateurs.

### `properties`

**Pourquoi :** la fiche bien, le catalogue, l'espace propriétaire et le catalogue admin du site utilisaient des champs qui n'existaient pas ici.

- **Nouveaux champs sur `Property` :**
  - `owner` : le propriétaire.
  - `transaction` : vente ou location.
  - `title_deed` : type de titre foncier.
  - `views_count` : nombre de vues.
  - `amenities_extra` : équipements supplémentaires.
  - Visite 3D : `tour_scan_requested`, `tour_scan_scheduled_at`, `tour_scan_technician`.
- **Statuts :**
  - Nouveau statut de vérification `REFUSE`.
  - `PUBLIC_STATUSES` définit ce qui est visible publiquement : un bien non vérifié n'apparaît plus dans le catalogue.
- **Slug et référence générés automatiquement :** le slug est unique, la référence suit le format `THI-AAAA-NNN`.
- **Images :** `PropertyImage.external_url` permet d'utiliser une image hébergée ailleurs. La méthode `url()` renvoie le fichier ou l'URL externe.
- **Programmes neufs :** `DevelopmentProject.cover_image_url` et `construction_progress` (avancement des travaux).
- **Nouvelles routes :**

  | Route | Usage |
  | :--- | :--- |
  | `home/` | Données de la page d'accueil, en un appel |
  | `search/` | Catalogue filtré (lecture publique, écriture équipe) |
  | `slug/<slug>/` | Fiche bien, avec comptage des vues (`?count_view=0` pour ne pas compter) |
  | `slugs/` | Liste des slugs (pré-rendu du site, sitemap) |
  | `meta/` | Valeurs des filtres (communes, types…) |
  | `invest/` | Biens et programmes pour la page « Investir » |
  | `projects/`, `projects/<id>/lots/`, `lots/<id>/` | Programmes neufs et lots |
  | `favorites/`, `favorites/<id>/toggle/` | Favoris de l'acheteur |
  | `owner/`, `owner/<id>/`, `owner/dashboard/` | Biens et tableau de bord du propriétaire |
  | `<id>/images/`, `images/<id>/` | Ajout et suppression de photos |
  | `admin/properties/` (`?tour=requested\|published`) | Catalogue complet pour l'équipe |

- **Données de démonstration :** `seed_data` a été réécrit.
  - Il reprend le catalogue de démonstration du site et crée 14 utilisateurs couvrant tous les rôles.
  - Il crée aussi des notaires, des programmes avec lots, des dossiers d'accréditation (avec PDF fictifs), des prospects, des visites, des plans d'investissement, des souscriptions, des baux, des reversements et des messages.
  - **Il refuse de s'exécuter si `DEBUG=False`**, sauf avec `--force`, pour ne pas polluer une base de production.

### `crm`

**Pourquoi :** le site a un formulaire de contact, un bouton WhatsApp, la réservation de visite, « Mes demandes », des alertes de recherche et un kanban de prospects côté admin. Avant, la logique de création de prospect était recopiée dans plusieurs vues.

- **Nouveau service** `domain/lead_service.py`, qui regroupe :
  - la normalisation des téléphones ;
  - la recherche d'un prospect existant avant d'en créer un (pas de doublon) ;
  - le passage d'étape ;
  - le recalcul du score.
- **Nouveau modèle `SearchAlert` :** alertes de recherche de l'acheteur, avec une fréquence.
- **Nouveau type de visite :** `VISITE_3D`.
- **Règles ajoutées :**
  - une date de visite passée est refusée ;
  - on ne peut pas réserver deux fois la même visite ;
  - un clic WhatsApp anonyme ne crée pas de prospect.
- **Nouvelles routes :**
  - `my-requests/`, `my-visits/<id>/cancel/` : acheteur.
  - `alerts/` : alertes de recherche.
  - `owner/visits/` : visites des biens du propriétaire.
  - `pipeline/kanban/` (`?agent=me`), `leads/`, `leads/<id>/notes/` : kanban et fiches prospects.
  - `visits/`, `inquiries/list/` : gestion par l'équipe.
  - `admin/dashboard/` : indicateurs du back-office.

### `simulators`

Les deux simulateurs (rendement, capacité d'emprunt) sont maintenant **explicitement publics**, puisque toutes les autres routes exigent désormais une connexion. Le site les appelle pour afficher le calcul officiel à côté de son estimation instantanée.

---

## 4. Nouveaux modules

Ils suivent la même organisation que les modules existants : `infrastructure/models.py`, `domain/services.py` pour les règles métier, `interfaces/` pour les serializers, vues et urls.

### `accreditation` — vérification des biens par un notaire

**Pourquoi :** le site promet des biens « certifiés », et l'espace propriétaire a un écran de dépôt des pièces. Rien de cela n'existait côté API.

- **Modèles :**
  - `Notary` : notaire partenaire, éventuellement lié à un compte utilisateur.
  - `AccreditationFile` : le dossier d'un bien (statut, étape, niveau de certification, motif de refus).
  - `PropertyDocument` : une pièce justificative, validée ou rejetée.
- **Parcours :**
  1. Le propriétaire dépose ses pièces : une seule par type, la nouvelle remplace l'ancienne. Le dossier est créé automatiquement.
  2. L'équipe assigne un notaire.
  3. Le notaire fait avancer le dossier, puis certifie ou refuse.
- **Règles** (`domain/services.py`) :
  - on ne fait pas avancer ni ne certifie un dossier auquel il manque une pièce obligatoire ;
  - un dossier certifié ou refusé n'est plus modifiable ;
  - un refus exige un motif ;
  - la certification et le refus mettent à jour le statut de vérification du bien.
- **Cloisonnement :** un notaire ne voit et ne modifie que **les dossiers qui lui sont assignés**. Seule l'équipe Thiebbro assigne les notaires.
- **Routes :**
  - `notaries/` : public.
  - `owner/files/`, `owner/properties/<id>/documents/` : propriétaire.
  - `queue/`, `queue/<id>/`, `documents/<id>/` : notaire et équipe.
  - `admin/notaries/` : lecture équipe, création admin.
- **Tests :** `apps/accreditation/tests.py`, 22 tests d'intégration couvrant le parcours complet et les droits de chaque rôle.

### `messaging` — messagerie interne

**Pourquoi :** les trois espaces du site ont un écran « Messages » et un compteur de non-lus.

- **Modèles :** `Conversation`, `ConversationParticipant` (suivi de lecture par participant) et `Message`.
- **Routes :** `conversations/`, `conversations/<id>/messages/`, `unread-count/`.

### `investments` — plans d'investissement et souscriptions

**Pourquoi :** la page « Investir » et les écrans « Mes investissements » (acheteur) et « Investissements » (admin) n'avaient pas de données réelles.

- **Modèles :**
  - `InvestmentPlan` : les plans proposés.
  - `Subscription` : la souscription d'un investisseur.
  - `ScheduleEntry` : une ligne de l'échéancier (versement ou revenu).
  - `InvestmentDocument` : un document lié à la souscription.
- **Règles** (`domain/services.py`) :
  - on ne souscrit qu'à un plan ouvert ;
  - souscrire génère l'échéancier ;
  - confirmer le premier paiement active la souscription ; le dernier versement payé la termine ;
  - les dates d'échéance sont calculées mois par mois.
- **Routes :**
  - `plans/`, `subscriptions/`, `me/` : acheteur.
  - `admin/plans/`, `admin/stats/`, `admin/subscriptions/…`, `admin/entries/<id>/confirm/` : équipe.

### `rentals` — gestion locative

**Pourquoi :** l'écran « Revenus » de l'espace propriétaire affichait des loyers inventés.

- **Modèles :** `Lease` (bail), `RentPayment` (loyer encaissé) et `OwnerPayout` (reversement au propriétaire).
- **Routes :**
  - `owner/summary/` : revenus du propriétaire.
  - `admin/leases/`, `admin/payments/`, `admin/payouts/` : équipe.

---

## 5. Back-office `admin-web`

**Pourquoi :** maintenant que l'API exige une connexion, le back-office TanStack ne pouvait plus rien charger.

- **Nouvel écran de connexion** (`LoginScreen.tsx`), réservé à l'équipe (administrateurs et conseillers).
- `src/lib/api.ts` :
  - l'URL de l'API vient de `VITE_API_URL` ;
  - le jeton est envoyé à chaque requête ;
  - une réponse 401 déconnecte l'utilisateur et ramène à l'écran de connexion.

---

## 6. Limites connues

- **Pas de prestataire de paiement :** l'équipe valide les paiements à la main (« Valider le paiement »).
- **Aucun e-mail ni SMS n'est envoyé** : alertes de recherche, notifications, confirmations de visite. Les préférences sont enregistrées, mais rien ne part encore.
- **« Mot de passe oublié »** ouvre un simple e-mail vers le support : il n'y a pas encore de route de réinitialisation.
