export type TicketStatus = 'OPEN' | 'ASSIGNED' | 'ONGOING' | 'RESOLVED' | 'CANCELLED'

export interface Ticket {
  id: number
  problem_title: string
  problem_description: string
  status: TicketStatus
  customer: number
  customer_name: string
  created_at: string
  updated_at: string
}

export interface CreateTicketPayload {
  problem_title: string
  problem_description: string
}
