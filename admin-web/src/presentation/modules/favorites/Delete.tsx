import React from 'react'
import { Modal } from '@/presentation/components/shared/ui/Modal'
import { AlertTriangle } from 'lucide-react'

interface FavoriteDeleteModalProps {
  favorite: any | null
  isOpen: boolean
  onClose: () => void
  onConfirm: () => void
  isLoading?: boolean
}

export function FavoriteDeleteModal({
  favorite,
  isOpen,
  onClose,
  onConfirm,
  isLoading,
}: FavoriteDeleteModalProps) {
  if (!favorite) return null

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Retirer le favori"
      description="Cette action supprimera l'association de favori de cet utilisateur."
      size="md"
      footer={
        <div className="flex items-center justify-end gap-3 w-full">
          <button
            type="button"
            onClick={onClose}
            disabled={isLoading}
            className="px-4 py-2 text-xs font-semibold rounded-xl border border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300 transition-colors cursor-pointer"
          >
            Annuler
          </button>
          <button
            type="button"
            onClick={onConfirm}
            disabled={isLoading}
            className="px-4 py-2 text-xs font-bold rounded-xl bg-rose-600 hover:bg-rose-700 text-white shadow-xs transition-colors cursor-pointer"
          >
            {isLoading ? 'Suppression...' : 'Retirer des favoris'}
          </button>
        </div>
      }
    >
      <div className="p-4 rounded-xl bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-900/50 flex items-start gap-3">
        <AlertTriangle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
        <div className="text-xs text-rose-800 dark:text-rose-200">
          Voulez-vous supprimer le favori pour le bien <strong>{favorite.property_title}</strong> associé au compte <strong>{favorite.user_email}</strong> ?
        </div>
      </div>
    </Modal>
  )
}
