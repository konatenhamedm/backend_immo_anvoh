import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  Building2,
  Search,
  Plus,
  Flame,
  RotateCw,
  FileSpreadsheet,
  RotateCcw,
  Sparkles
} from 'lucide-react'
import { fetchApi } from '@/lib/api'
import { formatFCFA } from '@/lib/utils'
import { StatutBadge } from '@/presentation/components/shared/ui/StatutBadge'
import { TableHeaderCustom, TableCardWrapper } from '@/presentation/components/shared/ui/TableHeaderCustom'
import { TableRowActions } from '@/presentation/components/shared/ui/TableRowActions'
import { Select2, Select2Option } from '@/presentation/components/shared/ui/Select2'
import { PropertyAddModal } from './Add'
import { PropertyEditModal } from './Edit'
import { PropertyShowModal } from './Show'
import { PropertyDeleteModal } from './Delete'

const COMMUNE_OPTIONS: Select2Option[] = [
  { value: '', label: 'Toutes les communes' },
  { value: 'Cocody', label: 'Cocody' },
  { value: 'Bingerville', label: 'Bingerville' },
  { value: 'Marcory', label: 'Marcory' },
  { value: 'Grand-Bassam', label: 'Grand-Bassam' },
  { value: 'Yamoussoukro', label: 'Yamoussoukro' },
]

const TYPE_OPTIONS: Select2Option[] = [
  { value: '', label: 'Tous les types' },
  { value: 'APPARTEMENT', label: 'Appartement' },
  { value: 'VILLA', label: 'Villa Individuelle' },
  { value: 'RESIDENCE_MEUBLEE', label: 'Résidence Meublée' },
  { value: 'TERRAIN', label: 'Terrain constructible' },
  { value: 'IMMEUBLE', label: 'Immeuble de rapport' },
]

const TYPOLOGY_OPTIONS: Select2Option[] = [
  { value: '', label: 'Toutes typologies' },
  { value: 'F2', label: 'F2 (2 pièces)' },
  { value: 'F3', label: 'F3 (3 pièces)' },
  { value: 'F4', label: 'F4 (4 pièces)' },
  { value: 'F5', label: 'F5 (5 pièces et +)' },
]

const STATUS_OPTIONS: Select2Option[] = [
  { value: '', label: 'Tous les statuts' },
  { value: 'VERIFIE', label: 'Bien vérifié' },
  { value: 'VERIFICATION_RENFORCEE', label: 'ACD certifié' },
  { value: 'EN_ATTENTE', label: 'En attente' },
]

const BUDGET_OPTIONS: Select2Option[] = [
  { value: '', label: 'Tous les budgets' },
  { value: '50000000', label: 'Moins de 50 Millions' },
  { value: '100000000', label: 'Moins de 100 Millions' },
  { value: '250000000', label: 'Moins de 250 Millions' },
]

