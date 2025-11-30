function UserInfo({ user, onLogout, onDeleteAccount }) {
  return (
    <div className="card">
      <h3>Utilisateur Connecté</h3>
      <div className="user-info">
        <p><strong>Nom:</strong> {user.prenom} {user.nom}</p>
        <p><strong>Email:</strong> {user.email}</p>
        <p><strong>Entreprise:</strong> {user.entreprise}</p>
        <p><strong>Compte actif:</strong> {user.is_active ? '✓ Oui' : '✗ Non (en attente validation admin)'}</p>
        <p><strong>Email vérifié:</strong> {user.email_verified ? '✓ Oui' : '✗ Non'}</p>
        <p><strong>Administrateur:</strong> {user.is_admin ? '✓ Oui' : '✗ Non'}</p>
      </div>
      <div className="button-group">
        <button onClick={onLogout} className="btn-secondary">Déconnexion</button>
        <button onClick={onDeleteAccount} className="btn-danger">Supprimer le compte</button>
      </div>
    </div>
  )
}

export default UserInfo
