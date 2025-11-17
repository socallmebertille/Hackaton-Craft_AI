/**
 * Module d'authentification
 * Gère la connexion, inscription, vérification des tokens
 */

/**
 * SÉCURITÉ: Helper pour créer les headers d'authentification
 * Utilise Authorization header au lieu de query parameter
 */
function getAuthHeaders(token) {
    return {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    };
}

const AuthModule = {
    data: {
        user: null,
        token: localStorage.getItem('authToken') || null,
        showAuthModal: true,
        authMode: 'login',
        authForm: {
            name: '',
            email: '',
            password: '',
            consent: false
        },
        isAuthLoading: false,
        showProfileDropdown: false
    },

    computed: {
        isAuthenticated() {
            return this.token && this.user;
        }
    },

    methods: {
        async login() {
            if (this.isAuthLoading) return;

            this.isAuthLoading = true;

            try {
                const response = await axios.post(`${this.API_URL}/api/auth/login`, {
                    email: this.authForm.email,
                    password: this.authForm.password
                });
                
                this.token = response.data.token;
                this.user = response.data.user;

                localStorage.setItem('authToken', this.token);
                this.showAuthModal = false;
                this.resetAuthForm();

                // Ajouter le message de bienvenue approprié
                this.addWelcomeMessage();

                console.log('Connexion réussie');
            } catch (error) {
                console.error('Erreur de connexion:', error);
                Alert.error(
                    error.response?.data?.detail || 'Erreur inconnue lors de la connexion',
                    'Erreur de connexion'
                );
            } finally {
                this.isAuthLoading = false;
            }
        },

        async signup() {
            if (this.isAuthLoading) return;

            // Vérifier le consentement
            if (!this.authForm.consent) {
                Alert.warning(
                    'Vous devez accepter les conditions d\'utilisation et la politique de confidentialité pour vous inscrire.',
                    'Consentement requis'
                );
                return;
            }

            this.isAuthLoading = true;

            try {
                const response = await axios.post(`${this.API_URL}/api/auth/signup`, {
                    email: this.authForm.email,
                    password: this.authForm.password,
                    cgu_accepted: true,
                    privacy_policy_accepted: true
                });
                
                this.token = response.data.token;
                this.user = response.data.user;

                localStorage.setItem('authToken', this.token);
                this.showAuthModal = false;
                this.resetAuthForm();

                // Ajouter le message de bienvenue approprié (normalement PENDING pour les nouveaux inscrits)
                this.addWelcomeMessage();

                console.log('Inscription réussie - En attente de validation');
            } catch (error) {
                console.error('Erreur d\'inscription:', error);
                Alert.error(
                    error.response?.data?.detail || 'Erreur inconnue lors de l\'inscription',
                    'Erreur d\'inscription'
                );
            } finally {
                this.isAuthLoading = false;
            }
        },

        logout() {
            this.user = null;
            this.token = null;
            localStorage.removeItem('authToken');
            this.showAuthModal = true;
            this.showProfileDropdown = false;
            this.resetChat();
            console.log('Déconnexion effectuée');
        },

        async checkAuth() {
            if (!this.token) {
                console.log('Aucun token trouvé, affichage de la modal d\'authentification');
                this.showAuthModal = true;
                return;
            }
            
            console.log('Token trouvé, vérification...');

            try {
                const response = await axios.get(`${this.API_URL}/api/auth/me`, {
                    headers: getAuthHeaders(this.token)
                });

                this.user = response.data.user || response.data;
                this.showAuthModal = false;

                console.log('Authentification réussie:', this.user);

                // Ajouter le message de bienvenue approprié
                this.addWelcomeMessage();
            } catch (error) {
                console.error('Token invalide:', error);
                this.logout();
            }
        },

        resetAuthForm() {
            this.authForm = {
                name: '',
                email: '',
                password: '',
                consent: false
            };
        },

        /**
         * Ajoute le message de bienvenue approprié selon le rôle de l'utilisateur
         * Vérifie qu'il n'y a pas déjà de message de bienvenue pour éviter les doublons
         */
        addWelcomeMessage() {
            // Ne pas ajouter si l'utilisateur n'est pas défini
            if (!this.user) {
                console.log('[Auth] Pas d\'utilisateur, message de bienvenue non ajouté');
                return;
            }

            // Vérifier s'il y a déjà un message de bienvenue (PENDING ou WELCOME)
            const hasWelcomeMessage = this.messages.some(msg =>
                msg.content && (
                    msg.content.includes('Compte en attente de validation') ||
                    msg.content.includes('Je suis votre assistant juridique')
                )
            );

            if (hasWelcomeMessage) {
                console.log('[Auth] Message de bienvenue déjà présent, pas de duplication');
                return;
            }

            // Ajouter le message approprié selon le rôle
            if (this.user.role === 0) {
                // Utilisateur en attente de validation
                this.addMessage({
                    type: 'assistant',
                    content: AppConfig.PENDING_MESSAGE,
                    sender: '🤖 Assistant Juridique'
                });
                console.log('[Auth] Message d\'attente de validation ajouté');
            } else {
                // Utilisateur validé (role >= 1)
                this.addMessage({
                    type: 'assistant',
                    content: AppConfig.WELCOME_MESSAGE,
                    sender: '🤖 Assistant Juridique'
                });
                console.log('[Auth] Message de bienvenue ajouté');
            }
        },

        toggleProfileDropdown() {
            this.showProfileDropdown = !this.showProfileDropdown;
        },

        // openSettings() est maintenant géré par SettingsModule
        // Cette méthode est conservée ici pour compatibilité mais sera écrasée par SettingsModule

        openAdminPanel() {
            this.showProfileDropdown = false;
            window.location.href = 'features/admin/admin.html';
        },

        setupAxiosInterceptors() {
            const vueInstance = this;
            
            // Interceptor pour ajouter le token à toutes les requêtes
            axios.interceptors.request.use(config => {
                if (vueInstance.token) {
                    config.headers.Authorization = `Bearer ${vueInstance.token}`;
                }
                return config;
            });

            // Interceptor pour gérer les erreurs d'authentification
            axios.interceptors.response.use(
                response => response,
                error => {
                    if (error.response?.status === 401) {
                        // Token expiré ou invalide
                        vueInstance.logout();
                    }
                    return Promise.reject(error);
                }
            );
        }
    }
};