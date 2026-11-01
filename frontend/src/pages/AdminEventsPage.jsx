import { useEffect, useState } from 'react'
import api from '../services/api'
import { useToast } from '../components/Toast'
import { FIELD_TYPES, PROFILE_FIELDS, profileField } from '../profileFields'

const inputCls = 'mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm'
const errMsg = (err, fallback) => err.response?.data?.detail?.[0]?.msg || err.response?.data?.detail || fallback

const emptyEvent = { title: '', description: '', status: 'DRAFT' }
const emptyRules = {
  min_cgpa: '',
  min_tenth_percentage: '',
  min_twelfth_percentage: '',
  no_atkt: false,
  courses: '',
  batches: '',
  passing_years: '',
}
const emptyForm = { title: '', description: '', registration_deadline: '', external_link: '', status: 'OPEN', fields: [], eligibility: emptyRules }

function StatusSelect({ value, onChange, options }) {
  return (
    <select className={inputCls} value={value} onChange={onChange}>
      {options.map((o) => (
        <option key={o}>{o}</option>
      ))}
    </select>
  )
}

function Events() {
  const { push } = useToast()
  const [items, setItems] = useState([])
  const [draft, setDraft] = useState(emptyEvent)

  const load = () => api.get('/api/events').then((r) => setItems(r.data.items))

  useEffect(() => {
    load()
  }, [])

  const create = async (e) => {
    e.preventDefault()
    try {
      await api.post('/api/events', draft)
      setDraft(emptyEvent)
      push('Event created', 'success')
      load()
    } catch (err) {
      push(errMsg(err, 'Could not create event'), 'error')
    }
  }

  const setStatus = async (ev, status) => {
    await api.put(`/api/events/${ev.id}`, {
      title: ev.title,
      description: ev.description,
      company_id: ev.company_id,
      registration_deadline: ev.registration_deadline,
      status,
    })
    load()
  }

  const remove = async (id) => {
    if (!window.confirm('Delete this event?')) return
    await api.delete(`/api/events/${id}`)
    load()
  }

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-semibold">Events & announcements</h2>
      <form onSubmit={create} className="bg-white border rounded-xl p-5 space-y-3 max-w-2xl">
        <h3 className="font-semibold">New event</h3>
        <input className={inputCls} placeholder="Title" value={draft.title} onChange={(e) => setDraft({ ...draft, title: e.target.value })} required />
        <textarea className={inputCls} rows={3} placeholder="Description" value={draft.description} onChange={(e) => setDraft({ ...draft, description: e.target.value })} required />
        <StatusSelect value={draft.status} onChange={(e) => setDraft({ ...draft, status: e.target.value })} options={['DRAFT', 'PUBLISHED']} />
        <button type="submit" className="rounded-lg bg-indigo-600 text-white px-4 py-2 text-sm">
          Create event
        </button>
      </form>
      <div className="space-y-3">
        {items.map((ev) => (
          <div key={ev.id} className="hover-grow-soft bg-white border rounded-xl p-5 flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="font-medium">{ev.title}</p>
              <p className="text-sm text-slate-600 mt-1">{ev.description}</p>
              <p className="text-xs text-slate-500 mt-2">Status: {ev.status}</p>
            </div>
            <div className="flex gap-3 text-sm">
              {ev.status !== 'PUBLISHED' && (
                <button type="button" className="text-emerald-600" onClick={() => setStatus(ev, 'PUBLISHED')}>
                  Publish
                </button>
              )}
              {ev.status === 'PUBLISHED' && (
                <button type="button" className="text-amber-600" onClick={() => setStatus(ev, 'CLOSED')}>
                  Close
                </button>
              )}
              <button type="button" className="text-red-600" onClick={() => remove(ev.id)}>
                Delete
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

// Builds the list of questions a student answers when registering.
// Profile-linked questions are pre-filled from the student's profile; custom ones start empty.
function FieldBuilder({ fields, onChange }) {
  const update = (i, patch) => onChange(fields.map((f, idx) => (idx === i ? { ...f, ...patch } : f)))
  const remove = (i) => onChange(fields.filter((_, idx) => idx !== i))
  const used = new Set(fields.map((f) => f.profile_key).filter(Boolean))

  const addProfile = (key) => {
    if (!key) return
    const p = profileField(key)
    onChange([
      ...fields,
      { key, label: p.label, type: p.type, required: false, profile_key: key, options: (p.options || []).join(', ') },
    ])
  }
  const addCustom = () =>
    onChange([...fields, { key: `q_${Date.now()}`, label: '', type: 'text', required: false, profile_key: '', options: '' }])

  return (
    <div className="space-y-3">
      <p className="text-sm font-medium">Questions students answer</p>
      <p className="text-xs text-slate-500">
        Profile questions are filled in automatically from the student's profile; they only correct what changed.
      </p>
      {fields.map((f, i) => (
        <div key={f.key} className="rounded-lg border border-slate-200 p-3 space-y-2">
          <div className="flex flex-wrap gap-2 items-center">
            <input
              className={`${inputCls} flex-1 min-w-[12rem] !mt-0`}
              placeholder="Question"
              value={f.label}
              onChange={(e) => update(i, { label: e.target.value })}
              required
            />
            <select
              className={`${inputCls} !w-auto !mt-0`}
              value={f.type}
              disabled={!!f.profile_key}
              onChange={(e) => update(i, { type: e.target.value })}
            >
              {FIELD_TYPES.map(([v, l]) => (
                <option key={v} value={v}>
                  {l}
                </option>
              ))}
            </select>
            <label className="text-sm flex items-center gap-1">
              <input type="checkbox" checked={f.required} onChange={(e) => update(i, { required: e.target.checked })} />
              Required
            </label>
            <button type="button" className="text-red-600 text-sm" onClick={() => remove(i)}>
              Remove
            </button>
          </div>
          {f.profile_key && (
            <p className="text-xs text-indigo-600">Auto-filled from profile: {profileField(f.profile_key).label}</p>
          )}
          {f.type === 'select' && !f.profile_key && (
            <input
              className={inputCls}
              placeholder="Options, comma separated (e.g. Yes, No, Maybe)"
              value={f.options}
              onChange={(e) => update(i, { options: e.target.value })}
              required
            />
          )}
        </div>
      ))}
      <div className="flex flex-wrap gap-2 items-center">
        <select className={`${inputCls} !w-auto !mt-0`} value="" onChange={(e) => addProfile(e.target.value)}>
          <option value="">+ Add from student profile</option>
          {PROFILE_FIELDS.filter((p) => !used.has(p.key)).map((p) => (
            <option key={p.key} value={p.key}>
              {p.label}
            </option>
          ))}
        </select>
        <button
          type="button"
          className="rounded-lg border border-indigo-600 text-indigo-600 px-3 py-2 text-sm"
          onClick={addCustom}
        >
          + Add custom question
        </button>
      </div>
    </div>
  )
}

const parseJson = (json, fallback) => {
  try {
    return json ? JSON.parse(json) : fallback
  } catch {
    return fallback
  }
}

const splitOptions = (o) => (typeof o === 'string' ? o.split(',').map((x) => x.trim()).filter(Boolean) : o)

const serializeFields = (fields) =>
  JSON.stringify(
    fields.map((f) => ({
      key: f.key,
      label: f.label.trim(),
      type: f.type,
      required: f.required,
      profile_key: f.profile_key || null,
      options: f.type === 'select' ? splitOptions(f.options) : [],
    })),
  )

// Who may register. Students who don't meet these are told why and can't submit.
function EligibilityEditor({ rules, onChange }) {
  const set = (k) => (e) => onChange({ ...rules, [k]: e.target.type === 'checkbox' ? e.target.checked : e.target.value })
  const num = (k, label, max) => (
    <label className="text-sm">
      {label}
      <input type="number" min={0} max={max} step="0.01" className={inputCls} value={rules[k]} onChange={set(k)} placeholder="No minimum" />
    </label>
  )
  return (
    <div className="rounded-lg border border-slate-200 p-3 space-y-3">
      <p className="text-sm font-medium">Eligibility (optional)</p>
      <p className="text-xs text-slate-500">
        Checked against the student's profile when they register. Leave blank for no restriction.
      </p>
      <div className="grid sm:grid-cols-3 gap-3">
        {num('min_cgpa', 'Minimum CGPA', 10)}
        {num('min_tenth_percentage', 'Minimum 10th %', 100)}
        {num('min_twelfth_percentage', 'Minimum 12th %', 100)}
      </div>
      <label className="text-sm flex items-center gap-2">
        <input type="checkbox" checked={rules.no_atkt} onChange={set('no_atkt')} />
        Only students with no current ATKT
      </label>
      <div className="grid sm:grid-cols-3 gap-3">
        <label className="text-sm">
          Courses
          <input className={inputCls} value={rules.courses} onChange={set('courses')} placeholder="MBA Tech, B.Tech" />
        </label>
        <label className="text-sm">
          Batches
          <input className={inputCls} value={rules.batches} onChange={set('batches')} placeholder="2022-2027" />
        </label>
        <label className="text-sm">
          Passing years
          <input className={inputCls} value={rules.passing_years} onChange={set('passing_years')} placeholder="2026, 2027" />
        </label>
      </div>
    </div>
  )
}

const csv = (v) => String(v).split(',').map((x) => x.trim()).filter(Boolean)

const serializeRules = (r) =>
  JSON.stringify({
    min_cgpa: r.min_cgpa === '' ? null : Number(r.min_cgpa),
    min_tenth_percentage: r.min_tenth_percentage === '' ? null : Number(r.min_tenth_percentage),
    min_twelfth_percentage: r.min_twelfth_percentage === '' ? null : Number(r.min_twelfth_percentage),
    no_atkt: r.no_atkt,
    courses: csv(r.courses),
    batches: csv(r.batches),
    passing_years: csv(r.passing_years).map(Number),
  })

const rulesFromJson = (json) => {
  const r = parseJson(json, {})
  return {
    min_cgpa: r.min_cgpa ?? '',
    min_tenth_percentage: r.min_tenth_percentage ?? '',
    min_twelfth_percentage: r.min_twelfth_percentage ?? '',
    no_atkt: !!r.no_atkt,
    courses: (r.courses || []).join(', '),
    batches: (r.batches || []).join(', '),
    passing_years: (r.passing_years || []).join(', '),
  }
}

function Registrations() {
  const { push } = useToast()
  const [forms, setForms] = useState([])
  const [draft, setDraft] = useState(emptyForm)
  const [openId, setOpenId] = useState(null)
  const [regs, setRegs] = useState([])
  const [editingId, setEditingId] = useState(null)

  const load = () => api.get('/api/registrations/forms').then((r) => setForms(r.data.items))

  useEffect(() => {
    load()
  }, [])

  const create = async (e) => {
    e.preventDefault()
    try {
      const { fields, eligibility, ...rest } = draft
      const body = {
        ...rest,
        registration_deadline: new Date(draft.registration_deadline).toISOString(),
        external_link: draft.external_link || null,
        form_fields_json: fields.length ? serializeFields(fields) : null,
        eligibility_json: serializeRules(eligibility),
      }
      if (editingId) await api.put(`/api/registrations/forms/${editingId}`, body)
      else await api.post('/api/registrations/forms', body)
      setDraft(emptyForm)
      setEditingId(null)
      push(editingId ? 'Registration form updated' : 'Registration form created', 'success')
      load()
    } catch (err) {
      push(errMsg(err, editingId ? 'Could not update form' : 'Could not create form'), 'error')
    }
  }

  const startEdit = (f) => {
    const deadline = new Date(f.registration_deadline)
    deadline.setMinutes(deadline.getMinutes() - deadline.getTimezoneOffset())
    setDraft({
      title: f.title,
      description: f.description,
      registration_deadline: deadline.toISOString().slice(0, 16),
      external_link: f.external_link || '',
      status: f.status,
      eligibility: rulesFromJson(f.eligibility_json),
      fields: parseJson(f.form_fields_json, []).map((x) => ({
        ...x,
        profile_key: x.profile_key || '',
        options: (x.options || []).join(', '),
      })),
    })
    setEditingId(f.id)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const cancelEdit = () => {
    setDraft(emptyForm)
    setEditingId(null)
  }

  const exportCsv = async (f) => {
    try {
      const { data } = await api.get(`/api/registrations/forms/${f.id}/export.csv`, { responseType: 'blob' })
      const url = URL.createObjectURL(data)
      const a = document.createElement('a')
      a.href = url
      a.download = `${f.title.replace(/[^a-z0-9]+/gi, '_')}_registrations.csv`
      a.click()
      URL.revokeObjectURL(url)
    } catch (err) {
      push(errMsg(err, 'Could not export registrations'), 'error')
    }
  }

  const setStatus = async (f, status) => {
    await api.put(`/api/registrations/forms/${f.id}`, {
      title: f.title,
      description: f.description,
      company_id: f.company_id,
      role_id: f.role_id,
      registration_deadline: f.registration_deadline,
      external_link: f.external_link,
      status,
    })
    load()
  }

  const remove = async (id) => {
    if (!window.confirm('Delete this form and its registrations?')) return
    await api.delete(`/api/registrations/forms/${id}`)
    load()
  }

  const toggleRegs = async (id) => {
    if (openId === id) return setOpenId(null)
    const { data } = await api.get(`/api/registrations/forms/${id}/registrations`)
    setRegs(data.items)
    setOpenId(id)
  }

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-semibold">Registration forms</h2>
      <form onSubmit={create} className="bg-white border rounded-xl p-5 space-y-3 max-w-2xl">
        <h3 className="font-semibold">{editingId ? 'Edit registration form' : 'New registration form'}</h3>
        {editingId && (
          <p className="text-xs text-amber-700">
            Students who already registered keep their saved answers, even if you change the questions.
          </p>
        )}
        <input className={inputCls} placeholder="Title" value={draft.title} onChange={(e) => setDraft({ ...draft, title: e.target.value })} required />
        <textarea className={inputCls} rows={3} placeholder="Description" value={draft.description} onChange={(e) => setDraft({ ...draft, description: e.target.value })} required />
        <label className="text-sm font-medium block">
          Registration deadline
          <input type="datetime-local" className={inputCls} value={draft.registration_deadline} onChange={(e) => setDraft({ ...draft, registration_deadline: e.target.value })} required />
        </label>
        <input className={inputCls} placeholder="External link (optional)" value={draft.external_link} onChange={(e) => setDraft({ ...draft, external_link: e.target.value })} />
        <FieldBuilder fields={draft.fields} onChange={(fields) => setDraft({ ...draft, fields })} />
        <EligibilityEditor rules={draft.eligibility} onChange={(eligibility) => setDraft({ ...draft, eligibility })} />
        <StatusSelect value={draft.status} onChange={(e) => setDraft({ ...draft, status: e.target.value })} options={editingId ? ['DRAFT', 'OPEN', 'CLOSED'] : ['DRAFT', 'OPEN']} />
        <div className="flex gap-3 items-center">
          <button type="submit" className="rounded-lg bg-indigo-600 text-white px-4 py-2 text-sm">
            {editingId ? 'Save changes' : 'Create form'}
          </button>
          {editingId && (
            <button type="button" className="text-sm text-slate-600" onClick={cancelEdit}>
              Cancel
            </button>
          )}
        </div>
      </form>
      <div className="space-y-3">
        {forms.map((f) => (
          <div key={f.id} className="bg-white border rounded-xl p-5">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="font-medium">{f.title}</p>
                <p className="text-sm text-slate-600 mt-1">{f.description}</p>
                <p className="text-xs text-slate-500 mt-2">
                  Deadline: {new Date(f.registration_deadline).toLocaleString()} · Status: {f.status}
                </p>
              </div>
              <div className="flex flex-wrap gap-x-3 gap-y-1 text-sm">
                <button type="button" className="text-indigo-600" onClick={() => toggleRegs(f.id)}>
                  {openId === f.id ? 'Hide registrations' : 'View registrations'}
                </button>
                <button type="button" className="text-indigo-600" onClick={() => exportCsv(f)}>
                  Export CSV
                </button>
                <button type="button" className="text-slate-700" onClick={() => startEdit(f)}>
                  Edit
                </button>
                {f.status === 'DRAFT' && (
                  <button type="button" className="text-emerald-600" onClick={() => setStatus(f, 'OPEN')}>
                    Open
                  </button>
                )}
                {f.status === 'OPEN' && (
                  <button type="button" className="text-amber-600" onClick={() => setStatus(f, 'CLOSED')}>
                    Close
                  </button>
                )}
                <button type="button" className="text-red-600" onClick={() => remove(f.id)}>
                  Delete
                </button>
              </div>
            </div>
            {openId === f.id && (() => {
              const cols = parseJson(f.form_fields_json, [])
              return (
                <div className="overflow-x-auto mt-4 border-t">
                  <table className="w-full text-sm">
                    <thead className="text-left text-slate-500">
                      <tr>
                        <th className="py-2 pr-4">Student</th>
                        <th className="py-2 pr-4">Email</th>
                        {cols.map((c) => (
                          <th key={c.key} className="py-2 pr-4 whitespace-nowrap">
                            {c.label}
                          </th>
                        ))}
                        <th className="py-2 pr-4">Registered</th>
                      </tr>
                    </thead>
                    <tbody>
                      {regs.map((r) => {
                        const data = parseJson(r.responses_json, {})
                        return (
                          <tr key={r.id} className="border-t">
                            <td className="py-2 pr-4">{r.student_name}</td>
                            <td className="py-2 pr-4">{r.student_email}</td>
                            {cols.map((c) => (
                              <td key={c.key} className="py-2 pr-4">
                                {data[c.key] ?? '—'}
                              </td>
                            ))}
                            <td className="py-2 pr-4 whitespace-nowrap">{new Date(r.created_at).toLocaleString()}</td>
                          </tr>
                        )
                      })}
                      {regs.length === 0 && (
                        <tr>
                          <td colSpan={cols.length + 3} className="py-3 text-slate-500">
                            No registrations yet.
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              )
            })()}
          </div>
        ))}
      </div>
    </div>
  )
}

export default function AdminEventsPage({ section }) {
  return section === 'registrations' ? <Registrations /> : <Events />
}
