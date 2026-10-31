import React from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { fetchApi } from '@/lib/api'
import { Modal } from '@/presentation/components/shared/ui/Modal'
import { AlertTriangle } from 'lucide-react'

interface PropertyDeleteModalProps {
  property: any | null
  isOpen: boolean
  onClose: () => void
}

export function PropertyDeleteModal({ property, isOpen, onClose }: PropertyDeleteModalProps) {
  const queryClient = useQueryClient()

  const deleteMutation = useMutation({
    mutationFn: () =>
      fetchApi(`/properties/${property?.id}/`, {
        method: 'DELETE',
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['properties-list'] })
      queryClient.invalidateQueries({ queryKey: ['properties-dashboard'] })
      onClose()
    },
    onError: (err: any) => {
      alert(`Erreur de suppression : ${err.message}`)
    },
  })

  if (!property) return null

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Confirmer la suppression"
      description="Cette action est irréversible dans la base de données PostgreSQL."
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
            className="px-4 py-2 text-xs font-bold rounded-xl bg-rose-600 hover:bg-rose-700 text-white shadow-xs transition-colors flex items-center gap-2 cursor-pointer"
          >
            {deleteMutation.isPending ? 'Suppression en cours...' : 'Oui, supprimer définitivement'}
          </button>
        </div>
      }
    >
      <div className="space-y-4">
        <div className="p-4 rounded-xl bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-900/50 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
          <div className="text-xs text-rose-800 dark:text-rose-200">
            Êtes-vous certain de vouloir supprimer le bien <strong>{property.title}</strong> (Réf: {property.reference}) ? Les demandes de visite et leads associés à ce bien devront être réassignés.
          </div>
        </div>
      </div>
    </Modal>
  )
}
