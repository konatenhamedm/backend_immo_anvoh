import React from 'react'
import { Modal } from '@/presentation/components/shared/ui/Modal'
import { formatFCFA } from '@/lib/utils'
import { Mail, Phone, Globe, Shield, Calendar, UserCheck } from 'lucide-react'

interface UserShowModalProps {
  user: any | null
  isOpen: boolean
  onClose: () => void
  onEdit?: (user: any) => void
}

export function UserShowModal({ user, isOpen, onClose, onEdit }: UserShowModalProps) {
  if (!user) return null

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={`Profil : ${user.first_name} ${user.last_name}`}
      description={`Compte : ${user.email}`}
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
                onEdit(user)
              }}
              className="px-4 py-2 text-xs font-bold rounded-xl bg-blue-600 hover:bg-blue-700 text-white shadow-xs transition-colors cursor-pointer"
            >
              Modifier ce compte
            </button>
          )}
        </div>
      }
    >
      <div className="space-y-4 text-xs">
        <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-blue-600 text-white flex items-center justify-center font-black text-sm">
              {user.first_name?.[0] || 'U'}{user.last_name?.[0] || 'N'}
            </div>
            <div>
              <div className="font-bold text-sm text-slate-900 dark:text-white">
                {user.first_name} {user.last_name}
              </div>
              <div className="text-slate-400 text-[11px]">{user.email}</div>
            </div>
          </div>

          <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300">
            {user.role}
          </span>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div className="p-3 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
            <div className="text-slate-400 flex items-center gap-1.5 mb-1">
              <Phone className="w-3.5 h-3.5 text-emerald-500" />
              Téléphone
            </div>
            <div className="font-bold">{user.phone_number || 'Non renseigné'}</div>
          </div>

          <div className="p-3 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
            <div className="text-slate-400 flex items-center gap-1.5 mb-1">
              <Globe className="w-3.5 h-3.5 text-blue-500" />
              Résidence
            </div>
            <div className="font-bold">{user.residence_country || 'Côte d’Ivoire'}</div>
            {user.is_diaspora && (
              <span className="text-[10px] text-indigo-600 font-semibold">Membre Diaspora</span>
            )}
          </div>
        </div>

        {user.target_budget && (
          <div className="p-3 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
            <div className="text-slate-400 mb-1">Budget d'Investissement Prévu</div>
            <div className="font-black text-emerald-600 dark:text-emerald-400 text-sm">
              {formatFCFA(user.target_budget)}
            </div>
          </div>
        )}
      </div>
    </Modal>
  )
}
