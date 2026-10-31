import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  Users,
  Search,
  Plus,
  RotateCw,
  RotateCcw,
  Mail,
  ShieldCheck,
  Globe
} from 'lucide-react'
import { fetchApi } from '@/lib/api'
import { TableHeaderCustom, TableCardWrapper } from '@/presentation/components/shared/ui/TableHeaderCustom'
import { TableRowActions } from '@/presentation/components/shared/ui/TableRowActions'
import { Select2, Select2Option } from '@/presentation/components/shared/ui/Select2'
import { UserAddModal } from './Add'
import { UserEditModal } from './Edit'
import { UserShowModal } from './Show'
import { UserDeleteModal } from './Delete'

const ROLE_OPTIONS: Select2Option[] = [
  { value: '', label: 'Tous les rôles d\'utilisateurs' },
  { value: 'AGENT', label: 'Conseillers Commerciaux (AGENT)' },
  { value: 'ADMIN', label: 'Administrateurs (ADMIN)' },
  { value: 'INVESTISSEUR', label: 'Investisseurs Diaspora / Privés' },
  { value: 'PARTICULIER', label: 'Acheteurs Particuliers' },
]

export function UsersModule() {
  const [roleFilter, setRoleFilter] = useState('')
  const [search, setSearch] = useState('')

  const [isAddOpen, setIsAddOpen] = useState(false)
  const [isEditOpen, setIsEditOpen] = useState(false)
  const [isShowOpen, setIsShowOpen] = useState(false)
  const [isDeleteOpen, setIsDeleteOpen] = useState(false)
  const [selectedUser, setSelectedUser] = useState<any | null>(null)

  const { data: usersData, isLoading, refetch, isFetching } = useQuery({
    queryKey: ['admin-users'],
    queryFn: () => fetchApi<{ results: any[] }>('/auth/users/'),
  })

  const users = usersData?.results || []
  const filteredUsers = users.filter((u: any) => {
    const matchRole = !roleFilter || u.role === roleFilter
    const matchSearch =
      !search ||
      u.email?.toLowerCase().includes(search.toLowerCase()) ||
      `${u.first_name} ${u.last_name}`.toLowerCase().includes(search.toLowerCase()) ||
      u.phone_number?.includes(search)
    return matchRole && matchSearch
  })

  const columns = [
    { key: 'id', label: 'ID', className: 'w-16' },
    { key: 'user', label: 'COLLABORATEUR & IDENTIFIANT' },
    { key: 'phone', label: 'TÉLÉPHONE' },
    { key: 'role', label: 'RÔLE / HABILITATION' },
    { key: 'residence', label: 'PAYS / LOCALISATION' },
    { key: 'date', label: 'DATE CRÉATION' },
    { key: 'actions', label: 'ACTIONS', className: 'text-right w-28' },
  ]

  const handleResetFilters = () => {
    setRoleFilter('')
    setSearch('')
  }

  const handleOpenShow = (u: any) => {
    setSelectedUser(u)
    setIsShowOpen(true)
  }

  const handleOpenEdit = (u: any) => {
    setSelectedUser(u)
    setIsEditOpen(true)
  }

  const handleOpenDelete = (u: any) => {
    setSelectedUser(u)
    setIsDeleteOpen(true)
  }

  return (
    <div className="w-full space-y-4 animate-fade-in">
      {/* 1. Barre d'action supérieure pleine largeur */}
      <div className="w-full flex flex-col lg:flex-row lg:items-center justify-between gap-4 bg-white dark:bg-slate-900 px-6 py-4 rounded-2xl border border-slate-200/90 dark:border-slate-800 shadow-2xs">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl sm:text-2xl font-black tracking-tight text-slate-900 dark:text-white">
              Gestion des Utilisateurs & Conseillers
            </h1>
            <span className="px-2 py-0.5 rounded-full text-[10px] font-black bg-blue-100 text-blue-800 dark:bg-blue-950/70 dark:text-blue-300">
              Django Auth DB
            </span>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Supervisez les conseillers commerciaux THIEBBRO, investisseurs de la diaspora et administrateurs.
          </p>
        </div>

        <div className="flex items-center flex-wrap gap-2.5">
          <button
            type="button"
            onClick={() => refetch()}
            disabled={isFetching}
            className="px-3.5 py-2 text-xs font-semibold rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-200 hover:bg-slate-50 transition-colors flex items-center gap-1.5 cursor-pointer shadow-2xs"
          >
            <RotateCw className={`w-3.5 h-3.5 ${isFetching ? 'animate-spin text-blue-600' : ''}`} />
            <span>Actualiser</span>
          </button>

          <button
            type="button"
            onClick={() => setIsAddOpen(true)}
            className="px-4 py-2 text-xs font-bold rounded-xl bg-blue-600 hover:bg-blue-700 text-white shadow-md shadow-blue-600/25 transition-all flex items-center gap-2 cursor-pointer"
          >
            <Plus className="w-4 h-4" />
            <span>Nouveau Compte</span>
          </button>
        </div>
      </div>

      {/* 2. Barre de Filtres avec Sélecteur Select2 Pleine Largeur */}
      <div className="w-full p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-800 shadow-2xs space-y-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 w-full">
          <Select2
            label="Habilitation / Rôle"
            placeholder="Tous les rôles"
            options={ROLE_OPTIONS}
            value={roleFilter}
            onChange={setRoleFilter}
          />

          <div className="flex flex-col sm:col-span-2">
            <label className="text-[11px] font-bold text-slate-600 dark:text-slate-400 mb-1 tracking-wide">
              Recherche Collaborateur ou Email
            </label>
            <div className="relative w-full">
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Rechercher par nom, prénom, email, téléphone..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full pl-9 pr-3 h-9.5 text-xs rounded-xl bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-700/80 focus:outline-hidden focus:border-blue-500 text-slate-900 dark:text-white"
              />
            </div>
          </div>
        </div>

        <div className="flex items-center justify-between pt-2 border-t border-slate-100 dark:border-slate-800">
          <div className="text-xs text-slate-500">
            Total affiché : <strong>{filteredUsers.length}</strong> compte(s) actif(s)
          </div>
          <button
            type="button"
            onClick={handleResetFilters}
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
          title="LISTE DES COMPTES UTILISATEURS"
          count={`${filteredUsers.length} COMPTES`}
          icon={<Users className="w-4 h-4" />}
        >
          <TableHeaderCustom columns={columns} />
          <tbody className="divide-y divide-slate-100 dark:divide-slate-800/80">
            {isLoading ? (
              <tr>
                <td colSpan={7} className="py-12 text-center text-slate-400 italic">
                  Chargement des comptes depuis PostgreSQL...
                </td>
              </tr>
            ) : filteredUsers.length === 0 ? (
              <tr>
                <td colSpan={7} className="py-12 text-center text-slate-400 italic">
                  Aucun compte ne correspond à ces critères.
                </td>
              </tr>
            ) : (
              filteredUsers.map((u: any, idx: number) => (
                <tr
                  key={u.id}
                  onClick={() => handleOpenShow(u)}
                  className="hover:bg-blue-50/40 dark:hover:bg-slate-800/50 transition-colors cursor-pointer group"
                >
                  <td className="py-3 px-4 font-mono text-[11px] text-slate-400">
                    #{String(idx + 1).padStart(3, '0')}
                  </td>

                  <td className="py-3 px-4">
                    <div className="font-bold text-xs uppercase text-slate-900 dark:text-white group-hover:text-blue-600 transition-colors">
                      {u.first_name} {u.last_name}
                    </div>
                    <div className="text-[11px] text-slate-500 font-mono flex items-center gap-1.5 mt-0.5">
                      <Mail className="w-3 h-3 text-slate-400" />
                      {u.email}
                    </div>
                  </td>

                  <td className="py-3 px-4 text-xs font-mono font-medium text-slate-600 dark:text-slate-300 whitespace-nowrap">
                    {u.phone_number || '—'}
                  </td>

                  <td className="py-3 px-4 whitespace-nowrap">
                    <span
                      className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold ${
                        u.role === 'ADMIN'
                          ? 'bg-purple-100 text-purple-800 dark:bg-purple-950 dark:text-purple-300'
                          : u.role === 'AGENT'
                          ? 'bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300'
                          : 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300'
                      }`}
                    >
                      <ShieldCheck className="w-3 h-3" />
                      {u.role}
                    </span>
                  </td>

                  <td className="py-3 px-4 text-xs whitespace-nowrap">
                    <div className="flex items-center gap-1.5 text-slate-700 dark:text-slate-300">
                      <Globe className="w-3.5 h-3.5 text-blue-500" />
                      {u.residence_country || 'Côte d’Ivoire'}
                    </div>
                    {u.is_diaspora && (
                      <span className="text-[10px] text-indigo-600 font-bold">Diaspora</span>
                    )}
                  </td>

                  <td className="py-3 px-4 text-[11px] text-slate-500 whitespace-nowrap">
                    {u.created_at ? new Date(u.created_at).toLocaleDateString('fr-FR') : '—'}
                  </td>

                  <td className="py-3 px-4 text-right whitespace-nowrap">
                    <TableRowActions
                      onShow={() => handleOpenShow(u)}
                      onEdit={() => handleOpenEdit(u)}
                      onDelete={() => handleOpenDelete(u)}
                    />
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </TableCardWrapper>
      </div>

      {/* Modales Découplées */}
      <UserAddModal
        isOpen={isAddOpen}
        onClose={() => setIsAddOpen(false)}
      />

      <UserEditModal
        user={selectedUser}
        isOpen={isEditOpen}
        onClose={() => {
          setIsEditOpen(false)
          setSelectedUser(null)
        }}
      />

      <UserShowModal
        user={selectedUser}
        isOpen={isShowOpen}
        onClose={() => {
          setIsShowOpen(false)
          setSelectedUser(null)
        }}
        onEdit={(u) => {
          setSelectedUser(u)
          setIsEditOpen(true)
        }}
      />

      <UserDeleteModal
        user={selectedUser}
        isOpen={isDeleteOpen}
        onClose={() => {
          setIsDeleteOpen(false)
          setSelectedUser(null)
        }}
      />
    </div>
  )
}
