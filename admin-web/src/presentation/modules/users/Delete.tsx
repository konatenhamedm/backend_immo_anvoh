import React from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { fetchApi } from '@/lib/api'
import { Modal } from '@/presentation/components/shared/ui/Modal'
import { AlertTriangle } from 'lucide-react'

interface UserDeleteModalProps {
  user: any | null
  isOpen: boolean
  onClose: () => void
}

export function UserDeleteModal({ user, isOpen, onClose }: UserDeleteModalProps) {
  const queryClient = useQueryClient()

  const deleteMutation = useMutation({
    mutationFn: () =>
      fetchApi(`/auth/users/${user?.id}/`, {
        method: 'DELETE',
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-users'] })
      onClose()
    },
    onError: (err: any) => alert(`Erreur de suppression : ${err.message}`),
  })

  if (!user) return null

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Désactiver ou Supprimer le Compte"
      description="Cette action révoquera les accès et sessions de l'utilisateur."
      size="md"
      footer={
        <div className="flex items-center justify-end gap-3 w-full">
          <button
            type="button"
            onClick={onClose}
            disabled={deleteMutation.isPending}
            className="px-4 py-2 text-xs font-semibold rounded-xl border border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300 transition-colors cursor-pointer"
          >
            Annuler
          </button>
          <button
            type="button"
            onClick={() => deleteMutation.mutate()}
            disabled={deleteMutation.isPending}
            className="px-4 py-2 text-xs font-bold rounded-xl bg-rose-600 hover:bg-rose-700 text-white shadow-xs transition-colors cursor-pointer"
          >
            {deleteMutation.isPending ? 'Suppression...' : 'Supprimer le compte'}
          </button>
        </div>
      }
    >
      <div className="p-4 rounded-xl bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-900/50 flex items-start gap-3">
        <AlertTriangle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
        <div className="text-xs text-rose-800 dark:text-rose-200">
          Êtes-vous certain de vouloir supprimer le compte de <strong>{user.first_name} {user.last_name}</strong> ({user.email}) ?
        </div>
      </div>
    </Modal>
  )
}
