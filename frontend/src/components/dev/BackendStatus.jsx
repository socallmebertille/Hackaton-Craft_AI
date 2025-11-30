import { useState, useEffect } from 'react'
import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function BackendStatus() {
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

  return (
    <div className="card">
      <h2>Statut du Backend</h2>
      {loading && <p>Connexion au backend...</p>}
      {error && <p className="error">Erreur: {error}</p>}
      {status && (
        <div className="status-info">
          <p className="success">✓ Backend connecté</p>
          <ul>
            <li>Status: {status.status}</li>
            <li>Environment: {status.environment}</li>
            <li>Version: {status.version}</li>
          </ul>
        </div>
      )}
    </div>
  )
}

export default BackendStatus
