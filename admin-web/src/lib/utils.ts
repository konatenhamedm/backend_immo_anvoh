import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatFCFA(val: number | string | undefined | null): string {
  if (val === null || val === undefined) return '0 FCFA'
  const num = typeof val === 'string' ? parseFloat(val) : val
  return new Intl.NumberFormat('fr-CI', { style: 'currency', currency: 'XOF', maximumFractionDigits: 0 }).format(num).replace('XOF', 'FCFA')
}
