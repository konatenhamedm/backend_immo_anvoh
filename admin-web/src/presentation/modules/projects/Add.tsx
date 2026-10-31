import React, { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { fetchApi } from '@/lib/api'
import { Modal, ModalFooterButtons } from '@/presentation/components/shared/ui/Modal'

interface ProjectAddModalProps {
  isOpen: boolean
  onClose: () => void
  projectId?: string | null
  mode?: 'project' | 'lot'
}

export function ProjectAddModal({
  isOpen,
  onClose,
  projectId,
  mode = 'project',
}: ProjectAddModalProps) {
  const queryClient = useQueryClient()

  // Formulaire projet
  const [projectForm, setProjectForm] = useState({
    name: '',
    developer_name: '',
    commune: 'Cocody',
    neighborhood: '',
    delivery_date: '2026-12-31',
    total_lots: 24,
    starting_price: '45000000',
    description: '',
  })

  // Formulaire lot
  const [lotForm, setLotForm] = useState({
    lot_number: '',
    typology: 'F3',
    building_name: 'Bâtiment A',
    floor: 1,
    surface_sqm: '85.00',
    price: '75000000',
    status: 'DISPONIBLE',
  })

  // Mutation création projet
  const createProjectMutation = useMutation({
    mutationFn: (newProj: any) =>
      fetchApi('/properties/projects/', {
        method: 'POST',
        body: JSON.stringify(newProj),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects-list'] })
      onClose()
      setProjectForm({
        name: '',
        developer_name: '',
        commune: 'Cocody',
        neighborhood: '',
        delivery_date: '2026-12-31',
        total_lots: 24,
        starting_price: '45000000',
        description: '',
      })
    },
    onError: (err: any) => alert(`Erreur : ${err.message}`),
  })

  // Mutation création lot
  const createLotMutation = useMutation({
    mutationFn: ({ pId, lot }: { pId: string; lot: any }) =>
      fetchApi(`/properties/projects/${pId}/lots/`, {
        method: 'POST',
        body: JSON.stringify(lot),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects-list'] })
      onClose()
      setLotForm({
        lot_number: '',
        typology: 'F3',
        building_name: 'Bâtiment A',
        floor: 1,
        surface_sqm: '85.00',
        price: '75000000',
        status: 'DISPONIBLE',
      })
    },
    onError: (err: any) => alert(`Erreur : ${err.message}`),
  })

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault()
    if (mode === 'lot') {
      if (!projectId) return
      createLotMutation.mutate({ pId: projectId, lot: lotForm })
    } else {
      createProjectMutation.mutate(projectForm)
    }
  }

  const isPending = createProjectMutation.isPending || createLotMutation.isPending

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={mode === 'lot' ? 'Ajouter un Lot au Programme' : 'Créer un Nouveau Programme Neuf'}
      description={
        mode === 'lot'
          ? 'Renseignez les détails du nouveau lot (superficie, étage, prix commercial).'
          : 'Enregistrez une nouvelle opération de promotion immobilière (VEFA / En cours).'
      }
      size="md"
      footer={
        <ModalFooterButtons
          onCancel={onClose}
          onConfirm={handleSubmit}
          confirmText={mode === 'lot' ? 'Ajouter ce lot' : 'Créer le programme'}
          isLoading={isPending}
        />
      }
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {mode === 'lot' ? (
          <>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                  Numéro de Lot *
                </label>
                <input
                  type="text"
                  placeholder="Ex: LOT-B12"
                  value={lotForm.lot_number}
                  onChange={(e) => setLotForm({ ...lotForm, lot_number: e.target.value })}
                  className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white font-mono focus:border-blue-500 focus:outline-hidden"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                  Typologie
                </label>
                <select
                  value={lotForm.typology}
                  onChange={(e) => setLotForm({ ...lotForm, typology: e.target.value })}
                  className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:border-blue-500 focus:outline-hidden"
                >
                  <option value="F2">F2 (2 pièces)</option>
                  <option value="F3">F3 (3 pièces)</option>
                  <option value="F4">F4 (4 pièces)</option>
                  <option value="F5">F5 (5 pièces et plus)</option>
                  <option value="VILLA">Villa Duplex</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                  Bâtiment
                </label>
                <input
                  type="text"
                  value={lotForm.building_name}
                  onChange={(e) => setLotForm({ ...lotForm, building_name: e.target.value })}
                  className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:border-blue-500 focus:outline-hidden"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                  Étage
                </label>
                <input
                  type="number"
                  value={lotForm.floor}
                  onChange={(e) => setLotForm({ ...lotForm, floor: parseInt(e.target.value) || 0 })}
                  className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:border-blue-500 focus:outline-hidden"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                  Superficie (m²)
                </label>
                <input
                  type="number"
                  value={lotForm.surface_sqm}
                  onChange={(e) => setLotForm({ ...lotForm, surface_sqm: e.target.value })}
                  className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:border-blue-500 focus:outline-hidden"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                  Prix de Vente (FCFA) *
                </label>
                <input
                  type="number"
                  value={lotForm.price}
                  onChange={(e) => setLotForm({ ...lotForm, price: e.target.value })}
                  className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:border-blue-500 focus:outline-hidden"
                  required
                />
              </div>
            </div>
          </>
        ) : (
          <>
            <div>
              <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                Nom du Programme *
              </label>
              <input
                type="text"
                placeholder="Ex: Résidence Les Jardins d'Éden"
                value={projectForm.name}
                onChange={(e) => setProjectForm({ ...projectForm, name: e.target.value })}
                className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:border-blue-500 focus:outline-hidden"
                required
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                  Promoteur *
                </label>
                <input
                  type="text"
                  placeholder="Ex: GROUPE ANVOH PROMOTION"
                  value={projectForm.developer_name}
                  onChange={(e) => setProjectForm({ ...projectForm, developer_name: e.target.value })}
                  className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:border-blue-500 focus:outline-hidden"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                  Commune
                </label>
                <select
                  value={projectForm.commune}
                  onChange={(e) => setProjectForm({ ...projectForm, commune: e.target.value })}
                  className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:border-blue-500 focus:outline-hidden"
                >
                  <option value="Cocody">Cocody</option>
                  <option value="Bingerville">Bingerville</option>
                  <option value="Marcory">Marcory</option>
                  <option value="Grand-Bassam">Grand-Bassam</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                  Prix à partir de (FCFA)
                </label>
                <input
                  type="number"
                  value={projectForm.starting_price}
                  onChange={(e) => setProjectForm({ ...projectForm, starting_price: e.target.value })}
                  className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:border-blue-500 focus:outline-hidden"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                  Date prévisionnelle de livraison
                </label>
                <input
                  type="date"
                  value={projectForm.delivery_date}
                  onChange={(e) => setProjectForm({ ...projectForm, delivery_date: e.target.value })}
                  className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:border-blue-500 focus:outline-hidden"
                />
              </div>
            </div>
          </>
        )}
      </form>
    </Modal>
  )
}
