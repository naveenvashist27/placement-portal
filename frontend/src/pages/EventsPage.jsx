import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../services/api'
import { useToast } from '../components/Toast'
import FieldInput from '../components/FieldInput'
import { toInputValue } from '../profileFields'

const parseFields = (json) => {
  try {
    return json ? JSON.parse(json) : []
  } catch {
    return []
  }
}

// Starting answers: profile-linked questions are pre-filled from the student's profile, the rest are empty.
const initialAnswers = (fields, profile) =>
  Object.fromEntries(
    fields.map((f) => [f.key, f.profile_key && profile ? toInputValue(f.type, profile[f.profile_key]) : '']),
  )

function RegistrationCard({ form, profile, registered, onRegistered }) {
  const { push } = useToast()
  const fields = parseFields(form.form_fields_json)
  const [open, setOpen] = useState(false)
  const [answers, setAnswers] = useState({})
  const [saving, setSaving] = useState(false)

  const start = () => {
    setAnswers(initialAnswers(fields, profile))
    setOpen(true)
  }

  const submit = async (e) => {
    e.preventDefault()
    setSaving(true)
    try {
      await api.post(`/api/registrations/forms/${form.id}/register`, { responses: answers })
      push('Registered successfully', 'success')
      setOpen(false)
      onRegistered(form.id)
    } catch (err) {
      const detail = err.response?.data?.detail
      push(Array.isArray(detail) ? detail[0]?.msg : detail || 'Registration failed', 'error')
    } finally {
      setSaving(false)
    }
  }

  const ineligible = form.ineligible_reasons?.length > 0
  const prefilled = fields.filter((f) => f.profile_key && answers[f.key] !== '' && answers[f.key] !== undefined)
  const missingProfile = fields.filter((f) => f.profile_key && f.profile_key !== 'email' && answers[f.key] === '')

  return (
    <div id={`form-${form.id}`} className="bg-white border rounded-xl p-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="font-medium">{form.title}</p>
          <p className="text-sm text-slate-500">{form.description}</p>
          <p className="text-sm mt-1">
            Deadline: {new Date(form.registration_deadline).toLocaleString()} · Status:{' '}
            <span className="font-semibold">{form.status}</span>
          </p>
          {form.eligibility_summary?.length > 0 && (
            <p className="text-sm mt-1 text-slate-600">
              <span className="font-medium">Eligibility:</span> {form.eligibility_summary.join(' · ')}
            </p>
          )}
          {form.external_link && (
            <a href={form.external_link} target="_blank" rel="noreferrer" className="text-sm text-indigo-600 hover:underline">
              Open external link
            </a>
          )}
        </div>
        {registered ? (
          <span className="rounded-lg bg-emerald-50 text-emerald-700 px-4 py-2 text-sm font-medium">Registered ✓</span>
        ) : form.status !== 'OPEN' ? (
          <span className="text-sm text-slate-400">Closed</span>
        ) : ineligible ? (
          <span className="text-sm text-red-600 font-medium">Not eligible</span>
        ) : !open ? (
          <button
            type="button"
            onClick={fields.length ? start : () => submit({ preventDefault() {} })}
            className="rounded-lg bg-indigo-600 text-white px-4 py-2 text-sm"
          >
            Register now
          </button>
        ) : null}
      </div>

      {ineligible && !registered && form.status === 'OPEN' && (
        <div className="mt-3 rounded-lg bg-red-50 text-red-800 p-3 text-sm">
          <p className="font-medium">You can't register for this one yet:</p>
          <ul className="list-disc ml-5 mt-1">
            {form.ineligible_reasons.map((r) => (
              <li key={r}>{r}</li>
            ))}
          </ul>
          <p className="mt-2">
            If your profile is out of date,{' '}
            <Link to="/profile" className="underline">
              update it
            </Link>{' '}
            and come back.
          </p>
        </div>
      )}

      {open && !registered && (
        <form onSubmit={submit} className="mt-4 border-t pt-4 space-y-4">
          {prefilled.length > 0 && (
            <div className="rounded-lg bg-indigo-50 p-3 text-sm text-indigo-800">
              {prefilled.length} detail{prefilled.length > 1 ? 's were' : ' was'} filled in from your profile. Check them
              and correct anything that has changed; corrections also update your profile.
            </div>
          )}
          {missingProfile.length > 0 && (
            <p className="text-sm text-amber-700">
              Some profile details are empty, so fill them in below. They will be saved to your profile for next time (
              <Link to="/profile" className="underline">
                or edit your profile
              </Link>
              ).
            </p>
          )}
          <div className="grid sm:grid-cols-2 gap-4">
            {fields.map((f) => (
              <div key={f.key} className={f.type === 'textarea' ? 'sm:col-span-2' : ''}>
                <label className="text-sm font-medium">
                  {f.label}
                  {f.required && <span className="text-red-600"> *</span>}
                  {f.profile_key && <span className="ml-2 text-xs font-normal text-indigo-600">from profile</span>}
                </label>
                <FieldInput
                  field={f}
                  value={answers[f.key] ?? ''}
                  onChange={(v) => setAnswers({ ...answers, [f.key]: v })}
                  required={f.required}
                  disabled={f.profile_key === 'email'}
                />
              </div>
            ))}
          </div>
          <div className="flex gap-3">
            <button
              type="submit"
              disabled={saving}
              className="rounded-lg bg-indigo-600 text-white px-4 py-2 text-sm disabled:opacity-60"
            >
              {saving ? 'Submitting...' : 'Submit registration'}
            </button>
            <button type="button" onClick={() => setOpen(false)} className="text-sm text-slate-600">
              Cancel
            </button>
          </div>
        </form>
      )}
    </div>
  )
}

export default function EventsPage() {
  const [forms, setForms] = useState([])
  const [events, setEvents] = useState([])
  const [profile, setProfile] = useState(null)
  const [registeredIds, setRegisteredIds] = useState([])

  useEffect(() => {
    api.get('/api/registrations/forms').then((r) => setForms(r.data.items))
    api.get('/api/events').then((r) => setEvents(r.data.items))
    api.get('/api/profile').then((r) => setProfile(r.data))
    api.get('/api/registrations/forms/mine').then((r) => setRegisteredIds(r.data.form_ids))
  }, [])

  // Registering can change profile values (corrections), so reload it for the next form.
  const onRegistered = (formId) => {
    setRegisteredIds((ids) => [...ids, formId])
    api.get('/api/profile').then((r) => setProfile(r.data))
  }

  return (
    <div className="space-y-8">
      <h2 className="text-2xl font-semibold">Events & announcements</h2>

      <section className="space-y-3">
        <h3 className="font-semibold">Registration forms</h3>
        {forms.map((f) => (
          <RegistrationCard
            key={f.id}
            form={f}
            profile={profile}
            registered={registeredIds.includes(f.id)}
            onRegistered={onRegistered}
          />
        ))}
        {forms.length === 0 && <p className="text-sm text-slate-500">No registration forms right now.</p>}
      </section>

      <section className="space-y-3">
        <h3 className="font-semibold">Announcements</h3>
        {events.map((e) => (
          <div key={e.id} className="hover-grow-soft bg-white border rounded-xl p-5">
            <p className="font-medium">{e.title}</p>
            <p className="text-sm text-slate-600 mt-1">{e.description}</p>
          </div>
        ))}
      </section>
    </div>
  )
}
