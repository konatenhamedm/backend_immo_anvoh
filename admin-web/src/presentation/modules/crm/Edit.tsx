import React, { useState, useEffect } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { fetchApi } from '@/lib/api'
import { Modal, ModalFooterButtons } from '@/presentation/components/shared/ui/Modal'

interface CrmEditModalProps {
  lead: any | null
  isOpen: boolean
  onClose: () => void
}

export function CrmEditModal({ lead, isOpen, onClose }: CrmEditModalProps) {
  const queryClient = useQueryClient()

  const [formData, setFormData] = useState({
    full_name: '',
    stage: 'NOUVEAU',
    budget_max: '',
    financing_mode: 'CREDIT_BANCAIRE',
    objective: 'HABITATION',
  })

  useEffect(() => {
    if (lead) {
      setFormData({
        full_name: lead.full_name || '',
        stage: lead.stage || 'NOUVEAU',
        budget_max: lead.budget_max ? String(lead.budget_max) : '',
        financing_mode: lead.financing_mode || 'CREDIT_BANCAIRE',
        objective: lead.objective || 'HABITATION',
      })
    }
  }, [lead])

  const updateMutation = useMutation({
    mutationFn: (updated: any) =>
      fetchApi(`/crm/leads/${lead?.id}/`, {
        method: 'PATCH',
        body: JSON.stringify(updated),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['kanban-pipeline'] })
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
      title={`Édition Commerciale : ${lead?.full_name || ''}`}
      description="Faites progresser le prospect dans les étapes de négociation et de conclusion."
      size="md"
      footer={
        <ModalFooterButtons
          onCancel={onClose}
          onConfirm={handleSubmit}
          confirmText="Mettre à jour l'étape"
          isLoading={updateMutation.isPending}
        />
      }
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
            Étape du Pipeline Commercial
          </label>
          <select
            value={formData.stage}
            onChange={(e) => setFormData({ ...formData, stage: e.target.value })}
            className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white font-bold text-blue-600 focus:border-blue-500 focus:outline-hidden"
          >
            <option value="NOUVEAU">Nouveau Prospect</option>
            <option value="QUALIFIE">Prospect Qualifié</option>
            <option value="RDV">Rendez-vous Fixé</option>
            <option value="VISITE">Visite Programmée</option>
            <option value="PROPOSITION">Proposition / Offre</option>
            <option value="NEGOCIATION">En Négociation</option>
            <option value="VENTE">Vente Conclue / Acte Notarié</option>
          </select>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
              Budget (FCFA)
            </label>
            <input
              type="number"
              value={formData.budget_max}
              onChange={(e) => setFormData({ ...formData, budget_max: e.target.value })}
              className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:border-blue-500 focus:outline-hidden"
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
              Mode Financement
            </label>
            <select
              value={formData.financing_mode}
              onChange={(e) => setFormData({ ...formData, financing_mode: e.target.value })}
              className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:border-blue-500 focus:outline-hidden"
            >
              <option value="CREDIT_BANCAIRE">Crédit Bancaire</option>
              <option value="COMPTANT">Fonds Propres / Comptant</option>
              <option value="ECHELONNE">Échelonné</option>
            </select>
          </div>
        </div>
      </form>
    </Modal>
  )
}
