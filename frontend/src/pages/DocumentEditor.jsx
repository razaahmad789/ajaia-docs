import { useCallback, useEffect, useRef, useState } from 'react'
import { useNavigate, useParams, Link } from 'react-router-dom'
import Header from '../components/Header.jsx'
import Editor from '../components/Editor.jsx'
import ShareDialog from '../components/ShareDialog.jsx'
import { api } from '../lib/api.js'
import { useToast } from '../lib/ToastContext.jsx'

const AUTOSAVE_MS = 900

export default function DocumentEditor() {
  const { id } = useParams()
  const navigate = useNavigate()
  const toast = useToast()

  const [doc, setDoc] = useState(null)
  const [loading, setLoading] = useState(true)
  const [status, setStatus] = useState('saved') // saved | saving | error
  const [showShare, setShowShare] = useState(false)

  // Latest unsaved values + debounce timer live in refs so the autosave
  // closure always sees current data without re-subscribing effects.
  const pending = useRef({ title: null, content: null })
  const timer = useRef(null)

  useEffect(() => {
    let active = true
    setLoading(true)
    api
      .getDocument(id)
      .then((d) => {
        if (active) setDoc(d)
      })
      .catch((err) => {
        toast.show(err.message, 'error')
        if (err.status === 404 || err.status === 403) navigate('/')
      })
      .finally(() => active && setLoading(false))
    return () => {
      active = false
      if (timer.current) clearTimeout(timer.current)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id])

  const flush = useCallback(async () => {
    const payload = {}
    if (pending.current.title !== null) payload.title = pending.current.title
    if (pending.current.content !== null)
      payload.content = pending.current.content
    if (Object.keys(payload).length === 0) return
    pending.current = { title: null, content: null }
    setStatus('saving')
    try {
      const updated = await api.updateDocument(id, payload)
      // Keep server-sanitized content/title in local state without clobbering
      // the live editor (editor holds its own doc; we only track metadata).
      setDoc((prev) => ({ ...prev, ...updated }))
      setStatus('saved')
    } catch (err) {
      setStatus('error')
      toast.show(err.message, 'error')
    }
  }, [id, toast])

  const scheduleSave = useCallback(
    (patch) => {
      pending.current = { ...pending.current, ...patch }
      setStatus('saving')
      if (timer.current) clearTimeout(timer.current)
      timer.current = setTimeout(flush, AUTOSAVE_MS)
    },
    [flush],
  )

  function onTitleChange(e) {
    const title = e.target.value
    setDoc((prev) => ({ ...prev, title }))
    scheduleSave({ title })
  }

  function onContentChange(html) {
    scheduleSave({ content: html })
  }

  async function deleteDoc() {
    if (!window.confirm(`Delete “${doc.title}”? This cannot be undone.`)) return
    try {
      await api.deleteDocument(id)
      toast.show('Document deleted')
      navigate('/')
    } catch (err) {
      toast.show(err.message, 'error')
    }
  }

  if (loading) {
    return (
      <>
        <Header />
        <div className="center-screen">
          <span className="spinner" />
        </div>
      </>
    )
  }
  if (!doc) return null

  const canEdit = doc.role === 'owner' || doc.role === 'editor'
  const isOwner = doc.role === 'owner'

  const statusText =
    status === 'saving' ? 'Saving…' : status === 'error' ? 'Save failed' : 'All changes saved'

  return (
    <>
      <Header>
        <Link to="/" className="btn btn-sm btn-ghost">
          ← All documents
        </Link>
        {isOwner && (
          <button className="btn btn-sm" onClick={() => setShowShare(true)}>
            Share{doc.shared_count ? ` (${doc.shared_count})` : ''}
          </button>
        )}
        {isOwner && (
          <button className="btn btn-sm btn-danger" onClick={deleteDoc}>
            Delete
          </button>
        )}
      </Header>

      <div className="container">
        <div className="editor-topbar">
          <input
            className="title-input"
            value={doc.title}
            onChange={onTitleChange}
            readOnly={!canEdit}
            placeholder="Untitled document"
            aria-label="Document title"
          />
          <span className={`badge badge-${doc.role}`}>{doc.role}</span>
          {canEdit && <span className="save-status">{statusText}</span>}
        </div>

        {!canEdit && (
          <div className="demo-hint" style={{ marginBottom: 14, marginTop: 0 }}>
            You have <strong>view-only</strong> access to this document
            (owner: {doc.owner.email}).
          </div>
        )}

        <Editor
          key={doc.id}
          content={doc.content}
          editable={canEdit}
          onChange={onContentChange}
        />
      </div>

      {showShare && (
        <ShareDialog
          doc={doc}
          onClose={() => setShowShare(false)}
          onChanged={() =>
            api.getDocument(id).then(setDoc).catch(() => {})
          }
        />
      )}
    </>
  )
}
