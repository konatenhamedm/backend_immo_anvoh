import React from 'react'

interface LogoProps {
  variant?: 'full' | 'icon'
  size?: 'sm' | 'md' | 'lg'
  className?: string
  textColor?: 'white' | 'dark'
}

export function Logo({
  variant = 'full',
  size = 'md',
  className = '',
  textColor = 'white',
}: LogoProps) {
  // Dimensions de l'icône selon la taille
  const iconDimensions = {
    sm: { width: 32, height: 32, rx: 8 },
    md: { width: 40, height: 40, rx: 11 },
    lg: { width: 48, height: 48, rx: 14 },
  }

  const dim = iconDimensions[size]

  return (
    <div className={`flex items-center gap-3 select-none ${className}`}>
      {/* 1. Emblème Iconographique Vectoriel Architectural */}
      <div className="relative shrink-0 flex items-center justify-center">
        <svg
          width={dim.width}
          height={dim.height}
          viewBox="0 0 64 64"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className="transition-transform duration-200 group-hover:scale-105"
        >
          <defs>
            <linearGradient id="logo-blue-grad" x1="0" y1="0" x2="64" y2="64" gradientUnits="userSpaceOnUse">
              <stop offset="0%" stop-color="#2563EB" />
              <stop offset="60%" stop-color="#38BDF8" />
              <stop offset="100%" stop-color="#00D2B4" />
            </linearGradient>

            <linearGradient id="logo-bg-grad" x1="0" y1="0" x2="64" y2="64" gradientUnits="userSpaceOnUse">
              <stop offset="0%" stop-color="#0B1E3B" />
              <stop offset="100%" stop-color="#051020" />
            </linearGradient>

            <filter id="logo-shadow" x="-10%" y="-10%" width="120%" height="120%">
              <feDropShadow dx="0" dy="2" stdDeviation="3" flood-color="#2563EB" flood-opacity="0.35" />
            </filter>
          </defs>

          {/* Fond Squircle avec bordure subtile */}
          <rect width="64" height="64" rx="16" fill="url(#logo-bg-grad)" />
          <rect x="0.75" y="0.75" width="62.5" height="62.5" rx="15.25" stroke="#1D4ED8" stroke-width="1.5" stroke-opacity="0.5" />

          {/* Formes Architecturales Épurées */}
          <g filter="url(#logo-shadow)">
            {/* Tour gauche */}
            <path d="M16 28L26 20V50H16V28Z" fill="url(#logo-blue-grad)" fill-opacity="0.9" />

            {/* Tour droite haute */}
            <path d="M28 14L40 24V50H28V14Z" fill="url(#logo-blue-grad)" />

            {/* Toiture dynamique formant le T de THIEBBRO */}
            <path d="M12 28L32 12L52 28H42L32 20L22 28H12Z" fill="#38BDF8" />

            {/* Fenêtres d'immeuble lumineuses */}
            <rect x="20" y="31" width="2.5" height="3.5" rx="0.5" fill="#FFFFFF" fill-opacity="0.95" />
            <rect x="20" y="38" width="2.5" height="3.5" rx="0.5" fill="#FFFFFF" fill-opacity="0.95" />

            <rect x="32" y="25" width="3" height="4" rx="0.5" fill="#FFFFFF" fill-opacity="0.95" />
            <rect x="32" y="32" width="3" height="4" rx="0.5" fill="#FFFFFF" fill-opacity="0.95" />
            <rect x="32" y="39" width="3" height="4" rx="0.5" fill="#FFFFFF" fill-opacity="0.95" />

            {/* Étincelle d'excellence PropTech */}
            <circle cx="48" cy="16" r="3" fill="#00D2B4" />
            <path d="M48 11V21M43 16H53" stroke="#00D2B4" stroke-width="1.2" stroke-linecap="round" />
          </g>
        </svg>

        {/* Pastille verte de statut connecté / en ligne */}
        <span className="absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 bg-emerald-400 border-2 border-[#091931] rounded-full animate-pulse" />
      </div>

      {/* 2. Typographie & Marque (Si variant="full") */}
      {variant === 'full' && (
        <div className="flex flex-col min-w-0">
          <div className="flex items-center gap-1.5">
            <span
              className={`font-black tracking-tight leading-none ${
                size === 'sm' ? 'text-sm' : size === 'lg' ? 'text-xl' : 'text-base'
              } ${textColor === 'white' ? 'text-white' : 'text-slate-900 dark:text-white'}`}
            >
              THIEBBRO<span className="text-cyan-400 font-black">.IMMO</span>
            </span>
            <span className="px-1.5 py-0.5 text-[8px] font-black uppercase tracking-wider bg-gradient-to-r from-blue-600/30 to-cyan-500/20 text-cyan-300 rounded border border-cyan-500/30">
              PRO
            </span>
          </div>
          <span className="text-[10px] font-semibold text-slate-400 mt-0.5 tracking-wide uppercase">
            PropTech Côte d’Ivoire
          </span>
        </div>
      )}
    </div>
  )
}
