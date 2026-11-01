import { useEffect, useState } from 'react'
import api from '../services/api'
import { useToast } from '../components/Toast'

export default function AdminQuestionReview() {
  const [items, setItems] = useState([])
  const { push } = useToast()

  const load = () => api.get('/api/question-submissions').then((r) => setItems(r.data.items))

  useEffect(() => {
    load()
  }, [])

  const act = async (id, action) => {
    try {
      await api.post(`/api/question-submissions/${id}/${action}`)
      push(`Submission ${action}d`, 'success')
      load()
    } catch (err) {
      push(err.response?.data?.detail || 'Action failed', 'error')
    }
  }

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-semibold">Question verification</h2>
      <p className="text-sm text-slate-500">Contributor details are visible here for PCELL verification only.</p>
      {items.map((s) => (
        <div key={s.id} className="hover-grow-soft bg-white border rounded-xl p-5">
          <p className="font-medium">{s.submitted_text}</p>
          <p className="text-sm text-slate-600 mt-2">
            Submitted by: {s.student_name} ({s.student_email}) · Status: {s.status}
          </p>
          <div className="flex gap-2 mt-3">
            <button type="button" onClick={() => act(s.id, 'approve')} className="text-sm bg-emerald-600 text-white px-3 py-1.5 rounded-lg">
              Approve
            </button>
            <button type="button" onClick={() => act(s.id, 'reject')} className="text-sm bg-red-600 text-white px-3 py-1.5 rounded-lg">
              Reject
            </button>
          </div>
        </div>
      ))}
    </div>
  )
}
