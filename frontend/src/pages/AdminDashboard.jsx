import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../services/api'
import StatsCards from '../components/StatsCards'

export default function AdminDashboard() {
  const [pending, setPending] = useState(0)
  const [forms, setForms] = useState([])

  useEffect(() => {
    api.get('/api/question-submissions', { params: { status: 'PENDING' } }).then((r) => setPending(r.data.total))
    api.get('/api/registrations/forms').then((r) => setForms(r.data.items.slice(0, 5)))
  }, [])

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-semibold">PCELL dashboard</h2>
      <StatsCards editable />
      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="hover-grow bg-white border rounded-xl p-4">
          <p className="text-sm text-slate-500">Pending questions</p>
          <p className="text-3xl font-semibold">{pending}</p>
        </div>
      </div>
      <div className="flex flex-wrap gap-2">
        {[
          ['Add company', '/admin/companies'],
          ['Review questions', '/admin/questions'],
          ['Registration forms', '/admin/registrations'],
          ['Analytics', '/admin/analytics'],
        ].map(([label, to]) => (
          <Link key={to} to={to} className="rounded-lg bg-indigo-600 text-white text-sm px-4 py-2">
            {label}
          </Link>
        ))}
      </div>
      <div className="hover-grow-soft bg-white border rounded-xl p-5">
        <h3 className="font-semibold">Latest registrations</h3>
        <ul className="mt-3 text-sm space-y-2">
          {forms.map((f) => (
            <li key={f.id}>
              {f.title} — deadline {new Date(f.registration_deadline).toLocaleDateString()} ({f.status})
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}
