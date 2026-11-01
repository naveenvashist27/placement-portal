import { useEffect, useState } from 'react'
import api from '../services/api'
import { useToast } from '../components/Toast'

export default function ResumePage() {
  const [resume, setResume] = useState(null)
  const { push } = useToast()

  const load = () =>
    api
      .get('/api/resumes/me')
      .then((r) => setResume(r.data))
      .catch(() => setResume(null))

  useEffect(() => {
    load()
  }, [])

  const upload = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    const form = new FormData()
    form.append('file', file)
    try {
      await api.post('/api/resumes/upload', form, { headers: { 'Content-Type': 'multipart/form-data' } })
      push('Resume uploaded and skills extracted', 'success')
      load()
    } catch (err) {
      push(err.response?.data?.detail || 'Upload failed', 'error')
    }
  }

  // The file is behind login, so fetch it with the auth header and open the blob.
  const view = async () => {
    try {
      const { data } = await api.get(`/api/resumes/${resume.id}/file`, { responseType: 'blob' })
      window.open(URL.createObjectURL(data), '_blank')
    } catch {
      push('Could not open the resume', 'error')
    }
  }

  return (
    <div className="space-y-6 max-w-2xl">
      <h2 className="text-2xl font-semibold">Resume</h2>
      <p className="text-sm text-slate-500">Upload PDF → extract text → detect skills (no role comparison).</p>
      <label className="inline-flex items-center rounded-lg bg-indigo-600 text-white px-4 py-2 text-sm cursor-pointer">
        Upload / replace PDF
        <input type="file" accept="application/pdf" className="hidden" onChange={upload} />
      </label>
      {resume && (
        <div className="hover-grow-soft bg-white border rounded-xl p-5">
          <button type="button" onClick={view} className="text-sm text-indigo-600 hover:underline mb-3">
            View my uploaded resume
          </button>
          <p className="text-sm text-slate-500">Detected skills</p>
          <div className="flex flex-wrap gap-2 mt-3">
            {resume.skills?.map((s) => (
              <span key={s} className="text-sm bg-slate-100 rounded-full px-3 py-1">
                {s}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
