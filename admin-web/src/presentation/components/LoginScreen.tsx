import { useState, type FormEvent } from 'react'
import { API_BASE_URL, TOKEN_KEY } from '@/lib/api'

/** Connexion de l'équipe (admin / conseiller) : obtient un jeton JWT auprès de l'API Django. */
export function LoginScreen({ onLoggedIn }: { onLoggedIn: () => void }) {
  const [error, setError] = useState<string | null>(null)
  const [pending, setPending] = useState(false)

  const submit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const form = new FormData(e.currentTarget)
    setPending(true)
    setError(null)
    try {
      const res = await fetch(`${API_BASE_URL}/auth/login/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: form.get('email'), password: form.get('password') }),
      })
      const data = await res.json().catch(() => ({}))
      if (!res.ok) throw new Error(data.detail || 'Connexion impossible')
      if (!(data.user?.is_admin || data.user?.role === 'AGENT')) {
        throw new Error("Ce back-office est réservé à l'équipe Thiebbro.")
      }
      localStorage.setItem(TOKEN_KEY, data.access)
      onLoggedIn()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Connexion impossible')
    } finally {
      setPending(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4 dark:bg-slate-950">
      <form onSubmit={submit} className="w-full max-w-sm space-y-4 rounded-2xl border border-slate-200 bg-white p-8 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <div>
          <h1 className="text-xl font-bold text-slate-900 dark:text-white">Back-office Thiebbro</h1>
          <p className="mt-1 text-sm text-slate-500">Connectez-vous avec votre compte équipe.</p>
        </div>
        {error && <p role="alert" className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
        <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
          E-mail
          <input name="email" type="email" required autoComplete="email" className="mt-1 h-10 w-full rounded-lg border border-slate-300 px-3 text-sm dark:border-slate-700 dark:bg-slate-950" />
        </label>
        <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
          Mot de passe
          <input name="password" type="password" required autoComplete="current-password" className="mt-1 h-10 w-full rounded-lg border border-slate-300 px-3 text-sm dark:border-slate-700 dark:bg-slate-950" />
        </label>
        <button type="submit" disabled={pending} className="h-10 w-full rounded-lg bg-[#2ca58d] text-sm font-semibold text-white disabled:opacity-60">
          {pending ? 'Connexion…' : 'Se connecter'}
        </button>
      </form>
    </div>
  )
}
