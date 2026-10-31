import React, { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { fetchApi } from '@/lib/api'
import { Modal, ModalFooterButtons } from '@/presentation/components/shared/ui/Modal'
import { Select2, Select2Option } from '@/presentation/components/shared/ui/Select2'
import {
  Building2,
  DollarSign,
  MapPin,
  Layers,
  Sparkles,
  ArrowRight,
  ArrowLeft,
  Video,
  ShieldCheck,
  CheckCircle2
} from 'lucide-react'

interface PropertyAddModalProps {
  isOpen: boolean
  onClose: () => void
}

const PROPERTY_TYPE_OPTIONS: Select2Option[] = [
  { value: 'APPARTEMENT', label: 'Appartement' },
  { value: 'VILLA', label: 'Villa Individuelle' },
  { value: 'MAISON', label: 'Maison' },
  { value: 'DUPLEX', label: 'Duplex' },
  { value: 'TERRAIN', label: 'Terrain constructible' },
  { value: 'IMMEUBLE', label: 'Immeuble de rapport' },
  { value: 'RESIDENCE_MEUBLEE', label: 'Résidence meublée' },
  { value: 'BUREAU', label: 'Bureau' },
  { value: 'COMMERCIAL', label: 'Local commercial' },
]

const TYPOLOGY_OPTIONS: Select2Option[] = [
  { value: 'F1', label: 'F1 / Studio' },
  { value: 'F2', label: 'F2 (2 pièces)' },
  { value: 'F3', label: 'F3 (3 pièces)' },
  { value: 'F4', label: 'F4 (4 pièces)' },
  { value: 'F5', label: 'F5 (5 pièces et plus)' },
  { value: 'AUTRE', label: 'Autre configuration / Terrain' },
]

const TARGET_GOAL_OPTIONS: Select2Option[] = [
  { value: 'MIXTE', label: 'Mixte (Investissement & Habitation)' },
  { value: 'HABITATION', label: 'Résidence principale / Habitation' },
  { value: 'INVESTISSEMENT', label: 'Investissement locatif pur' },
  { value: 'LOCATION', label: 'Location simple' },
]

const STATUS_COMMERCIAL_OPTIONS: Select2Option[] = [
  { value: 'DISPONIBLE', label: 'Publié / Disponible' },
  { value: 'EN_ATTENTE', label: 'En attente de validation' },
  { value: 'BROUILLON', label: 'Brouillon interne' },
  { value: 'OPTION', label: 'Option posée' },
  { value: 'RESERVE', label: 'Réservé' },
  { value: 'VENDU', label: 'Vendu' },
]

const VERIFICATION_OPTIONS: Select2Option[] = [
  { value: 'VERIFIE', label: 'Bien vérifié (Documents certifiés)' },
  { value: 'VERIFICATION_RENFORCEE', label: 'Vérification renforcée (ACD / Titre validé)' },
  { value: 'EN_ATTENTE', label: 'En cours d\'instruction foncière' },
  { value: 'NON_VERIFIE', label: 'Non vérifié' },
]

const COMMUNE_OPTIONS: Select2Option[] = [
  { value: 'Cocody', label: 'Cocody' },
  { value: 'Bingerville', label: 'Bingerville' },
  { value: 'Marcory', label: 'Marcory' },
  { value: 'Grand-Bassam', label: 'Grand-Bassam' },
  { value: 'Yamoussoukro', label: 'Yamoussoukro' },
  { value: 'Plateau', label: 'Plateau' },
  { value: 'Port-Bouët', label: 'Port-Bouët' },
  { value: 'Assinie', label: 'Assinie' },
]

export function PropertyAddModal({ isOpen, onClose }: PropertyAddModalProps) {
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState<'general' | 'finances' | 'location' | 'features' | 'media'>('general')

  const [formData, setFormData] = useState({
    title: '',
    reference: '',
    property_type: 'APPARTEMENT',
    typology: 'F3',
    target_goal: 'MIXTE',
    status: 'DISPONIBLE',
    verification_status: 'VERIFIE',
    description: '',

    price: '',
    recommended_down_payment: '',
    estimated_monthly_rent: '',
    estimated_yield_rate: '',
    investment_score: 80,

    city: 'Abidjan',
    commune: 'Cocody',
    neighborhood: '',
    address: '',
    latitude: '',
    longitude: '',

    surface_sqm: '85',
    rooms_count: 3,
    bedrooms_count: 2,
    bathrooms_count: 2,
    has_parking: true,
    has_swimming_pool: false,
    has_elevator: false,
    has_security: true,
    has_generator: false,
    has_green_space: false,

    video_url: '',
    virtual_tour_url: '',
    is_featured: false,
    is_selected_investment: false,
  })

  const createMutation = useMutation({
    mutationFn: (newProp: any) =>
      fetchApi('/properties/search/', {
        method: 'POST',
        body: JSON.stringify(newProp),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['properties-list'] })
      queryClient.invalidateQueries({ queryKey: ['properties-dashboard'] })
      onClose()
      setActiveTab('general')
    },
    onError: (err: any) => {
      alert(`Erreur lors de la création : ${err.message}`)
    },
  })

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault()
    createMutation.mutate(formData)
  }

  const tabList = [
    { id: 'general', step: '01', title: 'Général', subtitle: 'Mandat & Types', icon: Building2 },
    { id: 'finances', step: '02', title: 'Finances', subtitle: 'Prix & Rentabilité', icon: DollarSign },
    { id: 'location', step: '03', title: 'Localisation', subtitle: 'Commune & GPS', icon: MapPin },
    { id: 'features', step: '04', title: 'Spécifications', subtitle: 'Surfaces & Confort', icon: Layers },
    { id: 'media', step: '05', title: 'Médias', subtitle: '3D & Marketing', icon: Sparkles },
  ] as const

  const currentIndex = tabList.findIndex((t) => t.id === activeTab)

  const handleNext = () => {
    if (currentIndex < tabList.length - 1) {
      setActiveTab(tabList[currentIndex + 1].id)
    }
  }

  const handlePrev = () => {
    if (currentIndex > 0) {
      setActiveTab(tabList[currentIndex - 1].id)
    }
  }

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Ajouter un Bien Immobilier au Catalogue"
      description="Renseignez l'intégralité des caractéristiques foncières, juridiques et financières du bien."
      size="2xl"
      footer={
        <div className="flex items-center justify-between w-full">
          <div className="flex items-center gap-2">
            {currentIndex > 0 && (
              <button
                type="button"
                onClick={handlePrev}
                className="px-4 py-2 text-xs font-bold rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-50 transition-colors flex items-center gap-1.5 cursor-pointer"
              >
                <ArrowLeft className="w-3.5 h-3.5" />
                <span>Précédent</span>
              </button>
            )}
            {currentIndex < tabList.length - 1 && (
              <button
                type="button"
                onClick={handleNext}
                className="px-4 py-2 text-xs font-bold rounded-xl border border-blue-200 dark:border-blue-800 bg-blue-50 dark:bg-blue-950/40 text-blue-600 dark:text-blue-300 hover:bg-blue-100 transition-colors flex items-center gap-1.5 cursor-pointer"
              >
                <span>Étape suivante</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            )}
          </div>

          <ModalFooterButtons
            onCancel={onClose}
            onConfirm={handleSubmit}
            confirmText="Publier l'annonce définitive"
            isLoading={createMutation.isPending}
          />
        </div>
      }
    >
      <div className="space-y-6">
        {/* NOUVEAU STYLE D'ONGLETS PREMIUM ET ÉLÉGANT (Segmented Navigation Bar) */}
        <div className="w-full bg-slate-100/90 dark:bg-slate-800/80 p-1.5 rounded-2xl border border-slate-200/80 dark:border-slate-700/80 shadow-2xs">
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-1.5 w-full">
            {tabList.map((tab) => {
              const Icon = tab.icon
              const isActive = activeTab === tab.id
              return (
                <button
                  key={tab.id}
                  type="button"
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-2.5 p-2 rounded-xl transition-all cursor-pointer text-left select-none ${
                    isActive
                      ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-white shadow-md shadow-slate-200/60 dark:shadow-none border border-slate-200/90 dark:border-slate-700'
                      : 'text-slate-500 hover:text-slate-900 dark:hover:text-slate-200 hover:bg-white/50 dark:hover:bg-slate-700/50'
                  }`}
                >
                  <div
                    className={`w-7 h-7 rounded-lg flex items-center justify-center shrink-0 font-black text-[11px] transition-colors ${
                      isActive
                        ? 'bg-blue-600 text-white shadow-xs shadow-blue-500/30'
                        : 'bg-slate-200 dark:bg-slate-700 text-slate-600 dark:text-slate-300'
                    }`}
                  >
                    {tab.step}
                  </div>
                  <div className="min-w-0">
                    <div className={`text-xs font-black truncate leading-tight ${isActive ? 'text-blue-600 dark:text-blue-400' : ''}`}>
                      {tab.title}
                    </div>
                    <div className="text-[10px] text-slate-400 truncate hidden lg:block">
                      {tab.subtitle}
                    </div>
                  </div>
                </button>
              )
            })}
          </div>
        </div>

        {/* CONTENU DES ÉTAPES */}
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* ONGLET 1 : GÉNÉRAL */}
          {activeTab === 'general' && (
            <div className="space-y-4 animate-fade-in">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="sm:col-span-2">
                  <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                    Titre de l'annonce *
                  </label>
                  <input
                    type="text"
                    placeholder="Ex: Villa Duplex Contemporaine 5P avec Piscine à Débordement"
                    value={formData.title}
                    onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                    className="w-full px-3.5 py-2.5 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:border-blue-500 focus:outline-hidden font-medium"
                    required
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                    Référence Unique Mandat *
                  </label>
                  <input
                    type="text"
                    placeholder="Ex: THI-2026-009"
                    value={formData.reference}
                    onChange={(e) => setFormData({ ...formData, reference: e.target.value })}
                    className="w-full px-3.5 py-2.5 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white font-mono focus:border-blue-500 focus:outline-hidden font-bold"
                    required
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <Select2
                  label="Type de Bien *"
                  options={PROPERTY_TYPE_OPTIONS}
                  value={formData.property_type}
                  onChange={(val) => setFormData({ ...formData, property_type: val })}
                  isClearable={false}
                />

                <Select2
                  label="Typologie *"
                  options={TYPOLOGY_OPTIONS}
                  value={formData.typology}
                  onChange={(val) => setFormData({ ...formData, typology: val })}
                  isClearable={false}
                />

                <Select2
                  label="Objectif Cible"
                  options={TARGET_GOAL_OPTIONS}
                  value={formData.target_goal}
                  onChange={(val) => setFormData({ ...formData, target_goal: val })}
                  isClearable={false}
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Select2
                  label="Statut Commercial *"
                  options={STATUS_COMMERCIAL_OPTIONS}
                  value={formData.status}
                  onChange={(val) => setFormData({ ...formData, status: val })}
                  isClearable={false}
                />

                <Select2
                  label="Badge de Vérification Juridique *"
                  options={VERIFICATION_OPTIONS}
                  value={formData.verification_status}
                  onChange={(val) => setFormData({ ...formData, verification_status: val })}
                  isClearable={false}
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                  Description détaillée du mandat
                </label>
                <textarea
                  rows={4}
                  placeholder="Décrivez les finitions, la hauteur sous plafond, l'ensoleillement, la vue dégagée, la proximité des commodités..."
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="w-full px-3.5 py-2.5 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:border-blue-500 focus:outline-hidden"
                />
              </div>
            </div>
          )}

          {/* ONGLET 2 : FINANCES */}
          {activeTab === 'finances' && (
            <div className="space-y-4 animate-fade-in">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="p-4 rounded-2xl bg-emerald-50/50 dark:bg-emerald-950/20 border border-emerald-200/80 dark:border-emerald-900/40 space-y-2">
                  <label className="block text-xs font-bold text-emerald-900 dark:text-emerald-300">
                    Prix de Vente Net Vendeur (FCFA) *
                  </label>
                  <input
                    type="number"
                    placeholder="Ex: 85000000"
                    value={formData.price}
                    onChange={(e) => setFormData({ ...formData, price: e.target.value })}
                    className="w-full px-3.5 py-2.5 text-sm rounded-xl border border-emerald-300 dark:border-emerald-700 bg-white dark:bg-slate-900 text-emerald-700 dark:text-emerald-300 focus:border-emerald-500 focus:outline-hidden font-mono font-black"
                    required
                  />
                  <span className="text-[11px] text-emerald-600 dark:text-emerald-400 block">
                    Montant net affiché sur les fiches de commercialisation.
                  </span>
                </div>

                <div className="p-4 rounded-2xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700 space-y-2">
                  <label className="block text-xs font-bold text-slate-700 dark:text-slate-300">
                    Apport Recommandé Suggéré (FCFA)
                  </label>
                  <input
                    type="number"
                    placeholder="Ex: 17000000"
                    value={formData.recommended_down_payment}
                    onChange={(e) => setFormData({ ...formData, recommended_down_payment: e.target.value })}
                    className="w-full px-3.5 py-2.5 text-sm rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:border-blue-500 focus:outline-hidden font-mono font-bold"
                  />
                  <span className="text-[11px] text-slate-500 block">
                    Base de calcul pour le simulateur de crédit bancaire.
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                    Loyer Estimatif Mensuel (FCFA)
                  </label>
                  <input
                    type="number"
                    placeholder="Ex: 600000"
                    value={formData.estimated_monthly_rent}
                    onChange={(e) => {
                      const rent = parseFloat(e.target.value) || 0
                      const price = parseFloat(formData.price) || 0
                      const yieldRate = price > 0 ? ((rent * 12) / price * 100).toFixed(2) : ''
                      setFormData({
                        ...formData,
                        estimated_monthly_rent: e.target.value,
                        estimated_yield_rate: yieldRate,
                      })
                    }}
                    className="w-full px-3.5 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:border-blue-500 focus:outline-hidden font-mono font-semibold"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                    Rentabilité Brute Calculée (%)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    placeholder="Ex: 8.47"
                    value={formData.estimated_yield_rate}
                    onChange={(e) => setFormData({ ...formData, estimated_yield_rate: e.target.value })}
                    className="w-full px-3.5 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:border-blue-500 focus:outline-hidden font-mono font-bold text-indigo-600"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                    Score Attractivité IA (0 - 100)
                  </label>
                  <input
                    type="number"
                    min="0"
                    max="100"
                    value={formData.investment_score}
                    onChange={(e) => setFormData({ ...formData, investment_score: parseInt(e.target.value) || 75 })}
                    className="w-full px-3.5 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:border-blue-500 focus:outline-hidden font-bold text-amber-600"
                  />
                </div>
              </div>
            </div>
          )}

          {/* ONGLET 3 : LOCALISATION */}
          {activeTab === 'location' && (
            <div className="space-y-4 animate-fade-in">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                    Ville / Métropole *
                  </label>
                  <input
                    type="text"
                    value={formData.city}
                    onChange={(e) => setFormData({ ...formData, city: e.target.value })}
                    className="w-full px-3.5 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:border-blue-500 focus:outline-hidden"
                    required
                  />
                </div>

                <Select2
                  label="Commune *"
                  options={COMMUNE_OPTIONS}
                  value={formData.commune}
                  onChange={(val) => setFormData({ ...formData, commune: val })}
                  isClearable={false}
                />

                <div>
                  <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                    Quartier / Cité *
                  </label>
                  <input
                    type="text"
                    placeholder="Ex: Abatta Nouveau Goudron, Angré 8e Tranche..."
                    value={formData.neighborhood}
                    onChange={(e) => setFormData({ ...formData, neighborhood: e.target.value })}
                    className="w-full px-3.5 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:border-blue-500 focus:outline-hidden"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                  Adresse précise & Repères d'accès
                </label>
                <input
                  type="text"
                  placeholder="Ex: Voie principale face Pharmacie de la Riviera, Ilot 44 Lot 12"
                  value={formData.address}
                  onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                  className="w-full px-3.5 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:border-blue-500 focus:outline-hidden"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                    Latitude GPS (optionnel)
                  </label>
                  <input
                    type="text"
                    placeholder="Ex: 5.360155"
                    value={formData.latitude}
                    onChange={(e) => setFormData({ ...formData, latitude: e.target.value })}
                    className="w-full px-3.5 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white font-mono focus:border-blue-500 focus:outline-hidden"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                    Longitude GPS (optionnel)
                  </label>
                  <input
                    type="text"
                    placeholder="Ex: -3.953215"
                    value={formData.longitude}
                    onChange={(e) => setFormData({ ...formData, longitude: e.target.value })}
                    className="w-full px-3.5 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white font-mono focus:border-blue-500 focus:outline-hidden"
                  />
                </div>
              </div>
            </div>
          )}

          {/* ONGLET 4 : SPÉCIFICATIONS PHYSIQUES & COMMODITÉS */}
          {activeTab === 'features' && (
            <div className="space-y-4 animate-fade-in">
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
                  <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                    Superficie Utile (m²) *
                  </label>
                  <input
                    type="number"
                    value={formData.surface_sqm}
                    onChange={(e) => setFormData({ ...formData, surface_sqm: e.target.value })}
                    className="w-full px-3 py-1.5 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:border-blue-500 focus:outline-hidden font-bold"
                    required
                  />
                </div>

                <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
                  <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                    Nombre de Pièces
                  </label>
                  <input
                    type="number"
                    value={formData.rooms_count}
                    onChange={(e) => setFormData({ ...formData, rooms_count: parseInt(e.target.value) || 1 })}
                    className="w-full px-3 py-1.5 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:border-blue-500 focus:outline-hidden font-bold"
                  />
                </div>

                <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
                  <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                    Chambres
                  </label>
                  <input
                    type="number"
                    value={formData.bedrooms_count}
                    onChange={(e) => setFormData({ ...formData, bedrooms_count: parseInt(e.target.value) || 1 })}
                    className="w-full px-3 py-1.5 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:border-blue-500 focus:outline-hidden font-bold"
                  />
                </div>

                <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
                  <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                    Salles d'eau / Bain
                  </label>
                  <input
                    type="number"
                    value={formData.bathrooms_count}
                    onChange={(e) => setFormData({ ...formData, bathrooms_count: parseInt(e.target.value) || 1 })}
                    className="w-full px-3 py-1.5 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:border-blue-500 focus:outline-hidden font-bold"
                  />
                </div>
              </div>

              {/* Commodités */}
              <div className="pt-2">
                <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-2">
                  Équipements & Prestations Certifiées
                </label>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                  {[
                    { key: 'has_parking', label: '🚗 Parking sécurisé' },
                    { key: 'has_swimming_pool', label: '🏊 Piscine' },
                    { key: 'has_elevator', label: '🛗 Ascenseur' },
                    { key: 'has_security', label: '🛡️ Sécurité 24/7' },
                    { key: 'has_generator', label: '⚡ Groupe électrogène' },
                    { key: 'has_green_space', label: '🌳 Espace vert / Jardin' },
                  ].map((item) => (
                    <label
                      key={item.key}
                      className="flex items-center gap-2.5 p-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/60 hover:bg-white dark:hover:bg-slate-800 cursor-pointer transition-all shadow-2xs"
                    >
                      <input
                        type="checkbox"
                        checked={(formData as any)[item.key]}
                        onChange={(e) => setFormData({ ...formData, [item.key]: e.target.checked })}
                        className="rounded text-blue-600 focus:ring-blue-500 h-4 w-4"
                      />
                      <span className="text-xs font-semibold text-slate-800 dark:text-slate-200">
                        {item.label}
                      </span>
                    </label>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* ONGLET 5 : MÉDIAS & MARKETING */}
          {activeTab === 'media' && (
            <div className="space-y-4 animate-fade-in">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1 flex items-center gap-1.5">
                    <Video className="w-3.5 h-3.5 text-blue-500" />
                    Lien Vidéo / Drone (YouTube / Vimeo)
                  </label>
                  <input
                    type="url"
                    placeholder="https://youtu.be/..."
                    value={formData.video_url}
                    onChange={(e) => setFormData({ ...formData, video_url: e.target.value })}
                    className="w-full px-3.5 py-2.5 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:border-blue-500 focus:outline-hidden"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1 flex items-center gap-1.5">
                    <Sparkles className="w-3.5 h-3.5 text-indigo-500" />
                    Lien Visite Virtuelle 3D (Matterport)
                  </label>
                  <input
                    type="url"
                    placeholder="https://my.matterport.com/show/?m=..."
                    value={formData.virtual_tour_url}
                    onChange={(e) => setFormData({ ...formData, virtual_tour_url: e.target.value })}
                    className="w-full px-3.5 py-2.5 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:border-blue-500 focus:outline-hidden"
                  />
                </div>
              </div>

              <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 space-y-3">
                <div className="text-xs font-bold uppercase tracking-wider text-slate-500">
                  Visibilité Mobile & Web THIEBBRO IMMO
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <label className="flex items-center gap-2.5 p-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 cursor-pointer shadow-2xs">
                    <input
                      type="checkbox"
                      checked={formData.is_featured}
                      onChange={(e) => setFormData({ ...formData, is_featured: e.target.checked })}
                      className="rounded text-blue-600 focus:ring-blue-500 h-4 w-4"
                    />
                    <div>
                      <div className="text-xs font-bold text-slate-900 dark:text-white">
                        ⭐ Opportunité du Moment
                      </div>
                      <div className="text-[10px] text-slate-400">
                        Mise en avant sur l'écran d'accueil de l'application
                      </div>
                    </div>
                  </label>

                  <label className="flex items-center gap-2.5 p-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 cursor-pointer shadow-2xs">
                    <input
                      type="checkbox"
                      checked={formData.is_selected_investment}
                      onChange={(e) => setFormData({ ...formData, is_selected_investment: e.target.checked })}
                      className="rounded text-blue-600 focus:ring-blue-500 h-4 w-4"
                    />
                    <div>
                      <div className="text-xs font-bold text-slate-900 dark:text-white">
                        📈 Sélection Espace Investir
                      </div>
                      <div className="text-[10px] text-slate-400">
                        Destiné aux investisseurs de la diaspora (rentabilité élevée)
                      </div>
                    </div>
                  </label>
                </div>
              </div>
            </div>
          )}
        </form>
      </div>
    </Modal>
  )
}
