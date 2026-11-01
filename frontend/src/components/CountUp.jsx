import { useEffect, useRef, useState } from 'react'

const prefersReducedMotion = () => window.matchMedia?.('(prefers-reduced-motion: reduce)').matches

// Counts from 0 up to `value` with an ease-out curve; when `value` changes it continues from the number on screen.
export default function CountUp({ value, duration = 1800 }) {
  const [display, setDisplay] = useState(prefersReducedMotion() ? value : 0)
  const current = useRef(display)

  useEffect(() => {
    const from = current.current
    const start = performance.now()
    let frame
    const tick = (now) => {
      const t = prefersReducedMotion() ? 1 : Math.min(1, (now - start) / duration)
      const eased = 1 - Math.pow(1 - t, 3)
      current.current = Math.round(from + (value - from) * eased)
      setDisplay(current.current)
      if (t < 1) frame = requestAnimationFrame(tick)
    }
    frame = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(frame)
  }, [value, duration])

  return <span className="tabular-nums">{display}</span>
}
