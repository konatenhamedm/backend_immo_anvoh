import React, { useEffect, useState } from 'react'
import { createRootRoute, Outlet } from '@tanstack/react-router'
import { Sidebar } from '@/presentation/components/Sidebar'
import { Header } from '@/presentation/components/Header'
import { LoginScreen } from '@/presentation/components/LoginScreen'
import { SESSION_EXPIRED, TOKEN_KEY } from '@/lib/api'

export const Route = createRootRoute({
  component: RootLayout,
})

function RootLayout() {
  // L'API exige désormais une connexion : sans jeton, on affiche l'écran de connexion de l'équipe.
  const [logged, setLogged] = useState(() => Boolean(localStorage.getItem(TOKEN_KEY)))
  useEffect(() => {
    const onExpired = () => setLogged(false)
    window.addEventListener(SESSION_EXPIRED, onExpired)
    return () => window.removeEventListener(SESSION_EXPIRED, onExpired)
  }, [])
  if (!logged) return <LoginScreen onLoggedIn={() => setLogged(true)} />

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100">
      {/* Barre latérale */}
      <Sidebar />

      {/* Contenu principal avec Header sticky */}
      <div className="flex-1 flex flex-col h-screen min-w-0 overflow-hidden">
        <Header />
        <main className="flex-1 w-full min-w-0 overflow-y-auto px-4 sm:px-6 py-6 bg-slate-50/50 dark:bg-slate-950">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
