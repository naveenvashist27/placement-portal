import { useState } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../components/Toast'
import GoogleSignInButton from '../components/GoogleSignInButton'
import api from '../services/api'
import logo from '../assets/iips-logo.png'
import campus from '../assets/iips-campus.png'

const inputCls = 'mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm'
const emptyDetails = { roll_number: '', course: '', batch: '', phone: '' }
const detailFields = [
  ['roll_number', 'Roll number', true],
  ['course', 'Course (e.g. MBA Tech, MCA)', true],
  ['batch', 'Batch (e.g. 2023-2028)', true],
  ['phone', 'Phone (optional)', false],
]

function homeFor(role) {
  if (role === 'TPO') return '/tpo'
  if (role === 'PCELL_MEMBER') return '/admin'
  return '/'
}

export default function LoginPage() {
  const { user, login, loginWithToken } = useAuth()
  const { push } = useToast()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [showStaff, setShowStaff] = useState(false)
  // step: 'login' | 'details' (first Google sign-in) | 'pending' (request sent)
  const [step, setStep] = useState('login')
  const [credential, setCredential] = useState(null)
  const [googleUser, setGoogleUser] = useState(null)
  const [details, setDetails] = useState(emptyDetails)

  if (user) return <Navigate to={homeFor(user.role)} replace />

  const googleSignIn = async (cred, extra) => {
    setLoading(true)
    try {
      const { data } = await api.post('/api/auth/google', { credential: cred, details: extra || null })
      if (data.status === 'OK') {
        const u = await loginWithToken(data.access_token)
        push('Welcome back', 'success')
        navigate(homeFor(u.role))
      } else if (data.status === 'DETAILS_REQUIRED') {
        setCredential(cred)
        setGoogleUser({ email: data.email, name: data.full_name })
        setStep('details')
      } else {
        setGoogleUser({ email: data.email, name: data.full_name })
        setStep('pending')
      }
    } catch (err) {
      push(err.response?.data?.detail || 'Google sign-in failed', 'error')
      setStep('login')
    } finally {
      setLoading(false)
    }
  }

  const submitDetails = (e) => {
    e.preventDefault()
    googleSignIn(credential, { ...details, phone: details.phone || null })
  }

  const submit = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      const u = await login(email, password)
      push('Welcome back', 'success')
      navigate(homeFor(u.role))
    } catch (err) {
      push(err.response?.data?.detail || 'Login failed', 'error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex">
      <div
        className="hidden lg:flex lg:w-1/2 relative text-white bg-cover bg-center"
        style={{ backgroundImage: `url(${campus})` }}
      >
        <div className="absolute inset-0 bg-gradient-to-t from-indigo-950 via-indigo-900/80 to-indigo-900/50" />
        <div className="relative z-10 flex flex-col justify-between p-12 w-full">
          <img src={logo} alt="IIPS DAVV logo" className="h-28 w-28 rounded-full bg-white p-2 object-contain shadow-lg" />
          <div>
            <p className="text-amber-300 uppercase tracking-widest text-xs font-medium">Training &amp; Placement Cell</p>
            <h1 className="text-4xl font-bold mt-2 leading-tight">International Institute of Professional Studies</h1>
            <p className="text-lg mt-2 text-indigo-100">Devi Ahilya Vishwavidyalaya, Indore</p>
            <p className="mt-6 text-indigo-200 italic">तमसो मा ज्योतिर्गमय</p>
          </div>
        </div>
      </div>

      <div className="flex-1 flex items-center justify-center bg-slate-50 px-4 py-10">
        <div className="w-full max-w-md">
          <div className="lg:hidden flex items-center gap-3 mb-6">
            <img src={logo} alt="IIPS DAVV logo" className="h-16 w-16 object-contain" />
            <div className="leading-tight">
              <p className="font-semibold text-indigo-900">IIPS, DAVV Indore</p>
              <p className="text-xs text-slate-500">Training &amp; Placement Portal</p>
            </div>
          </div>
          <div className="bg-white rounded-2xl shadow-xl border-t-4 border-amber-400 p-8">
            <h1 className="text-2xl font-semibold text-indigo-900">Placement Portal</h1>

            {step === 'login' && (
              <>
                <p className="text-sm text-slate-500 mt-1">Students: sign in with your Google account</p>
                <div className="mt-6">
                  <GoogleSignInButton onCredential={(c) => googleSignIn(c)} onError={(m) => push(m, 'error')} />
                </div>
                <p className="mt-4 text-xs text-slate-500 text-center">
                  First time? Sign in with Google and send your request. Once the placement cell approves it, you can sign
                  in and use the portal.
                </p>

                <div className="mt-8 border-t pt-4">
                  <button type="button" onClick={() => setShowStaff((v) => !v)} className="text-sm text-indigo-600">
                    {showStaff ? 'Hide staff login' : 'TPO / PCELL staff login'}
                  </button>
                  {showStaff && (
                    <form onSubmit={submit} className="mt-4 space-y-4">
                      <div>
                        <label className="text-sm font-medium text-slate-700">Email</label>
                        <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} className={inputCls} required />
                      </div>
                      <div>
                        <label className="text-sm font-medium text-slate-700">Password</label>
                        <input
                          type="password"
                          value={password}
                          onChange={(e) => setPassword(e.target.value)}
                          className={inputCls}
                          required
                        />
                      </div>
                      <button
                        type="submit"
                        disabled={loading}
                        className="w-full rounded-lg bg-indigo-600 text-white py-2.5 text-sm font-medium hover:bg-indigo-700 disabled:opacity-60"
                      >
                        {loading ? 'Signing in...' : 'Sign in'}
                      </button>
                      <Link to="/forgot-password" className="text-sm text-indigo-600 inline-block">
                        Forgot password?
                      </Link>
                    </form>
                  )}
                </div>
              </>
            )}

            {step === 'details' && (
              <form onSubmit={submitDetails} className="mt-2 space-y-4">
                <p className="text-sm text-slate-500">
                  Welcome, <span className="font-medium text-slate-700">{googleUser?.name}</span> ({googleUser?.email}). Tell
                  the placement cell who you are so they can approve your access.
                </p>
                {detailFields.map(([key, label, required]) => (
                  <div key={key}>
                    <label className="text-sm font-medium text-slate-700">{label}</label>
                    <input
                      value={details[key]}
                      onChange={(e) => setDetails({ ...details, [key]: e.target.value })}
                      className={inputCls}
                      required={required}
                    />
                  </div>
                ))}
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full rounded-lg bg-indigo-600 text-white py-2.5 text-sm font-medium hover:bg-indigo-700 disabled:opacity-60"
                >
                  {loading ? 'Sending...' : 'Send request to PCELL'}
                </button>
                <button type="button" onClick={() => setStep('login')} className="text-sm text-slate-500">
                  Cancel
                </button>
              </form>
            )}

            {step === 'pending' && (
              <div className="mt-4 space-y-3">
                <p className="text-sm text-slate-700">
                  Your request for <span className="font-medium">{googleUser?.email}</span> has been sent to the placement
                  cell.
                </p>
                <p className="text-sm text-slate-500">
                  Come back and sign in with Google once it is approved. You do not need to sign up again.
                </p>
                <button type="button" onClick={() => setStep('login')} className="text-sm text-indigo-600">
                  Back to sign in
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
