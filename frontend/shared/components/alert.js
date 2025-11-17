/**
 * Système d'alertes personnalisées pour MIBS
 * Remplace les alert() et confirm() natifs par des modales stylées
 */

class AlertSystem {
    constructor() {
        this.alertContainer = null;
        this.init();
    }

    init() {
        // Créer le conteneur des alertes
        this.alertContainer = document.createElement('div');
        this.alertContainer.id = 'alert-container';
        this.alertContainer.className = 'alert-container';
        document.body.appendChild(this.alertContainer);
    }

    /**
     * Affiche une alerte d'information
     * @param {string} message - Message à afficher
     * @param {string} title - Titre de l'alerte (optionnel)
     */
    show(message, title = 'Information') {
        return this._createAlert('info', title, message, [
            { text: 'OK', primary: true, callback: () => {} }
        ]);
    }

    /**
     * Affiche une alerte de succès
     * @param {string} message - Message à afficher
     * @param {string} title - Titre de l'alerte (optionnel)
     */
    success(message, title = 'Succès') {
        return this._createAlert('success', title, message, [
            { text: 'OK', primary: true, callback: () => {} }
        ]);
    }

    /**
     * Affiche une alerte d'erreur
     * @param {string} message - Message à afficher
     * @param {string} title - Titre de l'alerte (optionnel)
     */
    error(message, title = 'Erreur') {
        return this._createAlert('error', title, message, [
            { text: 'OK', primary: true, callback: () => {} }
        ]);
    }

    /**
     * Affiche une alerte d'avertissement
     * @param {string} message - Message à afficher
     * @param {string} title - Titre de l'alerte (optionnel)
     */
    warning(message, title = 'Attention') {
        return this._createAlert('warning', title, message, [
            { text: 'OK', primary: true, callback: () => {} }
        ]);
    }

    /**
     * Affiche une boîte de confirmation
     * @param {string} message - Message à afficher
     * @param {string} title - Titre de la confirmation
     * @returns {Promise<boolean>} - true si confirmé, false sinon
     */
    confirm(message, title = 'Confirmation') {
        return new Promise((resolve) => {
            this._createAlert('confirm', title, message, [
                { text: 'Annuler', primary: false, callback: () => resolve(false) },
                { text: 'Confirmer', primary: true, callback: () => resolve(true) }
            ]);
        });
    }

    /**
     * Affiche une confirmation de danger (suppression, etc.)
     * @param {string} message - Message à afficher
     * @param {string} title - Titre de la confirmation
     * @returns {Promise<boolean>} - true si confirmé, false sinon
     */
    confirmDanger(message, title = '⚠️ Attention') {
        return new Promise((resolve) => {
            this._createAlert('danger', title, message, [
                { text: 'Annuler', primary: true, callback: () => resolve(false) },
                { text: 'Supprimer', primary: false, danger: true, callback: () => resolve(true) }
            ]);
        });
    }

    /**
     * Échappe les caractères HTML pour prévenir les attaques XSS
     * @private
     */
    _escapeHtml(unsafe) {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    /**
     * Crée et affiche une alerte
     * @private
     */
    _createAlert(type, title, message, buttons) {
        // SÉCURITÉ: Échapper le titre et le message pour prévenir XSS
        const safeTitle = this._escapeHtml(String(title));
        const safeMessage = this._escapeHtml(String(message));

        // Créer l'overlay
        const overlay = document.createElement('div');
        overlay.className = 'alert-overlay';

        // Créer la modal
        const modal = document.createElement('div');
        modal.className = `alert-modal alert-${type}`;

        // Icône selon le type
        const icons = {
            info: '💬',
            success: '✅',
            error: '❌',
            warning: '⚠️',
            confirm: '❓',
            danger: '🗑️'
        };

        modal.innerHTML = `
            <div class="alert-icon">${icons[type] || '💬'}</div>
            <div class="alert-title">${safeTitle}</div>
            <div class="alert-message">${safeMessage}</div>
            <div class="alert-buttons">
                ${buttons.map((btn, index) => `
                    <button
                        class="alert-button ${btn.primary ? 'primary' : ''} ${btn.danger ? 'danger' : ''}"
                        data-index="${index}"
                    >
                        ${this._escapeHtml(btn.text)}
                    </button>
                `).join('')}
            </div>
        `;

        overlay.appendChild(modal);
        this.alertContainer.appendChild(overlay);

        // Animation d'entrée
        setTimeout(() => {
            overlay.classList.add('show');
        }, 10);

        // Gérer les clics sur les boutons
        const handleButtonClick = (event) => {
            const button = event.target.closest('.alert-button');
            if (!button) return;

            const index = parseInt(button.dataset.index);
            const callback = buttons[index].callback;

            // Animation de sortie
            overlay.classList.remove('show');
            setTimeout(() => {
                overlay.remove();
            }, 300);

            // Exécuter le callback
            if (callback) callback();
        };

        modal.addEventListener('click', handleButtonClick);

        // Fermer avec Escape (seulement pour les alertes simples)
        const handleEscape = (e) => {
            if (e.key === 'Escape' && type !== 'confirm' && type !== 'danger') {
                overlay.classList.remove('show');
                setTimeout(() => {
                    overlay.remove();
                }, 300);
                document.removeEventListener('keydown', handleEscape);
            }
        };
        document.addEventListener('keydown', handleEscape);
    }
}

// Créer une instance globale
window.Alert = new AlertSystem();

// Compatibilité : remplacer alert() et confirm() natives (optionnel)
// window.alert = (msg) => window.Alert.show(msg);
// window.confirm = (msg) => window.Alert.confirm(msg);
