import { useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import api from '../services/api'
import { useToast } from '../components/Toast'

export default function ResetPasswordPage() {
  const { push } = useToast()
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const [password, setPassword] = useState('')
  const token = params.get('token')

  const submit = async (e) => {
    e.preventDefault()
    try {
      await api.post('/api/auth/reset-password', { token, new_password: password })
      push('Password reset. Please sign in.', 'success')
      navigate('/login')
    } catch (err) {
      push(err.response?.data?.detail?.[0]?.msg || err.response?.data?.detail || 'Reset failed', 'error')
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-indigo-950 to-slate-900 px-4">
      <div className="w-full max-w-md bg-white rounded-2xl shadow-xl p-8">
        <h1 className="text-2xl font-semibold text-slate-900">Reset password</h1>
        {token ? (
          <form onSubmit={submit} className="mt-6 space-y-4">
            <input
              type="password"
              minLength={8}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="New password (min 8 characters)"
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              required
            />
            <button type="submit" className="w-full rounded-lg bg-indigo-600 text-white py-2.5 text-sm font-medium">
              Reset password
            </button>
          </form>
        ) : (
          <p className="mt-4 text-sm text-red-600">This reset link is missing its token.</p>
        )}
        <Link to="/login" className="text-sm text-indigo-600 mt-4 inline-block">
          Back to sign in
        </Link>
      </div>
    </div>
  )
}
