import { useCallback, useEffect, useState } from 'react'

const KEY = 'theme'

const preferred = () =>
  localStorage.getItem(KEY) || (window.matchMedia?.('(prefers-color-scheme: dark)').matches ? 'dark' : 'light')

// Light / dark mode. The class on <html> flips the colour variables in index.css; index.html applies it before first paint.
export function useTheme() {
  const [theme, setTheme] = useState(preferred)

  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark')
  }, [theme])

  const toggle = useCallback(() => {
    const root = document.documentElement
    root.classList.add('theme-anim') // fade colours for a moment, only while switching
    setTimeout(() => root.classList.remove('theme-anim'), 500)
    setTheme((t) => {
      const next = t === 'dark' ? 'light' : 'dark'
      localStorage.setItem(KEY, next)
      return next
    })
  }, [])

  return { theme, toggle }
}
