import { useEffect, useRef } from 'react'

export const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID

const GSI_SRC = 'https://accounts.google.com/gsi/client'
let gsiPromise

function loadGsi() {
  if (!gsiPromise) {
    gsiPromise = new Promise((resolve, reject) => {
      const s = document.createElement('script')
      s.src = GSI_SRC
      s.async = true
      s.onload = resolve
      s.onerror = () => {
        gsiPromise = undefined
        reject(new Error('Could not load Google sign-in'))
      }
      document.head.appendChild(s)
    })
  }
  return gsiPromise
}

// Renders Google's own button. `onCredential` receives the Google ID token.
export default function GoogleSignInButton({ onCredential, onError }) {
  const ref = useRef(null)
  const cb = useRef({ onCredential, onError })
  useEffect(() => {
    cb.current = { onCredential, onError }
  })

  useEffect(() => {
    if (!GOOGLE_CLIENT_ID) return
    let cancelled = false
    loadGsi()
      .then(() => {
        if (cancelled || !ref.current) return
        window.google.accounts.id.initialize({
          client_id: GOOGLE_CLIENT_ID,
          callback: (resp) => cb.current.onCredential(resp.credential),
        })
        window.google.accounts.id.renderButton(ref.current, {
          theme: 'outline',
          size: 'large',
          text: 'continue_with',
          shape: 'pill',
          width: 320,
        })
      })
      .catch((e) => cb.current.onError?.(e.message))
    return () => {
      cancelled = true
    }
  }, [])

  if (!GOOGLE_CLIENT_ID) {
    return (
      <p className="text-sm text-red-600 text-center">
        Google sign-in is not configured. Set VITE_GOOGLE_CLIENT_ID in frontend/.env.
      </p>
    )
  }
  return <div ref={ref} className="flex justify-center min-h-[44px]" />
}
