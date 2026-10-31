import React from 'react'
import { Modal } from '@/presentation/components/shared/ui/Modal'
import { formatFCFA } from '@/lib/utils'
import { Phone, Mail, Building, Flame, Target, DollarSign, Calendar } from 'lucide-react'

interface CrmShowModalProps {
  lead: any | null
  isOpen: boolean
  onClose: () => void
  onEdit?: (lead: any) => void
}

export function CrmShowModal({ lead, isOpen, onClose, onEdit }: CrmShowModalProps) {
  if (!lead) return null

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={`Fiche Prospect : ${lead.full_name}`}
      description={`Source : ${lead.source || 'Demande directe'} • Statut : ${lead.stage}`}
      size="md"
      footer={
        <div className="flex items-center justify-between w-full">
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
                onEdit(lead)
              }}
              className="px-4 py-2 text-xs font-bold rounded-xl bg-blue-600 hover:bg-blue-700 text-white shadow-xs transition-colors cursor-pointer"
            >
              Faire évoluer l'étape
            </button>
          )}
        </div>
      }
    >
      <div className="space-y-4 text-xs">
        {/* Score d'Intention IA */}
        <div className="p-4 rounded-xl bg-blue-50/70 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-900/60 flex items-center justify-between">
          <div>
            <div className="text-[11px] font-bold text-blue-900 dark:text-blue-200 uppercase">
              Score Intention d'Achat IA
            </div>
            <div className="text-2xl font-black text-blue-600 dark:text-blue-400">
              {lead.qualification_score || 85} / 100
            </div>
          </div>
          <span className="p-2.5 rounded-full bg-blue-600 text-white">
            <Flame className="w-6 h-6" />
          </span>
        </div>

        {/* Coordonnées */}
        <div className="grid grid-cols-2 gap-3">
          <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
            <div className="text-slate-400 flex items-center gap-1.5 mb-1">
              <Phone className="w-3.5 h-3.5 text-emerald-500" />
              Téléphone WhatsApp
            </div>
            <div className="font-bold font-mono">{lead.phone_number}</div>
          </div>

          <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
            <div className="text-slate-400 flex items-center gap-1.5 mb-1">
              <Mail className="w-3.5 h-3.5 text-blue-500" />
              Email
            </div>
            <div className="font-bold truncate">{lead.email || 'Non communiqué'}</div>
          </div>
        </div>

        {/* Détails financiers & projet */}
        <div className="grid grid-cols-2 gap-3">
          <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
            <div className="text-slate-400 mb-1">Budget Déclaré</div>
            <div className="font-black text-emerald-600 dark:text-emerald-400 text-sm">
              {lead.budget_max ? formatFCFA(lead.budget_max) : 'Non défini'}
            </div>
          </div>

          <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
            <div className="text-slate-400 mb-1">Financement</div>
            <div className="font-bold">{lead.financing_mode || 'Fonds propres'}</div>
          </div>
        </div>

        {lead.consulted_property && (
          <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
            <div className="text-slate-400 flex items-center gap-1.5 mb-1">
              <Building className="w-3.5 h-3.5 text-blue-500" />
              Bien Immobilier Consulté
            </div>
            <div className="font-bold text-slate-900 dark:text-white">
              {lead.consulted_property.title}
            </div>
            <div className="text-[11px] text-slate-500">
              Réf: {lead.consulted_property.reference} • {lead.consulted_property.commune}
            </div>
          </div>
        )}
      </div>
    </Modal>
  )
}
