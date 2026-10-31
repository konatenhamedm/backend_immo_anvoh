import React from 'react'
import { cn } from '@/lib/utils'

interface StatutBadgeProps {
  status: string
  label?: string
  className?: string
}

export const StatutBadge: React.FC<StatutBadgeProps> = ({ status, label, className }) => {
  const normalized = status.toUpperCase()

  let style = 'bg-slate-100 text-slate-700 border-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-700'

  if (['DISPONIBLE', 'VERIFIE', 'VENTE', 'CONFIRMEE', 'TRES_CHAUD'].includes(normalized)) {
    style = 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-400 dark:border-emerald-800/50'
  } else if (['CHAUD', 'VERIFICATION_RENFORCEE', 'OPTION', 'QUALIFIE', 'RDV'].includes(normalized)) {
    style = 'bg-teal-50 text-teal-700 border-teal-200 dark:bg-teal-950/40 dark:text-teal-400 dark:border-teal-800/50'
  } else if (['EN_ATTENTE', 'TIEDE', 'CONTACTE', 'PROPOSITION', 'NEGOCIATION'].includes(normalized)) {
    style = 'bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/40 dark:text-amber-400 dark:border-amber-800/50'
  } else if (['RESERVE', 'VENDU', 'FROID', 'PERDU', 'ANNULEE'].includes(normalized)) {
    style = 'bg-rose-50 text-rose-700 border-rose-200 dark:bg-rose-950/40 dark:text-rose-400 dark:border-rose-800/50'
  }

  return (
    <span
      className={cn(
        'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border transition-colors shadow-xs',
        style,
        className
      )}
    >
      <span className="w-1.5 h-1.5 rounded-full bg-current mr-1.5 opacity-70"></span>
      {label || status}
    </span>
  )
}
