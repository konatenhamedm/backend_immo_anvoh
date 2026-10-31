import React from 'react'
import { createFileRoute } from '@tanstack/react-router'
import { InquiriesModule } from '@/presentation/modules/inquiries'

export const Route = createFileRoute('/inquiries')({
  component: InquiriesRoute,
})

function InquiriesRoute() {
  return <InquiriesModule />
}
