import { useEffect, useState } from 'react'
import api from '../services/api'

export default function SimpleListPage({ title, endpoint, field = 'name' }) {
  const [items, setItems] = useState([])
  useEffect(() => {
    api.get(endpoint).then((r) => setItems(r.data))
  }, [endpoint])
  return (
    <div>
      <h2 className="text-2xl font-semibold mb-4">{title}</h2>
      <div className="flex flex-wrap gap-2">
        {items.map((item) => (
          <span key={item.id} className="hover-grow bg-white border rounded-full px-4 py-2 text-sm">
            {item[field]}
          </span>
        ))}
      </div>
    </div>
  )
}
