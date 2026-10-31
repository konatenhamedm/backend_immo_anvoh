import React from 'react'
import { createFileRoute } from '@tanstack/react-router'
import { CrmModule } from '@/presentation/modules/crm'

export const Route = createFileRoute('/crm')({
  component: CrmRoute,
})

function CrmRoute() {
  return <CrmModule />
}
