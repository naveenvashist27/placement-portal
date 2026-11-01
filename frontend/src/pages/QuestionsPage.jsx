import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import api from '../services/api'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../components/Toast'

export default function QuestionsPage() {
  const [params] = useSearchParams()
  const { user } = useAuth()
  const { push } = useToast()
  const [items, setItems] = useState([])
  const [text, setText] = useState('')

  const filters = {
    company_id: params.get('company_id') || undefined,
    company_year_id: params.get('company_year_id') || undefined,
    role_id: params.get('role_id') || undefined,
  }

  const load = () => api.get('/api/questions', { params: filters }).then((r) => setItems(r.data.items))

  useEffect(() => {
    load()
  }, [params])

  const submit = async (e) => {
    e.preventDefault()
    try {
      await api.post('/api/questions/submit', { submitted_text: text, ...filters })
      push('Question submitted for verification', 'success')
      setText('')
    } catch (err) {
      push(err.response?.data?.detail || 'Submit failed', 'error')
    }
  }

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-semibold">Interview questions</h2>
      <p className="text-sm text-slate-500">Only verified canonical questions are shown. Contributor info is hidden.</p>

      {user?.role === 'STUDENT' && (
        <form onSubmit={submit} className="bg-white border rounded-xl p-4 space-y-3">
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Submit a question you were asked..."
            className="w-full border rounded-lg p-3 text-sm min-h-[90px]"
            required
          />
          <button type="submit" className="rounded-lg bg-indigo-600 text-white px-4 py-2 text-sm">
            Submit for verification
          </button>
        </form>
      )}

      <ul className="space-y-3">
        {items.map((q, idx) => (
          <li key={q.id} className="bg-white border rounded-lg p-4">
            <p className="font-medium">
              {idx + 1}. {q.question_text}
            </p>
            <p className="text-xs text-slate-500 mt-1">
              {q.round_label || 'Round N/A'} · {q.difficulty} · asked {q.frequency}×
            </p>
          </li>
        ))}
      </ul>
    </div>
  )
}
