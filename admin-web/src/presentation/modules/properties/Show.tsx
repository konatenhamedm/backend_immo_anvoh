import React from 'react'
import { Modal } from '@/presentation/components/shared/ui/Modal'
import { StatutBadge } from '@/presentation/components/shared/ui/StatutBadge'
import { formatFCFA } from '@/lib/utils'
import {
  MapPin,
  Maximize2,
  TrendingUp,
  ShieldCheck,
  Building,
  Calendar,
  Layers,
  Flame,
  FileText
} from 'lucide-react'

interface PropertyShowModalProps {
  property: any | null
  isOpen: boolean
  onClose: () => void
  onEdit?: (property: any) => void
}

export function PropertyShowModal({ property, isOpen, onClose, onEdit }: PropertyShowModalProps) {
  if (!property) return null

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={`Fiche Détail : ${property.title}`}
      description={`Référence Mandat : ${property.reference}`}
      size="lg"
      footer={
        <div className="flex items-center justify-between w-full">
          <div className="text-[11px] text-slate-500">
            Ajouté le {new Date(property.created_at).toLocaleDateString('fr-FR')}
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-xs font-semibold rounded-xl border border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300 transition-colors cursor-pointer"
            >
              Fermer
            </button>
            {onEdit && (
              <button
                type="button"
                onClick={() => {
                  onClose()
                  onEdit(property)
                }}
                className="px-4 py-2 text-xs font-bold rounded-xl bg-blue-600 hover:bg-blue-700 text-white shadow-xs transition-colors cursor-pointer"
              >
                Modifier ce bien
              </button>
            )}
          </div>
        </div>
      }
    >
      <div className="space-y-6 text-slate-900 dark:text-slate-100">
        {/* En-tête résumé financier & statut */}
        <div className="p-4 rounded-2xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-800 flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="text-xs uppercase tracking-wider text-slate-500 font-semibold">
              Prix d'acquisition
            </div>
            <div className="text-2xl font-black text-emerald-600 dark:text-emerald-400 mt-0.5">
              {formatFCFA(property.price)}
            </div>
          </div>

          <div className="flex items-center gap-2">
            <StatutBadge status={property.status || 'DISPONIBLE'} />
            <StatutBadge status={property.verification_status || 'VERIFIE'} />
          </div>
        </div>

        {/* Grille des caractéristiques clés */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
          <div className="p-3 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
            <div className="text-slate-400 flex items-center gap-1.5 mb-1">
              <MapPin className="w-3.5 h-3.5 text-blue-500" />
              Localisation
            </div>
            <div className="font-bold">{property.commune}</div>
            <div className="text-[11px] text-slate-500">{property.neighborhood || 'Centre'}</div>
          </div>

          <div className="p-3 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
            <div className="text-slate-400 flex items-center gap-1.5 mb-1">
              <Maximize2 className="w-3.5 h-3.5 text-emerald-500" />
              Superficie & Type
            </div>
            <div className="font-bold">{property.surface_sqm} m²</div>
            <div className="text-[11px] text-slate-500">{property.typology || 'F3'} • {property.property_type}</div>
          </div>

          <div className="p-3 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
            <div className="text-slate-400 flex items-center gap-1.5 mb-1">
              <TrendingUp className="w-3.5 h-3.5 text-indigo-500" />
              Rentabilité
            </div>
            <div className="font-bold text-indigo-600 dark:text-indigo-400">
              {property.estimated_yield_rate ? `${property.estimated_yield_rate} % / an` : 'À estimer'}
            </div>
            <div className="text-[11px] text-slate-500">
              Loyer: {property.estimated_monthly_rent ? formatFCFA(property.estimated_monthly_rent) : '—'}
            </div>
          </div>

          <div className="p-3 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
            <div className="text-slate-400 flex items-center gap-1.5 mb-1">
              <Flame className="w-3.5 h-3.5 text-amber-500" />
              Score Attractivité
            </div>
            <div className="font-bold text-amber-600 dark:text-amber-400">
              {property.investment_score || 85}/100
            </div>
            <div className="text-[11px] text-slate-500">Algorithme IA Thiebbro</div>
          </div>
        </div>

        {/* Description détaillée */}
        <div>
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2 flex items-center gap-1.5">
            <FileText className="w-3.5 h-3.5" />
            Description & Points forts du bien
          </h4>
          <div className="p-4 rounded-xl bg-white dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 text-xs leading-relaxed text-slate-700 dark:text-slate-300">
            {property.description || "Aucune description renseignée pour ce bien."}
          </div>
        </div>

        {/* Sécurité juridique & Documents */}
        <div className="p-3.5 rounded-xl bg-blue-50/70 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-900/60 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-blue-600 text-white flex items-center justify-center font-bold">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <div className="text-xs font-bold text-blue-900 dark:text-blue-200">
                Statut Foncier Certifié THIEBBRO IMMO
              </div>
              <div className="text-[11px] text-blue-700 dark:text-blue-400">
                Titre foncier et arrêté de concession définitive (ACD) vérifiés auprès de la conservation foncière.
              </div>
            </div>
          </div>
        </div>
      </div>
    </Modal>
  )
}
