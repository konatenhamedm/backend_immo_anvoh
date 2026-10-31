import React from 'react'
import { Eye, Edit3, Trash2 } from 'lucide-react'

interface TableRowActionsProps {
  onShow?: () => void
  onEdit?: () => void
  onDelete?: () => void
  showLabel?: string
  editLabel?: string
  deleteLabel?: string
}

export function TableRowActions({
  onShow,
  onEdit,
  onDelete,
  showLabel = 'Consulter',
  editLabel = 'Modifier',
  deleteLabel = 'Supprimer',
}: TableRowActionsProps) {
  return (
    <div className="flex items-center justify-end gap-1.5">
      {onShow && (
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation()
            onShow()
          }}
          title={showLabel}
          className="p-1.5 rounded-lg text-slate-500 hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-950/40 dark:hover:text-blue-400 transition-colors cursor-pointer"
        >
          <Eye className="w-4 h-4" />
        </button>
      )}

      {onEdit && (
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation()
            onEdit()
          }}
          title={editLabel}
          className="p-1.5 rounded-lg text-slate-500 hover:text-amber-600 hover:bg-amber-50 dark:hover:bg-amber-950/40 dark:hover:text-amber-400 transition-colors cursor-pointer"
        >
          <Edit3 className="w-4 h-4" />
        </button>
      )}

      {onDelete && (
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation()
            onDelete()
          }}
          title={deleteLabel}
          className="p-1.5 rounded-lg text-slate-500 hover:text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/40 dark:hover:text-rose-400 transition-colors cursor-pointer"
        >
          <Trash2 className="w-4 h-4" />
        </button>
      )}
    </div>
  )
}
