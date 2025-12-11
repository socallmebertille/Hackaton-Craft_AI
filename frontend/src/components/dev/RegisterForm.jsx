import { useState } from 'react'

function RegisterForm({ onRegister }) {
  const [formData, setFormData] = useState({
    prenom: '',
    nom: '',
    entreprise: '',
    email: '',
    password: ''
  })

  const handleSubmit = (e) => {
    e.preventDefault()
    onRegister(formData)
    setFormData({ prenom: '', nom: '', entreprise: '', email: '', password: '' })
  }

  return (
    <div className="card">
      <h3>Inscription</h3>
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          placeholder="Prénom"
          value={formData.prenom}
          onChange={(e) => setFormData({...formData, prenom: e.target.value})}
          required
        />
        <input
          type="text"
          placeholder="Nom"
          value={formData.nom}
          onChange={(e) => setFormData({...formData, nom: e.target.value})}
          required
        />
        <input
          type="text"
          placeholder="Entreprise"
          value={formData.entreprise}
          onChange={(e) => setFormData({...formData, entreprise: e.target.value})}
          required
        />
        <input
          type="email"
          placeholder="Email"
          value={formData.email}
          onChange={(e) => setFormData({...formData, email: e.target.value})}
          required
        />
        <input
          type="password"
          placeholder="Mot de passe (min 8 caractères)"
          value={formData.password}
          onChange={(e) => setFormData({...formData, password: e.target.value})}
          required
          minLength={8}
        />
        <button type="submit" className="btn-primary">S'inscrire</button>
      </form>
    </div>
  )
}

export default RegisterForm
