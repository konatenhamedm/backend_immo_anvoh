import React from 'react'
import { createFileRoute } from '@tanstack/react-router'
import { UsersModule } from '@/presentation/modules/users'

export const Route = createFileRoute('/users')({
  component: UsersRoute,
})

function UsersRoute() {
  return <UsersModule />
}
