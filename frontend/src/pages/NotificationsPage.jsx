import { useEffect, useState } from 'react'
import api from '../services/api'
import { useToast } from '../components/Toast'

export default function NotificationsPage() {
  const [items, setItems] = useState([])
  const { push } = useToast()

  const load = () => api.get('/api/notifications').then((r) => setItems(r.data))

  useEffect(() => {
    load()
  }, [])

  const markRead = async (id) => {
    await api.post(`/api/notifications/${id}/read`)
    load()
  }

  const markAll = async () => {
    await api.post('/api/notifications/read-all')
    push('All notifications marked as read', 'success')
    load()
  }

  const unread = items.filter((n) => !n.is_read).length

  return (
    <div className="space-y-4 max-w-3xl">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-semibold">Notifications</h2>
        {unread > 0 && (
          <button type="button" onClick={markAll} className="text-sm text-indigo-600 hover:underline">
            Mark all as read ({unread})
          </button>
        )}
      </div>
      {items.length === 0 && <p className="text-slate-500 text-sm">You have no notifications.</p>}
      {items.map((n) => (
        <div
          key={n.id}
          className={`hover-grow-soft border rounded-xl p-4 flex items-start justify-between gap-4 ${n.is_read ? 'bg-white' : 'bg-indigo-50 border-indigo-200'}`}
        >
          <div>
            <p className="font-medium">{n.title}</p>
            <p className="text-sm text-slate-600 mt-1">{n.message}</p>
            <p className="text-xs text-slate-400 mt-2">{new Date(n.created_at).toLocaleString()}</p>
          </div>
          {!n.is_read && (
            <button type="button" onClick={() => markRead(n.id)} className="text-xs text-indigo-600 whitespace-nowrap">
              Mark read
            </button>
          )}
        </div>
      ))}
    </div>
  )
}
