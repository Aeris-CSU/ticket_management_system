export type TicketStatus = 'OPEN' | 'ASSIGNED' | 'ONGOING' | 'RESOLVED' | 'CANCELLED'

export interface Ticket {
  ticket_number?: string
  id: number
  problem_title: string
  problem_description: string
  cancellation_reason?: string
  status: TicketStatus
  customer: number
  customer_name: string
  customer_address?: string
  address?: string
  contact_number?: string
  created_at: string
  updated_at: string
}

export interface CreateTicketPayload {
  address?: string
  contact_number?: string
  problem_title: string
  problem_description: string
}
