import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  Building2,
  Calendar,
  Layers,
  MapPin,
  Plus,
  RotateCw,
  RotateCcw,
  Search,
  Sparkles
} from 'lucide-react'
import { fetchApi } from '@/lib/api'
import { formatFCFA } from '@/lib/utils'
import { StatutBadge } from '@/presentation/components/shared/ui/StatutBadge'
import { TableHeaderCustom, TableCardWrapper } from '@/presentation/components/shared/ui/TableHeaderCustom'
import { TableRowActions } from '@/presentation/components/shared/ui/TableRowActions'
import { Select2, Select2Option } from '@/presentation/components/shared/ui/Select2'
import { ProjectAddModal } from './Add'
import { ProjectEditModal } from './Edit'
import { ProjectShowModal } from './Show'
import { ProjectDeleteModal } from './Delete'

const COMMUNE_OPTIONS: Select2Option[] = [
  { value: '', label: 'Toutes les communes' },
  { value: 'Cocody', label: 'Cocody' },
  { value: 'Bingerville', label: 'Bingerville' },
  { value: 'Marcory', label: 'Marcory' },
  { value: 'Grand-Bassam', label: 'Grand-Bassam' },
]

const STATUS_OPTIONS: Select2Option[] = [
  { value: '', label: 'Tous les états de chantier' },
  { value: 'EN_CONSTRUCTION', label: 'En Construction' },
  { value: 'LIVRE', label: 'Livré' },
  { value: 'LANCEMENT', label: 'Lancement Commercial' },
]

