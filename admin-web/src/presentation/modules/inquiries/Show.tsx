import React from 'react'
import { Modal } from '@/presentation/components/shared/ui/Modal'
import { formatFCFA } from '@/lib/utils'
import { Phone, Mail, Building, Target, Calendar, CheckCircle } from 'lucide-react'

interface InquiryShowModalProps {
  inquiry: any | null
  isOpen: boolean
  onClose: () => void
  onToggleProcessed?: (id: string, current: boolean) => void
}

export function InquiryShowModal({
  inquiry,
  isOpen,
  onClose,
  onToggleProcessed,
}: InquiryShowModalProps) {
  if (!inquiry) return null

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Détail de la Demande d'Information"
      description={`Reçue le ${new Date(inquiry.created_at).toLocaleDateString('fr-FR')}`}
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
          {onToggleProcessed && (
            <button
              type="button"
              onClick={() => {
                onToggleProcessed(inquiry.id, inquiry.is_processed)
                onClose()
              }}
              className="px-4 py-2 text-xs font-bold rounded-xl bg-blue-600 hover:bg-blue-700 text-white shadow-xs transition-colors cursor-pointer flex items-center gap-1.5"
            >
              <CheckCircle className="w-3.5 h-3.5" />
              {inquiry.is_processed ? 'Marquer comme non traité' : 'Marquer comme traité'}
            </button>
          )}
        </div>
      }
    >
      <div className="space-y-4 text-xs">
        {/* Contact prospect */}
        <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 space-y-2">
          <div className="font-bold text-sm text-slate-900 dark:text-white">
            {inquiry.lead?.full_name || 'Prospect Anonyme'}
          </div>
          <div className="flex items-center gap-4 text-slate-600 dark:text-slate-300">
            <span className="flex items-center gap-1 font-mono">
              <Phone className="w-3.5 h-3.5 text-emerald-500" />
              {inquiry.lead?.phone_number || 'Non renseigné'}
            </span>
            {inquiry.lead?.email && (
              <span className="flex items-center gap-1">
                <Mail className="w-3.5 h-3.5 text-blue-500" />
                {inquiry.lead.email}
              </span>
            )}
          </div>
        </div>

        {/* Bien d'intérêt */}
        <div className="p-4 rounded-xl bg-blue-50/60 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-900/60 space-y-1.5">
          <div className="text-[11px] font-bold text-blue-900 dark:text-blue-300 uppercase">
            Bien Immobilier Consulté
          </div>
          <div className="font-bold text-slate-900 dark:text-white">
            {inquiry.property?.title}
          </div>
          <div className="text-slate-500 text-[11px]">
            Réf: {inquiry.property?.reference} • {inquiry.property?.commune}
          </div>
          {inquiry.property?.price && (
            <div className="font-black text-emerald-600 dark:text-emerald-400 mt-1">
              {formatFCFA(inquiry.property.price)}
            </div>
          )}
        </div>

        {/* Objectif */}
        <div className="p-3 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 flex items-center justify-between">
          <span className="text-slate-500 font-semibold">Objectif d'acquisition :</span>
          <span className="font-bold uppercase text-blue-600 dark:text-blue-400">
            {inquiry.objective || 'Habitation'}
          </span>
        </div>
      </div>
    </Modal>
  )
}
