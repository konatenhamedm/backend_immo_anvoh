import React from 'react'
import { createFileRoute } from '@tanstack/react-router'
import { FavoritesModule } from '@/presentation/modules/favorites'

export const Route = createFileRoute('/favorites')({
  component: FavoritesRoute,
})

function FavoritesRoute() {
  return <FavoritesModule />
}
