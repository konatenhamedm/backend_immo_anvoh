import React, { useState, useRef, useEffect } from 'react'
import { ChevronDown, X, Search, Check } from 'lucide-react'

export interface Select2Option {
  value: string
  label: string
}

interface Select2Props {
  options: Select2Option[]
  value?: string | null
  onChange: (value: string) => void
  placeholder?: string
  label?: string
  isClearable?: boolean
  searchable?: boolean
  className?: string
  disabled?: boolean
}

export function Select2({
  options,
  value,
  onChange,
  placeholder = 'Sélectionner...',
  label,
  isClearable = true,
  searchable = true,
  className = '',
  disabled = false,
}: Select2Props) {
  const [isOpen, setIsOpen] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const containerRef = useRef<HTMLDivElement>(null)
  const searchInputRef = useRef<HTMLInputElement>(null)

  // Fermer le dropdown en cliquant à l'extérieur
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  // Focus automatique sur le champ de recherche à l'ouverture
  useEffect(() => {
    if (isOpen && searchable) {
      setTimeout(() => searchInputRef.current?.focus(), 50)
    } else {
      setSearchTerm('')
    }
  }, [isOpen, searchable])

  const selectedOption = options.find((opt) => opt.value === value)

  const filteredOptions = options.filter((opt) =>
    opt.label.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const handleClear = (e: React.MouseEvent) => {
    e.stopPropagation()
    onChange('')
  }

  const handleSelect = (val: string) => {
    onChange(val)
    setIsOpen(false)
  }

  return (
    <div className={`relative flex flex-col ${className}`} ref={containerRef}>
      {label && (
        <label className="text-[11px] font-bold text-slate-600 dark:text-slate-400 mb-1 tracking-wide">
          {label}
        </label>
      )}

      {/* Bouton déclencheur Select2 (Style signature de front-web) */}
      <div
        onClick={() => !disabled && setIsOpen(!isOpen)}
        className={`w-full h-9.5 px-3 rounded-xl border bg-white dark:bg-slate-900 flex items-center justify-between gap-1.5 cursor-pointer text-xs transition-all shadow-2xs select-none ${
          disabled
            ? 'opacity-60 cursor-not-allowed bg-slate-100 dark:bg-slate-800 border-slate-200 dark:border-slate-800'
            : isOpen
            ? 'border-blue-500 ring-2 ring-blue-500/10'
            : 'border-slate-200/90 dark:border-slate-700/80 hover:border-slate-300 dark:hover:border-slate-600'
        }`}
      >
        <span
          className={`truncate font-medium ${
            selectedOption ? 'text-slate-900 dark:text-white' : 'text-slate-400'
          }`}
        >
          {selectedOption ? selectedOption.label : placeholder}
        </span>

        <div className="flex items-center gap-1 shrink-0 text-slate-400">
          {isClearable && selectedOption && (
            <button
              type="button"
              onClick={handleClear}
              className="p-0.5 rounded-full hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-colors"
              title="Effacer la sélection"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
          <ChevronDown
            className={`w-3.5 h-3.5 transition-transform duration-200 ${
              isOpen ? 'rotate-180 text-blue-600' : ''
            }`}
          />
        </div>
      </div>

      {/* Menu déroulant Flottant */}
      {isOpen && (
        <div className="absolute top-[calc(100%+4px)] left-0 w-full min-w-[200px] bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl shadow-xl z-50 overflow-hidden animate-in fade-in zoom-in-95 duration-100">
          {searchable && (
            <div className="p-2 border-b border-slate-100 dark:border-slate-800 flex items-center gap-2 bg-slate-50/50 dark:bg-slate-800/40">
              <Search className="w-3.5 h-3.5 text-slate-400 shrink-0 ml-1" />
              <input
                ref={searchInputRef}
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Rechercher..."
                className="w-full text-xs bg-transparent border-none outline-hidden text-slate-900 dark:text-white placeholder-slate-400"
              />
            </div>
          )}

          <div className="max-h-56 overflow-y-auto py-1 divide-y divide-slate-50 dark:divide-slate-800/40">
            {filteredOptions.length === 0 ? (
              <div className="py-3 px-4 text-xs text-slate-400 text-center italic">
                Aucun résultat trouvé
              </div>
            ) : (
              filteredOptions.map((opt) => {
                const isSelected = opt.value === value
                return (
                  <div
                    key={opt.value}
                    onClick={() => handleSelect(opt.value)}
                    className={`px-3 py-2 text-xs flex items-center justify-between cursor-pointer transition-colors ${
                      isSelected
                        ? 'bg-blue-50 dark:bg-blue-950/50 text-blue-600 dark:text-blue-400 font-bold'
                        : 'text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800/70'
                    }`}
                  >
                    <span className="truncate">{opt.label}</span>
                    {isSelected && <Check className="w-3.5 h-3.5 text-blue-600 shrink-0 ml-2" />}
                  </div>
                )
              })
            )}
          </div>
        </div>
      )}
    </div>
  )
}
