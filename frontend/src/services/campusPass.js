// Holds the short-lived campus pass issued by the backend after a successful location check.
const KEY = 'campus_pass'

export function getPass() {
  try {
    const { token, expiresAt } = JSON.parse(sessionStorage.getItem(KEY) || 'null') || {}
    return token && Date.now() < expiresAt ? { token, expiresAt } : null
  } catch {
    return null
  }
}

export function savePass(token, expiresInSeconds) {
  sessionStorage.setItem(KEY, JSON.stringify({ token, expiresAt: Date.now() + expiresInSeconds * 1000 }))
}

export function clearPass() {
  sessionStorage.removeItem(KEY)
}

export const CAMPUS_REQUIRED_EVENT = 'campus-required'
