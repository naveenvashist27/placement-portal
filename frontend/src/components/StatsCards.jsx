import { useEffect, useState } from 'react'
import { Building2, GraduationCap } from 'lucide-react'
import api from '../services/api'
import { useToast } from './Toast'
import CountUp from './CountUp'

const CARDS = [
  { key: 'companies_visited', label: 'Companies visited', icon: Building2 },
  { key: 'students_placed', label: 'Students placed', icon: GraduationCap },
]

// `editable` (PCELL / TPO) shows controls to set a manual number or fall back to the automatic count.
export default function StatsCards({ editable = false }) {
  const { push } = useToast()
  const [stats, setStats] = useState(null)
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState({})

  useEffect(() => {
    api.get('/api/stats/overview').then((r) => setStats(r.data))
  }, [])

  const startEdit = () => {
    setDraft({
      companies_visited: stats.companies_visited_override ?? '',
      students_placed: stats.students_placed_override ?? '',
    })
    setEditing(true)
  }

  const save = async (e) => {
    e.preventDefault()
    try {
      const body = Object.fromEntries(Object.entries(draft).map(([k, v]) => [k, v === '' ? null : Number(v)]))
      const { data } = await api.put('/api/stats/overview', body)
      setStats(data)
      setEditing(false)
      push('Dashboard numbers updated', 'success')
    } catch (err) {
      push(err.response?.data?.detail?.[0]?.msg || err.response?.data?.detail || 'Update failed', 'error')
    }
  }

  return (
    <div className="space-y-3">
      <div className="grid sm:grid-cols-2 gap-4">
        {CARDS.map(({ key, label, icon: Icon }) => (
          <div key={key} className="hover-grow bg-gradient-to-br from-indigo-600 to-indigo-800 text-white rounded-2xl p-6 shadow-sm">
            <Icon size={22} className="opacity-80" />
            <p className="text-5xl font-bold mt-3">{stats ? <CountUp value={stats[key]} /> : 0}</p>
            <p className="text-sm text-indigo-100 mt-1">{label}</p>
          </div>
        ))}
      </div>

      {editable && stats && !editing && (
        <button type="button" onClick={startEdit} className="text-sm text-indigo-600 hover:underline">
          Edit these numbers
        </button>
      )}

      {editable && editing && (
        <form onSubmit={save} className="bg-white border rounded-xl p-5 space-y-3 max-w-2xl">
          <p className="text-sm text-slate-500">
            Leave a field empty to use the automatic count from the portal data.
          </p>
          <div className="grid sm:grid-cols-2 gap-3">
            {CARDS.map(({ key, label }) => (
              <label key={key} className="text-sm font-medium">
                {label}
                <input
                  type="number"
                  min={0}
                  value={draft[key]}
                  onChange={(e) => setDraft({ ...draft, [key]: e.target.value })}
                  placeholder={`Automatic: ${stats[`${key}_auto`]}`}
                  className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                />
              </label>
            ))}
          </div>
          <div className="flex gap-3">
            <button type="submit" className="rounded-lg bg-indigo-600 text-white px-4 py-2 text-sm">
              Save
            </button>
            <button type="button" onClick={() => setEditing(false)} className="text-sm text-slate-600">
              Cancel
            </button>
          </div>
        </form>
      )}
    </div>
  )
}
