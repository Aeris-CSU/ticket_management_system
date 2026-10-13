import { api } from '@/services/api'
import type { CustomerDirectoryEntry, Technician } from '@/types/admin'

export interface NewTechnician {
  username: string
  password: string
  first_name: string
  last_name: string
  email: string
  specialization: string
}

export type CreatedTechnician = Omit<Technician, 'role'>

export async function listCustomers() {
  const { data } = await api.get<CustomerDirectoryEntry[]>('customers/')
  return data
}

export async function listTechnicians() {
  const { data } = await api.get<Technician[]>('technicians/')
  return data
}

export async function createTechnician(details: NewTechnician) {
  const { data } = await api.post<CreatedTechnician>('register-technicians/', details)
  return data
}
