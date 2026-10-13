import { api } from '@/services/api'
import type { Assignment } from '@/types/admin'

export async function listAssignments() {
  const { data } = await api.get<Assignment[]>('assignments/')
  return data
}

export async function createAssignment(ticketId: number, technicianId: number) {
  const { data } = await api.post<Assignment>('assignments/', {
    tickets: ticketId,
    technicians: technicianId,
  })
  return data
}

export async function reassignTechnician(assignmentId: number, technicianId: number) {
  const { data } = await api.put<Assignment>(`assignments/${assignmentId}/`, {
    technicians: technicianId,
  })
  return data
}
