import { Navigate, Route, Routes } from 'react-router-dom'
import { useAuth } from './lib/AuthContext.jsx'
import Login from './pages/Login.jsx'
import DocumentsList from './pages/DocumentsList.jsx'
import DocumentEditor from './pages/DocumentEditor.jsx'

function Protected({ children }) {
  const { user, loading } = useAuth()
  if (loading) {
    return (
      <div className="center-screen">
        <span className="spinner" />
      </div>
    )
  }
  if (!user) return <Navigate to="/login" replace />
  return children
}

export default function App() {
  const { user } = useAuth()
  return (
    <Routes>
      <Route
        path="/login"
        element={user ? <Navigate to="/" replace /> : <Login />}
      />
      <Route
        path="/"
        element={
          <Protected>
            <DocumentsList />
          </Protected>
        }
      />
      <Route
        path="/documents/:id"
        element={
          <Protected>
            <DocumentEditor />
          </Protected>
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
