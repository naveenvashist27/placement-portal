import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import api from '../services/api'

export default function SearchPage() {
  const [params] = useSearchParams()
  const q = params.get('q') || ''
  const [data, setData] = useState(null)

  useEffect(() => {
    if (!q) return
    api.get('/api/search', { params: { q } }).then((r) => setData(r.data))
  }, [q])

  if (!q) return <p>Enter a search query from the top bar.</p>
  if (!data) return <p className="text-slate-500">Searching...</p>

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold">Results for “{q}”</h2>
      {[
        ['Companies', data.companies, (c) => `/companies/${c.id}`, 'name'],
        ['Questions', data.questions, null, 'text'],
        ['Topics', data.topics, null, 'name'],
        ['Skills', data.skills, null, 'name'],
        ['Events', data.events, null, 'title'],
      ].map(([label, items, linkFn, field]) =>
        items?.length ? (
          <section key={label}>
            <h3 className="font-medium">{label}</h3>
            <ul className="mt-2 space-y-1 text-sm">
              {items.map((item) => (
                <li key={item.id}>
                  {linkFn ? <Link to={linkFn(item)}>{item[field]}</Link> : item[field]}
                </li>
              ))}
            </ul>
          </section>
        ) : null,
      )}
    </div>
  )
}
