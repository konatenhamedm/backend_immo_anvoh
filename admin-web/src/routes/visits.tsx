import React, { useState } from 'react'
import { createFileRoute } from '@tanstack/react-router'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Calendar,
  Clock,
  Video,
  MapPin,
  CheckCircle,
  XCircle,
  User,
  Building
} from 'lucide-react'
import { fetchApi } from '@/lib/api'
import { StatutBadge } from '@/presentation/components/shared/ui/StatutBadge'

export const Route = createFileRoute('/visits')({
  component: VisitsManagementPage,
})

function VisitsManagementPage() {
  const queryClient = useQueryClient()
  const [filterType, setFilterType] = useState('')

  const { data: visitsData, isLoading } = useQuery({
    queryKey: ['admin-visits'],
    queryFn: () => fetchApi<{ results: any[] }>('/crm/visits/'),
  })

  const updateStatusMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) =>
      fetchApi(`/crm/visits/${id}/`, {
        method: 'PATCH',
        body: JSON.stringify({ status }),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-visits'] })
    },
  })

  const visits = visitsData?.results || []
  const filteredVisits = filterType
    ? visits.filter((v: any) => v.visit_type === filterType)
    : visits

  return (
    <div className="w-full space-y-6 animate-fade-in">
      {/* En-tête */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black tracking-tight text-slate-900 dark:text-white flex items-center gap-2">
            Gestion des Rendez-vous & Visites
            <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-indigo-100 text-indigo-800 dark:bg-indigo-950/60 dark:text-indigo-300">
              Écran 16
            </span>
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Validez, confirmez ou reprogrammez les visites physiques sur site et les visites visio pour la diaspora.
          </p>
        </div>

        <div className="flex items-center gap-2">
          {['', 'PHYSIQUE', 'VISIO'].map((t) => (
            <button
              key={t}
              onClick={() => setFilterType(t)}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all ${
                filterType === t
                  ? 'bg-teal-600 text-white shadow-xs'
                  : 'bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-700'
              }`}
            >
              {t === '' ? 'Toutes' : t === 'PHYSIQUE' ? 'Visites Physiques' : 'Visites Vidéo (Diaspora)'}
            </button>
          ))}
        </div>
      </div>

      {/* Grille des visites */}
      {isLoading ? (
        <div className="p-12 text-center text-slate-400 italic">Chargement des visites...</div>
      ) : filteredVisits.length === 0 ? (
        <div className="p-12 text-center text-slate-400 italic bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800">
          Aucune demande de visite enregistrée pour ce filtre.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filteredVisits.map((v: any) => (
            <div
              key={v.id}
              className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-xs space-y-4 flex flex-col justify-between"
            >
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-bold bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300">
                    {v.visit_type === 'VISIO' ? (
                      <>
                        <Video className="w-3.5 h-3.5 text-indigo-500" />
                        Visite Vidéo Diaspora
                      </>
                    ) : (
                      <>
                        <MapPin className="w-3.5 h-3.5 text-teal-600" />
                        Visite Physique sur Site
                      </>
                    )}
                  </span>
                  <StatutBadge status={v.status} label={v.status_display} />
                </div>

                <div>
                  <h3 className="font-bold text-sm text-slate-900 dark:text-white line-clamp-1">
                    {v.property?.title || 'Bien concerné'}
                  </h3>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                    {v.property?.commune} {v.property?.reference ? `(${v.property.reference})` : ''}
                  </p>
                </div>

                <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-700/60 space-y-1.5 text-xs text-slate-600 dark:text-slate-300">
                  <div className="flex items-center gap-2">
                    <Calendar className="w-4 h-4 text-slate-400" />
                    <span className="font-semibold">{v.scheduled_date}</span>
                    <Clock className="w-4 h-4 text-slate-400 ml-2" />
                    <span>{v.scheduled_time}</span>
                  </div>
                  {v.notes && (
                    <div className="text-[11px] text-slate-400 italic mt-1 border-t border-slate-200/60 dark:border-slate-700/60 pt-1">
                      "{v.notes}"
                    </div>
                  )}
                </div>
              </div>

              {/* Actions de validation */}
              <div className="pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between gap-2">
                <span className="text-[10px] text-slate-400">Action :</span>
                <div className="flex items-center gap-2">
                  {v.status !== 'CONFIRMEE' && (
                    <button
                      onClick={() => updateStatusMutation.mutate({ id: v.id, status: 'CONFIRMEE' })}
                      className="px-2.5 py-1 text-xs font-semibold rounded-lg bg-emerald-50 text-emerald-700 hover:bg-emerald-100 dark:bg-emerald-950/60 dark:text-emerald-300 transition-colors flex items-center gap-1"
                    >
                      <CheckCircle className="w-3.5 h-3.5" /> Confirmer
                    </button>
                  )}
                  {v.status !== 'EFFECTUEE' && (
                    <button
                      onClick={() => updateStatusMutation.mutate({ id: v.id, status: 'EFFECTUEE' })}
                      className="px-2.5 py-1 text-xs font-semibold rounded-lg bg-teal-50 text-teal-700 hover:bg-teal-100 dark:bg-teal-950/60 dark:text-teal-300 transition-colors"
                    >
                      Effectuée
                    </button>
                  )}
                  {v.status !== 'ANNULEE' && (
                    <button
                      onClick={() => updateStatusMutation.mutate({ id: v.id, status: 'ANNULEE' })}
                      className="px-2 py-1 text-xs text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/40 rounded-lg transition-colors"
                      title="Annuler la visite"
                    >
                      <XCircle className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
