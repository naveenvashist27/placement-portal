import axios from 'axios'
import { CAMPUS_REQUIRED_EVENT, clearPass, getPass } from './campusPass'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  const pass = getPass()
  if (pass) config.headers['X-Campus-Pass'] = pass.token
  return config
})

// The backend rejected us for being off campus (or the pass expired): send the user back to the location check.
api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 403 && err.response.data?.code === 'CAMPUS_REQUIRED') {
      clearPass()
      window.dispatchEvent(new Event(CAMPUS_REQUIRED_EVENT))
    }
    return Promise.reject(err)
  },
)

export default api
