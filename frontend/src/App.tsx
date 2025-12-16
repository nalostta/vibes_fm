import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import { PlayerProvider } from './context/PlayerContext'
import Layout from './components/Layout'
import Login from './pages/Login'
import Register from './pages/Register'
import Home from './pages/Home'
import Search from './pages/Search'
import Library from './pages/Library'
import Playlist from './pages/Playlist'
import Album from './pages/Album'
import Artist from './pages/Artist'

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, loading } = useAuth()
  
  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-dark-100">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-500"></div>
      </div>
    )
  }
  
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" />
}

function App() {
  return (
    <AuthProvider>
      <PlayerProvider>
        <Router>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/" element={
              <PrivateRoute>
                <Layout>
                  <Home />
                </Layout>
              </PrivateRoute>
            } />
            <Route path="/search" element={
              <PrivateRoute>
                <Layout>
                  <Search />
                </Layout>
              </PrivateRoute>
            } />
            <Route path="/library" element={
              <PrivateRoute>
                <Layout>
                  <Library />
                </Layout>
              </PrivateRoute>
            } />
            <Route path="/playlist/:id" element={
              <PrivateRoute>
                <Layout>
                  <Playlist />
                </Layout>
              </PrivateRoute>
            } />
            <Route path="/album/:id" element={
              <PrivateRoute>
                <Layout>
                  <Album />
                </Layout>
              </PrivateRoute>
            } />
            <Route path="/artist/:id" element={
              <PrivateRoute>
                <Layout>
                  <Artist />
                </Layout>
              </PrivateRoute>
            } />
          </Routes>
        </Router>
      </PlayerProvider>
    </AuthProvider>
  )
}

export default App
