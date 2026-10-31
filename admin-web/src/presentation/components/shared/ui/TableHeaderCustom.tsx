import React from 'react'
import { cn } from '@/lib/utils'

interface TableHeaderCustomProps {
  columns: {
    key: string
    label: string
    className?: string
    align?: 'left' | 'center' | 'right'
  }[]
  className?: string
}

export const TableHeaderCustom: React.FC<TableHeaderCustomProps> = ({ columns, className }) => {
  return (
    <thead>
      <tr className={cn('bg-[#0A2540] text-white border-b border-[#133863]', className)}>
        {columns.map((col) => (
          <th
            key={col.key}
            className={cn(
              'py-3.5 px-4 text-xs font-bold uppercase tracking-wider text-white whitespace-nowrap',
              col.align === 'center' ? 'text-center' : col.align === 'right' ? 'text-right' : 'text-left',
              col.className
            )}
          >
            {col.label}
          </th>
        ))}
      </tr>
    </thead>
  )
}

interface TableCardWrapperProps {
  title: string
  count?: number | string
  badgeRight?: string
  children: React.ReactNode
  icon?: React.ReactNode
  actionButton?: React.ReactNode
}

export const TableCardWrapper: React.FC<TableCardWrapperProps> = ({
  title,
  count,
  badgeRight,
  children,
  icon,
  actionButton,
}) => {
  return (
    <div className="rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-800 shadow-xs overflow-hidden">
      {/* Bandeau d'en-tête de carte (Style front-web) */}
      <div className="px-6 py-4 border-b border-slate-100 dark:border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-white dark:bg-slate-900">
        <div className="flex items-center gap-2.5">
          {icon && <span className="text-blue-600 dark:text-blue-400">{icon}</span>}
          <h3 className="text-xs sm:text-sm font-black tracking-wide uppercase text-slate-800 dark:text-slate-100">
            {title} {count !== undefined && <span className="text-slate-400 font-bold">({count})</span>}
          </h3>
        </div>

        <div className="flex items-center gap-3">
          {badgeRight && (
            <span className="text-xs font-bold text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/60 px-3 py-1 rounded-full border border-emerald-200 dark:border-emerald-800">
              {badgeRight}
            </span>
          )}
          {actionButton}
        </div>
      </div>

      {/* Contenu du tableau */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          {children}
        </table>
      </div>
    </div>
  )
}
