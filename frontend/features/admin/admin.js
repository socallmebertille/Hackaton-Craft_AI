/**
 * Module d'administration
 * Gère la liste des utilisateurs, validations et suppressions
 */

// Configuration de l'API - Utilise le même origin que le site (via nginx proxy)
// Nginx fait le proxy vers le backend:8000 dans Docker
const API_URL = window.location.origin;

/**
 * SÉCURITÉ: Helper pour créer les headers d'authentification
 * Utilise Authorization header au lieu de query parameter pour éviter:
 * - Exposition dans les logs serveur
 * - Exposition dans l'historique du navigateur
 * - Exposition dans les headers Referer
 */
function getAuthHeaders(token) {
    return {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    };
}

// Charger le template settings au démarrage et initialiser Vue après
async function initApp() {
    try {
        const response = await fetch('../settings/settings.html');
        const html = await response.text();
        document.getElementById('settings-placeholder').innerHTML = html;
        console.log('Template settings chargé avec succès');
    } catch (error) {
        console.error('Erreur lors du chargement du template settings:', error);
    }

    // Initialiser Vue après le chargement du template
    new Vue({
    el: '#admin-app',
    data: {
        user: null,
        token: localStorage.getItem('authToken') || null,
        isLoading: true,
        error: null,
        activeTab: 'pending',
        allUsers: [],
        processingUsers: [], // Liste des IDs des utilisateurs en cours de traitement
        showProfileDropdown: false,
        // Settings data
        showSettingsModal: false,
        settingsTab: 'profile',
        profileForm: {},
        isLoadingProfile: false,
        profileSuccess: false,
        passwordForm: {
            current_password: '',
            new_password: '',
            confirm_password: ''
        },
        isLoadingPassword: false,
        passwordSuccess: false,
        passwordError: '',
        deleteForm: {
            password: '',
            confirmation: false
        },
        showDeleteConfirmation: false,
        isLoadingDelete: false,
        deleteError: ''
    },

    computed: {
        pendingUsers() {
            return this.allUsers.filter(u => u.role === 0);
        },
        validatedUsers() {
            return this.allUsers.filter(u => u.role === 1);
        }
    },

    mounted() {
        this.checkAuth();
    },

    methods: {
        /**
         * Vérifie l'authentification et les droits admin
         */
        async checkAuth() {
            if (!this.token) {
                await Alert.warning('Vous devez être connecté pour accéder à cette page', 'Authentification requise');
                window.location.href = '../../index.html';
                return;
            }

            try {
                const response = await axios.get(`${API_URL}/api/auth/me`, {
                    headers: getAuthHeaders(this.token)
                });

                this.user = response.data.user || response.data;

                // Vérifier que l'utilisateur est admin (role = 2)
                if (this.user.role !== 2) {
                    await Alert.error('Vous devez être administrateur pour accéder à cette page', 'Accès refusé');
                    window.location.href = '../../index.html';
                    return;
                }

                // Charger les utilisateurs
                await this.loadUsers();
                console.log('Authentification admin réussie : my user', this.user.email);
            } catch (error) {
                console.error('Erreur d\'authentification:', error);
                await Alert.error('Votre session a expiré. Veuillez vous reconnecter.', 'Session expirée');
                localStorage.removeItem('authToken');
                window.location.href = '../../index.html';
            }
        },

        /**
         * Charge tous les utilisateurs depuis l'API
         */
        async loadUsers() {
            this.isLoading = true;
            this.error = null;

            try {
                const response = await axios.get(`${API_URL}/api/admin/users`, {
                    headers: getAuthHeaders(this.token)
                });

                this.allUsers = response.data.users;
                console.log('Utilisateurs chargés:', this.allUsers.length);
            } catch (error) {
                console.error('Erreur lors du chargement des utilisateurs:', error);
                this.error = error.response?.data?.detail || 'Impossible de charger les utilisateurs';
            } finally {
                this.isLoading = false;
            }
        },

        /**
         * Valide un utilisateur en attente (passe de role 0 à role 1)
         */
        async validateUser(userId) {
            if (this.processingUsers.includes(userId)) return;

            const user = this.allUsers.find(u => u.id === userId);
            if (!user) return;

            const confirmed = await Alert.confirm(
                `Voulez-vous vraiment valider l'utilisateur ${user.email} ?`,
                'Validation utilisateur'
            );

            if (!confirmed) {
                return;
            }

            this.processingUsers.push(userId);

            try {
                const response = await axios.post(
                    `${API_URL}/api/admin/users/${userId}/validate`,
                    {},
                    { headers: getAuthHeaders(this.token) }
                );

                console.log('Utilisateur validé:', response.data);

                // Mettre à jour l'utilisateur dans la liste
                const index = this.allUsers.findIndex(u => u.id === userId);
                if (index !== -1) {
                    this.allUsers[index].role = 1;
                    this.allUsers[index].role_name = 'Utilisateur validé';
                }

                // Message de succès
                this.showSuccess(`✅ ${user.email} a été validé avec succès`);
                await Alert.success(`L'utilisateur ${user.email} a été validé avec succès`, 'Validation réussie');
            } catch (error) {
                console.error('Erreur lors de la validation:', error);
                Alert.error(
                    error.response?.data?.detail || 'Erreur inconnue lors de la validation',
                    'Erreur de validation'
                );
            } finally {
                this.processingUsers = this.processingUsers.filter(id => id !== userId);
            }
        },

        /**
         * Supprime un utilisateur
         */
        async deleteUser(userId, userEmail) {
            if (this.processingUsers.includes(userId)) return;

            const confirmed = await Alert.confirmDanger(
                `Voulez-vous vraiment supprimer l'utilisateur ${userEmail} ?\n\nCette action est irréversible.`,
                '⚠️ Suppression d\'utilisateur'
            );

            if (!confirmed) {
                return;
            }

            this.processingUsers.push(userId);

            try {
                await axios.delete(
                    `${API_URL}/api/admin/users/${userId}`,
                    { headers: getAuthHeaders(this.token) }
                );

                console.log('Utilisateur supprimé:', userId);

                // Retirer l'utilisateur de la liste
                this.allUsers = this.allUsers.filter(u => u.id !== userId);

                // Message de succès
                this.showSuccess(`🗑️ ${userEmail} a été supprimé`);
                await Alert.success(`L'utilisateur ${userEmail} a été supprimé avec succès`, 'Suppression réussie');
            } catch (error) {
                console.error('Erreur lors de la suppression:', error);
                Alert.error(
                    error.response?.data?.detail || 'Erreur inconnue lors de la suppression',
                    'Erreur de suppression'
                );
            } finally {
                this.processingUsers = this.processingUsers.filter(id => id !== userId);
            }
        },

        /**
         * Formate une date au format français
         */
        formatDate(dateString) {
            if (!dateString) return 'Date inconnue';

            try {
                const date = new Date(dateString);
                return date.toLocaleDateString('fr-FR', {
                    day: '2-digit',
                    month: '2-digit',
                    year: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                });
            } catch (error) {
                return 'Date invalide';
            }
        },

        /**
         * Affiche un message de succès temporaire
         */
        showSuccess(message) {
            // Créer un élément de notification
            const notification = document.createElement('div');
            notification.className = 'success-notification';
            notification.textContent = message;
            document.body.appendChild(notification);

            // Faire apparaître avec animation
            setTimeout(() => notification.classList.add('show'), 10);

            // Retirer après 3 secondes
            setTimeout(() => {
                notification.classList.remove('show');
                setTimeout(() => notification.remove(), 300);
            }, 3000);
        },

        /**
         * Retour à la page de chat
         */
        goBackToChat() {
            window.location.href = '../../index.html';
        },

        /**
         * Toggle profile dropdown
         */
        toggleProfileDropdown() {
            this.showProfileDropdown = !this.showProfileDropdown;
        },

        /**
         * Ouvre les paramètres
         */
        openSettings() {
            this.showSettingsModal = true;
            this.showProfileDropdown = false;
            this.settingsTab = 'profile';
            this.loadUserProfileData();
        },

        closeSettings() {
            this.showSettingsModal = false;
            this.resetSettingsForms();
        },

        loadUserProfileData() {
            // Réservé pour future utilisation
        },

        async updateProfile() {
            // Réservé pour future utilisation
        },

        async updatePassword() {
            this.passwordError = '';
            this.passwordSuccess = false;

            if (this.passwordForm.new_password.length < 6) {
                this.passwordError = 'Le nouveau mot de passe doit contenir au moins 6 caractères';
                return;
            }

            if (this.passwordForm.new_password !== this.passwordForm.confirm_password) {
                this.passwordError = 'Les mots de passe ne correspondent pas';
                return;
            }

            this.isLoadingPassword = true;

            try {
                await axios.put(
                    `${API_URL}/api/user/password`,
                    {
                        current_password: this.passwordForm.current_password,
                        new_password: this.passwordForm.new_password
                    },
                    {
                        headers: {
                            Authorization: `Bearer ${this.token}`
                        }
                    }
                );

                this.passwordSuccess = true;
                this.passwordForm = {
                    current_password: '',
                    new_password: '',
                    confirm_password: ''
                };

                setTimeout(() => {
                    this.passwordSuccess = false;
                }, 3000);
            } catch (error) {
                console.error('Erreur mise à jour mot de passe:', error);
                this.passwordError = error.response?.data?.detail || 'Erreur lors de la modification du mot de passe';
            } finally {
                this.isLoadingPassword = false;
            }
        },

        async deleteAccount() {
            this.deleteError = '';
            this.isLoadingDelete = true;

            try {
                await axios.delete(
                    `${API_URL}/api/user/account`,
                    {
                        headers: {
                            Authorization: `Bearer ${this.token}`
                        },
                        data: {
                            password: this.deleteForm.password,
                            confirmation: this.deleteForm.confirmation
                        }
                    }
                );

                Alert.success('Votre compte a été supprimé définitivement. Conformément au RGPD, toutes vos données ont été effacées.', 'Compte supprimé');

                // Supprimer le token du localStorage
                localStorage.removeItem('authToken');

                // Rediriger vers la page principale
                window.location.href = '../../index.html';
            } catch (error) {
                console.error('Erreur suppression compte:', error);
                this.deleteError = error.response?.data?.detail || 'Erreur lors de la suppression du compte';
            } finally {
                this.isLoadingDelete = false;
            }
        },

        async cancelDeletion() {
            try {
                await axios.post(
                    `${API_URL}/api/user/cancel-deletion`,
                    {},
                    {
                        headers: {
                            Authorization: `Bearer ${this.token}`
                        }
                    }
                );

                const response = await axios.get(`${API_URL}/api/auth/me`, {
                    headers: getAuthHeaders(this.token)
                });
                this.user = response.data.user || response.data;
                Alert.success('Demande de suppression annulée avec succès', 'Annulation réussie');
            } catch (error) {
                console.error('Erreur annulation suppression:', error);
                Alert.error(error.response?.data?.detail || 'Erreur inconnue', 'Erreur d\'annulation');
            }
        },

        viewPrivacyPolicy() {
            window.open('../../privacy-policy.html', '_blank');
        },

        viewTermsOfUse() {
            window.open('../../terms-of-use.html', '_blank');
        },

        getRoleLabel(role) {
            const roles = {
                0: 'En attente de validation',
                1: 'Utilisateur validé',
                2: 'Administrateur'
            };
            return roles[role] || 'Inconnu';
        },

        resetSettingsForms() {
            this.profileSuccess = false;
            this.passwordSuccess = false;
            this.passwordError = '';
            this.deleteError = '';
            this.showDeleteConfirmation = false;
            this.deleteForm = {
                password: '',
                confirmation: false
            };
        },

        /**
         * Déconnexion
         */
        logout() {
            localStorage.removeItem('authToken');
            window.location.href = '../../index.html';
        }
    }
    });
}

// Lancer l'initialisation
initApp();
