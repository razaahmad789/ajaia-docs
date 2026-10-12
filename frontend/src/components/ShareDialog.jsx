import { useEffect, useState } from 'react'
import { api } from '../lib/api.js'
import { useToast } from '../lib/ToastContext.jsx'

// Owner-only dialog to grant/revoke access by email with a viewer/editor role.
export default function ShareDialog({ doc, onClose, onChanged }) {
  const toast = useToast()
  const [shares, setShares] = useState(doc.shares || [])
  const [email, setEmail] = useState('')
  const [role, setRole] = useState('viewer')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    api
      .listShares(doc.id)
      .then(setShares)
      .catch((err) => toast.show(err.message, 'error'))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [doc.id])

  async function add(e) {
    e.preventDefault()
    if (!email.trim()) return
    setBusy(true)
    try {
      const share = await api.addShare(doc.id, email.trim(), role)
      setShares((prev) => {
        const without = prev.filter((s) => s.user.id !== share.user.id)
        return [share, ...without]
      })
      setEmail('')
      toast.show(`Shared with ${share.user.email} as ${share.role}`)
      onChanged?.()
    } catch (err) {
      toast.show(err.message, 'error')
    } finally {
      setBusy(false)
    }
  }

  async function revoke(share) {
    try {
      await api.removeShare(doc.id, share.id)
      setShares((prev) => prev.filter((s) => s.id !== share.id))
      toast.show('Access revoked')
      onChanged?.()
    } catch (err) {
      toast.show(err.message, 'error')
    }
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h2>Share “{doc.title}”</h2>
        <p className="sub">
          Grant another seeded user access by email. Viewers can read; editors
          can edit.
        </p>

        <form onSubmit={add} style={{ display: 'flex', gap: 8, marginBottom: 14 }}>
          <input
            className="input"
            type="email"
            placeholder="teammate@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            style={{ flex: 1 }}
          />
          <select
            className="select"
            value={role}
            onChange={(e) => setRole(e.target.value)}
            style={{ width: 120 }}
          >
            <option value="viewer">Viewer</option>
            <option value="editor">Editor</option>
          </select>
          <button className="btn btn-primary" disabled={busy}>
            Share
          </button>
        </form>

        <div>
          <div className="label">People with access</div>
          <div className="share-row">
            <span>
              <strong>{doc.owner.email}</strong>
            </span>
            <span className="badge badge-owner">owner</span>
          </div>
          {shares.length === 0 ? (
            <div style={{ color: 'var(--text-muted)', fontSize: 14, padding: '10px 0' }}>
              Not shared with anyone yet.
            </div>
          ) : (
            shares.map((s) => (
              <div className="share-row" key={s.id}>
                <span>{s.user.email}</span>
                <span style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <span className={`badge badge-${s.role}`}>{s.role}</span>
                  <button
                    className="btn btn-sm btn-danger"
                    onClick={() => revoke(s)}
                  >
                    Remove
                  </button>
                </span>
              </div>
            ))
          )}
        </div>

        <div style={{ textAlign: 'right', marginTop: 18 }}>
          <button className="btn" onClick={onClose}>
            Done
          </button>
        </div>
      </div>
    </div>
  )
}
