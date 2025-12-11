import sendIcon from '../../../../assets/images/send_icon.png'

/**
 * MessageInput - Formulaire d'envoi de message
 * Affiche l'input et le bouton d'envoi (seulement si aucun message)
 */
function MessageInput({
  inputMessage,
  isSending,
  hasActiveRequest,
  onInputChange,
  onSubmit
}) {
  return (
    <form className="message-input-form" onSubmit={onSubmit}>
      <input
        type="text"
        className="message-input"
        placeholder={hasActiveRequest ? "Veuillez attendre la réponse en cours..." : "Posez votre question juridique..."}
        value={inputMessage}
        onChange={onInputChange}
        disabled={isSending || hasActiveRequest}
      />
      <button
        type="submit"
        className="btn-send"
        disabled={isSending || hasActiveRequest || !inputMessage.trim()}
        aria-label="Envoyer le message"
      >
        <img src={sendIcon} alt="Envoyer" className="send-icon" />
      </button>
    </form>
  )
}

export default MessageInput
