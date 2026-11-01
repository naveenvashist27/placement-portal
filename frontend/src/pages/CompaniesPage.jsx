import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../services/api'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../components/Toast'

export default function CompaniesPage() {
  const { user } = useAuth()
  const { push } = useToast()
  const canManage = user?.role === 'PCELL_MEMBER' || user?.role === 'TPO'
  const [items, setItems] = useState([])
  const [q, setQ] = useState('')
  const [draft, setDraft] = useState({ name: '', industry: '', description: '' })

  const load = (search = '') => {
    api.get('/api/companies', { params: { q: search || undefined } }).then((r) => setItems(r.data.items))
  }

  useEffect(() => {
    load()
  }, [])

  const create = async (e) => {
    e.preventDefault()
    try {
      await api.post('/api/companies', {
        name: draft.name,
        industry: draft.industry || null,
        description: draft.description || null,
      })
      setDraft({ name: '', industry: '', description: '' })
      push('Company added', 'success')
      load()
    } catch (err) {
      push(err.response?.data?.detail?.[0]?.msg || err.response?.data?.detail || 'Could not add company', 'error')
    }
  }

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-semibold">Companies</h2>
      <div className="flex gap-2 max-w-md">
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Search companies"
          className="flex-1 rounded-lg border px-3 py-2 text-sm"
        />
        <button type="button" onClick={() => load(q)} className="rounded-lg bg-indigo-600 text-white px-4 text-sm">
          Search
        </button>
      </div>
      {canManage && (
        <form onSubmit={create} className="bg-white border rounded-xl p-5 space-y-3 max-w-2xl">
          <h3 className="font-semibold">Add company</h3>
          <input
            className="w-full rounded-lg border px-3 py-2 text-sm"
            placeholder="Name"
            value={draft.name}
            onChange={(e) => setDraft({ ...draft, name: e.target.value })}
            required
          />
          <input
            className="w-full rounded-lg border px-3 py-2 text-sm"
            placeholder="Industry"
            value={draft.industry}
            onChange={(e) => setDraft({ ...draft, industry: e.target.value })}
          />
          <textarea
            className="w-full rounded-lg border px-3 py-2 text-sm"
            rows={2}
            placeholder="Description"
            value={draft.description}
            onChange={(e) => setDraft({ ...draft, description: e.target.value })}
          />
          <button type="submit" className="rounded-lg bg-indigo-600 text-white px-4 py-2 text-sm">
            Add company
          </button>
        </form>
      )}
      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {items.map((c) => (
          <Link key={c.id} to={`/companies/${c.id}`} className="hover-grow bg-white rounded-xl border p-5 hover:border-indigo-300">
            <h3 className="font-semibold text-lg">{c.name}</h3>
            <p className="text-sm text-slate-500 mt-1">{c.industry}</p>
            <p className="text-sm text-slate-600 mt-3 line-clamp-3">{c.description}</p>
          </Link>
        ))}
      </div>
    </div>
  )
}
