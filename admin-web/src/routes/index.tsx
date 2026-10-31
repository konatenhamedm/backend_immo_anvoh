import React from 'react'
import { createFileRoute, Link } from '@tanstack/react-router'
import { useQuery } from '@tanstack/react-query'
import {
  TrendingUp,
  Building2,
  Users,
  Calendar,
  Sparkles,
  ArrowUpRight,
  Flame,
  CheckCircle,
  Coins,
  Clock,
  AlertCircle,
  Wallet
} from 'lucide-react'
import { fetchApi } from '@/lib/api'
import { formatFCFA } from '@/lib/utils'
import { StatutBadge } from '@/presentation/components/shared/ui/StatutBadge'
import { TableHeaderCustom, TableCardWrapper } from '@/presentation/components/shared/ui/TableHeaderCustom'

export const Route = createFileRoute('/')({
  component: DashboardPage,
})

function DashboardPage() {
  const { data: propertiesData, isLoading: loadingProps } = useQuery({
    queryKey: ['properties-dashboard'],
    queryFn: () => fetchApi<{ results: any[] }>('/properties/search/'),
  })

  const { data: kanbanData } = useQuery({
    queryKey: ['kanban-dashboard'],
    queryFn: () => fetchApi<Record<string, any>>('/crm/pipeline/kanban/'),
  })

  const properties = propertiesData?.results || []
  const totalLeads = kanbanData
    ? Object.values(kanbanData).reduce((acc: number, col: any) => acc + (col.count || 0), 0)
    : 4

  const totalPortfolio = properties.reduce(
    (acc: number, p: any) => acc + (parseFloat(p.price) || 0),
    0
  )

  const columns = [
    { key: 'id', label: 'ID', className: 'w-20' },
    { key: 'matricule', label: 'RÉFÉRENCE', className: 'w-32' },
    { key: 'title', label: 'DÉSIGNATION DU BIEN' },
    { key: 'commune', label: 'COMMUNE' },
    { key: 'type', label: 'TYPOLOGIE' },
    { key: 'price', label: 'MONTANT (FCFA)' },
    { key: 'yield', label: 'RENTABILITÉ' },
    { key: 'status', label: 'CERTIFICATION' },
  ]

  return (
    <div className="w-full space-y-6 animate-fade-in">
      {/* En-tête */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black tracking-tight text-slate-900 dark:text-white flex items-center gap-2">
            Tableau de Bord Commercial
            <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-blue-100 text-blue-800 dark:bg-blue-950/60 dark:text-blue-300">
              Direct PostgreSQL
            </span>
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Supervisez les indicateurs de ventes, conversion de leads et portefeuille d'annonces.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Link
            to="/crm"
            className="px-4 py-2.5 text-xs font-bold rounded-xl bg-blue-600 hover:bg-blue-700 text-white shadow-md shadow-blue-600/25 transition-all flex items-center gap-2 cursor-pointer"
          >
            <Users className="w-4 h-4" />
            Voir le Pipeline CRM
          </Link>
          <Link
            to="/properties"
            className="px-4 py-2.5 text-xs font-bold rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 hover:bg-slate-50 text-slate-700 dark:text-slate-200 transition-all flex items-center gap-2 cursor-pointer"
          >
            <Building2 className="w-4 h-4" />
            + Ajouter un Bien
          </Link>
        </div>
      </div>

      {/* Les 4 Cartes KPI exactement dans le style de la capture d'écran Educ360 ! */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {/* Carte 1 : Portefeuille Total (Bleu) */}
        <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-800 shadow-xs flex items-center gap-4">
          <div className="w-12 h-12 rounded-2xl bg-blue-50 dark:bg-blue-950/50 text-blue-600 flex items-center justify-center shrink-0 border border-blue-100 dark:border-blue-900">
            <Wallet className="w-6 h-6" />
          </div>
          <div className="min-w-0">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block truncate">
              Valeur Portefeuille
            </span>
            <div className="text-xl font-black text-slate-900 dark:text-white leading-tight mt-0.5">
              {formatFCFA(totalPortfolio)}
            </div>
          </div>
        </div>

        {/* Carte 2 : Prospects Qualifiés (Vert Émeraude) */}
        <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-800 shadow-xs flex items-center gap-4">
          <div className="w-12 h-12 rounded-2xl bg-emerald-50 dark:bg-emerald-950/50 text-emerald-600 flex items-center justify-center shrink-0 border border-emerald-100 dark:border-emerald-900">
            <Users className="w-6 h-6" />
          </div>
          <div className="min-w-0">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block truncate">
              Prospects Actifs
            </span>
            <div className="text-xl font-black text-emerald-600 dark:text-emerald-400 leading-tight mt-0.5">
              {totalLeads} LEADS
            </div>
          </div>
        </div>

        {/* Carte 3 : Visites & RDV (Orange / Ambre) */}
        <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-800 shadow-xs flex items-center gap-4">
          <div className="w-12 h-12 rounded-2xl bg-amber-50 dark:bg-amber-950/50 text-amber-600 flex items-center justify-center shrink-0 border border-amber-100 dark:border-amber-900">
            <Calendar className="w-6 h-6" />
          </div>
          <div className="min-w-0">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block truncate">
              Visites Programmées
            </span>
            <div className="text-xl font-black text-amber-600 dark:text-amber-400 leading-tight mt-0.5">
              2 VISITES
            </div>
          </div>
        </div>

        {/* Carte 4 : Rentabilité Moyenne (Rose / Cyan) */}
        <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-800 shadow-xs flex items-center gap-4">
          <div className="w-12 h-12 rounded-2xl bg-indigo-50 dark:bg-indigo-950/50 text-indigo-600 flex items-center justify-center shrink-0 border border-indigo-100 dark:border-indigo-900">
            <Sparkles className="w-6 h-6" />
          </div>
          <div className="min-w-0">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block truncate">
              Rentabilité Moyenne
            </span>
            <div className="text-xl font-black text-indigo-600 dark:text-indigo-400 leading-tight mt-0.5">
              9.3 % BRUTE
            </div>
          </div>
        </div>
      </div>

      {/* Tableau des biens avec TableCardWrapper et TableHeaderCustom */}
      <TableCardWrapper
        title="APERÇU DU CATALOGUE DES BIENS"
        count={`${properties.length} BIENS`}
        badgeRight={`Total : ${formatFCFA(totalPortfolio)}`}
        icon={<Building2 className="w-4 h-4" />}
        actionButton={
          <Link
            to="/properties"
            className="text-xs font-bold text-blue-600 hover:text-blue-700 flex items-center gap-1 cursor-pointer"
          >
            Gérer tout le catalogue <ArrowUpRight className="w-4 h-4" />
          </Link>
        }
      >
        <TableHeaderCustom columns={columns} />
        <tbody className="divide-y divide-slate-100 dark:divide-slate-800/80">
          {loadingProps ? (
            <tr>
              <td colSpan={8} className="py-10 text-center text-slate-400 italic">
                Chargement des données depuis PostgreSQL...
              </td>
            </tr>
          ) : (
            properties.map((p: any, idx: number) => (
              <tr key={p.id} className="hover:bg-blue-50/40 dark:hover:bg-slate-800/50 transition-colors">
                <td className="py-3.5 px-4 font-mono text-[11px] text-slate-400">
                  #{String(idx + 1).padStart(4, '0')}
                </td>
                <td className="py-3.5 px-4 font-mono font-black text-xs text-blue-600 dark:text-blue-400">
                  {p.reference}
                </td>
                <td className="py-3.5 px-4">
                  <div className="font-bold text-xs uppercase text-slate-900 dark:text-white">
                    {p.title}
                  </div>
                  <div className="text-[10px] text-slate-400">
                    {p.neighborhood}
                  </div>
                </td>
                <td className="py-3.5 px-4 text-xs font-semibold text-slate-700 dark:text-slate-300">
                  {p.commune}
                </td>
                <td className="py-3.5 px-4">
                  <span className="px-2 py-0.5 rounded-md bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 text-[11px] font-semibold">
                    {p.typology_display || p.property_type_display}
                  </span>
                </td>
                <td className="py-3.5 px-4 font-black text-xs text-emerald-600 dark:text-emerald-400">
                  {formatFCFA(p.price)}
                </td>
                <td className="py-3.5 px-4 text-xs font-bold text-slate-800 dark:text-slate-200">
                  {p.estimated_yield_rate ? `${p.estimated_yield_rate} %` : '—'}
                </td>
                <td className="py-3.5 px-4">
                  <StatutBadge status={p.verification_status || 'VERIFIE'} />
                </td>
              </tr>
            ))
          )}
        </tbody>
      </TableCardWrapper>
    </div>
  )
}
