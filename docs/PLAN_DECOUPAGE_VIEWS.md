# Plan — découper `views.py` par public (crm et properties)

**Statut : RÉALISÉ** (crm et properties découpés, dépôt reformaté avec Ruff). Contrôles effectués : schéma OpenAPI régénéré **identique octet pour octet** (10 789 lignes), 193 routes identiques (vues, permissions, quotas), 39 tests et 68 contrôles de recette réussis, avant et après le reformatage.

Le reste de ce document décrit le plan suivi.

## Pourquoi

| Fichier | Lignes | Classes | Publics mélangés |
| :--- | ---: | ---: | :--- |
| `apps/properties/interfaces/views.py` | 489 | 22 | visiteurs, acheteur, propriétaire, équipe, programmes neufs, photos |
| `apps/crm/interfaces/views.py` | 476 | 20 | visiteurs (formulaires), acheteur, propriétaire, équipe (prospects, visites, demandes, tableau de bord, recherche) |

Les autres modules sont courts et lisibles : `investments` 205 lignes, `accreditation` 169, `users` 135, `rentals` 127, `messaging` 124, `simulators` 62. **Seuls ces deux-là sont à découper.**

Les classes elles-mêmes sont petites (20 lignes en moyenne). Ce qui fait « se perdre », c'est de passer d'une vue publique à une vue réservée à l'équipe, puis à une vue propriétaire, dans le même fichier, avec des fonctions utilitaires au milieu.

## Ce qui rend l'opération sûre

- **Aucun autre fichier n'importe ces vues** : seuls `apps/crm/interfaces/urls.py` et `apps/properties/interfaces/urls.py` le font (vérifié par recherche dans `apps/` et `config/`).
- Les **tests utilisent des URL**, jamais des noms de classes ni `reverse()`.
- Aucune route, aucun nom de classe, aucune permission, aucun `@extend_schema` ne change : ce sont des **déplacements de code**, sans modification de logique.

## Découpage proposé

`views.py` devient un **paquet** `views/`. Son `__init__.py` ré-exporte toutes les vues : les `urls.py` actuels continuent de fonctionner sans aucune modification (ils pourront importer directement les sous-modules plus tard).

### `apps/properties/interfaces/views/`

| Fichier | Contenu | Public |
| :--- | :--- | :--- |
| `_common.py` | `cards_qs`, `public_qs`, `ctx`, `can_manage`, `apply_search_filters`, `owner_qs`, `_visible_or_404` | — |
| `catalog.py` | `HomeScreenView`, `PropertySearchView`, `PropertyDetailView`, `PropertyBySlugView`, `PropertySlugListView`, `CatalogMetaView`, `InvestmentScreenView` | visiteurs (lecture) |
| `projects.py` | `DevelopmentProject*View`, `ProjectLot*View` | visiteurs (lecture) / équipe (écriture) |
| `favorites.py` | `FavoritesListView`, `FavoriteToggleView`, `AdminPropertyFavorite*View` | acheteur / équipe |
| `owner.py` | `OwnerPropertyListCreateView`, `OwnerPropertyDetailView`, `OwnerDashboardView` | propriétaire |
| `images.py` | `PropertyImageUploadView`, `PropertyImageDetailView` | propriétaire / équipe |
| `admin.py` | `AdminPropertyListCreateView`, `AdminPropertyDetailView` | équipe |

### `apps/crm/interfaces/views/`

| Fichier | Contenu | Public |
| :--- | :--- | :--- |
| `_common.py` | `_user`, `_public_property`, `PROPERTY_CARD_RELATED` | — |
| `public_forms.py` | `PropertyInquiryView`, `WhatsAppClickTrackView`, `FindMyPropertyView`, `ScheduleVisitView` | visiteurs (quota `public_forms`) |
| `buyer.py` | `MyRequestsView`, `MyVisitCancelView`, `SearchAlertListCreateView`, `SearchAlertDetailView` | acheteur |
| `owner.py` | `OwnerVisitListView`, `OwnerVisitUpdateView` | propriétaire |
| `admin_leads.py` | `PipelineKanbanView`, `LeadDetailAdminView`, `LeadNoteView`, `LeadCreateAdminView` | équipe |
| `admin_requests.py` | `VisitRequestListAdminView`, `VisitRequestDetailAdminView`, `PropertyInquiryListAdminView`, `PropertyInquiryDetailAdminView` | équipe |
| `admin_dashboard.py` | `AdminDashboardView`, `GlobalSearchView` | équipe |

Ordre dans chaque fichier : imports, puis les vues du plus simple au plus complexe. Un fichier fait entre 40 et 130 lignes.

## Méthode (mécanique, vérifiable à chaque étape)

1. **Point de départ** : `python manage.py test apps` (39 tests), `python3 scripts/recette_api.py` (68 contrôles), et deux « empreintes » :
   ```bash
   python manage.py spectacular --file /tmp/openapi_avant.yaml
   python manage.py shell -c "from django.urls import get_resolver; ..."   # liste triée des routes et de leurs classes
   ```
2. Créer `views/__init__.py` en ré-exportant les classes de l'ancien fichier, puis déplacer **un sous-module à la fois** (`git mv` pour le premier, copie du code ensuite). Après chaque déplacement : `python manage.py check` et les tests.
3. **Contrôle final** : le schéma OpenAPI régénéré doit être **identique octet pour octet** à `openapi_avant.yaml` (mêmes routes, mêmes `operationId`, mêmes permissions) ; la liste des routes aussi. Tests et recette inchangés.
4. Aucun reformatage dans ce commit (voir ci-dessous).

## Ordre des commits (pour garder des diffs lisibles)

1. **Découpage** : déplacements purs, aucune modification de ligne.
2. **Reformatage Ruff** de tout le dépôt (`ruff format .`), seul dans son commit, puis son hash dans `.git-blame-ignore-revs`.
3. Ensuite seulement, les évolutions fonctionnelles.

## Risques et précautions

- **Conflits de fusion** : si quelqu'un modifie `views.py` pendant l'opération, git ne sait pas suivre le code déplacé. → faire l'opération **juste après** la fusion des branches en cours, avec un gel de ces deux fichiers pendant ~1 heure.
- **`git blame`** : l'historique des lignes déplacées pointera vers le commit de découpage. → message de commit explicite ; `git log -S "NomDeLaClasse"` retrouve l'origine.
- **Imports circulaires** : `_common.py` ne doit importer aucune vue ; les sous-modules n'importent que `_common.py` et les modèles/serializers.

## Règle pour la suite

Un fichier de vues par **public** dans un module : `public`, `buyer` (ou `me`), `owner`, `admin`. Découper un module dès qu'il dépasse ~250 lignes ou 3 publics. Les modules actuels sous ce seuil restent des fichiers uniques.

## Effort estimé

Environ 1 à 2 heures pour les deux modules, presque entièrement mécanique, avec les contrôles ci-dessus à chaque étape.
