import { ReactNode } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { Home, Search, Library, LogOut } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import Player from './Player'

interface LayoutProps {
  children: ReactNode
}

export default function Layout({ children }: LayoutProps) {
  const { user, logout } = useAuth()
  const location = useLocation()

  const navItems = [
    { path: '/', icon: Home, label: 'Home' },
    { path: '/search', icon: Search, label: 'Search' },
    { path: '/library', icon: Library, label: 'Your Library' },
  ]

  return (
    <div className="flex flex-col h-screen bg-dark-100">
      <div className="flex flex-1 overflow-hidden">
        <aside className="w-64 bg-black p-6 flex flex-col">
          <div className="mb-8">
            <h1 className="text-2xl font-bold text-primary-500">Vibes FM</h1>
          </div>

          <nav className="flex-1">
            <ul className="space-y-2">
              {navItems.map(({ path, icon: Icon, label }) => (
                <li key={path}>
                  <Link
                    to={path}
                    className={`flex items-center gap-4 px-4 py-3 rounded-lg transition-colors ${
                      location.pathname === path
                        ? 'bg-dark-200 text-white'
                        : 'text-gray-400 hover:text-white hover:bg-dark-300'
                    }`}
                  >
                    <Icon size={24} />
                    <span className="font-medium">{label}</span>
                  </Link>
                </li>
              ))}
            </ul>
          </nav>

          <div className="border-t border-dark-300 pt-4 mt-4">
            <div className="flex items-center justify-between px-4">
              <div>
                <p className="text-sm font-medium text-white">{user?.username}</p>
                <p className="text-xs text-gray-400">{user?.email}</p>
              </div>
              <button
                onClick={logout}
                className="p-2 text-gray-400 hover:text-white transition-colors"
                title="Logout"
              >
                <LogOut size={20} />
              </button>
            </div>
          </div>
        </aside>

        <main className="flex-1 overflow-y-auto bg-gradient-to-b from-dark-200 to-dark-100 p-8">
          {children}
        </main>
      </div>

      <Player />
    </div>
  )
}
