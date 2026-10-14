export type UserRole = 'ADMIN' | 'TECHNICIAN' | 'CUSTOMER'

export interface AuthUser {
  id: number | string
  username: string
  first_name?: string
  last_name?: string
  email?: string
  role: UserRole
}

export interface LoginCredentials {
  username: string
  password: string
}

export interface RegistrationDetails extends LoginCredentials {
  contact_number?: string
  email?: string
  address: string
}

export interface LoginResponse {
  message: string
  account: AuthUser
  tokens: {
    access: string
    refresh: string
  }
}

export interface TokenRefreshResponse {
  access: string
}
