import React, { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { fetchApi } from '@/lib/api'
import { Modal, ModalFooterButtons } from '@/presentation/components/shared/ui/Modal'

interface CrmAddModalProps {
  isOpen: boolean
  onClose: () => void
}

export function CrmAddModal({ isOpen, onClose }: CrmAddModalProps) {
  const queryClient = useQueryClient()

  const [formData, setFormData] = useState({
    full_name: '',
    phone_number: '',
    email: '',
    objective: 'HABITATION',
    budget_max: '65000000',
    financing_mode: 'CREDIT_BANCAIRE',
    stage: 'NOUVEAU',
  })

  const createMutation = useMutation({
    mutationFn: (newLead: any) =>
      fetchApi('/crm/inquiries/', {
        method: 'POST',
        body: JSON.stringify(newLead),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['kanban-pipeline'] })
      onClose()
      setFormData({
        full_name: '',
        phone_number: '',
        email: '',
        objective: 'HABITATION',
        budget_max: '65000000',
        financing_mode: 'CREDIT_BANCAIRE',
        stage: 'NOUVEAU',
      })
    },
    onError: (err: any) => alert(`Erreur : ${err.message}`),
  })

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault()
    createMutation.mutate(formData)
  }

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Créer une Fiche Prospect (Lead)"
      description="Enregistrez une nouvelle opportunité commerciale dans le pipeline de vente."
      size="md"
      footer={
        <ModalFooterButtons
          onCancel={onClose}
          onConfirm={handleSubmit}
          confirmText="Enregistrer le prospect"
          isLoading={createMutation.isPending}
        />
      }
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
            Nom et Prénoms du Prospect *
          </label>
          <input
            type="text"
            placeholder="Ex: Kouamé N'Guessan"
            value={formData.full_name}
            onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
            className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:border-blue-500 focus:outline-hidden"
            required
          />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
              Téléphone WhatsApp *
            </label>
            <input
              type="tel"
              placeholder="+225 07 00 00 00 00"
              value={formData.phone_number}
              onChange={(e) => setFormData({ ...formData, phone_number: e.target.value })}
              className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:border-blue-500 focus:outline-hidden"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
              Email
            </label>
            <input
              type="email"
              placeholder="client@gmail.com"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:border-blue-500 focus:outline-hidden"
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
              Budget Prévu (FCFA)
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
              Mode de Financement
            </label>
            <select
              value={formData.financing_mode}
              onChange={(e) => setFormData({ ...formData, financing_mode: e.target.value })}
              className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:border-blue-500 focus:outline-hidden"
            >
              <option value="CREDIT_BANCAIRE">Crédit Bancaire</option>
              <option value="COMPTANT">Fonds Propres / Comptant</option>
              <option value="ECHELONNE">Paiement Échelonné</option>
            </select>
          </div>
        </div>
      </form>
    </Modal>
  )
}
