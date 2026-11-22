> **OBSOLÈTE** — Le back-office vit désormais dans le front Next.js (`thiebbroimmobilier`, route `/admin`), avec les mêmes composants (`src/components/admin-ui/`).
> Cette application est conservée comme référence de design le temps de la recette, puis sera supprimée. Elle ne fonctionne plus telle quelle : l'API exige une connexion avec rafraîchissement du jeton, et certaines routes qu'elle appelle n'existent plus.

# 🖥️ THIEBBRO IMMO - Back-Office (TanStack & Tailwind v4)

Application web d'administration et CRM développée avec **TanStack Router**, **TanStack Query** et **Tailwind CSS v4**, reprenant l'architecture et le design system soigné de votre projet `front-web`.

---

## 🛠️ Stack Technique

- **Framework & Bundler** : React 19 + TypeScript + Vite 6
- **Routing** : TanStack Router (`@tanstack/react-router`) avec routage basé sur les fichiers (`src/routes/`)
- **Data Fetching & Cache** : TanStack Query (`@tanstack/react-query` v5)
- **Styling** : Tailwind CSS v4 (`@tailwindcss/vite`) avec palette personnalisée émeraude (`#2ca58d`), mode sombre/clair et glassmorphism
- **Composants & Icônes** : Lucide React, classes utilitaires `clsx` & `tailwind-merge`

---

## 🧭 Pages et Écrans Implémentés

| Route | Écran CDC | Description |
| :--- | :--- | :--- |
| **`/`** | **Écran 22** | **Tableau de bord :** KPIs en temps réel (Prospects, biens publiés, visites, rentabilité moyenne) et tableau des derniers biens. |
| **`/properties`** | **Écran 23** | **Gestion des biens :** Catalogue interactif avec recherche texte et filtrage par commune (Cocody, Bingerville, Marcory, Bassam). |
| **`/projects`** | **Écran 24** | **Programmes neufs :** Gestion des résidences et suivi de disponibilité de chaque lot (Disponible, Option, Réservé, Vendu). |
| **`/crm`** | **Écran 26 & 27** | **Pipeline CRM Kanban :** Découpage en colonnes avec score automatique THIEBBRO, température commerciale et détails du projet. |
| **`/simulators`** | **Écran 12** | **Calculateur de rentabilité :** Simulateur financier interactif connecté à l'API Django Clean Architecture. |

---

## 🚀 Lancement en Développement

Dans un terminal dédié :

```bash
cd admin-web
npm run dev
```

L'application s'ouvre sur **[http://localhost:5174](http://localhost:5174)** et communique directement avec le backend Django sur `http://127.0.0.1:8000/api/v1`.
