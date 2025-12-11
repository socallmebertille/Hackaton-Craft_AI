import { useState, useEffect } from 'react'
import axios from 'axios'
import { API_URL } from '../../config/api'

function DatabaseStatus() {
  const [dbStatus, setDbStatus] = useState(null)
  const [dbLoading, setDbLoading] = useState(true)
  const [dbError, setDbError] = useState(null)

  useEffect(() => {
    const fetchDbStatus = async () => {
      try {
        const response = await axios.get(`${API_URL}/api/test-db`)
        setDbStatus(response.data)
        setDbLoading(false)
      } catch (err) {
        setDbError(err.message)
        setDbLoading(false)
      }
    }

    fetchDbStatus()
  }, [])

  return (
    <div className="card">
      <h2>Statut de la Base de Données</h2>
      {dbLoading && <p>Vérification de la connexion...</p>}
      {dbError && <p className="error">Erreur: {dbError}</p>}
      {dbStatus && (
        <div className="status-info">
          {dbStatus.status === 'success' ? (
            <>
              <p className="success">✓ PostgreSQL connecté</p>
              <ul>
                <li>Message: {dbStatus.message}</li>
                <li>Utilisateurs: {dbStatus.user_count}</li>
                <li>Chats: {dbStatus.chat_count}</li>
              </ul>
            </>
          ) : (
            <>
              <p className="error">✗ Erreur de connexion</p>
              <p className="error">{dbStatus.message}</p>
            </>
          )}
        </div>
      )}
    </div>
  )
}

export default DatabaseStatus
