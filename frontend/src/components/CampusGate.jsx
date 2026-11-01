import { useCallback, useEffect, useRef, useState } from 'react'
import { MapPin } from 'lucide-react'
import api from '../services/api'
import { CAMPUS_REQUIRED_EVENT, clearPass, getPass, savePass } from '../services/campusPass'

const RECHECK_MS = 10 * 60 * 1000 // the pass lasts 15 min on the server, so renew it well before then

function getPosition() {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) return reject({ code: 'UNSUPPORTED' })
    navigator.geolocation.getCurrentPosition(resolve, reject, {
      enableHighAccuracy: true,
      timeout: 20000,
      maximumAge: 0,
    })
  })
}

function Screen({ title, children, action }) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-100 p-6">
      <div className="bg-white border rounded-2xl shadow-sm p-8 max-w-md text-center space-y-4">
        <div className="mx-auto h-14 w-14 rounded-full bg-indigo-50 flex items-center justify-center text-indigo-600">
          <MapPin size={28} />
        </div>
        <h1 className="text-xl font-semibold text-indigo-900">{title}</h1>
        <div className="text-sm text-slate-600 space-y-2">{children}</div>
        {action}
      </div>
    </div>
  )
}

// Blocks the whole app until the browser's location is confirmed to be on the IIPS campus.
export default function CampusGate({ children }) {
  // state: checking | ok | outside | denied | unavailable | error
  const [state, setState] = useState('checking')
  const [distance, setDistance] = useState(null)
  const [radius, setRadius] = useState(null)
  const running = useRef(false)

  const verify = useCallback(async (silent = false) => {
    if (running.current) return
    running.current = true
    if (!silent) setState('checking')
    try {
      const { data: status } = await api.get('/api/campus/status')
      setRadius(status.radius_m)
      if (!status.enabled) return setState('ok')

      const pos = await getPosition()
      const { data } = await api.post('/api/campus/check', {
        latitude: pos.coords.latitude,
        longitude: pos.coords.longitude,
        accuracy: pos.coords.accuracy,
      })
      setDistance(data.distance_m)
      if (data.allowed) {
        savePass(data.pass_token, data.expires_in)
        setState('ok')
      } else {
        clearPass()
        setState('outside')
      }
    } catch (err) {
      if (err.code === 1) setState('denied') // PERMISSION_DENIED
      else if (err.code === 'UNSUPPORTED') setState('unavailable')
      else if (err.code === 2 || err.code === 3) setState('unavailable') // position unavailable / timeout
      else if (silent && getPass()) return // transient network error, keep the current pass
      else setState('error')
    } finally {
      running.current = false
    }
  }, [])

  useEffect(() => {
    verify()
    const timer = setInterval(() => verify(true), RECHECK_MS)
    const onRequired = () => verify()
    window.addEventListener(CAMPUS_REQUIRED_EVENT, onRequired)
    return () => {
      clearInterval(timer)
      window.removeEventListener(CAMPUS_REQUIRED_EVENT, onRequired)
    }
  }, [verify])

  if (state === 'ok') return children

  const retry = (
    <button type="button" onClick={() => verify()} className="rounded-lg bg-indigo-600 text-white px-5 py-2 text-sm">
      Check again
    </button>
  )

  if (state === 'checking') {
    return (
      <Screen title="Checking your location...">
        <p>Please allow location access when your browser asks. The portal is available only on the IIPS campus.</p>
      </Screen>
    )
  }
  if (state === 'outside') {
    return (
      <Screen title="Campus access only" action={retry}>
        <p>This portal can only be used inside the IIPS, DAVV Indore campus.</p>
        <p>
          You appear to be about {distance >= 1000 ? `${(distance / 1000).toFixed(1)} km` : `${distance} m`} from the
          campus centre{radius ? ` (allowed: within ${radius} m)` : ''}.
        </p>
      </Screen>
    )
  }
  if (state === 'denied') {
    return (
      <Screen title="Location permission needed" action={retry}>
        <p>Access is limited to the campus, so we need your location to confirm you are here.</p>
        <p>Click the lock icon next to the address bar, set Location to "Allow", then press Check again.</p>
      </Screen>
    )
  }
  if (state === 'unavailable') {
    return (
      <Screen title="Could not get your location" action={retry}>
        <p>Turn on your device's location (GPS), then try again. Weak signal indoors can also cause this.</p>
        <p>Location also requires a secure (https) connection.</p>
      </Screen>
    )
  }
  return (
    <Screen title="Something went wrong" action={retry}>
      <p>We could not reach the server to verify your location. Please try again.</p>
    </Screen>
  )
}
