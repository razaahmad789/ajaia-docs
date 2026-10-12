// Thin fetch wrapper around the backend API.
// - Prefixes the configured API base URL (empty in dev -> Vite proxy).
// - Attaches the auth token when present.
// - Normalizes error responses into thrown ApiError objects.

const BASE = import.meta.env.VITE_API_BASE_URL || ''
const TOKEN_KEY = 'ajaia.token'

export class ApiError extends Error {
  constructor(message, status, data) {
    super(message)
    this.status = status
    this.data = data
  }
}

export function getToken() {
  try {
    return localStorage.getItem(TOKEN_KEY)
  } catch {
    return null
  }
}

export function setToken(token) {
  try {
    if (token) localStorage.setItem(TOKEN_KEY, token)
    else localStorage.removeItem(TOKEN_KEY)
  } catch {
    /* ignore storage errors (private mode etc.) */
  }
}

// Pull a human-friendly message out of a DRF error body.
function messageFromData(data, fallback) {
  if (!data) return fallback
  if (typeof data === 'string') return data
  if (data.detail) return data.detail
  const firstKey = Object.keys(data)[0]
  if (firstKey) {
    const val = data[firstKey]
    const text = Array.isArray(val) ? val[0] : val
    return firstKey === 'non_field_errors' ? text : `${text}`
  }
  return fallback
}

async function request(path, { method = 'GET', body, isForm = false } = {}) {
  const headers = {}
  const token = getToken()
  if (token) headers['Authorization'] = `Token ${token}`

  let payload = body
  if (body && !isForm) {
    headers['Content-Type'] = 'application/json'
    payload = JSON.stringify(body)
  }

  let res
  try {
    res = await fetch(`${BASE}/api${path}`, { method, headers, body: payload })
  } catch {
    throw new ApiError('Network error — is the backend running?', 0, null)
  }

  if (res.status === 204) return null

  let data = null
  const text = await res.text()
  if (text) {
    try {
      data = JSON.parse(text)
    } catch {
      data = text
    }
  }

  if (!res.ok) {
    throw new ApiError(
      messageFromData(data, `Request failed (${res.status})`),
      res.status,
      data,
    )
  }
  return data
}

export const api = {
  login: (email, password) =>
    request('/auth/login/', { method: 'POST', body: { email, password } }),
  me: () => request('/me/'),

  listDocuments: () => request('/documents/'),
  getDocument: (id) => request(`/documents/${id}/`),
  createDocument: (data) =>
    request('/documents/', { method: 'POST', body: data }),
  updateDocument: (id, data) =>
    request(`/documents/${id}/`, { method: 'PATCH', body: data }),
  deleteDocument: (id) =>
    request(`/documents/${id}/`, { method: 'DELETE' }),

  importDocument: (file) => {
    const form = new FormData()
    form.append('file', file)
    return request('/documents/import/', {
      method: 'POST',
      body: form,
      isForm: true,
    })
  },

  listShares: (id) => request(`/documents/${id}/shares/`),
  addShare: (id, email, role) =>
    request(`/documents/${id}/shares/`, {
      method: 'POST',
      body: { email, role },
    }),
  removeShare: (id, shareId) =>
    request(`/documents/${id}/shares/${shareId}/`, { method: 'DELETE' }),
}
