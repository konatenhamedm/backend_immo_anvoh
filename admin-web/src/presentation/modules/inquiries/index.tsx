import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  MessageSquare,
  Search,
  RotateCw,
  RotateCcw,
  CheckCircle2,
  Clock,
  Phone,
  Eye
} from 'lucide-react'
import { fetchApi } from '@/lib/api'
import { formatFCFA } from '@/lib/utils'
import { TableHeaderCustom, TableCardWrapper } from '@/presentation/components/shared/ui/TableHeaderCustom'
import { Select2, Select2Option } from '@/presentation/components/shared/ui/Select2'
import { InquiryShowModal } from './Show'

const PROCESSED_OPTIONS: Select2Option[] = [
  { value: '', label: 'Tous les statuts de traitement' },
  { value: 'false', label: 'En attente de traitement (Nouveaux)' },
  { value: 'true', label: 'Déjà Traités / Contactés' },
]

export function InquiriesModule() {
  const [search, setSearch] = useState('')
  const [processedFilter, setProcessedFilter] = useState('')
  const [selectedInquiry, setSelectedInquiry] = useState<any | null>(null)
  const [isShowOpen, setIsShowOpen] = useState(false)

  const { data: inquiriesData, isLoading, refetch, isFetching } = useQuery({
    queryKey: ['admin-inquiries'],
    queryFn: () => fetchApi<{ results: any[] }>('/crm/inquiries/list/'),
  })

  const inquiries = inquiriesData?.results || []

  const filteredInquiries = inquiries.filter((inq: any) => {
    const matchProcessed =
      processedFilter === ''
        ? true
        : processedFilter === 'true'
        ? inq.is_processed === true
        : inq.is_processed === false
    const matchSearch =
      !search ||
      inq.lead?.full_name?.toLowerCase().includes(search.toLowerCase()) ||
      inq.lead?.phone_number?.includes(search) ||
      inq.property?.title?.toLowerCase().includes(search.toLowerCase()) ||
      inq.property?.reference?.toLowerCase().includes(search.toLowerCase())
    return matchProcessed && matchSearch
  })

  const pendingCount = inquiries.filter((i: any) => !i.is_processed).length

  const columns = [
    { key: 'id', label: 'ID', className: 'w-16' },
    { key: 'prospect', label: 'PROSPECT & TÉLÉPHONE' },
    { key: 'prop_ref', label: 'RÉF. BIEN' },
    { key: 'property', label: 'BIEN CIBLÉ' },
    { key: 'obj', label: 'OBJECTIF' },
    { key: 'date', label: 'DATE DEMANDE' },
    { key: 'statut', label: 'STATUT TRAITEMENT' },
    { key: 'actions', label: 'ACTIONS', className: 'text-right w-20' },
  ]

  const handleOpenShow = (inq: any) => {
    setSelectedInquiry(inq)
    setIsShowOpen(true)
  }

  return (
    <div className="w-full space-y-4 animate-fade-in">
      {/* 1. Barre d'action supérieure pleine largeur */}
      <div className="w-full flex flex-col lg:flex-row lg:items-center justify-between gap-4 bg-white dark:bg-slate-900 px-6 py-4 rounded-2xl border border-slate-200/90 dark:border-slate-800 shadow-2xs">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl sm:text-2xl font-black tracking-tight text-slate-900 dark:text-white flex items-center gap-2">
              Demandes d'Informations & Messages
            </h1>
            <span className="px-2 py-0.5 rounded-full text-[10px] font-black bg-blue-100 text-blue-800 dark:bg-blue-950/70 dark:text-blue-300">
              Django Model PropertyInquiry
            </span>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Messages reçus des acquéreurs potentiels depuis les fiches de biens (Écran 08).
          </p>
        </div>

        <button
          type="button"
          onClick={() => refetch()}
          disabled={isFetching}
          className="px-3.5 py-2 text-xs font-semibold rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-200 hover:bg-slate-50 transition-colors flex items-center gap-1.5 cursor-pointer shadow-2xs self-start lg:self-auto"
        >
          <RotateCw className={`w-3.5 h-3.5 ${isFetching ? 'animate-spin text-blue-600' : ''}`} />
          <span>Actualiser</span>
        </button>
      </div>

      {/* 2. Filtres Select2 Pleine Largeur */}
      <div className="w-full p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-800 shadow-2xs space-y-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 w-full">
          <Select2
            label="Statut Commercial"
            placeholder="Tous les statuts"
            options={PROCESSED_OPTIONS}
            value={processedFilter}
            onChange={setProcessedFilter}
          />

          <div className="flex flex-col sm:col-span-2">
            <label className="text-[11px] font-bold text-slate-600 dark:text-slate-400 mb-1 tracking-wide">
              Recherche Prospect ou Titre Bien
            </label>
            <div className="relative w-full">
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Rechercher par nom, téléphone WhatsApp, référence..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full pl-9 pr-3 h-9.5 text-xs rounded-xl bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-700/80 focus:outline-hidden focus:border-blue-500 text-slate-900 dark:text-white"
              />
            </div>
          </div>
        </div>

        <div className="flex items-center justify-between pt-2 border-t border-slate-100 dark:border-slate-800">
          <div className="text-xs text-slate-500">
            Total affiché : <strong>{filteredInquiries.length}</strong> demandes
          </div>
          <button
            type="button"
            onClick={() => {
              setSearch('')
              setProcessedFilter('')
            }}
            className="px-3 py-1.5 text-xs font-semibold text-slate-500 hover:text-slate-900 dark:hover:text-white flex items-center gap-1.5 transition-colors cursor-pointer"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Réinitialiser les filtres</span>
          </button>
        </div>
      </div>

      {/* 3. Tableau Pleine Largeur */}
      <div className="w-full">
        <TableCardWrapper
          title="LISTE DES DEMANDES D'INFORMATIONS ENTRANTES"
          count={`${filteredInquiries.length} DEMANDES`}
          badgeRight={`${pendingCount} en attente de traitement`}
          icon={<MessageSquare className="w-4 h-4 text-blue-500" />}
        >
          <TableHeaderCustom columns={columns} />
          <tbody className="divide-y divide-slate-100 dark:divide-slate-800/80">
            {isLoading ? (
              <tr>
                <td colSpan={8} className="py-12 text-center text-slate-400 italic">
                  Chargement des demandes...
                </td>
              </tr>
            ) : filteredInquiries.length === 0 ? (
              <tr>
                <td colSpan={8} className="py-12 text-center text-slate-400 italic">
                  Aucune demande ne correspond à ces critères.
                </td>
              </tr>
            ) : (
              filteredInquiries.map((inq: any, idx: number) => (
                <tr
                  key={inq.id}
                  onClick={() => handleOpenShow(inq)}
                  className="hover:bg-blue-50/40 dark:hover:bg-slate-800/50 transition-colors cursor-pointer"
                >
                  <td className="py-3 px-4 font-mono text-[11px] text-slate-400">
                    #{String(idx + 1).padStart(3, '0')}
                  </td>

                  <td className="py-3 px-4">
                    <div className="font-bold text-xs text-slate-900 dark:text-white">
                      {inq.lead?.full_name || 'Prospect'}
                    </div>
                    <div className="text-[11px] text-slate-500 font-mono flex items-center gap-1">
                      <Phone className="w-3 h-3 text-emerald-500" />
                      {inq.lead?.phone_number}
                    </div>
                  </td>

                  <td className="py-3 px-4 font-mono font-black text-xs text-blue-600 dark:text-blue-400 whitespace-nowrap">
                    {inq.property?.reference}
                  </td>

                  <td className="py-3 px-4">
                    <div className="font-bold text-xs uppercase text-slate-900 dark:text-white">
                      {inq.property?.title}
                    </div>
                    <div className="text-[10px] text-slate-400">
                      {inq.property?.commune}
                    </div>
                  </td>

                  <td className="py-3 px-4 text-xs font-semibold whitespace-nowrap">
                    <span className="px-2 py-0.5 rounded-md bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 text-[11px]">
                      {inq.objective || 'Habitation'}
                    </span>
                  </td>

                  <td className="py-3 px-4 text-[11px] text-slate-500 whitespace-nowrap">
                    {new Date(inq.created_at).toLocaleDateString('fr-FR')}
                  </td>

                  <td className="py-3 px-4 whitespace-nowrap">
                    {inq.is_processed ? (
                      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300">
                        <CheckCircle2 className="w-3 h-3" /> Traité
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300">
                        <Clock className="w-3 h-3" /> À contacter
                      </span>
                    )}
                  </td>

                  <td className="py-3 px-4 text-right whitespace-nowrap">
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation()
                        handleOpenShow(inq)
                      }}
                      className="p-1.5 rounded-lg text-slate-400 hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-950/40 transition-colors cursor-pointer"
                      title="Voir la demande"
                    >
                      <Eye className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </TableCardWrapper>
      </div>

      <InquiryShowModal
        inquiry={selectedInquiry}
        isOpen={isShowOpen}
        onClose={() => {
          setIsShowOpen(false)
          setSelectedInquiry(null)
        }}
      />
    </div>
  )
}
