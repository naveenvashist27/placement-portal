import { useState } from 'react'
import api from '../services/api'
import { useToast } from './Toast'

// PCELL / TPO: opens a student's uploaded resume (it sits behind login, so it is fetched with the auth header).
export default function ResumeLink({ studentId, hasResume }) {
  const { push } = useToast()
  const [loading, setLoading] = useState(false)

  if (!hasResume) return <span className="text-amber-600">Not uploaded</span>

  const open = async () => {
    setLoading(true)
    try {
      const { data } = await api.get(`/api/resumes/by-student/${studentId}/file`, { responseType: 'blob' })
      window.open(URL.createObjectURL(data), '_blank')
    } catch {
      push('Could not open the resume', 'error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <button type="button" onClick={open} disabled={loading} className="text-indigo-600 hover:underline disabled:opacity-60">
      {loading ? 'Opening...' : 'View resume'}
    </button>
  )
}
