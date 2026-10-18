import { api } from './api'
export interface NotificationItem { id: number; message: string; event: string; is_read: boolean; created_at: string; ticket_id: number | null }
export interface NotificationPage { results: NotificationItem[]; unread_count: number; total: number; has_more: boolean }
export async function getNotifications(filter = 'all', page = 1) {
  const { data } = await api.get<NotificationPage>('notifications/', { params: { filter, page } })
  return data
}
export async function updateNotifications(action: 'read' | 'delete', ids: number[] = [], all = false) {
  await api.post('notifications/', { action, ids, all })
  window.dispatchEvent(new Event('tickarla:notifications-changed'))
}
