import { useEffect, useState } from 'react'
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { Bell, LogOut, Menu, Moon, Search, Sun, X } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import api from '../services/api'
import logo from '../assets/iips-logo.png'
import TypewriterText from '../components/TypewriterText'
import { useTheme } from '../theme'

const YEAR = new Date().getFullYear()

const studentNav = [
  ['Dashboard', '/'],
  ['Companies', '/companies'],
  ['Interview Experiences', '/experiences'],
  ['Interview Questions', '/questions'],
  ['Topics', '/topics'],
  ['Skills', '/skills'],
  ['Resume', '/resume'],
  ['Events & Announcements', '/events'],
  ['Notifications', '/notifications'],
  ['Profile', '/profile'],
]

const pcellNav = [
  ['Dashboard', '/admin'],
  ['Students', '/admin/students'],
  ['Student Requests', '/admin/requests'],
  ['Companies', '/admin/companies'],
  ['Question Verification', '/admin/questions'],
  ['Experiences', '/admin/experiences'],
  ['Registration Forms', '/admin/registrations'],
  ['Events', '/admin/events'],
  ['Placements', '/admin/placements'],
  ['Analytics', '/admin/analytics'],
]

const tpoNav = [
  ['Dashboard', '/tpo'],
  ['PCELL Members', '/tpo/pcell'],
  ['Audit Logs', '/tpo/audit'],
  ['Analytics', '/admin/analytics'],
  ...pcellNav.slice(1),
]

function navForRole(role) {
  if (role === 'TPO') return tpoNav
  if (role === 'PCELL_MEMBER') return pcellNav
  return studentNav
}

export default function AppLayout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const items = navForRole(user?.role)
  const location = useLocation()
  const [unread, setUnread] = useState(0)
  const [menuOpen, setMenuOpen] = useState(false)
  const { theme, toggle } = useTheme()

  // On phones the sidebar is a drawer; close it after navigating.
  useEffect(() => {
    setMenuOpen(false)
  }, [location.pathname])

  useEffect(() => {
    api
      .get('/api/notifications/unread-count')
      .then((r) => setUnread(r.data.count))
      .catch(() => setUnread(0))
  }, [location.pathname])

  const onSearch = (e) => {
    e.preventDefault()
    const q = new FormData(e.currentTarget).get('q')
    if (q) navigate(`/search?q=${encodeURIComponent(q)}`)
  }

  return (
    <div className="min-h-screen flex bg-slate-100">
      {menuOpen && <div className="fixed inset-0 z-30 bg-black/50 md:hidden" onClick={() => setMenuOpen(false)} />}
      <aside
        className={`fixed inset-y-0 left-0 z-40 w-64 bg-indigo-950 text-slate-100 flex flex-col transition-transform duration-300 md:static md:translate-x-0 ${
          menuOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="p-4 border-b border-slate-700 flex items-center gap-3">
          <img src={logo} alt="IIPS DAVV logo" className="h-14 w-14 rounded-full bg-white p-1 object-contain shrink-0" />
          <div className="leading-tight">
            <h1 className="font-semibold text-sm">IIPS, DAVV Indore</h1>
            <p className="text-[11px] uppercase tracking-wider text-amber-300 mt-1">Training &amp; Placement</p>
          </div>
        </div>
        <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
          {items.map(([label, to]) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/' || to === '/admin' || to === '/tpo'}
              className={({ isActive }) =>
                `block rounded-md px-3 py-2 text-sm ${isActive ? 'bg-indigo-600 text-white' : 'text-slate-300 hover:bg-slate-800'}`
              }
            >
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="p-4 border-t border-slate-700 text-sm">
          <p className="font-medium truncate">{user?.full_name}</p>
          <p className="text-slate-400 text-xs">{user?.role}</p>
          <button
            type="button"
            onClick={() => {
              logout()
              navigate('/login')
            }}
            className="mt-3 inline-flex items-center gap-2 text-slate-300 hover:text-white"
          >
            <LogOut size={16} /> Logout
          </button>
        </div>
      </aside>
      <div className="flex-1 flex flex-col min-w-0">
        <header className="bg-white border-b-2 border-b-amber-400 border-x-0 border-t-0 border-slate-200 px-3 md:px-6 py-3 md:py-4 flex items-center gap-2 md:gap-4">
          <button
            type="button"
            aria-label={menuOpen ? 'Close menu' : 'Open menu'}
            className="md:hidden p-2 rounded-lg text-indigo-900 hover:bg-slate-100"
            onClick={() => setMenuOpen((o) => !o)}
          >
            {menuOpen ? <X size={22} /> : <Menu size={22} />}
          </button>
          <div className="hidden xl:block leading-tight shrink-0">
            <p className="font-semibold text-indigo-900 text-sm">
              <TypewriterText text="International Institute of Professional Studies" />
            </p>
            <p className="text-xs text-slate-500 fade-in-late">Devi Ahilya Vishwavidyalaya, Indore</p>
          </div>
          <form onSubmit={onSearch} className="flex-1 max-w-xl ml-auto relative">
            <Search className="absolute left-3 top-2.5 text-slate-400" size={18} />
            <input
              name="q"
              placeholder="Search companies, questions, topics..."
              className="w-full rounded-lg border border-slate-300 pl-10 pr-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </form>
          <button
            type="button"
            onClick={toggle}
            aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
            title={theme === 'dark' ? 'Light mode' : 'Dark mode'}
            className="theme-toggle p-2 rounded-lg hover:bg-slate-100 text-slate-600"
          >
            {theme === 'dark' ? <Sun size={20} /> : <Moon size={20} />}
          </button>
          <NavLink to="/notifications" className="relative p-2 rounded-lg hover:bg-slate-100 text-slate-600">
            <Bell size={20} />
            {unread > 0 && (
              <span className="absolute -top-0.5 -right-0.5 min-w-4 h-4 px-1 rounded-full bg-red-600 text-white text-[10px] flex items-center justify-center">
                {unread > 99 ? '99+' : unread}
              </span>
            )}
          </NavLink>
        </header>
        <main className="flex-1 p-4 md:p-6 overflow-y-auto">
          <div key={location.pathname} className="page-enter">
            <Outlet />
          </div>
        </main>
        <footer className="px-4 md:px-6 py-3 text-xs text-slate-500 border-t bg-white">
          © {YEAR} International Institute of Professional Studies, DAVV Indore · तमसो मा ज्योतिर्गमय
        </footer>
      </div>
    </div>
  )
}
