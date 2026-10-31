import React from 'react'
import { Modal } from '@/presentation/components/shared/ui/Modal'
import { StatutBadge } from '@/presentation/components/shared/ui/StatutBadge'
import { formatFCFA } from '@/lib/utils'
import { Building2, Calendar, MapPin, Layers, Award } from 'lucide-react'

interface ProjectShowModalProps {
  project: any | null
  isOpen: boolean
  onClose: () => void
  onEdit?: (project: any) => void
  onAddLot?: (projectId: string) => void
}

export function ProjectShowModal({
  project,
  isOpen,
  onClose,
  onEdit,
  onAddLot,
}: ProjectShowModalProps) {
  if (!project) return null

  const lots = project.lots || []
  const availableLots = lots.filter((l: any) => l.status === 'DISPONIBLE').length

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={`Programme : ${project.name}`}
      description={`Promoteur : ${project.developer_name || 'Non spécifié'}`}
      size="lg"
      footer={
        <div className="flex items-center justify-between w-full">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-xs font-semibold rounded-xl border border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300 transition-colors cursor-pointer"
          >
            Fermer
          </button>
          <div className="flex items-center gap-2">
            {onAddLot && (
              <button
                type="button"
                onClick={() => {
                  onClose()
                  onAddLot(project.id)
                }}
                className="px-4 py-2 text-xs font-bold rounded-xl border border-blue-600 text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-950/40 transition-colors cursor-pointer"
              >
                + Ajouter un lot
              </button>
            )}
            {onEdit && (
              <button
                type="button"
                onClick={() => {
                  onClose()
                  onEdit(project)
                }}
                className="px-4 py-2 text-xs font-bold rounded-xl bg-blue-600 hover:bg-blue-700 text-white shadow-xs transition-colors cursor-pointer"
              >
                Modifier le programme
              </button>
            )}
          </div>
        </div>
      }
    >
      <div className="space-y-6 text-slate-900 dark:text-slate-100">
        {/* KPI Programme */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
          <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
            <div className="text-slate-400 flex items-center gap-1.5 mb-1">
              <MapPin className="w-3.5 h-3.5 text-blue-500" />
              Zone
            </div>
            <div className="font-bold">{project.commune}</div>
            <div className="text-[11px] text-slate-500">{project.neighborhood || 'Grand Abidjan'}</div>
          </div>

          <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
            <div className="text-slate-400 flex items-center gap-1.5 mb-1">
              <Calendar className="w-3.5 h-3.5 text-emerald-500" />
              Livraison
            </div>
            <div className="font-bold text-emerald-600 dark:text-emerald-400">
              {project.delivery_date ? new Date(project.delivery_date).toLocaleDateString('fr-FR') : 'Non définie'}
            </div>
            <div className="text-[11px] text-slate-500">Chantier sécurisé</div>
          </div>

          <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
            <div className="text-slate-400 flex items-center gap-1.5 mb-1">
              <Layers className="w-3.5 h-3.5 text-indigo-500" />
              Lots Disponibles
            </div>
            <div className="font-bold text-indigo-600 dark:text-indigo-400">
              {availableLots} / {project.total_lots || lots.length}
            </div>
            <div className="text-[11px] text-slate-500">Stock commercial</div>
          </div>

          <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
            <div className="text-slate-400 flex items-center gap-1.5 mb-1">
              <Award className="w-3.5 h-3.5 text-amber-500" />
              Prix d'appel
            </div>
            <div className="font-bold text-amber-600 dark:text-amber-400">
              {formatFCFA(project.starting_price)}
            </div>
            <div className="text-[11px] text-slate-500">À partir de</div>
          </div>
        </div>

        {/* Liste des lots rattachés */}
        <div>
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">
            Lots intégrés ({lots.length})
          </h4>
          {lots.length === 0 ? (
            <div className="p-6 text-center text-xs text-slate-400 border border-dashed border-slate-200 dark:border-slate-700 rounded-xl">
              Aucun lot enregistré pour ce programme pour l'instant.
            </div>
          ) : (
            <div className="divide-y divide-slate-100 dark:divide-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl overflow-hidden text-xs">
              {lots.map((lot: any) => (
                <div key={lot.id} className="p-3 flex items-center justify-between bg-white dark:bg-slate-800/80">
                  <div className="flex items-center gap-3">
                    <span className="font-mono font-bold text-blue-600 dark:text-blue-400">
                      {lot.lot_number}
                    </span>
                    <span className="font-semibold">{lot.typology} • {lot.surface_sqm} m²</span>
                    <span className="text-slate-400 text-[11px]">{lot.building_name} (Étage {lot.floor})</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="font-bold text-emerald-600 dark:text-emerald-400">
                      {formatFCFA(lot.price)}
                    </span>
                    <StatutBadge status={lot.status || 'DISPONIBLE'} />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </Modal>
  )
}
