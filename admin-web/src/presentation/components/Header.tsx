import React, { useState, useEffect } from 'react'
import {
  Bell,
  Moon,
  Sun,
  ShieldCheck,
  Calendar
} from 'lucide-react'

export const Header: React.FC = () => {
  const [isDark, setIsDark] = useState(false)

  useEffect(() => {
    if (isDark) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }, [isDark])

  // Date du jour formatée en français
  const todayFormatted = new Intl.DateTimeFormat('fr-FR', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
    year: 'numeric'
  }).format(new Date())

  return (
    <header className="h-16 w-full border-b bg-white dark:bg-slate-900 border-slate-200/90 dark:border-slate-800 px-6 flex items-center justify-between sticky top-0 z-20 shadow-2xs">
      {/* 1. Contexte & Date épurés (remplace les filtres redondants) */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 text-xs font-semibold text-slate-700 dark:text-slate-300">
          <Calendar className="w-4 h-4 text-blue-600 dark:text-blue-400" />
          <span className="capitalize">{todayFormatted}</span>
        </div>
        <div className="hidden sm:flex items-center gap-2 pl-3 border-l border-slate-200 dark:border-slate-800">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
          <span className="text-[11px] font-medium text-slate-500 dark:text-slate-400">
            Espace Direction & Gestion Immobilière
          </span>
        </div>
      </div>

      {/* 2. Actions & Profil Administrateur */}
      <div className="flex items-center gap-3">
        {/* Toggle Dark/Light */}
        <button
          onClick={() => setIsDark(!isDark)}
          className="p-2 text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors cursor-pointer"
          title="Changer de thème"
        >
          {isDark ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
        </button>

        {/* Notifications */}
        <button className="relative p-2 text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors cursor-pointer">
          <Bell className="w-4 h-4" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-blue-600 rounded-full animate-pulse"></span>
        </button>

        <div className="h-5 w-px bg-slate-200 dark:border-slate-800 mx-1"></div>

        {/* Profil Utilisateur (Style ADMIN SUPER comme sur la capture) */}
        <div className="flex items-center gap-2.5 pl-1 cursor-pointer">
          <div className="w-9 h-9 rounded-full bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center text-white font-bold text-xs shadow-md shadow-blue-500/20 ring-2 ring-blue-100 dark:ring-blue-900">
            AS
          </div>
          <div className="flex flex-col text-left">
            <span className="text-xs font-black text-slate-900 dark:text-white leading-tight flex items-center gap-1">
              ADMIN SUPER
              <ShieldCheck className="w-3.5 h-3.5 text-blue-600" />
            </span>
            <span className="text-[10px] font-semibold text-emerald-600 dark:text-emerald-400 uppercase tracking-wider">
              ROLE_SUPER_ADMIN
            </span>
          </div>
        </div>
      </div>
    </header>
  )
}
