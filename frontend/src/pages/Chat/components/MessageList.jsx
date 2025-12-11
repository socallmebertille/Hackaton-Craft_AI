import ReactMarkdown from 'react-markdown'

// Configuration sécurisée pour ReactMarkdown
const markdownComponents = {
  html: () => null,
  a: ({ node, ...props }) => {
    return <a {...props} rel="noopener noreferrer" target="_blank" />
  }
}

/**
 * MessageList - Affichage de la liste des messages
 * Gère l'affichage des messages utilisateur et assistant (débat, citations)
 */
function MessageList({
  messages,
  isSending,
  sendingChatId,
  currentChatId,
  messagesEndRef
}) {
  return (
    <div className="messages-container">
      {messages.map((msg, idx) => {
        // Détecter si c'est un message de débat
        const isDebateMessage = msg.role === 'assistant' && msg.content.intention === 'DEBAT'
        const isCitationMessage = msg.role === 'assistant' && msg.content.intention === 'CITATIONS'
        const messageText = msg.content.message || msg.content.response || ''

        // Détecter le type de message de débat
        const isPourPosition = isDebateMessage && (
          messageText.includes('## Arguments POUR') ||
          messageText.includes('## Réfutation et renforcement POUR')
        )
        const isContraPosition = isDebateMessage && (
          messageText.includes('## Arguments CONTRE') ||
          messageText.includes('## Réfutation et renforcement CONTRE')
        )
        const isPositionsMessage = isDebateMessage && messageText.includes('## Positions du débat')

        // Déterminer la classe CSS
        const messageClass = msg.role === 'user'
          ? 'message-user'
          : isContraPosition
            ? 'message-debate-contre'
            : isPourPosition
              ? 'message-debate-pour'
              : isPositionsMessage
                ? 'message-debate-positions'
                : isCitationMessage
                  ? 'message-citation'
                  : 'message-assistant'

        return (
          <div key={idx} className={`message ${messageClass}`}>
            {msg.role === 'user' && (
              <div className="message-header">
                <strong>Vous</strong>
              </div>
            )}
            <div className="message-content">
              {msg.role === 'assistant' ? (
                <ReactMarkdown
                  components={markdownComponents}
                  skipHtml={true}
                >
                  {messageText}
                </ReactMarkdown>
              ) : (
                messageText
              )}
            </div>
          </div>
        )
      })}

      {isSending && sendingChatId === currentChatId && (
        <div className="message message-assistant loading-message">
          <div className="loading-spinner"></div>
          <span>L'assistant réfléchit...</span>
        </div>
      )}

      <div ref={messagesEndRef} />
    </div>
  )
}

export default MessageList
