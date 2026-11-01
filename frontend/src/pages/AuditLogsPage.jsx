import { useEffect, useState } from 'react'
import api from '../services/api'

const PAGE_SIZE = 50

export default function AuditLogsPage() {
  const [data, setData] = useState({ items: [], total: 0 })
  const [page, setPage] = useState(1)

  useEffect(() => {
    api.get('/api/tpo/audit-logs', { params: { page, page_size: PAGE_SIZE } }).then((r) => setData(r.data))
  }, [page])

  const pages = Math.max(1, Math.ceil(data.total / PAGE_SIZE))

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-semibold">Audit logs</h2>
      <div className="bg-white border rounded-xl overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-left">
            <tr>
              <th className="p-3">When</th>
              <th className="p-3">Actor</th>
              <th className="p-3">Action</th>
              <th className="p-3">Entity</th>
              <th className="p-3">Details</th>
            </tr>
          </thead>
          <tbody>
            {data.items.map((l) => (
              <tr key={l.id} className="border-t">
                <td className="p-3 whitespace-nowrap">{new Date(l.created_at).toLocaleString()}</td>
                <td className="p-3">
                  #{l.actor_id} <span className="text-slate-400">({l.actor_role})</span>
                </td>
                <td className="p-3 font-mono text-xs">{l.action}</td>
                <td className="p-3">
                  {l.entity_type}
                  {l.entity_id != null && ` #${l.entity_id}`}
                </td>
                <td className="p-3 text-slate-600">{l.details || '—'}</td>
              </tr>
            ))}
            {data.items.length === 0 && (
              <tr>
                <td colSpan={5} className="p-4 text-slate-500">
                  No audit entries yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      <div className="flex items-center gap-3 text-sm">
        <button type="button" disabled={page <= 1} onClick={() => setPage(page - 1)} className="px-3 py-1 border rounded disabled:opacity-40">
          Previous
        </button>
        <span>
          Page {page} of {pages}
        </span>
        <button type="button" disabled={page >= pages} onClick={() => setPage(page + 1)} className="px-3 py-1 border rounded disabled:opacity-40">
          Next
        </button>
      </div>
    </div>
  )
}
