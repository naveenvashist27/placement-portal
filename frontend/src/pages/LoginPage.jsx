import { useState } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../components/Toast'
import logo from '../assets/iips-logo.png'
import campus from '../assets/iips-campus.png'

export default function LoginPage() {
  const { user, login } = useAuth()
  const { push } = useToast()
  const navigate = useNavigate()
  const [email, setEmail] = useState('student@college.demo')
  const [password, setPassword] = useState('Demo@12345')
  const [loading, setLoading] = useState(false)

  if (user) {
    if (user.role === 'TPO') return <Navigate to="/tpo" replace />
    if (user.role === 'PCELL_MEMBER') return <Navigate to="/admin" replace />
    return <Navigate to="/" replace />
  }

  const submit = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      const u = await login(email, password)
      push('Welcome back', 'success')
      if (u.role === 'TPO') navigate('/tpo')
      else if (u.role === 'PCELL_MEMBER') navigate('/admin')
      else navigate('/')
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
        <p className="text-sm text-slate-500 mt-1">Sign in with your college account</p>
        <form onSubmit={submit} className="mt-6 space-y-4">
          <div>
            <label className="text-sm font-medium text-slate-700">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              required
            />
          </div>
          <div>
            <label className="text-sm font-medium text-slate-700">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
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
        </form>
        <p className="mt-4 text-xs text-slate-500">
          Student self-registration is disabled until college email verification is connected. Use demo accounts from
          README.
        </p>
        <Link to="/forgot-password" className="text-sm text-indigo-600 mt-2 inline-block">
          Forgot password?
        </Link>
      </div>
        </div>
      </div>
    </div>
  )
}
