import { useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../services/api'
import { useToast } from '../components/Toast'

export default function ForgotPasswordPage() {
  const { push } = useToast()
  const [email, setEmail] = useState('')
  const [sent, setSent] = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    try {
      await api.post('/api/auth/forgot-password', { email })
      setSent(true)
    } catch (err) {
      push(err.response?.data?.detail?.[0]?.msg || 'Request failed', 'error')
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-indigo-950 to-slate-900 px-4">
      <div className="w-full max-w-md bg-white rounded-2xl shadow-xl p-8">
        <h1 className="text-2xl font-semibold text-slate-900">Forgot password</h1>
        {sent ? (
          <p className="mt-4 text-sm text-slate-600">
            If the account exists, password reset instructions were sent. Contact your TPO if you do not receive them.
          </p>
        ) : (
          <form onSubmit={submit} className="mt-6 space-y-4">
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="College email"
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              required
            />
            <button type="submit" className="w-full rounded-lg bg-indigo-600 text-white py-2.5 text-sm font-medium">
              Send reset instructions
            </button>
          </form>
        )}
        <Link to="/login" className="text-sm text-indigo-600 mt-4 inline-block">
          Back to sign in
        </Link>
      </div>
    </div>
  )
}