export function ProjectsModule() {
  const [communeFilter, setCommuneFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [search, setSearch] = useState('')

  const [isAddProjectOpen, setIsAddProjectOpen] = useState(false)
  const [isAddLotOpen, setIsAddLotOpen] = useState(false)
  const [isEditOpen, setIsEditOpen] = useState(false)
  const [isShowOpen, setIsShowOpen] = useState(false)
  const [isDeleteOpen, setIsDeleteOpen] = useState(false)

  const [selectedProject, setSelectedProject] = useState<any | null>(null)
  const [selectedProjectIdForLot, setSelectedProjectIdForLot] = useState<string | null>(null)

  const { data, isLoading, refetch, isFetching } = useQuery({
    queryKey: ['projects-list'],
    queryFn: () => fetchApi<{ results: any[] }>('/properties/projects/'),
  })

  const projects = data?.results || []

  // Filtrage local
  const filteredProjects = projects.filter((p: any) => {
    const matchCommune = !communeFilter || p.commune?.toLowerCase().includes(communeFilter.toLowerCase())
    const matchStatus = !statusFilter || p.status === statusFilter
    const matchSearch =
      !search ||
      p.name?.toLowerCase().includes(search.toLowerCase()) ||
      p.developer_name?.toLowerCase().includes(search.toLowerCase())
    return matchCommune && matchStatus && matchSearch
  })

  // Calculs cumulés
  const totalLots = filteredProjects.reduce((acc, p) => acc + (p.lots?.length || 0), 0)
  const availableLots = filteredProjects.reduce(
    (acc, p) => acc + (p.lots?.filter((l: any) => l.status === 'DISPONIBLE').length || 0),
    0
  )

  const columns = [
    { key: 'id', label: 'ID', className: 'w-16' },
    { key: 'name', label: 'PROGRAMME NEUF' },
    { key: 'developer', label: 'PROMOTEUR' },
    { key: 'commune', label: 'COMMUNE / ZONE' },
    { key: 'delivery', label: 'LIVRAISON PRÉVUE' },
    { key: 'lots', label: 'LOTS (DISPO / TOTAL)' },
    { key: 'price', label: 'PRIX D\'APPEL' },
    { key: 'status', label: 'ÉTAT DU CHANTIER' },
    { key: 'actions', label: 'ACTIONS', className: 'text-right w-28' },
  ]

  const lotColumns = [
    { key: 'num', label: 'LOT N°' },
    { key: 'typ', label: 'TYPOLOGIE' },
    { key: 'bat', label: 'BÂTIMENT / ÉTAGE' },
    { key: 'surf', label: 'SUPERFICIE' },
    { key: 'prix', label: 'PRIX COMMERCIALISÉ' },
    { key: 'stat', label: 'DISPONIBILITÉ' },
  ]

  const handleResetFilters = () => {
    setCommuneFilter('')
    setStatusFilter('')
    setSearch('')
  }

  return (
    <div className="w-full space-y-4 animate-fade-in">
      {/* 1. Barre d'action supérieure pleine largeur */}
      <div className="w-full flex flex-col lg:flex-row lg:items-center justify-between gap-4 bg-white dark:bg-slate-900 px-6 py-4 rounded-2xl border border-slate-200/90 dark:border-slate-800 shadow-2xs">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl sm:text-2xl font-black tracking-tight text-slate-900 dark:text-white">
              Programmes Neufs & Gestion des Lots
            </h1>
            <span className="px-2 py-0.5 rounded-full text-[10px] font-black bg-blue-100 text-blue-800 dark:bg-blue-950/70 dark:text-blue-300">
              VEFA Promotion
            </span>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Supervisez les chantiers, commercialisation par lot et respect des calendriers de livraison.
          </p>
        </div>

        <div className="flex items-center flex-wrap gap-2.5">
          <button
            type="button"
            onClick={() => refetch()}
            disabled={isFetching}
            className="px-3.5 py-2 text-xs font-semibold rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-200 hover:bg-slate-50 transition-colors flex items-center gap-1.5 cursor-pointer shadow-2xs"
          >
            <RotateCw className={`w-3.5 h-3.5 ${isFetching ? 'animate-spin text-blue-600' : ''}`} />
            <span>Actualiser</span>
          </button>

          <button
            type="button"
            onClick={() => setIsAddProjectOpen(true)}
            className="px-4 py-2 text-xs font-bold rounded-xl bg-blue-600 hover:bg-blue-700 text-white shadow-md shadow-blue-600/25 transition-all flex items-center gap-2 cursor-pointer"
          >
            <Plus className="w-4 h-4" />
            <span>Nouveau Programme</span>
          </button>
        </div>
      </div>

      {/* 2. Barre de Filtres avec Sélecteurs Select2 Pleine Largeur */}
      <div className="w-full p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-800 shadow-2xs space-y-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 w-full">
          <Select2
            label="Commune"
            placeholder="Toutes les communes"
            options={COMMUNE_OPTIONS}
            value={communeFilter}
            onChange={setCommuneFilter}
          />

          <Select2
            label="Avancement Chantier"
            placeholder="Tous les états"
            options={STATUS_OPTIONS}
            value={statusFilter}
            onChange={setStatusFilter}
          />

          <div className="flex flex-col sm:col-span-2">
            <label className="text-[11px] font-bold text-slate-600 dark:text-slate-400 mb-1 tracking-wide">
              Recherche Promoteur ou Programme
            </label>
            <div className="relative w-full">
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Ex: Résidence Eden, ANVOH Promotion..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full pl-9 pr-3 h-9.5 text-xs rounded-xl bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-700/80 focus:outline-hidden focus:border-blue-500 text-slate-900 dark:text-white"
              />
            </div>
          </div>
        </div>

        <div className="flex items-center justify-between pt-2 border-t border-slate-100 dark:border-slate-800">
          <div className="text-xs text-slate-500">
            Affichage de <strong>{filteredProjects.length}</strong> programme(s) neuf(s)
          </div>
          <button
            type="button"
            onClick={handleResetFilters}
            className="px-3 py-1.5 text-xs font-semibold text-slate-500 hover:text-slate-900 dark:hover:text-white flex items-center gap-1.5 transition-colors cursor-pointer"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Réinitialiser les filtres</span>
          </button>
        </div>
      </div>

      {/* 3. Tableau des Programmes Neufs Pleine Largeur */}
      <div className="w-full">
        <TableCardWrapper
          title="LISTE DES PROGRAMMES NEUFS EN COMMERCIALISATION"
          count={`${filteredProjects.length} PROGRAMMES`}
          badgeRight={`Stock Lots : ${availableLots} disponibles sur ${totalLots}`}
          icon={<Building2 className="w-4 h-4" />}
        >
          <TableHeaderCustom columns={columns} />
          <tbody className="divide-y divide-slate-100 dark:divide-slate-800/80">
            {isLoading ? (
              <tr>
                <td colSpan={9} className="py-12 text-center text-slate-400 italic">
                  Chargement des programmes depuis PostgreSQL...
                </td>
              </tr>
            ) : filteredProjects.length === 0 ? (
              <tr>
                <td colSpan={9} className="py-12 text-center text-slate-400 italic">
                  Aucun programme neuf ne correspond à votre filtre.
                </td>
              </tr>
            ) : (
              filteredProjects.map((proj: any, idx: number) => {
                const lotsCount = proj.lots?.length || 0
                const avail = proj.lots?.filter((l: any) => l.status === 'DISPONIBLE').length || 0

                return (
                  <tr
                    key={proj.id}
                    onClick={() => {
                      setSelectedProject(proj)
                      setIsShowOpen(true)
                    }}
                    className="hover:bg-blue-50/40 dark:hover:bg-slate-800/50 transition-colors cursor-pointer group"
                  >
                    <td className="py-3 px-4 font-mono text-[11px] text-slate-400">
                      #{String(idx + 1).padStart(3, '0')}
                    </td>

                    <td className="py-3 px-4">
                      <div className="font-bold text-xs uppercase text-slate-900 dark:text-white group-hover:text-blue-600 transition-colors">
                        {proj.name}
                      </div>
                      <div className="text-[10px] text-slate-400">
                        Réf: {proj.id?.slice(0, 8)}
                      </div>
                    </td>

                    <td className="py-3 px-4 text-xs font-semibold text-slate-700 dark:text-slate-300">
                      {proj.developer_name || 'ANVOH GROUP'}
                    </td>

                    <td className="py-3 px-4 text-xs text-slate-600 dark:text-slate-300 whitespace-nowrap">
                      {proj.commune}
                    </td>

                    <td className="py-3 px-4 text-[11px] text-slate-500 whitespace-nowrap">
                      {proj.delivery_date ? new Date(proj.delivery_date).toLocaleDateString('fr-FR') : 'Fin 2026'}
                    </td>

                    <td className="py-3 px-4 whitespace-nowrap">
                      <span className="font-bold text-xs text-blue-600 dark:text-blue-400">
                        {avail} dispo
                      </span>
                      <span className="text-slate-400 text-xs"> / {proj.total_lots || lotsCount}</span>
                    </td>

                    <td className="py-3 px-4 font-black text-xs text-emerald-600 dark:text-emerald-400 whitespace-nowrap">
                      {formatFCFA(proj.starting_price)}
                    </td>

                    <td className="py-3 px-4 whitespace-nowrap">
                      <StatutBadge status={proj.status || 'EN_CONSTRUCTION'} />
                    </td>

                    <td className="py-3 px-4 text-right whitespace-nowrap">
                      <TableRowActions
                        onShow={() => {
                          setSelectedProject(proj)
                          setIsShowOpen(true)
                        }}
                        onEdit={() => {
                          setSelectedProject(proj)
                          setIsEditOpen(true)
                        }}
                        onDelete={() => {
                          setSelectedProject(proj)
                          setIsDeleteOpen(true)
                        }}
                      />
                    </td>
                  </tr>
                )
              })
            )}
          </tbody>
        </TableCardWrapper>
      </div>

      {/* 4. Section Détail des Lots par Programme (Pleine Largeur) */}
      <div className="w-full space-y-4">
        <h2 className="text-sm font-black uppercase tracking-wider text-slate-700 dark:text-slate-300">
          Lots Rattachés aux Programmes
        </h2>

        {filteredProjects.map((proj: any) => (
          <div
            key={proj.id}
            className="w-full p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-800 shadow-2xs space-y-4"
          >
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 dark:border-slate-800 pb-3">
              <div className="flex items-center gap-3">
                <span className="p-2 rounded-xl bg-blue-50 dark:bg-blue-950/50 text-blue-600">
                  <Building2 className="w-5 h-5" />
                </span>
                <div>
                  <h3 className="font-bold text-sm text-slate-900 dark:text-white">
                    {proj.name}
                  </h3>
                  <div className="text-xs text-slate-500">
                    {proj.commune} • {proj.developer_name}
                  </div>
                </div>
              </div>

              <button
                type="button"
                onClick={() => {
                  setSelectedProjectIdForLot(proj.id)
                  setIsAddLotOpen(true)
                }}
                className="px-3.5 py-1.5 text-xs font-bold rounded-xl border border-blue-600 text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-950/40 transition-colors flex items-center gap-1.5 self-start sm:self-auto cursor-pointer"
              >
                <Plus className="w-3.5 h-3.5" />
                Ajouter un Lot
              </button>
            </div>

            {/* Grille des lots */}
            <div className="overflow-x-auto w-full">
              <table className="w-full text-left">
                <TableHeaderCustom columns={lotColumns} />
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                  {(!proj.lots || proj.lots.length === 0) ? (
                    <tr>
                      <td colSpan={6} className="py-6 text-center text-xs text-slate-400 italic">
                        Aucun lot créé pour ce programme. Cliquez sur "Ajouter un Lot" pour commencer.
                      </td>
                    </tr>
                  ) : (
                    proj.lots.map((lot: any) => (
                      <tr key={lot.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/40 transition-colors">
                        <td className="py-2.5 px-4 font-mono font-bold text-xs text-blue-600 dark:text-blue-400">
                          {lot.lot_number}
                        </td>
                        <td className="py-2.5 px-4 text-xs font-semibold">
                          {lot.typology}
                        </td>
                        <td className="py-2.5 px-4 text-xs text-slate-500">
                          {lot.building_name} (Étage {lot.floor})
                        </td>
                        <td className="py-2.5 px-4 text-xs font-semibold">
                          {lot.surface_sqm} m²
                        </td>
                        <td className="py-2.5 px-4 text-xs font-black text-emerald-600 dark:text-emerald-400">
                          {formatFCFA(lot.price)}
                        </td>
                        <td className="py-2.5 px-4">
                          <StatutBadge status={lot.status || 'DISPONIBLE'} />
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        ))}
      </div>

      {/* Modales Découplées */}
      <ProjectAddModal
        isOpen={isAddProjectOpen}
        onClose={() => setIsAddProjectOpen(false)}
        mode="project"
      />

      <ProjectAddModal
        isOpen={isAddLotOpen}
        onClose={() => setIsAddLotOpen(false)}
        projectId={selectedProjectIdForLot}
        mode="lot"
      />

      <ProjectEditModal
        project={selectedProject}
        isOpen={isEditOpen}
        onClose={() => {
          setIsEditOpen(false)
          setSelectedProject(null)
        }}
      />

      <ProjectShowModal
        project={selectedProject}
        isOpen={isShowOpen}
        onClose={() => {
          setIsShowOpen(false)
          setSelectedProject(null)
        }}
        onEdit={(p) => {
          setSelectedProject(p)
          setIsEditOpen(true)
        }}
        onAddLot={(pId) => {
          setSelectedProjectIdForLot(pId)
          setIsAddLotOpen(true)
        }}
      />

      <ProjectDeleteModal
        project={selectedProject}
        isOpen={isDeleteOpen}
        onClose={() => {
          setIsDeleteOpen(false)
          setSelectedProject(null)
        }}
      />
    </div>
  )
}
