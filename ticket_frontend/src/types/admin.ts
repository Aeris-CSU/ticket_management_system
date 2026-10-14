export interface Assignment {
  id: number
  tickets: number
  ticket_title: string
  technicians: number
  technician_name: string
  is_active: boolean
  created_at: string
  assigned_at: string
}

export interface Technician {
  id: number
  username: string
  first_name: string
  last_name: string
  email: string
  role: 'TECHNICIAN'
  specialization: string
  availability_status: 'AVAILABLE' | 'UNAVAILABLE'
}

export interface CustomerDirectoryEntry {
  contact_number?: string
  address?: string
  id: number
  username: string
  first_name: string
  last_name: string
  email: string
  role: 'CUSTOMER'
}
