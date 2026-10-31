import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  Users,
  Flame,
  Phone,
  RotateCw,
  RotateCcw,
  Plus,
  LayoutGrid,
  Table as TableIcon,
  Search
} from 'lucide-react'
import { fetchApi } from '@/lib/api'
import { formatFCFA } from '@/lib/utils'
import { TableHeaderCustom, TableCardWrapper } from '@/presentation/components/shared/ui/TableHeaderCustom'
import { TableRowActions } from '@/presentation/components/shared/ui/TableRowActions'
import { Select2, Select2Option } from '@/presentation/components/shared/ui/Select2'
import { CrmAddModal } from './Add'
import { CrmEditModal } from './Edit'
import { CrmShowModal } from './Show'
import { CrmDeleteModal } from './Delete'

const STAGE_OPTIONS: Select2Option[] = [
  { value: '', label: 'Toutes les étapes du pipeline' },
  { value: 'NOUVEAU', label: 'Nouveau Prospect' },
  { value: 'QUALIFIE', label: 'Prospect Qualifié' },
  { value: 'RDV', label: 'Rendez-vous Fixé' },
  { value: 'VISITE', label: 'Visite Programmée' },
  { value: 'PROPOSITION', label: 'Proposition Commerciale' },
  { value: 'NEGOCIATION', label: 'Négociation' },
  { value: 'VENTE', label: 'Vente Conclue' },
]

const FINANCING_OPTIONS: Select2Option[] = [
  { value: '', label: 'Tous modes de financement' },
  { value: 'CREDIT_BANCAIRE', label: 'Crédit Bancaire' },
  { value: 'COMPTANT', label: 'Fonds Propres / Comptant' },
  { value: 'ECHELONNE', label: 'Paiement Échelonné' },
]

