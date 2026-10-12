import { Link } from 'react-router-dom'
import { useAuth } from '../lib/AuthContext.jsx'

function initials(user) {
  const base = user?.username || user?.email || '?'
  return base.slice(0, 2).toUpperCase()
}

export default function Header({ children }) {
  const { user, logout } = useAuth()
  return (
    <header className="app-header">
      <Link to="/" className="brand">
        <span className="brand-mark">A</span>
        Ajaia Docs
      </Link>
      <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
        {children}
        {user && (
          <div className="user-chip">
            <span className="avatar">{initials(user)}</span>
            <span>{user.email}</span>
            <button className="btn btn-sm btn-ghost" onClick={logout}>
              Sign out
            </button>
          </div>
        )}
      </div>
    </header>
  )
}
