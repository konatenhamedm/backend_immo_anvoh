import React, { useState } from 'react'
import {
  LayoutDashboard,
  Building2,
  FolderKanban,
  Calculator,
  ChevronRight,
  ChevronLeft,
  Home,
  Calendar,
  Users,
  Heart,
  MessageSquare
} from 'lucide-react'
import { Link } from '@tanstack/react-router'
import { Logo } from './shared/ui/Logo'

export const Sidebar: React.FC = () => {
  const [collapsed, setCollapsed] = useState(false)

  const modulesPrincipaux = [
    { label: 'Tableau de Bord', to: '/', icon: LayoutDashboard },
    { label: 'Catalogue Biens', to: '/properties', icon: Home },
    { label: 'Programmes Neufs', to: '/projects', icon: Building2 },
    { label: 'Favoris Clients', to: '/favorites', icon: Heart, badge: 'Popularité' },
  ]

  const modulesCommercial = [
    { label: 'Pipeline CRM (Kanban)', to: '/crm', icon: FolderKanban },
    { label: 'Demandes d\'Infos', to: '/inquiries', icon: MessageSquare },
    { label: 'Rendez-vous & Visites', to: '/visits', icon: Calendar },
  ]

  const modulesGestion = [
    { label: 'Simulateurs Prêt & Renta', to: '/simulators', icon: Calculator },
    { label: 'Utilisateurs & Équipe', to: '/users', icon: Users },
  ]

  return (
    <aside
      className={`relative h-screen flex flex-col border-r transition-all duration-300 z-30 select-none ${
        collapsed ? 'w-20' : 'w-72'
      } bg-[#091931] border-[#132744] text-white`}
    >
      {/* 1. Header Logo THIEBBRO IMMO */}
      <div className="h-16 flex items-center justify-between px-4 border-b border-[#132744]">
        <Link to="/" className="flex items-center group overflow-hidden">
          <Logo variant={collapsed ? 'icon' : 'full'} size="md" />
        </Link>
      </div>

      {/* 2. Navigation Complète par Sections */}
      <nav className="flex-1 overflow-y-auto px-3 py-3 space-y-4">
        {/* SECTION 1 : MODULES PRINCIPAUX */}
        <div>
          <div className="px-3 py-1 text-[10px] font-bold uppercase tracking-wider text-white/80">
            {!collapsed ? 'CATALOGUE & PROGRAMMES' : '•••'}
          </div>
          <div className="space-y-0.5 mt-1">
            {modulesPrincipaux.map((item) => {
              const Icon = item.icon
              return (
                <Link
                  key={item.to}
                  to={item.to}
                  activeProps={{
                    className:
                      'bg-blue-600/30 text-white font-bold border-l-4 border-blue-400 shadow-xs',
                  }}
                  inactiveProps={{
                    className:
                      'text-white font-medium hover:bg-[#12284b] hover:text-white',
                  }}
                  className="flex items-center justify-between px-3 py-2.5 rounded-xl transition-all text-xs group cursor-pointer"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <Icon className="w-4 h-4 text-cyan-400 shrink-0 group-hover:scale-110 transition-transform" />
                    {!collapsed && <span className="truncate text-white">{item.label}</span>}
                  </div>
                  {!collapsed && (
                    <div className="flex items-center gap-1.5">
                      {item.badge && (
                        <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-rose-500/20 text-rose-300 border border-rose-500/30">
                          {item.badge}
                        </span>
                      )}
                      <ChevronRight className="w-3.5 h-3.5 text-white/60 group-hover:text-white transition-colors" />
                    </div>
                  )}
                </Link>
              )
            })}
          </div>
        </div>

        {/* SECTION 2 : COMMERCIAL & CRM */}
        <div>
          <div className="px-3 py-1 text-[10px] font-bold uppercase tracking-wider text-white/80">
            {!collapsed ? 'COMMERCIAL & CRM' : '•••'}
          </div>
          <div className="space-y-0.5 mt-1">
            {modulesCommercial.map((item) => {
              const Icon = item.icon
              return (
                <Link
                  key={item.to}
                  to={item.to}
                  activeProps={{
                    className:
                      'bg-blue-600/30 text-white font-bold border-l-4 border-blue-400 shadow-xs',
                  }}
                  inactiveProps={{
                    className:
                      'text-white font-medium hover:bg-[#12284b] hover:text-white',
                  }}
                  className="flex items-center justify-between px-3 py-2.5 rounded-xl transition-all text-xs group cursor-pointer"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <Icon className="w-4 h-4 text-cyan-400 shrink-0 group-hover:scale-110 transition-transform" />
                    {!collapsed && <span className="truncate text-white">{item.label}</span>}
                  </div>
                  {!collapsed && (
                    <ChevronRight className="w-3.5 h-3.5 text-white/60 group-hover:text-white transition-colors" />
                  )}
                </Link>
              )
            })}
          </div>
        </div>

        {/* SECTION 3 : FINANCE & ADMINISTRATION */}
        <div>
          <div className="px-3 py-1 text-[10px] font-bold uppercase tracking-wider text-white/80">
            {!collapsed ? 'GESTION & OUTILS' : '•••'}
          </div>
          <div className="space-y-0.5 mt-1">
            {modulesGestion.map((item) => {
              const Icon = item.icon
              return (
                <Link
                  key={item.to}
                  to={item.to}
                  activeProps={{
                    className:
                      'bg-blue-600/30 text-white font-bold border-l-4 border-blue-400 shadow-xs',
                  }}
                  inactiveProps={{
                    className:
                      'text-white font-medium hover:bg-[#12284b] hover:text-white',
                  }}
                  className="flex items-center justify-between px-3 py-2.5 rounded-xl transition-all text-xs group cursor-pointer"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <Icon className="w-4 h-4 text-cyan-400 shrink-0 group-hover:scale-110 transition-transform" />
                    {!collapsed && <span className="truncate text-white">{item.label}</span>}
                  </div>
                  {!collapsed && (
                    <ChevronRight className="w-3.5 h-3.5 text-white/60 group-hover:text-white transition-colors" />
                  )}
                </Link>
              )
            })}
          </div>
        </div>
      </nav>

      {/* 4. Footer avec Statut SaaS & Bouton Toggle */}
      <div className="p-3.5 border-t border-[#132744] flex items-center justify-between">
        {!collapsed ? (
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            <span className="text-[11px] font-semibold text-white">
              Thiebbro v1.0 • SaaS
            </span>
          </div>
        ) : (
          <span className="w-2 h-2 rounded-full bg-emerald-400 mx-auto"></span>
        )}

        <button
          onClick={() => setCollapsed(!collapsed)}
          className="p-1.5 rounded-lg bg-[#0f2343] hover:bg-[#16315c] text-white transition-colors cursor-pointer"
          title={collapsed ? 'Agrandir la barre' : 'Réduire la barre'}
        >
          {collapsed ? (
            <ChevronRight className="w-4 h-4" />
          ) : (
            <ChevronLeft className="w-4 h-4" />
          )}
        </button>
      </div>
    </aside>
  )
}
