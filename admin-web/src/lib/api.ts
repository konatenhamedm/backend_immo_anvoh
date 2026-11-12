// URL de l'API (VITE_API_URL dans .env), par défaut l'API locale.
export const API_BASE_URL = (import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8000/api/v1').replace(/\/+$/, '')
export const TOKEN_KEY = 'thiebbro_access_token'

/** Événement émis quand la session expire : la racine réaffiche l'écran de connexion. */
export const SESSION_EXPIRED = 'thiebbro:session-expired'

export async function fetchApi<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem(TOKEN_KEY)

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  })

  if (response.status === 401) {
    localStorage.removeItem(TOKEN_KEY)
    window.dispatchEvent(new Event(SESSION_EXPIRED))
  }

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    throw new Error(errorData.detail || errorData.message || `Erreur API (${response.status})`)
  }

  if (response.status === 204) {
    return {} as T
  }

  return response.json()
}
