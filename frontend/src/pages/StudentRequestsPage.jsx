import { useCallback, useEffect, useState } from 'react'
import api from '../services/api'
import { useToast } from '../components/Toast'

const PAGE_SIZE = 20
const TABS = [
  ['PENDING', 'Pending'],
  ['REJECTED', 'Rejected'],
  ['ACTIVE', 'Approved'],
]

export default function StudentRequestsPage() {
  const { push } = useToast()
  const [status, setStatus] = useState('PENDING')
  const [page, setPage] = useState(1)
  const [data, setData] = useState({ items: [], total: 0 })

  const load = useCallback(() => {
    api
      .get('/api/admin/student-requests', { params: { status, page, page_size: PAGE_SIZE } })
      .then((r) => setData(r.data))
      .catch(() => push('Could not load requests', 'error'))
  }, [status, page, push])

  useEffect(load, [load])

  const review = async (req, action) => {
    let note
    if (action === 'reject') {
      note = window.prompt('Reason for rejecting (visible to PCELL/TPO only):', '')
      if (note === null) return
    }
    try {
      await api.post(`/api/admin/student-requests/${req.id}/${action}`, { note: note || null })
      push(action === 'approve' ? `Approved ${req.full_name}` : `Rejected ${req.full_name}`, 'success')
      load()
    } catch (err) {
      push(err.response?.data?.detail || 'Action failed', 'error')
    }
  }

  const pages = Math.max(1, Math.ceil(data.total / PAGE_SIZE))

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-semibold">Student Requests</h2>
      <p className="text-sm text-slate-500">
        Students who signed in with Google for the first time. Approve only students who are eligible for placements.
      </p>
      <div className="flex gap-2">
        {TABS.map(([key, label]) => (
          <button
            key={key}
            type="button"
            onClick={() => {
              setStatus(key)
              setPage(1)
            }}
            className={`px-3 py-1.5 rounded-lg text-sm border ${status === key ? 'bg-indigo-600 text-white border-indigo-600' : 'bg-white'}`}
          >
            {label}
          </button>
        ))}
      </div>
      <div className="bg-white border rounded-xl overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-left">
            <tr>
              <th className="p-3">Name</th>
              <th className="p-3">Email</th>
              <th className="p-3">Roll no.</th>
              <th className="p-3">Course</th>
              <th className="p-3">Batch</th>
              <th className="p-3">Phone</th>
              <th className="p-3">Requested</th>
              <th className="p-3">Action</th>
            </tr>
          </thead>
          <tbody>
            {data.items.map((r) => (
              <tr key={r.id} className="border-t">
                <td className="p-3">{r.full_name}</td>
                <td className="p-3">{r.email}</td>
                <td className="p-3">{r.roll_number || '—'}</td>
                <td className="p-3">{r.course || '—'}</td>
                <td className="p-3">{r.batch || '—'}</td>
                <td className="p-3">{r.phone || '—'}</td>
                <td className="p-3">{new Date(r.created_at).toLocaleDateString()}</td>
                <td className="p-3 whitespace-nowrap space-x-2">
                  {status !== 'ACTIVE' && (
                    <button type="button" onClick={() => review(r, 'approve')} className="px-2 py-1 rounded bg-emerald-600 text-white">
                      Approve
                    </button>
                  )}
                  {status === 'PENDING' && (
                    <button type="button" onClick={() => review(r, 'reject')} className="px-2 py-1 rounded bg-red-600 text-white">
                      Reject
                    </button>
                  )}
                  {status === 'REJECTED' && r.review_note && <span className="text-slate-500">{r.review_note}</span>}
                </td>
              </tr>
            ))}
            {data.items.length === 0 && (
              <tr>
                <td colSpan={8} className="p-4 text-slate-500">
                  No requests.
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
          Page {page} of {pages} · {data.total} requests
        </span>
        <button type="button" disabled={page >= pages} onClick={() => setPage(page + 1)} className="px-3 py-1 border rounded disabled:opacity-40">
          Next
        </button>
      </div>
    </div>
  )
}
