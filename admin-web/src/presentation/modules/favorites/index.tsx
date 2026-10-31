import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Heart,
  Search,
  RotateCw,
  RotateCcw,
  Building,
  User,
  Calendar,
  Trash2
} from 'lucide-react'
import { fetchApi } from '@/lib/api'
import { formatFCFA } from '@/lib/utils'
import { TableHeaderCustom, TableCardWrapper } from '@/presentation/components/shared/ui/TableHeaderCustom'
import { Select2, Select2Option } from '@/presentation/components/shared/ui/Select2'
import { FavoriteDeleteModal } from './Delete'

export function FavoritesModule() {
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [communeFilter, setCommuneFilter] = useState('')
  const [selectedFavorite, setSelectedFavorite] = useState<any | null>(null)
  const [isDeleteOpen, setIsDeleteOpen] = useState(false)

  const { data: favoritesData, isLoading, refetch, isFetching } = useQuery({
    queryKey: ['admin-favorites'],
    queryFn: () => fetchApi<{ results: any[] }>('/properties/admin/favorites/'),
  })

  const favorites = favoritesData?.results || []

  // Extraction unique des communes pour le Select2
  const communeOptions: Select2Option[] = [
    { value: '', label: 'Toutes les communes' },
    ...Array.from(new Set(favorites.map((f: any) => f.property_commune).filter(Boolean))).map((com) => ({
      value: String(com),
      label: String(com),
    })),
  ]

  const filteredFavorites = favorites.filter((f: any) => {
    const matchCommune = !communeFilter || f.property_commune === communeFilter
    const matchSearch =
      !search ||
      f.user_email?.toLowerCase().includes(search.toLowerCase()) ||
      f.user_name?.toLowerCase().includes(search.toLowerCase()) ||
      f.property_title?.toLowerCase().includes(search.toLowerCase()) ||
      f.property_reference?.toLowerCase().includes(search.toLowerCase())
    return matchCommune && matchSearch
  })

  const columns = [
    { key: 'id', label: 'ID', className: 'w-16' },
    { key: 'user', label: 'UTILISATEUR / CLIENT' },
    { key: 'prop_ref', label: 'RÉFÉRENCE DU BIEN', className: 'w-28' },
    { key: 'prop_title', label: 'BIEN IMMOBILIER' },
    { key: 'commune', label: 'COMMUNE' },
    { key: 'price', label: 'PRIX DU BIEN (FCFA)' },
    { key: 'date', label: 'DATE AJOUT FAVORI' },
    { key: 'actions', label: 'ACTIONS', className: 'text-right w-20' },
  ]

  const deleteMutation = useMutation({
    mutationFn: (favId: string) =>
      fetchApi(`/properties/admin/favorites/${favId}/`, {
        method: 'DELETE',
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-favorites'] })
      setIsDeleteOpen(false)
      setSelectedFavorite(null)
    },
    onError: (err: any) => {
      alert(`Erreur : ${err.message}`)
    },
  })

  return (
    <div className="w-full space-y-4 animate-fade-in">
      {/* 1. Barre d'action supérieure pleine largeur */}
      <div className="w-full flex flex-col lg:flex-row lg:items-center justify-between gap-4 bg-white dark:bg-slate-900 px-6 py-4 rounded-2xl border border-slate-200/90 dark:border-slate-800 shadow-2xs">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl sm:text-2xl font-black tracking-tight text-slate-900 dark:text-white flex items-center gap-2">
              Favoris Clients & Popularité des Biens
            </h1>
          {/*   <span className="px-2 py-0.5 rounded-full text-[10px] font-black bg-rose-100 text-rose-800 dark:bg-rose-950/70 dark:text-rose-300">
              Django Model PropertyFavorite
            </span> */}
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Suivez l'intérêt manifesté par les acheteurs particuliers et la diaspora sur le catalogue.
          </p>
        </div>

        <button
          type="button"
          onClick={() => refetch()}
          disabled={isFetching}
          className="px-3.5 py-2 text-xs font-semibold rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-200 hover:bg-slate-50 transition-colors flex items-center gap-1.5 cursor-pointer shadow-2xs self-start lg:self-auto"
        >
          <RotateCw className={`w-3.5 h-3.5 ${isFetching ? 'animate-spin text-blue-600' : ''}`} />
          <span>Actualiser</span>
        </button>
      </div>

      {/* 2. Barre de Filtres avec Select2 Pleine Largeur */}
      <div className="w-full p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-800 shadow-2xs space-y-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 w-full">
          <Select2
            label="Filtrer par Commune"
            placeholder="Toutes les communes"
            options={communeOptions}
            value={communeFilter}
            onChange={setCommuneFilter}
          />

          <div className="flex flex-col sm:col-span-2">
            <label className="text-[11px] font-bold text-slate-600 dark:text-slate-400 mb-1 tracking-wide">
              Recherche Client ou Titre du Bien
            </label>
            <div className="relative w-full">
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Rechercher par email client, référence mandat, titre..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full pl-9 pr-3 h-9.5 text-xs rounded-xl bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-700/80 focus:outline-hidden focus:border-blue-500 text-slate-900 dark:text-white"
              />
            </div>
          </div>
        </div>

        <div className="flex items-center justify-between pt-2 border-t border-slate-100 dark:border-slate-800">
          <div className="text-xs text-slate-500">
            Total favoris enregistrés : <strong>{filteredFavorites.length}</strong>
          </div>
          <button
            type="button"
            onClick={() => {
              setSearch('')
              setCommuneFilter('')
            }}
            className="px-3 py-1.5 text-xs font-semibold text-slate-500 hover:text-slate-900 dark:hover:text-white flex items-center gap-1.5 transition-colors cursor-pointer"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Réinitialiser les filtres</span>
          </button>
        </div>
      </div>

      {/* 3. Tableau Pleine Largeur */}
      <div className="w-full">
        <TableCardWrapper
          title="LISTE DES INTERACTIONS FAVORIS"
          count={`${filteredFavorites.length} FAVORIS`}
          icon={<Heart className="w-4 h-4 text-rose-500 fill-rose-500" />}
        >
          <TableHeaderCustom columns={columns} />
          <tbody className="divide-y divide-slate-100 dark:divide-slate-800/80">
            {isLoading ? (
              <tr>
                <td colSpan={8} className="py-12 text-center text-slate-400 italic">
                  Chargement des favoris depuis PostgreSQL...
                </td>
              </tr>
            ) : filteredFavorites.length === 0 ? (
              <tr>
                <td colSpan={8} className="py-12 text-center text-slate-400 italic">
                  Aucun favori enregistré pour ce critère.
                </td>
              </tr>
            ) : (
              filteredFavorites.map((fav: any, idx: number) => (
                <tr key={fav.id} className="hover:bg-blue-50/40 dark:hover:bg-slate-800/50 transition-colors">
                  <td className="py-3 px-4 font-mono text-[11px] text-slate-400">
                    #{String(idx + 1).padStart(3, '0')}
                  </td>

                  <td className="py-3 px-4">
                    <div className="font-bold text-xs text-slate-900 dark:text-white">
                      {fav.user_name || 'Utilisateur'}
                    </div>
                    <div className="text-[11px] text-slate-500 font-mono">
                      {fav.user_email}
                    </div>
                  </td>

                  <td className="py-3 px-4 font-mono font-black text-xs text-blue-600 dark:text-blue-400 whitespace-nowrap">
                    {fav.property_reference}
                  </td>

                  <td className="py-3 px-4">
                    <div className="font-bold text-xs uppercase text-slate-900 dark:text-white">
                      {fav.property_title}
                    </div>
                  </td>

                  <td className="py-3 px-4 text-xs font-semibold text-slate-700 dark:text-slate-300 whitespace-nowrap">
                    {fav.property_commune}
                  </td>

                  <td className="py-3 px-4 font-black text-xs text-emerald-600 dark:text-emerald-400 whitespace-nowrap">
                    {formatFCFA(fav.property_price)}
                  </td>

                  <td className="py-3 px-4 text-[11px] text-slate-500 whitespace-nowrap">
                    {new Date(fav.created_at).toLocaleDateString('fr-FR')}
                  </td>

                  <td className="py-3 px-4 text-right whitespace-nowrap">
                    <button
                      type="button"
                      onClick={() => {
                        setSelectedFavorite(fav)
                        setIsDeleteOpen(true)
                      }}
                      className="p-1.5 rounded-lg text-slate-400 hover:text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/40 transition-colors cursor-pointer"
                      title="Supprimer ce favori"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </TableCardWrapper>
      </div>

      <FavoriteDeleteModal
        favorite={selectedFavorite}
        isOpen={isDeleteOpen}
        onClose={() => {
          setIsDeleteOpen(false)
          setSelectedFavorite(null)
        }}
        onConfirm={() => selectedFavorite && deleteMutation.mutate(selectedFavorite.id)}
        isLoading={deleteMutation.isPending}
      />
    </div>
  )
}
