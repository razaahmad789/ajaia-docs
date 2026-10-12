import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Header from '../components/Header.jsx'
import { api } from '../lib/api.js'
import { useToast } from '../lib/ToastContext.jsx'
import { SUPPORTED_IMPORT_LABEL, SUPPORTED_IMPORT_ACCEPT } from '../lib/constants.js'

function timeAgo(iso) {
  const d = new Date(iso)
  const mins = Math.round((Date.now() - d.getTime()) / 60000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.round(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  return d.toLocaleDateString()
}

function DocCard({ doc, onOpen, onDelete }) {
  return (
    <button className="doc-card" onClick={() => onOpen(doc.id)}>
      <h3>{doc.title}</h3>
      <div className="doc-meta">
        <span className={`badge badge-${doc.role}`}>{doc.role}</span>
        <span>{timeAgo(doc.updated_at)}</span>
      </div>
      <div className="doc-meta" style={{ marginTop: 0 }}>
        <span>
          {doc.is_owner
            ? doc.shared_count > 0
              ? `Shared with ${doc.shared_count}`
              : 'Private'
            : `Owner: ${doc.owner.email}`}
        </span>
        {doc.is_owner && (
          <span
            role="button"
            tabIndex={0}
            className="link-btn"
            style={{ color: 'var(--danger)' }}
            onClick={(e) => {
              e.stopPropagation()
              onDelete(doc)
            }}
          >
            Delete
          </span>
        )}
      </div>
    </button>
  )
}

export default function DocumentsList() {
  const navigate = useNavigate()
  const toast = useToast()
  const [docs, setDocs] = useState([])
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const fileRef = useRef(null)

  async function load() {
    setLoading(true)
    try {
      setDocs(await api.listDocuments())
    } catch (err) {
      toast.show(err.message, 'error')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  async function createDoc() {
    setBusy(true)
    try {
      const doc = await api.createDocument({
        title: 'Untitled document',
        content: '',
      })
      navigate(`/documents/${doc.id}`)
    } catch (err) {
      toast.show(err.message, 'error')
      setBusy(false)
    }
  }

  async function onImport(e) {
    const file = e.target.files?.[0]
    e.target.value = '' // allow re-selecting the same file
    if (!file) return
    setBusy(true)
    try {
      const doc = await api.importDocument(file)
      toast.show(`Imported “${doc.title}”`)
      navigate(`/documents/${doc.id}`)
    } catch (err) {
      toast.show(err.message, 'error')
      setBusy(false)
    }
  }

  async function deleteDoc(doc) {
    if (!window.confirm(`Delete “${doc.title}”? This cannot be undone.`)) return
    try {
      await api.deleteDocument(doc.id)
      setDocs((prev) => prev.filter((d) => d.id !== doc.id))
      toast.show('Document deleted')
    } catch (err) {
      toast.show(err.message, 'error')
    }
  }

  const owned = docs.filter((d) => d.is_owner)
  const shared = docs.filter((d) => !d.is_owner)

  return (
    <>
      <Header>
        <button className="btn" disabled={busy} onClick={() => fileRef.current?.click()}>
          Import file
        </button>
        <button className="btn btn-primary" disabled={busy} onClick={createDoc}>
          + New document
        </button>
        <input
          ref={fileRef}
          type="file"
          accept={SUPPORTED_IMPORT_ACCEPT}
          onChange={onImport}
          style={{ display: 'none' }}
        />
      </Header>

      <div className="container">
        <p style={{ color: 'var(--text-muted)', marginTop: 0, fontSize: 14 }}>
          Import supports {SUPPORTED_IMPORT_LABEL} files — they become new
          editable documents.
        </p>

        {loading ? (
          <div className="center-screen">
            <span className="spinner" />
          </div>
        ) : docs.length === 0 ? (
          <div className="empty">
            No documents yet. Create one or import a file to get started.
          </div>
        ) : (
          <>
            <div className="section-title">Owned by me ({owned.length})</div>
            {owned.length === 0 ? (
              <div className="empty">You don’t own any documents yet.</div>
            ) : (
              <div className="doc-grid">
                {owned.map((d) => (
                  <DocCard key={d.id} doc={d} onOpen={(id) => navigate(`/documents/${id}`)} onDelete={deleteDoc} />
                ))}
              </div>
            )}

            <div className="section-title">Shared with me ({shared.length})</div>
            {shared.length === 0 ? (
              <div className="empty">Nothing has been shared with you yet.</div>
            ) : (
              <div className="doc-grid">
                {shared.map((d) => (
                  <DocCard key={d.id} doc={d} onOpen={(id) => navigate(`/documents/${id}`)} onDelete={deleteDoc} />
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </>
  )
}
