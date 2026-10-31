import React from 'react'
import { createFileRoute } from '@tanstack/react-router'
import { ProjectsModule } from '@/presentation/modules/projects'

export const Route = createFileRoute('/projects')({
  component: ProjectsRoute,
})

function ProjectsRoute() {
  return <ProjectsModule />
}