export function PropertiesModule() {
  const [search, setSearch] = useState('')
  const [communeFilter, setCommuneFilter] = useState('')
  const [typeFilter, setTypeFilter] = useState('')
  const [typologyFilter, setTypologyFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [budgetFilter, setBudgetFilter] = useState('')

  // États pour les modales
  const [isAddOpen, setIsAddOpen] = useState(false)
  const [isEditOpen, setIsEditOpen] = useState(false)
  const [isShowOpen, setIsShowOpen] = useState(false)
  const [isDeleteOpen, setIsDeleteOpen] = useState(false)
  const [selectedProperty, setSelectedProperty] = useState<any | null>(null)

  // Récupération des données depuis l'API Django / PostgreSQL
  const { data, isLoading, refetch, isFetching } = useQuery({
    queryKey: ['properties-list', search, communeFilter, typeFilter, typologyFilter, statusFilter, budgetFilter],
    queryFn: () => {
      let url = '/properties/search/?'
      if (search) url += `q=${encodeURIComponent(search)}&`
      if (communeFilter) url += `commune=${encodeURIComponent(communeFilter)}&`
      if (typeFilter) url += `type=${encodeURIComponent(typeFilter)}&`
      if (typologyFilter) url += `typology=${encodeURIComponent(typologyFilter)}&`
      if (budgetFilter) url += `max_price=${encodeURIComponent(budgetFilter)}&`
      return fetchApi<{ results: any[] }>(url)
    },
  })

  const properties = data?.results || []

  // Filtrage local supplémentaire si nécessaire
  const filteredProperties = properties.filter((p: any) => {
    if (statusFilter && p.verification_status !== statusFilter) return false
    return true
  })

  // Calcul du cumul total du portefeuille
  const totalPortfolio = filteredProperties.reduce(
    (acc: number, p: any) => acc + (parseFloat(p.price) || 0),
    0
  )

  const handleResetFilters = () => {
    setSearch('')
    setCommuneFilter('')
    setTypeFilter('')
    setTypologyFilter('')
    setStatusFilter('')
    setBudgetFilter('')
  }

  const columns = [
    { key: 'id', label: 'ID', className: 'w-16' },
    { key: 'date', label: 'DATE AJOUT', className: 'w-24' },
    { key: 'matricule', label: 'RÉFÉRENCE', className: 'w-28' },
    { key: 'title', label: 'DÉSIGNATION DU BIEN' },
    { key: 'commune', label: 'COMMUNE / LOCALITÉ' },
    { key: 'type', label: 'TYPE & SURF.' },
    { key: 'price', label: 'PRIX DE VENTE (FCFA)' },
    { key: 'yield', label: 'RENTABILITÉ' },
    { key: 'score', label: 'INDICE IA' },
    { key: 'status', label: 'STATUT' },
    { key: 'actions', label: 'ACTIONS', className: 'text-right w-28' },
  ]

  const handleOpenShow = (prop: any) => {
    setSelectedProperty(prop)
    setIsShowOpen(true)
  }

  const handleOpenEdit = (prop: any) => {
    setSelectedProperty(prop)
    setIsEditOpen(true)
  }

  const handleOpenDelete = (prop: any) => {
    setSelectedProperty(prop)
    setIsDeleteOpen(true)
  }

  return (
    <div className="w-full space-y-4 animate-fade-in">
      {/* 1. Barre d'action supérieure pleine largeur */}
      <div className="w-full flex flex-col lg:flex-row lg:items-center justify-between gap-4 bg-white dark:bg-slate-900 px-6 py-4 rounded-2xl border border-slate-200/90 dark:border-slate-800 shadow-2xs">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl sm:text-2xl font-black tracking-tight text-slate-900 dark:text-white">
              Catalogue & Gestion des Biens
            </h1>
            {/* <span className="px-2 py-0.5 rounded-full text-[10px] font-black bg-blue-100 text-blue-800 dark:bg-blue-950/70 dark:text-blue-300">
              PostgreSQL Live
            </span> */}
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Administration complète du portefeuille immobilier, titrage foncier et calculs de rendement.
          </p>
        </div>

        {/* Boutons d'action globaux */}
        <div className="flex items-center flex-wrap gap-2.5">
          <button
            type="button"
            onClick={() => refetch()}
            disabled={isFetching}
            className="px-3.5 py-2 text-xs font-semibold rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-200 hover:bg-slate-50 transition-colors flex items-center gap-1.5 cursor-pointer shadow-2xs"
            title="Actualiser les données"
          >
            <RotateCw className={`w-3.5 h-3.5 ${isFetching ? 'animate-spin text-blue-600' : ''}`} />
            <span>Actualiser</span>
          </button>

          <button
            type="button"
            onClick={() => alert('Exportation Excel du portefeuille générée avec succès.')}
            className="px-3.5 py-2 text-xs font-semibold rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-200 hover:bg-slate-50 transition-colors flex items-center gap-1.5 cursor-pointer shadow-2xs"
          >
            <FileSpreadsheet className="w-3.5 h-3.5 text-emerald-600" />
            <span>Exporter</span>
          </button>

          <button
            type="button"
            onClick={() => setIsAddOpen(true)}
            className="px-4 py-2 text-xs font-bold rounded-xl bg-blue-600 hover:bg-blue-700 text-white shadow-md shadow-blue-600/25 transition-all flex items-center gap-2 cursor-pointer"
          >
            <Plus className="w-4 h-4" />
            <span>Ajouter une annonce</span>
          </button>
        </div>
      </div>

      {/* 2. Barre de Filtres avec Sélecteurs Select2 Pleine Largeur (Style Educ360 de la capture) */}
      <div className="w-full p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-800 shadow-2xs space-y-4">
        {/* Rangée des champs Select2 multi-colonnes */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3 w-full">
          <Select2
            label="Commune"
            placeholder="Toutes les communes"
            options={COMMUNE_OPTIONS}
            value={communeFilter}
            onChange={setCommuneFilter}
          />

          <Select2
            label="Type de bien"
            placeholder="Tous les types"
            options={TYPE_OPTIONS}
            value={typeFilter}
            onChange={setTypeFilter}
          />

          <Select2
            label="Typologie"
            placeholder="Toutes typologies"
            options={TYPOLOGY_OPTIONS}
            value={typologyFilter}
            onChange={setTypologyFilter}
          />

          <Select2
            label="Budget maximal"
            placeholder="Tous les budgets"
            options={BUDGET_OPTIONS}
            value={budgetFilter}
            onChange={setBudgetFilter}
          />

          <Select2
            label="Certification Foncière"
            placeholder="Tous les statuts"
            options={STATUS_OPTIONS}
            value={statusFilter}
            onChange={setStatusFilter}
          />
        </div>

        {/* Ligne inférieure : Raccourcis + Recherche textuelle + Réinitialiser */}
        <div className="flex flex-col md:flex-row items-center justify-between gap-3 pt-2 border-t border-slate-100 dark:border-slate-800">
          <div className="flex items-center gap-2 flex-wrap text-xs">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wide">
              Raccourci zone :
            </span>
            {['', 'Cocody', 'Bingerville', 'Marcory', 'Grand-Bassam'].map((com) => (
              <button
                key={com}
                type="button"
                onClick={() => setCommuneFilter(com)}
                className={`px-2.5 py-1 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                  communeFilter === com
                    ? 'bg-blue-600 text-white shadow-2xs'
                    : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200'
                }`}
              >
                {com || 'Tout Abidjan'}
              </button>
            ))}
          </div>

          <div className="flex items-center gap-3 w-full md:w-auto">
            <div className="relative w-full md:w-72">
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Rechercher par titre, quartier..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full pl-9 pr-3 py-1.5 text-xs rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 focus:outline-hidden focus:border-blue-500 text-slate-900 dark:text-white"
              />
            </div>

            <button
              type="button"
              onClick={handleResetFilters}
              className="px-3 py-1.5 text-xs font-semibold text-slate-500 hover:text-slate-900 dark:hover:text-white flex items-center gap-1.5 shrink-0 transition-colors cursor-pointer"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Réinitialiser les filtres</span>
            </button>
          </div>
        </div>
      </div>

      {/* 3. Tableau Pleine Largeur (Bandeau de titre + Entête sombre #0A2540) */}
      <div className="w-full">
        <TableCardWrapper
          title="LA LISTE DES BIENS EN CATALOGUE"
          count={`${filteredProperties.length} BIENS`}
          badgeRight={`Cumul portefeuille : ${formatFCFA(totalPortfolio)}`}
          icon={<Building2 className="w-4 h-4" />}
        >
          <TableHeaderCustom columns={columns} />
          <tbody className="divide-y divide-slate-100 dark:divide-slate-800/80">
            {isLoading ? (
              <tr>
                <td colSpan={11} className="py-12 text-center text-slate-400 italic">
                  Chargement des données depuis PostgreSQL...
                </td>
              </tr>
            ) : filteredProperties.length === 0 ? (
              <tr>
                <td colSpan={11} className="py-12 text-center text-slate-400 italic">
                  Aucun bien ne correspond aux filtres sélectionnés.
                </td>
              </tr>
            ) : (
              filteredProperties.map((p: any, idx: number) => (
                <tr
                  key={p.id}
                  onClick={() => handleOpenShow(p)}
                  className="hover:bg-blue-50/40 dark:hover:bg-slate-800/50 transition-colors cursor-pointer group"
                >
                  {/* ID stylisé */}
                  <td className="py-3 px-4 font-mono text-[11px] text-slate-400">
                    #{String(idx + 1).padStart(4, '0')}
                  </td>

                  {/* Date */}
                  <td className="py-3 px-4 text-[11px] text-slate-500 whitespace-nowrap">
                    {new Date(p.created_at).toLocaleDateString('fr-FR')}
                  </td>

                  {/* Référence en bleu gras cliquable */}
                  <td className="py-3 px-4 font-mono font-black text-xs text-blue-600 dark:text-blue-400 whitespace-nowrap">
                    {p.reference}
                  </td>

                  {/* Désignation */}
                  <td className="py-3 px-4">
                    <div className="font-bold text-xs uppercase text-slate-900 dark:text-white group-hover:text-blue-600 transition-colors">
                      {p.title}
                    </div>
                    <div className="text-[10px] text-slate-400 font-normal">
                      {p.neighborhood}
                    </div>
                  </td>

                  {/* Commune */}
                  <td className="py-3 px-4 text-xs font-semibold text-slate-700 dark:text-slate-300 whitespace-nowrap">
                    {p.commune}
                  </td>

                  {/* Type & Surface */}
                  <td className="py-3 px-4 whitespace-nowrap">
                    <span className="px-2 py-0.5 rounded-md bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 text-[11px] font-semibold">
                      {p.typology_display || p.property_type_display} • {p.surface_sqm} m²
                    </span>
                  </td>

                  {/* Montant en vert émeraude gras (Style front-web 100 000 F) */}
                  <td className="py-3 px-4 font-black text-xs text-emerald-600 dark:text-emerald-400 whitespace-nowrap">
                    {formatFCFA(p.price)}
                  </td>

                  {/* Rentabilité */}
                  <td className="py-3 px-4 text-xs font-bold text-slate-800 dark:text-slate-200 whitespace-nowrap">
                    {p.estimated_yield_rate ? `${p.estimated_yield_rate} %` : '—'}
                  </td>

                  {/* Score */}
                  <td className="py-3 px-4 whitespace-nowrap">
                    <span className="inline-flex items-center gap-1 font-bold text-amber-600 dark:text-amber-400 text-xs">
                      <Flame className="w-3.5 h-3.5" />
                      {p.investment_score || 80}/100
                    </span>
                  </td>

                  {/* Statut Badge */}
                  <td className="py-3 px-4 whitespace-nowrap">
                    <StatutBadge status={p.verification_status || 'VERIFIE'} />
                  </td>

                  {/* BOUTONS D'ACTION (Voir, Modifier, Supprimer) */}
                  <td className="py-3 px-4 text-right whitespace-nowrap">
                    <TableRowActions
                      onShow={() => handleOpenShow(p)}
                      onEdit={() => handleOpenEdit(p)}
                      onDelete={() => handleOpenDelete(p)}
                    />
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </TableCardWrapper>
      </div>

      {/* 4. Les Modales Découplées */}
      <PropertyAddModal
        isOpen={isAddOpen}
        onClose={() => setIsAddOpen(false)}
      />

      <PropertyEditModal
        property={selectedProperty}
        isOpen={isEditOpen}
        onClose={() => {
          setIsEditOpen(false)
          setSelectedProperty(null)
        }}
      />

      <PropertyShowModal
        property={selectedProperty}
        isOpen={isShowOpen}
        onClose={() => {
          setIsShowOpen(false)
          setSelectedProperty(null)
        }}
        onEdit={(prop) => {
          setSelectedProperty(prop)
          setIsEditOpen(true)
        }}
      />

      <PropertyDeleteModal
        property={selectedProperty}
        isOpen={isDeleteOpen}
        onClose={() => {
          setIsDeleteOpen(false)
          setSelectedProperty(null)
        }}
      />
    </div>
  )
}
