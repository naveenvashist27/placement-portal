import { createContext, useContext, useEffect, useMemo, useState } from 'react'
import api from '../services/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('access_token')
    if (!token) {
      setLoading(false)
      return
    }
    api
      .get('/api/auth/me')
      .then((res) => setUser(res.data))
      .catch(() => localStorage.removeItem('access_token'))
      .finally(() => setLoading(false))
  }, [])

  const login = async (email, password) => {
    const { data } = await api.post('/api/auth/login', { email, password })
    localStorage.setItem('access_token', data.access_token)
    const me = await api.get('/api/auth/me')
    setUser(me.data)
    return me.data
  }

  // Used after Google sign-in, which hands back a ready-made access token.
  const loginWithToken = async (accessToken) => {
    localStorage.setItem('access_token', accessToken)
    const me = await api.get('/api/auth/me')
    setUser(me.data)
    return me.data
  }

  const logout = () => {
    localStorage.removeItem('access_token')
    setUser(null)
  }

  const value = useMemo(() => ({ user, loading, login, loginWithToken, logout }), [user, loading])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  return useContext(AuthContext)
}
