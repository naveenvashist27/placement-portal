import { useEffect, useState } from 'react'
import api from '../services/api'
import ResumeLink from '../components/ResumeLink'

const PAGE_SIZE = 20

export default function StudentsPage() {
  const [data, setData] = useState({ items: [], total: 0 })
  const [q, setQ] = useState('')
  const [page, setPage] = useState(1)

  useEffect(() => {
    api
      .get('/api/students', { params: { q: q || undefined, page, page_size: PAGE_SIZE } })
      .then((r) => setData(r.data))
  }, [q, page])

  const pages = Math.max(1, Math.ceil(data.total / PAGE_SIZE))

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-semibold">Students</h2>
      <input
        value={q}
        onChange={(e) => {
          setQ(e.target.value)
          setPage(1)
        }}
        placeholder="Search by name, email or roll number"
        className="w-full max-w-md rounded-lg border px-3 py-2 text-sm"
      />
      <div className="bg-white border rounded-xl overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-left">
            <tr>
              <th className="p-3">Name</th>
              <th className="p-3">Email</th>
              <th className="p-3">Roll no.</th>
              <th className="p-3">Branch</th>
              <th className="p-3">Grad. year</th>
              <th className="p-3">Resume</th>
            </tr>
          </thead>
          <tbody>
            {data.items.map((s) => (
              <tr key={s.id} className="border-t">
                <td className="p-3">{s.full_name}</td>
                <td className="p-3">{s.email}</td>
                <td className="p-3">{s.roll_number || '—'}</td>
                <td className="p-3">{s.branch || '—'}</td>
                <td className="p-3">{s.graduation_year || '—'}</td>
                <td className="p-3">
                  <ResumeLink studentId={s.id} hasResume={s.has_resume} />
                </td>
              </tr>
            ))}
            {data.items.length === 0 && (
              <tr>
                <td colSpan={6} className="p-4 text-slate-500">
                  No students found.
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
          Page {page} of {pages} · {data.total} students
        </span>
        <button type="button" disabled={page >= pages} onClick={() => setPage(page + 1)} className="px-3 py-1 border rounded disabled:opacity-40">
          Next
        </button>
      </div>
    </div>
  )
}
