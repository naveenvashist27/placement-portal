import { useEffect, useState } from 'react'
import api from '../services/api'
import { useToast } from '../components/Toast'

const inputCls = 'mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm'
const errMsg = (err, fallback) => err.response?.data?.detail?.[0]?.msg || err.response?.data?.detail || fallback

const STATUSES = [
  ['OFFERED', 'Offered'],
  ['ACCEPTED', 'Accepted'],
  ['JOINED', 'Joined'],
  ['DECLINED', 'Declined'],
]
const TYPES = ['On-campus', 'Off-campus', 'Pool campus', 'Internship + PPO']

const emptyDraft = {
  company_id: '',
  company_year_id: '',
  role_id: '',
  package_lpa: '',
  placement_type: 'On-campus',
  placement_status: 'OFFERED',
}

// PCELL / TPO record which student got placed where. These records drive "Students placed" and the analytics.
export default function PlacementsPage() {
  const { push } = useToast()
  const [records, setRecords] = useState([])
  const [companies, setCompanies] = useState([])
  const [years, setYears] = useState([])
  const [roles, setRoles] = useState([])
  const [draft, setDraft] = useState(emptyDraft)
  const [student, setStudent] = useState(null)
  const [search, setSearch] = useState('')
  const [matches, setMatches] = useState([])

  const load = () => api.get('/api/placements').then((r) => setRecords(r.data.items))

  useEffect(() => {
    load()
    api.get('/api/companies', { params: { page_size: 100 } }).then((r) => setCompanies(r.data.items))
  }, [])

  useEffect(() => {
    if (search.trim().length < 2 || student) {
      setMatches([])
      return
    }
    const t = setTimeout(() => {
      api.get('/api/students', { params: { q: search.trim(), page_size: 8 } }).then((r) => setMatches(r.data.items))
    }, 250)
    return () => clearTimeout(t)
  }, [search, student])

  const pickCompany = async (id) => {
    setDraft({ ...draft, company_id: id, company_year_id: '', role_id: '' })
    setRoles([])
    setYears(id ? (await api.get(`/api/companies/${id}/years`)).data : [])
  }

  const pickYear = async (id) => {
    setDraft({ ...draft, company_year_id: id, role_id: '' })
    setRoles(id ? (await api.get(`/api/company-years/${id}/roles`)).data : [])
  }

  const create = async (e) => {
    e.preventDefault()
    if (!student) return push('Pick a student first', 'error')
    try {
      await api.post('/api/placements', {
        student_id: student.id,
        company_id: Number(draft.company_id),
        company_year_id: Number(draft.company_year_id),
        role_id: draft.role_id ? Number(draft.role_id) : null,
        package_lpa: draft.package_lpa === '' ? null : Number(draft.package_lpa),
        placement_type: draft.placement_type,
        placement_status: draft.placement_status,
      })
      push('Placement recorded', 'success')
      setStudent(null)
      setSearch('')
      setDraft({ ...emptyDraft, company_id: draft.company_id, company_year_id: draft.company_year_id })
      load()
    } catch (err) {
      push(errMsg(err, 'Could not save placement'), 'error')
    }
  }

  const setStatus = async (id, placement_status) => {
    try {
      await api.put(`/api/placements/${id}/status`, { placement_status })
      load()
    } catch (err) {
      push(errMsg(err, 'Could not update status'), 'error')
    }
  }

  const remove = async (id) => {
    if (!window.confirm('Delete this placement record?')) return
    await api.delete(`/api/placements/${id}`)
    load()
  }

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-semibold">Placement records</h2>

      <form onSubmit={create} className="bg-white border rounded-xl p-5 space-y-3 max-w-3xl">
        <h3 className="font-semibold">Record a placement</h3>

        <div className="relative">
          <label className="text-sm font-medium">
            Student
            {student ? (
              <div className="mt-1 flex items-center justify-between rounded-lg border border-emerald-300 bg-emerald-50 px-3 py-2 text-sm">
                <span>
                  {student.full_name} · {student.roll_number || student.email}
                </span>
                <button type="button" className="text-red-600" onClick={() => setStudent(null)}>
                  Change
                </button>
              </div>
            ) : (
              <input
                className={inputCls}
                placeholder="Search by name, email or roll number"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            )}
          </label>
          {matches.length > 0 && (
            <ul className="absolute z-10 mt-1 w-full rounded-lg border bg-white shadow-lg max-h-56 overflow-y-auto">
              {matches.map((m) => (
                <li key={m.id}>
                  <button
                    type="button"
                    className="w-full text-left px-3 py-2 text-sm hover:bg-indigo-50"
                    onClick={() => {
                      setStudent(m)
                      setMatches([])
                    }}
                  >
                    {m.full_name} <span className="text-slate-500">· {m.roll_number || m.email}</span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="grid sm:grid-cols-3 gap-3">
          <label className="text-sm font-medium">
            Company
            <select className={inputCls} value={draft.company_id} onChange={(e) => pickCompany(e.target.value)} required>
              <option value="">Select company</option>
              {companies.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </label>
          <label className="text-sm font-medium">
            Visit year
            <select
              className={inputCls}
              value={draft.company_year_id}
              onChange={(e) => pickYear(e.target.value)}
              disabled={!years.length}
              required
            >
              <option value="">{draft.company_id && !years.length ? 'Add a visit year first' : 'Select year'}</option>
              {years.map((y) => (
                <option key={y.id} value={y.id}>
                  {y.visit_year}
                </option>
              ))}
            </select>
          </label>
          <label className="text-sm font-medium">
            Role (optional)
            <select
              className={inputCls}
              value={draft.role_id}
              onChange={(e) => setDraft({ ...draft, role_id: e.target.value })}
              disabled={!roles.length}
            >
              <option value="">{draft.company_year_id && !roles.length ? 'No roles added' : 'Select role'}</option>
              {roles.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.title}
                </option>
              ))}
            </select>
          </label>
        </div>

        <div className="grid sm:grid-cols-3 gap-3">
          <label className="text-sm font-medium">
            Package (LPA)
            <input
              type="number"
              min={0}
              step="0.01"
              className={inputCls}
              placeholder="e.g. 6.5"
              value={draft.package_lpa}
              onChange={(e) => setDraft({ ...draft, package_lpa: e.target.value })}
            />
          </label>
          <label className="text-sm font-medium">
            Placement type
            <select
              className={inputCls}
              value={draft.placement_type}
              onChange={(e) => setDraft({ ...draft, placement_type: e.target.value })}
            >
              {TYPES.map((t) => (
                <option key={t}>{t}</option>
              ))}
            </select>
          </label>
          <label className="text-sm font-medium">
            Status
            <select
              className={inputCls}
              value={draft.placement_status}
              onChange={(e) => setDraft({ ...draft, placement_status: e.target.value })}
            >
              {STATUSES.map(([v, l]) => (
                <option key={v} value={v}>
                  {l}
                </option>
              ))}
            </select>
          </label>
        </div>

        <button type="submit" className="rounded-lg bg-indigo-600 text-white px-4 py-2 text-sm">
          Save placement
        </button>
      </form>

      <div className="bg-white border rounded-xl overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-left">
            <tr>
              <th className="p-3">Student</th>
              <th className="p-3">Course / batch</th>
              <th className="p-3">Company</th>
              <th className="p-3">Package</th>
              <th className="p-3">Status</th>
              <th className="p-3" />
            </tr>
          </thead>
          <tbody>
            {records.map((r) => (
              <tr key={r.id} className="border-t">
                <td className="p-3 whitespace-nowrap">
                  {r.student_name}
                  <span className="block text-xs text-slate-500">{r.roll_number || '—'}</span>
                </td>
                <td className="p-3 whitespace-nowrap">{[r.course, r.batch].filter(Boolean).join(' · ') || '—'}</td>
                <td className="p-3 whitespace-nowrap">
                  {r.company} · {r.visit_year}
                  <span className="block text-xs text-slate-500">{r.role || r.placement_type || ''}</span>
                </td>
                <td className="p-3">{r.package_lpa != null ? `${r.package_lpa} LPA` : '—'}</td>
                <td className="p-3">
                  <select
                    className="rounded-lg border border-slate-300 px-2 py-1 text-sm"
                    value={r.placement_status}
                    onChange={(e) => setStatus(r.id, e.target.value)}
                  >
                    {STATUSES.map(([v, l]) => (
                      <option key={v} value={v}>
                        {l}
                      </option>
                    ))}
                  </select>
                </td>
                <td className="p-3">
                  <button type="button" className="text-red-600" onClick={() => remove(r.id)}>
                    Delete
                  </button>
                </td>
              </tr>
            ))}
            {records.length === 0 && (
              <tr>
                <td colSpan={6} className="p-4 text-slate-500">
                  No placements recorded yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
