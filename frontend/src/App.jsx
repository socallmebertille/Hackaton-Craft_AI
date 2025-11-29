import { useState, useEffect } from 'react'
import axios from 'axios'
import './App.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function App() {
  const [status, setStatus] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const response = await axios.get(`${API_URL}/api/health`)
        setStatus(response.data)
        setLoading(false)
      } catch (err) {
        setError(err.message)
        setLoading(false)
      }
    }

    fetchStatus()
  }, [])

  // Détecter automatiquement le thème système
  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')

    const handleChange = (e) => {
      document.documentElement.setAttribute('data-theme', e.matches ? 'dark' : 'light')
    }

    // Appliquer le thème initial
    handleChange(mediaQuery)

    // Écouter les changements
    mediaQuery.addEventListener('change', handleChange)

    return () => mediaQuery.removeEventListener('change', handleChange)
  }, [])

  return (
    <div className="app">
      <header className="header">
        <h1>MIBS AI</h1>
      </header>

      <main className="main">
        <div className="card">
          <h2>Statut du Backend</h2>
          {loading && <p>Connexion au backend...</p>}
          {error && <p className="error">Erreur: {error}</p>}
          {status && (
            <div className="status-info">
              <p className="success">Backend connecté</p>
              <ul>
                <li>Status: {status.status}</li>
                <li>Environment: {status.environment}</li>
              </ul>
            </div>
          )}
        </div>
      </main>

      <footer className="footer">
        <p>MIBS AI v1.0.0 - En développement</p>
      </footer>
    </div>
  )
}

export default App
