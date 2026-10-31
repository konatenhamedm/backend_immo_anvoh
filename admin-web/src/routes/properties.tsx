import React from 'react'
import { createFileRoute } from '@tanstack/react-router'
import { PropertiesModule } from '@/presentation/modules/properties'

export const Route = createFileRoute('/properties')({
  component: PropertiesRoute,
})

function PropertiesRoute() {
  return <PropertiesModule />
}
