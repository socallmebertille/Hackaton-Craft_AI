/**
 * PdfPopup - Pop-up de téléchargement PDF
 * Affiche une notification quand la consultation est prête
 */
function PdfPopup({
  show,
  onClose,
  onDownload
}) {
  if (!show) return null

  return (
    <div className="pdf-popup">
      <div className="pdf-popup-content">
        <button className="pdf-popup-close" onClick={onClose}>×</button>
        <p>Votre consultation est prête</p>
        <button className="btn-download-pdf" onClick={onDownload}>
          Télécharger en PDF
        </button>
      </div>
    </div>
  )
}

export default PdfPopup