export function CrmModule() {
  const [viewMode, setViewMode] = useState<'table' | 'kanban'>('table')
  const [stageFilter, setStageFilter] = useState('')
  const [financingFilter, setFinancingFilter] = useState('')
  const [search, setSearch] = useState('')

  const [isAddOpen, setIsAddOpen] = useState(false)
  const [isEditOpen, setIsEditOpen] = useState(false)
  const [isShowOpen, setIsShowOpen] = useState(false)
  const [isDeleteOpen, setIsDeleteOpen] = useState(false)
  const [selectedLead, setSelectedLead] = useState<any | null>(null)

  const { data: kanbanData, isLoading, refetch, isFetching } = useQuery({
    queryKey: ['kanban-pipeline'],
    queryFn: () => fetchApi<Record<string, any>>('/crm/pipeline/kanban/'),
  })

  const stages = [
    { key: 'NOUVEAU', label: 'Nouveau', color: 'border-slate-300 dark:border-slate-700' },
    { key: 'QUALIFIE', label: 'Qualifié', color: 'border-teal-400 dark:border-teal-600' },
    { key: 'RDV', label: 'RDV Fixé', color: 'border-indigo-400 dark:border-indigo-600' },
    { key: 'VISITE', label: 'Visite', color: 'border-amber-400 dark:border-amber-600' },
    { key: 'PROPOSITION', label: 'Offre', color: 'border-cyan-400 dark:border-cyan-600' },
    { key: 'NEGOCIATION', label: 'Négociation', color: 'border-purple-400 dark:border-purple-600' },
    { key: 'VENTE', label: 'Vente Conclue', color: 'border-emerald-500 dark:border-emerald-500' },
  ]

  // Flatten leads for table view
  const allLeads = kanbanData
    ? Object.entries(kanbanData).flatMap(([stageKey, col]: [string, any]) =>
        (col.leads || []).map((l: any) => ({ ...l, stage: stageKey, stageLabel: col.label }))
      )
    : []

  const filteredLeads = allLeads.filter((l: any) => {
    const matchStage = !stageFilter || l.stage === stageFilter
    const matchFinancing = !financingFilter || l.financing_mode === financingFilter
    const matchSearch =
      !search ||
      l.full_name?.toLowerCase().includes(search.toLowerCase()) ||
      l.phone_number?.includes(search) ||
      l.email?.toLowerCase().includes(search.toLowerCase())
    return matchStage && matchFinancing && matchSearch
  })

  const columns = [
    { key: 'id', label: 'ID', className: 'w-16' },
    { key: 'name', label: 'PROSPECT & CONTACT' },
    { key: 'phone', label: 'TÉLÉPHONE' },
    { key: 'obj', label: 'OBJECTIF' },
    { key: 'budget', label: 'BUDGET (FCFA)' },
    { key: 'score', label: 'INDICE QUALIF.' },
    { key: 'stage', label: 'ÉTAPE PIPELINE' },
    { key: 'actions', label: 'ACTIONS', className: 'text-right w-28' },
  ]

  const handleResetFilters = () => {
    setStageFilter('')
    setFinancingFilter('')
    setSearch('')
  }

  const handleOpenShow = (lead: any) => {
    setSelectedLead(lead)
    setIsShowOpen(true)
  }

  const handleOpenEdit = (lead: any) => {
    setSelectedLead(lead)
    setIsEditOpen(true)
  }

  const handleOpenDelete = (lead: any) => {
    setSelectedLead(lead)
    setIsDeleteOpen(true)
  }

  return (
    <div className="w-full space-y-4 animate-fade-in">
      {/* 1. Barre d'action supérieure pleine largeur */}
      <div className="w-full flex flex-col lg:flex-row lg:items-center justify-between gap-4 bg-white dark:bg-slate-900 px-6 py-4 rounded-2xl border border-slate-200/90 dark:border-slate-800 shadow-2xs">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl sm:text-2xl font-black tracking-tight text-slate-900 dark:text-white">
              Pipeline CRM Commercial
            </h1>
            <span className="px-2 py-0.5 rounded-full text-[10px] font-black bg-blue-100 text-blue-800 dark:bg-blue-950/70 dark:text-blue-300">
              Scoring IA & Pipeline
            </span>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Gestion du cycle d'acquisition, relances clients et conversion des acheteurs.
          </p>
        </div>

        <div className="flex items-center flex-wrap gap-2.5">
          {/* Switcher Table / Kanban */}
          <div className="flex items-center bg-slate-100 dark:bg-slate-800 p-1 rounded-xl border border-slate-200 dark:border-slate-700">
            <button
              type="button"
              onClick={() => setViewMode('table')}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-1.5 cursor-pointer ${
                viewMode === 'table'
                  ? 'bg-white dark:bg-slate-900 text-blue-600 shadow-xs'
                  : 'text-slate-500 hover:text-slate-900 dark:hover:text-white'
              }`}
            >
              <TableIcon className="w-3.5 h-3.5" />
              Vue Grille
            </button>
            <button
              type="button"
              onClick={() => setViewMode('kanban')}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-1.5 cursor-pointer ${
                viewMode === 'kanban'
                  ? 'bg-white dark:bg-slate-900 text-blue-600 shadow-xs'
                  : 'text-slate-500 hover:text-slate-900 dark:hover:text-white'
              }`}
            >
              <LayoutGrid className="w-3.5 h-3.5" />
              Vue Kanban
            </button>
          </div>

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
            onClick={() => setIsAddOpen(true)}
            className="px-4 py-2 text-xs font-bold rounded-xl bg-blue-600 hover:bg-blue-700 text-white shadow-md shadow-blue-600/25 transition-all flex items-center gap-2 cursor-pointer"
          >
            <Plus className="w-4 h-4" />
            <span>Nouveau Prospect</span>
          </button>
        </div>
      </div>

      {/* 2. Barre de Filtres avec Sélecteurs Select2 Pleine Largeur */}
      <div className="w-full p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-800 shadow-2xs space-y-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 w-full">
          <Select2
            label="Étape du Pipeline"
            placeholder="Toutes les étapes"
            options={STAGE_OPTIONS}
            value={stageFilter}
            onChange={setStageFilter}
          />

          <Select2
            label="Mode de Financement"
            placeholder="Tous les modes"
            options={FINANCING_OPTIONS}
            value={financingFilter}
            onChange={setFinancingFilter}
          />

          <div className="flex flex-col">
            <label className="text-[11px] font-bold text-slate-600 dark:text-slate-400 mb-1 tracking-wide">
              Recherche Nom, Tél WhatsApp
            </label>
            <div className="relative w-full">
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Rechercher par nom, téléphone..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full pl-9 pr-3 h-9.5 text-xs rounded-xl bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-700/80 focus:outline-hidden focus:border-blue-500 text-slate-900 dark:text-white"
              />
            </div>
          </div>
        </div>

        <div className="flex items-center justify-between pt-2 border-t border-slate-100 dark:border-slate-800">
          <div className="text-xs text-slate-500">
            Prospects qualifiés : <strong>{filteredLeads.length}</strong>
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

      {/* 3. Affichage Pleine Largeur */}
      {viewMode === 'table' ? (
        <div className="w-full">
          <TableCardWrapper
            title="LISTE DES PROSPECTS COMMERCIAUX"
            count={`${filteredLeads.length} PROSPECTS`}
            icon={<Users className="w-4 h-4" />}
          >
            <TableHeaderCustom columns={columns} />
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800/80">
              {isLoading ? (
                <tr>
                  <td colSpan={8} className="py-12 text-center text-slate-400 italic">
                    Chargement des leads...
                  </td>
                </tr>
              ) : filteredLeads.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-12 text-center text-slate-400 italic">
                    Aucun prospect ne correspond aux filtres.
                  </td>
                </tr>
              ) : (
                filteredLeads.map((lead: any, idx: number) => (
                  <tr
                    key={lead.id}
                    onClick={() => handleOpenShow(lead)}
                    className="hover:bg-blue-50/40 dark:hover:bg-slate-800/50 transition-colors cursor-pointer group"
                  >
                    <td className="py-3 px-4 font-mono text-[11px] text-slate-400">
                      #{String(idx + 1).padStart(3, '0')}
                    </td>

                    <td className="py-3 px-4">
                      <div className="font-bold text-xs uppercase text-slate-900 dark:text-white group-hover:text-blue-600 transition-colors">
                        {lead.full_name}
                      </div>
                      <div className="text-[10px] text-slate-400">
                        Source : {lead.source || 'Demande directe'}
                      </div>
                    </td>

                    <td className="py-3 px-4 text-xs font-mono font-medium text-slate-700 dark:text-slate-300 whitespace-nowrap">
                      {lead.phone_number}
                    </td>

                    <td className="py-3 px-4 text-xs font-semibold whitespace-nowrap">
                      <span className="px-2 py-0.5 rounded-md bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 text-[11px]">
                        {lead.objective || 'Habitation'}
                      </span>
                    </td>

                    <td className="py-3 px-4 font-black text-xs text-emerald-600 dark:text-emerald-400 whitespace-nowrap">
                      {lead.budget_max ? formatFCFA(lead.budget_max) : '—'}
                    </td>

                    <td className="py-3 px-4 whitespace-nowrap">
                      <span className="inline-flex items-center gap-1 font-bold text-amber-600 dark:text-amber-400 text-xs">
                        <Flame className="w-3.5 h-3.5" />
                        {lead.qualification_score || 80}/100
                      </span>
                    </td>

                    <td className="py-3 px-4 whitespace-nowrap">
                      <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300">
                        {lead.stageLabel || lead.stage}
                      </span>
                    </td>

                    <td className="py-3 px-4 text-right whitespace-nowrap">
                      <TableRowActions
                        onShow={() => handleOpenShow(lead)}
                        onEdit={() => handleOpenEdit(lead)}
                        onDelete={() => handleOpenDelete(lead)}
                      />
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </TableCardWrapper>
        </div>
      ) : (
        /* Vue Kanban Pleine Largeur */
        <div className="flex gap-4 overflow-x-auto pb-6 w-full">
          {stages.map((stage) => {
            const colData = kanbanData ? kanbanData[stage.key] : null
            const leads = colData?.leads || []
            const count = colData?.count || leads.length

            return (
              <div
                key={stage.key}
                className="w-80 shrink-0 flex flex-col rounded-2xl bg-slate-100/70 dark:bg-slate-900/60 border border-slate-200/80 dark:border-slate-800 p-3.5 max-h-[calc(100vh-210px)]"
              >
                <div className="flex items-center justify-between pb-3 border-b border-slate-200 dark:border-slate-800 mb-3">
                  <span className="text-xs font-bold text-slate-800 dark:text-slate-200 flex items-center gap-1.5">
                    <span className={`w-2 h-2 rounded-full border-2 ${stage.color} bg-white`}></span>
                    {stage.label}
                  </span>
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-black bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700">
                    {count}
                  </span>
                </div>

                <div className="flex-1 overflow-y-auto space-y-3 pr-1">
                  {leads.length === 0 ? (
                    <div className="p-4 text-center text-slate-400 text-xs italic">
                      Aucun prospect
                    </div>
                  ) : (
                    leads.map((lead: any) => (
                      <div
                        key={lead.id}
                        onClick={() => handleOpenShow(lead)}
                        className="p-4 rounded-xl bg-white dark:bg-slate-800/90 border border-slate-200/90 dark:border-slate-700/80 shadow-xs hover:shadow-md transition-all space-y-2.5 cursor-pointer group"
                      >
                        <div className="flex items-start justify-between gap-2">
                          <h4 className="text-xs font-bold text-slate-900 dark:text-white truncate group-hover:text-blue-600 transition-colors">
                            {lead.full_name}
                          </h4>
                          <span className="inline-flex items-center gap-0.5 text-[10px] font-bold text-amber-600">
                            <Flame className="w-3 h-3" />
                            {lead.qualification_score || 80}
                          </span>
                        </div>

                        <div className="text-[11px] text-slate-500 font-mono">
                          {lead.phone_number}
                        </div>

                        {lead.budget_max && (
                          <div className="text-xs font-bold text-emerald-600">
                            {formatFCFA(lead.budget_max)}
                          </div>
                        )}
                      </div>
                    ))
                  )}
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* Modales Découplées */}
      <CrmAddModal
        isOpen={isAddOpen}
        onClose={() => setIsAddOpen(false)}
      />

      <CrmEditModal
        lead={selectedLead}
        isOpen={isEditOpen}
        onClose={() => {
          setIsEditOpen(false)
          setSelectedLead(null)
        }}
      />

      <CrmShowModal
        lead={selectedLead}
        isOpen={isShowOpen}
        onClose={() => {
          setIsShowOpen(false)
          setSelectedLead(null)
        }}
        onEdit={(lead) => {
          setSelectedLead(lead)
          setIsEditOpen(true)
        }}
      />

      <CrmDeleteModal
        lead={selectedLead}
        isOpen={isDeleteOpen}
        onClose={() => {
          setIsDeleteOpen(false)
          setSelectedLead(null)
        }}
      />
    </div>
  )
}
