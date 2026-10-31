import React, { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { fetchApi } from '@/lib/api'
import { Modal, ModalFooterButtons } from '@/presentation/components/shared/ui/Modal'

interface UserAddModalProps {
  isOpen: boolean
  onClose: () => void
}

export function UserAddModal({ isOpen, onClose }: UserAddModalProps) {
  const queryClient = useQueryClient()

  const [formData, setFormData] = useState({
    email: '',
    password: '',
    first_name: '',
    last_name: '',
    phone_number: '',
    role: 'AGENT',
    residence_country: 'Côte d’Ivoire',
    target_budget: '50000000',
  })

  const createMutation = useMutation({
    mutationFn: (newUser: any) =>
      fetchApi('/auth/users/', {
        method: 'POST',
        body: JSON.stringify(newUser),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-users'] })
      onClose()
      setFormData({
        email: '',
        password: '',
        first_name: '',
        last_name: '',
        phone_number: '',
        role: 'AGENT',
        residence_country: 'Côte d’Ivoire',
        target_budget: '50000000',
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
      title="Créer un Nouvel Utilisateur / Agent"
      description="Ajoutez un conseiller commercial, un administrateur ou un client avec ses droits d'accès."
      size="md"
      footer={
        <ModalFooterButtons
          onCancel={onClose}
          onConfirm={handleSubmit}
          confirmText="Créer le compte"
          isLoading={createMutation.isPending}
        />
      }
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
              Prénom *
            </label>
            <input
              type="text"
              placeholder="Ex: Amadou"
              value={formData.first_name}
              onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
              className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:border-blue-500 focus:outline-hidden"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
              Nom de Famille *
            </label>
            <input
              type="text"
              placeholder="Ex: Koné"
              value={formData.last_name}
              onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
              className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:border-blue-500 focus:outline-hidden"
              required
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
              Adresse Email *
            </label>
            <input
              type="email"
              placeholder="agent@thiebbro.ci"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:border-blue-500 focus:outline-hidden"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
              Mot de passe initial *
            </label>
            <input
              type="password"
              placeholder="••••••••"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:border-blue-500 focus:outline-hidden"
              required
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
              Rôle / Profil
            </label>
            <select
              value={formData.role}
              onChange={(e) => setFormData({ ...formData, role: e.target.value })}
              className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:border-blue-500 focus:outline-hidden"
            >
              <option value="AGENT">Conseiller Commercial (AGENT)</option>
              <option value="ADMIN">Administrateur Système</option>
              <option value="INVESTISSEUR">Client Investisseur</option>
              <option value="PARTICULIER">Particulier / Acheteur</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
              Téléphone (WhatsApp)
            </label>
            <input
              type="tel"
              placeholder="+225 07 00 00 00 00"
              value={formData.phone_number}
              onChange={(e) => setFormData({ ...formData, phone_number: e.target.value })}
              className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:border-blue-500 focus:outline-hidden"
            />
          </div>
        </div>
      </form>
    </Modal>
  )
}
