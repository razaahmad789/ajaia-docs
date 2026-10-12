import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../lib/AuthContext.jsx'

const DEMO = [
  { email: 'alice@example.com', note: 'owns a shared doc' },
  { email: 'bob@example.com', note: 'editor on Alice’s doc' },
  { email: 'carol@example.com', note: 'viewer (read-only)' },
]

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('alice@example.com')
  const [password, setPassword] = useState('password123')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function onSubmit(e) {
    e.preventDefault()
    setError('')
    setBusy(true)
    try {
      await login(email.trim(), password)
      navigate('/')
    } catch (err) {
      setError(err.message || 'Login failed')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="auth-wrap">
      <div className="auth-card">
        <h1>Sign in to Ajaia Docs</h1>
        <p className="sub">Collaborative rich-text documents.</p>

        <form onSubmit={onSubmit}>
          {error && <div className="form-error">{error}</div>}
          <div className="field">
            <label className="label" htmlFor="email">
              Email
            </label>
            <input
              id="email"
              className="input"
              type="email"
              autoComplete="username"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          <div className="field">
            <label className="label" htmlFor="password">
              Password
            </label>
            <input
              id="password"
              className="input"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          <button
            className="btn btn-primary"
            type="submit"
            disabled={busy}
            style={{ width: '100%', justifyContent: 'center' }}
          >
            {busy ? <span className="spinner" /> : 'Sign in'}
          </button>
        </form>

        <div className="demo-hint">
          <strong>Demo accounts</strong> (password <code>password123</code>):
          <br />
          {DEMO.map((d) => (
            <div key={d.email} style={{ marginTop: 4 }}>
              <button
                type="button"
                className="link-btn"
                onClick={() => setEmail(d.email)}
              >
                {d.email}
              </button>{' '}
              — {d.note}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
