import { useState } from 'react'

function LoginForm({ onLogin }) {
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  })

  const handleSubmit = (e) => {
    e.preventDefault()
    onLogin(formData)
    setFormData({ email: '', password: '' })
  }

  return (
    <div className="card">
      <h3>Connexion</h3>
      <form onSubmit={handleSubmit}>
        <input
          type="email"
          placeholder="Email"
          value={formData.email}
          onChange={(e) => setFormData({...formData, email: e.target.value})}
          required
        />
        <input
          type="password"
          placeholder="Mot de passe"
          value={formData.password}
          onChange={(e) => setFormData({...formData, password: e.target.value})}
          required
        />
        <button type="submit" className="btn-primary">Se connecter</button>
      </form>
    </div>
  )
}

export default LoginForm
