import { useEffect, useState } from 'react'
import api from '../services/api'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../components/Toast'
import ResumeLink from '../components/ResumeLink'

const inputCls = 'mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm'
const errMsg = (err, fallback) => err.response?.data?.detail?.[0]?.msg || err.response?.data?.detail || fallback

// API value -> wording students and PCELL both understand.
const DIFFICULTY = {
  UNKNOWN: 'Not sure',
  EASY: 'Easy',
  MEDIUM: 'Medium',
  HARD: 'Hard',
}

const emptyDraft = {
  company_id: '',
  company_year_id: '',
  overall_experience: '',
  preparation_advice: '',
  difficulty: 'UNKNOWN',
  selection_outcome: '',
}

function SubmitForm({ onDone }) {
  const { push } = useToast()
  const [companies, setCompanies] = useState([])
  const [years, setYears] = useState([])
  const [draft, setDraft] = useState(emptyDraft)

  useEffect(() => {
    api.get('/api/companies', { params: { page_size: 100 } }).then((r) => setCompanies(r.data.items))
  }, [])

  const pickCompany = async (id) => {
    setDraft({ ...draft, company_id: id, company_year_id: '' })
    setYears(id ? (await api.get(`/api/companies/${id}/years`)).data : [])
  }

  const submit = async (e) => {
    e.preventDefault()
    try {
      await api.post('/api/experiences', {
        ...draft,
        company_id: Number(draft.company_id),
        company_year_id: Number(draft.company_year_id),
        preparation_advice: draft.preparation_advice || null,
        selection_outcome: draft.selection_outcome || null,
      })
      setDraft(emptyDraft)
      setYears([])
      push('Experience submitted for PCELL review', 'success')
      onDone()
    } catch (err) {
      push(errMsg(err, 'Submission failed'), 'error')
    }
  }

  return (
    <form onSubmit={submit} className="bg-white border rounded-xl p-5 space-y-3 max-w-2xl">
      <h3 className="font-semibold">Share your interview experience</h3>
      <div className="grid sm:grid-cols-2 gap-3">
        <select className={inputCls} value={draft.company_id} onChange={(e) => pickCompany(e.target.value)} required>
          <option value="">Select company</option>
          {companies.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </select>
        <select
          className={inputCls}
          value={draft.company_year_id}
          onChange={(e) => setDraft({ ...draft, company_year_id: e.target.value })}
          disabled={!years.length}
          required
        >
          <option value="">{draft.company_id && !years.length ? 'No visit years yet' : 'Select visit year'}</option>
          {years.map((y) => (
            <option key={y.id} value={y.id}>
              {y.visit_year}
            </option>
          ))}
        </select>
      </div>
      <textarea
        className={inputCls}
        rows={5}
        minLength={20}
        placeholder="Describe your overall experience (min 20 characters)"
        value={draft.overall_experience}
        onChange={(e) => setDraft({ ...draft, overall_experience: e.target.value })}
        required
      />
      <textarea
        className={inputCls}
        rows={2}
        placeholder="Preparation advice (optional)"
        value={draft.preparation_advice}
        onChange={(e) => setDraft({ ...draft, preparation_advice: e.target.value })}
      />
      <div className="grid sm:grid-cols-2 gap-3">
        <label className="text-sm font-medium">
          How difficult was the interview overall?
          <select className={inputCls} value={draft.difficulty} onChange={(e) => setDraft({ ...draft, difficulty: e.target.value })}>
            {Object.entries(DIFFICULTY).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
          <span className="block text-xs font-normal text-slate-500 mt-1">
            Helps juniors know how much to prepare. Pick "Not sure" if you can't judge.
          </span>
        </label>
        <label className="text-sm font-medium">
          Result (optional)
          <input
            className={inputCls}
            placeholder="e.g. Selected, Rejected after round 2"
            value={draft.selection_outcome}
            onChange={(e) => setDraft({ ...draft, selection_outcome: e.target.value })}
          />
        </label>
      </div>
      <button type="submit" className="rounded-lg bg-indigo-600 text-white px-4 py-2 text-sm">
        Submit experience
      </button>
    </form>
  )
}

// Shown to PCELL / TPO only, so they know who is submitting before approving.
function SubmitterDetails({ s }) {
  const rows = [
    ['Name', s.full_name],
    ['Email', s.email],
    ['Roll no.', s.roll_number],
    ['Course', s.course],
    ['Branch', s.branch],
    ['Batch', s.batch],
    ['Passing year', s.passing_year],
    ['Phone', s.phone],
  ]
  return (
    <dl className="mt-3 grid grid-cols-2 md:grid-cols-4 gap-x-4 gap-y-2 rounded-lg bg-slate-50 border p-3 text-sm">
      {rows.map(([label, value]) => (
        <div key={label}>
          <dt className="text-xs text-slate-500">{label}</dt>
          <dd className={value ? 'text-slate-800' : 'text-amber-600'}>{value || 'Not in profile'}</dd>
        </div>
      ))}
      <div>
        <dt className="text-xs text-slate-500">Resume</dt>
        <dd>
          <ResumeLink studentId={s.id} hasResume={s.has_resume} />
        </dd>
      </div>
    </dl>
  )
}

const STATUS_STYLE = {
  PENDING: 'bg-amber-50 text-amber-700',
  APPROVED: 'bg-emerald-50 text-emerald-700',
  REJECTED: 'bg-red-50 text-red-700',
}
const STATUS_TEXT = { PENDING: 'Waiting for PCELL review', APPROVED: 'Approved', REJECTED: 'Not approved' }

// A student's own submissions, including the PCELL's reason when one was rejected.
function MySubmissions({ refreshKey, companies }) {
  const [items, setItems] = useState([])

  useEffect(() => {
    api.get('/api/experiences', { params: { mine: true, page_size: 50 } }).then((r) => setItems(r.data.items))
  }, [refreshKey])

  if (items.length === 0) return null
  return (
    <section className="space-y-3">
      <h3 className="font-semibold">My submissions</h3>
      {items.map((e) => (
        <article key={e.id} className="hover-grow-soft bg-white border rounded-xl p-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <p className="font-medium">
              {companies[e.company_id] || `Company #${e.company_id}`}
              {e.visit_year && <span className="text-slate-500 font-normal"> · {e.visit_year}</span>}
            </p>
            <span className={`text-xs rounded-full px-3 py-1 ${STATUS_STYLE[e.status]}`}>{STATUS_TEXT[e.status]}</span>
          </div>
          <p className="mt-2 text-sm text-slate-700 whitespace-pre-wrap line-clamp-3">{e.overall_experience}</p>
          {e.status === 'REJECTED' && e.review_note && (
            <p className="mt-3 text-sm rounded-lg bg-red-50 text-red-800 p-3">
              <span className="font-medium">Reason from PCELL:</span> {e.review_note}
            </p>
          )}
        </article>
      ))}
    </section>
  )
}

export default function ExperiencesPage() {
  const { user } = useAuth()
  const { push } = useToast()
  const [items, setItems] = useState([])
  const [companies, setCompanies] = useState({})
  const [mineKey, setMineKey] = useState(0)
  const [rejecting, setRejecting] = useState(null)
  const [reason, setReason] = useState('')
  const isStudent = user?.role === 'STUDENT'
  const canReview = user?.role === 'PCELL_MEMBER' || user?.role === 'TPO'

  const load = () => api.get('/api/experiences').then((r) => setItems(r.data.items))

  useEffect(() => {
    load()
    api.get('/api/companies', { params: { page_size: 100 } }).then((r) =>
      setCompanies(Object.fromEntries(r.data.items.map((c) => [c.id, c.name]))),
    )
  }, [])

  const review = async (id, action, note) => {
    try {
      await api.post(`/api/experiences/${id}/${action}`, { note: note || null })
      push(`Experience ${action}d`, 'success')
      setRejecting(null)
      setReason('')
      load()
    } catch (err) {
      push(errMsg(err, 'Action failed'), 'error')
    }
  }

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-semibold">Interview experiences</h2>
      {isStudent && (
        <SubmitForm
          onDone={() => {
            load()
            setMineKey((k) => k + 1)
          }}
        />
      )}
      {isStudent && <MySubmissions refreshKey={mineKey} companies={companies} />}
      <div className="space-y-3">
        {items.length === 0 && <p className="text-sm text-slate-500">No experiences yet.</p>}
        {items.map((e) => (
          <article key={e.id} className="hover-grow-soft bg-white border rounded-xl p-5">
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="font-medium">
                  {companies[e.company_id] || `Company #${e.company_id}`}
                  {e.visit_year && <span className="text-slate-500 font-normal"> · {e.visit_year}</span>}
                  {e.role_title && <span className="text-slate-500 font-normal"> · {e.role_title}</span>}
                </p>
                <p className="text-xs text-slate-500 mt-0.5">
                  Difficulty: {DIFFICULTY[e.difficulty] || e.difficulty}
                  {e.selection_outcome && ` · Result: ${e.selection_outcome}`}
                  {canReview && ` · Status: ${e.status}`}
                </p>
              </div>
              {canReview && e.status === 'PENDING' && (
                <div className="flex gap-3 text-sm">
                  <button type="button" className="text-emerald-600" onClick={() => review(e.id, 'approve')}>
                    Approve
                  </button>
                  <button type="button" className="text-red-600" onClick={() => setRejecting(e.id)}>
                    Reject
                  </button>
                </div>
              )}
            </div>
            {canReview && e.submitter && <SubmitterDetails s={e.submitter} />}
            {rejecting === e.id && (
              <div className="mt-3 rounded-lg border border-red-200 bg-red-50 p-3 space-y-2">
                <label className="text-sm font-medium text-red-800">
                  Reason for rejecting (the student will see this)
                  <textarea
                    className={`${inputCls} bg-white`}
                    rows={2}
                    value={reason}
                    onChange={(ev) => setReason(ev.target.value)}
                    placeholder="e.g. Please add details about the technical rounds"
                  />
                </label>
                <div className="flex gap-3 text-sm">
                  <button
                    type="button"
                    disabled={reason.trim().length < 3}
                    className="rounded-lg bg-red-600 text-white px-3 py-1.5 disabled:opacity-50"
                    onClick={() => review(e.id, 'reject', reason.trim())}
                  >
                    Confirm reject
                  </button>
                  <button type="button" className="text-slate-600" onClick={() => setRejecting(null)}>
                    Cancel
                  </button>
                </div>
              </div>
            )}
            <p className="mt-2 text-slate-800 whitespace-pre-wrap">{e.overall_experience}</p>
            {e.preparation_advice && (
              <p className="mt-3 text-sm text-indigo-900 bg-indigo-50 rounded-lg p-3">{e.preparation_advice}</p>
            )}
          </article>
        ))}
      </div>
    </div>
  )
}
