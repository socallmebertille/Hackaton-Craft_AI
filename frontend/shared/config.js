/**
 * Configuration globale de l'application
 */

const AppConfig = {
    // URL de l'API backend (via nginx proxy) - Utilise l'origine du site
    API_URL: window.location.origin,
    // Constantes de sécurité
    MAX_QUESTION_LENGTH: 1000,
    MIN_QUESTION_LENGTH: 10,
    
    // Configuration de polling
    POLLING_INTERVAL: 2000, // 2 secondes
    
    // Configuration Markdown
    MARKDOWN_OPTIONS: {
        sanitize: false,
        mangle: false,
        headerIds: false,
        gfm: true,
        breaks: true,
        pedantic: false,
        smartLists: true,
        smartypants: false
    },
    
    // Configuration DOMPurify
    DOMPURIFY_CONFIG: {
        ALLOWED_TAGS: ['p', 'br', 'strong', 'em', 'b', 'i', 'u', 'code', 'pre', 'blockquote', 'ul', 'ol', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'],
        ALLOWED_ATTR: [],
        KEEP_CONTENT: true,
        RETURN_DOM_FRAGMENT: false,
        RETURN_DOM: false
    },
    
    // Messages de statut
    STATUS_MESSAGES: {
        'processing': 'Analyse en cours',
        'completed': 'Débat terminé',
        'error': 'Erreur lors du traitement'
    },
    
    // Mapping des avatars
    AVATAR_MAP: {
        'user': '👤',
        'assistant': '🤖',
        'pour': '✅',
        'contre': '❌',
        'summary': '📄',
        'export': '🤖'
    },
    
    // Messages par défaut
    WELCOME_MESSAGE: 'Bonjour ! Je suis votre assistant juridique spécialisé dans les débats contradictoires.\n\nPosez-moi une question juridique et je vais organiser un débat entre deux avocats experts pour vous donner une vision complète de la question.\n\n**Exemple :** "Un CDD peut-il être renouvelé indéfiniment ?"',

    PENDING_MESSAGE: '⏳ **Compte en attente de validation**\n\nBienvenue sur MIBS ! Votre inscription a bien été prise en compte.\n\nVotre compte est actuellement **en attente de validation** par un administrateur. Vous pourrez accéder à l\'assistant juridique dès que votre compte sera approuvé.\n\n**Que faire en attendant ?**\n- Vous recevrez une notification par email une fois votre compte validé\n- Vous pourrez ensuite vous reconnecter et commencer à poser vos questions juridiques\n- La validation est généralement effectuée sous 24-48 heures\n\nMerci de votre patience ! 🙏'
};