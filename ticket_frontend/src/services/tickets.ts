import { api } from '@/services/api'
import type { CreateTicketPayload, Ticket, TicketStatus } from '@/types/ticket'

export async function listTickets() {
  const { data } = await api.get<Ticket[]>('tickets/')
  return data
}

export async function createTicket(payload: CreateTicketPayload) {
  const { data } = await api.post<Ticket>('tickets/', payload)
  return data
}

export async function getTicket(id: string) {
  const { data } = await api.get<Ticket>(`tickets/${encodeURIComponent(id)}/`)
  return data
}

export async function updateTicketStatus(id: string, status: TicketStatus) {
  const { data } = await api.patch<Ticket>(`tickets/${encodeURIComponent(id)}/status/`, { status })
  return data
}

export async function updateTicket(id: string, payload: CreateTicketPayload) {
  const { data } = await api.put<Ticket>(`tickets/${encodeURIComponent(id)}/`, payload)
  return data
}
