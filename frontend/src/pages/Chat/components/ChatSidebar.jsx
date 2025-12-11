/**
 * ChatSidebar - Liste des conversations
 * Affiche la liste des chats avec bouton nouveau chat
 */

function ChatSidebar({
  chats,
  currentChatId,
  hasActiveRequest,
  isSending,
  sidebarOpen,
  onStartNewChat,
  onSelectChat,
  onToggleSidebar
}) {
  return (
    <>
      {/* Overlay pour fermer la sidebar sur mobile */}
      {sidebarOpen && (
        <div
          className="sidebar-overlay"
          onClick={onToggleSidebar}
        />
      )}

      {/* Sidebar avec liste des chats */}
      <div className={`chat-sidebar ${sidebarOpen ? 'open' : ''}`}>
        <button
          className="btn-new-chat"
          onClick={onStartNewChat}
          disabled={hasActiveRequest || isSending}
          title={hasActiveRequest ? "Veuillez attendre la réponse en cours" : ""}
        >
          + Nouveau Chat
        </button>

        <div className="chat-list">
          {chats.map(chat => (
            <div
              key={chat.id}
              className={`chat-item ${currentChatId === chat.id ? 'active' : ''}`}
              onClick={() => onSelectChat(chat.id)}
            >
              <div className="chat-item-title">{chat.title}</div>
              <div className="chat-item-date">
                {new Date(chat.updated_at).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}, {new Date(chat.updated_at).toLocaleDateString('fr-FR')}
              </div>
            </div>
          ))}
        </div>
      </div>
    </>
  )
}

export default ChatSidebar
