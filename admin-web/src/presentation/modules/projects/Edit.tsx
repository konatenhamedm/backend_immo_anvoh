import React, { useState, useEffect } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { fetchApi } from '@/lib/api'
import { Modal, ModalFooterButtons } from '@/presentation/components/shared/ui/Modal'

interface ProjectEditModalProps {
  project: any | null
  isOpen: boolean
  onClose: () => void
}

export function ProjectEditModal({ project, isOpen, onClose }: ProjectEditModalProps) {
  const queryClient = useQueryClient()

  const [formData, setFormData] = useState({
    name: '',
    developer_name: '',
    commune: '',
    neighborhood: '',
    delivery_date: '',
    total_lots: 0,
    starting_price: '',
    status: 'EN_CONSTRUCTION',
  })

  useEffect(() => {
    if (project) {
      setFormData({
        name: project.name || '',
        developer_name: project.developer_name || '',
        commune: project.commune || 'Cocody',
        neighborhood: project.neighborhood || '',
        delivery_date: project.delivery_date || '',
        total_lots: project.total_lots || 0,
        starting_price: project.starting_price ? String(project.starting_price) : '',
        status: project.status || 'EN_CONSTRUCTION',
      })
    }
  }, [project])

  const updateMutation = useMutation({
    mutationFn: (updated: any) =>
      fetchApi(`/properties/projects/${project?.id}/`, {
        method: 'PATCH',
        body: JSON.stringify(updated),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects-list'] })
      onClose()
    },
    onError: (err: any) => alert(`Erreur : ${err.message}`),
  })

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault()
    updateMutation.mutate(formData)
  }

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={`Modifier le Programme : ${project?.name || ''}`}
      description="Mettez à jour les informations du promoteur, dates clés et statut du chantier."
      size="md"
      footer={
        <ModalFooterButtons
          onCancel={onClose}
          onConfirm={handleSubmit}
          confirmText="Enregistrer"
          isLoading={updateMutation.isPending}
        />
      }
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
            Nom du Programme
          </label>
          <input
            type="text"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:border-blue-500 focus:outline-hidden"
            required
          />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
              Promoteur
            </label>
            <input
              type="text"
              value={formData.developer_name}
              onChange={(e) => setFormData({ ...formData, developer_name: e.target.value })}
              className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:border-blue-500 focus:outline-hidden"
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
              Prix d'appel (FCFA)
            </label>
            <input
              type="number"
              value={formData.starting_price}
              onChange={(e) => setFormData({ ...formData, starting_price: e.target.value })}
              className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:border-blue-500 focus:outline-hidden"
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
              Date de Livraison
            </label>
            <input
              type="date"
              value={formData.delivery_date}
              onChange={(e) => setFormData({ ...formData, delivery_date: e.target.value })}
              className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:border-blue-500 focus:outline-hidden"
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
              Statut
            </label>
            <select
              value={formData.status}
              onChange={(e) => setFormData({ ...formData, status: e.target.value })}
              className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:border-blue-500 focus:outline-hidden"
            >
              <option value="EN_CONSTRUCTION">En Construction</option>
              <option value="LIVRE">Livré</option>
              <option value="LANCEMENT">En Lancement Commercial</option>
            </select>
          </div>
        </div>
      </form>
    </Modal>
  )
}
