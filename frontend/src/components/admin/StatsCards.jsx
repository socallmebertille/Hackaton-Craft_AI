import '../../styles/admin/index.css'

function StatsCards({ stats, user }) {
  return (
    <div className="stats-cards">
      <div className="stat-card">
        <div className="stat-icon">👥</div>
        <div className="stat-info">
          <h3>Total utilisateurs</h3>
          <p className="stat-value">{stats.total_users}</p>
        </div>
      </div>

      <div className="stat-card">
        <div className="stat-icon">✅</div>
        <div className="stat-info">
          <h3>Utilisateurs actifs</h3>
          <p className="stat-value">{stats.active_users}</p>
        </div>
      </div>

      <div className="stat-card highlight">
        <div className="stat-icon">⏳</div>
        <div className="stat-info">
          <h3>En attente</h3>
          <p className="stat-value">{stats.pending_users}</p>
        </div>
      </div>

      {user?.is_moderator && !user?.is_admin && (
        <div className="stat-card">
          <div className="stat-icon">🎯</div>
          <div className="stat-info">
            <h3>Limite autorisée</h3>
            <p className="stat-value">
              {stats.active_users} / {stats.max_users || '∞'}
            </p>
          </div>
        </div>
      )}

      {user?.is_admin && (
        <div className="stat-card">
          <div className="stat-icon">🛡️</div>
          <div className="stat-info">
            <h3>Modérateurs</h3>
            <p className="stat-value">{stats.moderators}</p>
          </div>
        </div>
      )}
    </div>
  )
}

export default StatsCards
