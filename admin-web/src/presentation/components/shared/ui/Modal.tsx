import React, { ReactNode } from 'react'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter
} from './dialog'
import { cn } from '@/lib/utils'

interface ModalProps {
  isOpen: boolean
  onClose: () => void
  title: string | ReactNode
  description?: string
  children: ReactNode
  size?: 'sm' | 'md' | 'lg' | 'xl' | '2xl' | 'full'
  footer?: ReactNode
  showCloseButton?: boolean
}

export const Modal: React.FC<ModalProps> = ({
  isOpen,
  onClose,
  title,
  description,
  children,
  size = 'md',
  footer,
  showCloseButton = true,
}) => {
  const sizeClasses = {
    sm: 'sm:max-w-[440px]',
    md: 'sm:max-w-[600px]',
    lg: 'sm:max-w-[820px] w-full',
    xl: 'sm:max-w-[1060px] w-[92vw]',
    '2xl': 'sm:max-w-[1260px] w-[95vw]',
    full: '!max-w-[96vw] w-[96vw] !h-[92vh] max-h-[92vh]',
  }

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent
        showCloseButton={showCloseButton}
        className={cn(
          sizeClasses[size],
          'flex flex-col p-0 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-2xl z-[120]'
        )}
      >
        {/* Header Signature Bleu Nuit #0A2540 (Inspiré de front-web) */}
        <div className="bg-[#0A2540] text-white px-6 py-4.5 rounded-t-2xl flex-shrink-0 border-b border-[#133863]">
          <DialogHeader>
            <DialogTitle className="text-base sm:text-lg font-bold text-white tracking-tight">
              {title}
            </DialogTitle>
            {description && (
              <DialogDescription className="text-xs text-white/80 mt-1">
                {description}
              </DialogDescription>
            )}
          </DialogHeader>
        </div>

        {/* Corps de modal scrollable */}
        <div className="flex-1 overflow-y-auto px-6 py-6 bg-white dark:bg-slate-900 max-h-[75vh]">
          {children}
        </div>

        {/* Footer stylisé */}
        {footer && (
          <div className="bg-slate-50 dark:bg-slate-950/70 px-6 py-4 rounded-b-2xl border-t border-slate-100 dark:border-slate-800 flex-shrink-0">
            <DialogFooter>{footer}</DialogFooter>
          </div>
        )}
      </DialogContent>
    </Dialog>
  )
}

interface ModalFooterButtonsProps {
  onCancel?: () => void
  onConfirm?: () => void | Promise<void>
  cancelText?: string
  confirmText?: string
  isLoading?: boolean
  confirmVariant?: 'default' | 'danger'
}

export const ModalFooterButtons: React.FC<ModalFooterButtonsProps> = ({
  onCancel,
  onConfirm,
  cancelText = 'Annuler',
  confirmText = 'Confirmer',
  isLoading = false,
  confirmVariant = 'default',
}) => {
  return (
    <div className="flex items-center justify-end gap-3 w-full">
      {onCancel && (
        <button
          type="button"
          onClick={onCancel}
          disabled={isLoading}
          className="px-5 py-2.5 text-xs font-bold rounded-xl border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition-all cursor-pointer"
        >
          {cancelText}
        </button>
      )}
      {onConfirm && (
        <button
          type="button"
          onClick={onConfirm}
          disabled={isLoading}
          className={cn(
            'px-6 py-2.5 text-xs font-bold rounded-xl text-white shadow-md transition-all flex items-center gap-2 cursor-pointer',
            confirmVariant === 'danger'
              ? 'bg-rose-600 hover:bg-rose-700 shadow-rose-600/20'
              : 'bg-blue-600 hover:bg-blue-700 shadow-blue-600/25'
          )}
        >
          {isLoading && (
            <svg className="animate-spin h-3.5 w-3.5" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
          )}
          {confirmText}
        </button>
      )}
    </div>
  )
}
