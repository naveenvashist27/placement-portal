import { useEffect, useState } from 'react'
import api from '../services/api'
import { useToast } from '../components/Toast'
import FieldInput from '../components/FieldInput'
import { PROFILE_FIELDS, profileCompleteness, toInputValue } from '../profileFields'

const inputCls = 'mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm'

const STUDENT_FIELDS = PROFILE_FIELDS.filter((f) => !['full_name', 'email'].includes(f.key))

const errMsg = (err, fallback) => err.response?.data?.detail?.[0]?.msg || err.response?.data?.detail || fallback

// Form input string -> API value ('' becomes null, numbers/booleans are converted).
function toApiValue(field, value) {
  if (value === '' || value === null || value === undefined) return null
  if (field.type === 'number') return Number(value)
  if (field.type === 'yesno') return value === true || value === 'Yes'
  return value
}

export default function ProfilePage() {
  const { push } = useToast()
  const [profile, setProfile] = useState(null)
  const [pw, setPw] = useState({ current_password: '', new_password: '' })

  useEffect(() => {
    api.get('/api/profile').then((r) => setProfile(r.data))
  }, [])

  if (!profile) return <p className="text-slate-500 text-sm">Loading...</p>

  const isStudent = profile.role === 'STUDENT'
  const set = (k) => (e) => setProfile({ ...profile, [k]: e.target.value })

  const save = async (e) => {
    e.preventDefault()
    try {
      const { data } = await api.put('/api/profile', {
        full_name: profile.full_name,
        ...(isStudent && {
          ...Object.fromEntries(STUDENT_FIELDS.map((f) => [f.key, toApiValue(f, profile[f.key])])),
          bio: profile.bio || null,
        }),
      })
      setProfile(data)
      push('Profile updated', 'success')
    } catch (err) {
      push(errMsg(err, 'Update failed'), 'error')
    }
  }

  const changePassword = async (e) => {
    e.preventDefault()
    try {
      await api.post('/api/auth/change-password', pw)
      setPw({ current_password: '', new_password: '' })
      push('Password updated', 'success')
    } catch (err) {
      push(errMsg(err, 'Password change failed'), 'error')
    }
  }

  return (
    <div className="space-y-8 max-w-3xl">
      <h2 className="text-2xl font-semibold">Profile</h2>

      <form onSubmit={save} className="bg-white border rounded-xl p-6 space-y-4">
        <div>
          <label className="text-sm font-medium">Full name</label>
          <input className={inputCls} value={profile.full_name} onChange={set('full_name')} required />
        </div>
        <div>
          <label className="text-sm font-medium">Email</label>
          <input className={`${inputCls} bg-slate-50`} value={profile.email} disabled />
        </div>
        {isStudent && (
          <>
            <div className="rounded-lg bg-indigo-50 p-3 text-sm text-indigo-800">
              Profile {profileCompleteness(profile)}% complete. Registration forms use these details to fill
              themselves in, so keep them up to date.
            </div>
            <div className="grid sm:grid-cols-2 gap-4">
              {STUDENT_FIELDS.map((f) => (
                <div key={f.key}>
                  <label className="text-sm font-medium">{f.label}</label>
                  <FieldInput
                    field={f}
                    value={toInputValue(f.type, profile[f.key])}
                    onChange={(v) => setProfile({ ...profile, [f.key]: v })}
                  />
                </div>
              ))}
            </div>
            <div>
              <label className="text-sm font-medium">Bio</label>
              <textarea className={inputCls} rows={3} value={profile.bio || ''} onChange={set('bio')} />
            </div>
          </>
        )}
        <button type="submit" className="rounded-lg bg-indigo-600 text-white px-4 py-2 text-sm">
          Save changes
        </button>
      </form>

      <form onSubmit={changePassword} className="bg-white border rounded-xl p-6 space-y-4">
        <h3 className="font-semibold">Change password</h3>
        <div>
          <label className="text-sm font-medium">Current password</label>
          <input
            type="password"
            className={inputCls}
            value={pw.current_password}
            onChange={(e) => setPw({ ...pw, current_password: e.target.value })}
            required
          />
        </div>
        <div>
          <label className="text-sm font-medium">New password (min 8 characters)</label>
          <input
            type="password"
            minLength={8}
            className={inputCls}
            value={pw.new_password}
            onChange={(e) => setPw({ ...pw, new_password: e.target.value })}
            required
          />
        </div>
        <button type="submit" className="rounded-lg bg-slate-800 text-white px-4 py-2 text-sm">
          Update password
        </button>
      </form>
    </div>
  )
}
