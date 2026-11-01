import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../services/api'
import StatsCards from '../components/StatsCards'

function formatDate(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' })
}

export default function StudentDashboard() {
  const [feed, setFeed] = useState(null)

  useEffect(() => {
    api.get('/api/dashboard/feed').then((r) => setFeed(r.data))
  }, [])

  if (!feed) return <p className="text-slate-500">Loading latest placement updates...</p>

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-semibold text-slate-900">Latest placement updates</h2>
        <p className="text-slate-500 text-sm">Registrations with nearest deadlines appear first.</p>
      </div>

      <StatsCards />

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {feed.registrations?.map((r) => (
          <article key={r.id} className="hover-grow-soft bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
            <p className="text-xs uppercase tracking-wide text-indigo-600 font-medium">Registration</p>
            <h3 className="font-semibold text-lg mt-1">{r.title}</h3>
            <p className="text-sm text-slate-600 mt-2">
              Deadline: <span className="font-medium">{formatDate(r.deadline)}</span>
            </p>
            <p className="text-sm mt-1">
              Status:{' '}
              <span
                className={`font-semibold ${r.status === 'OPEN' ? 'text-emerald-600' : 'text-slate-500'}`}
              >
                {r.status}
              </span>
            </p>
            {r.status === 'OPEN' ? (
              <Link
                to={`/events#form-${r.id}`}
                className="inline-block mt-4 rounded-lg bg-indigo-600 text-white text-sm px-4 py-2 hover:bg-indigo-700"
              >
                Register now
              </Link>
            ) : (
              <span className="inline-block mt-4 text-sm text-slate-400">Registration closed</span>
            )}
          </article>
        ))}
      </section>

      <section className="grid md:grid-cols-2 gap-4">
        <div className="hover-grow-soft bg-white rounded-xl border p-5">
          <h3 className="font-semibold">Announcements & events</h3>
          <ul className="mt-3 space-y-2 text-sm">
            {feed.events?.map((e) => (
              <li key={e.id} className="flex justify-between gap-2 border-b border-slate-100 pb-2">
                <span>{e.title}</span>
                <span className="text-slate-500 shrink-0">{formatDate(e.deadline)}</span>
              </li>
            ))}
          </ul>
        </div>
        <div className="hover-grow-soft bg-white rounded-xl border p-5">
          <h3 className="font-semibold">Recently verified questions</h3>
          <ul className="mt-3 space-y-2 text-sm list-disc pl-5">
            {feed.recent_questions?.map((q) => (
              <li key={q.id}>{q.text}</li>
            ))}
          </ul>
          <Link to="/questions" className="text-indigo-600 text-sm mt-3 inline-block">
            Browse all questions
          </Link>
        </div>
      </section>
    </div>
  )
}
