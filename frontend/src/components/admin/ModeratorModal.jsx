import { useState } from 'react'
import axios from 'axios'
import Modal from '../auth/Modal'
import '../../styles/AdminPanel.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function ModeratorModal({ user, onClose, onUpdate }) {
  const [formData, setFormData] = useState({
    is_moderator: true,
    moderator_company: user.entreprise,
    max_users: 5
  })
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setLoading(true)

    try {
      const token = localStorage.getItem('jwt_token')
      await axios.patch(
        `${API_URL}/api/admin/users/${user.id}`,
        formData,
        { headers: { Authorization: `Bearer ${token}` } }
      )
      onUpdate()
    } catch (err) {
      setError(err.response?.data?.detail || 'Une erreur est survenue')
      setLoading(false)
    }
  }

  return (
    <Modal
      isOpen={true}
      onClose={onClose}
      title="Nommer modérateur"
    >
      <form className="moderator-form" onSubmit={handleSubmit}>
        {error && <div className="error-message">{error}</div>}

        <div className="user-info-display">
          <p><strong>Utilisateur :</strong> {user.prenom} {user.nom}</p>
          <p><strong>Email :</strong> {user.email}</p>
        </div>

        <div className="form-group">
          <label htmlFor="moderator-company">Entreprise à gérer</label>
          <input
            id="moderator-company"
            type="text"
            value={formData.moderator_company}
            onChange={(e) => setFormData({...formData, moderator_company: e.target.value})}
            required
          />
          <small className="form-hint">
            Le modérateur pourra gérer les utilisateurs de cette entreprise
          </small>
        </div>

        <div className="form-group">
          <label htmlFor="max-users">Nombre maximum d'utilisateurs</label>
          <input
            id="max-users"
            type="number"
            min="1"
            max="1000"
            value={formData.max_users}
            onChange={(e) => setFormData({...formData, max_users: parseInt(e.target.value)})}
            required
          />
          <small className="form-hint">
            Nombre maximum de comptes actifs autorisés pour cette entreprise
          </small>
        </div>

        <div className="modal-actions">
          <button
            type="button"
            onClick={onClose}
            className="btn-secondary"
            disabled={loading}
          >
            Annuler
          </button>
          <button
            type="submit"
            className="btn-primary"
            disabled={loading}
          >
            {loading ? 'Enregistrement...' : 'Nommer modérateur'}
          </button>
        </div>
      </form>
    </Modal>
  )
}

export default ModeratorModal
