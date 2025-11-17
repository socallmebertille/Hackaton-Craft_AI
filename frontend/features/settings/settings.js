/**
 * Module des paramètres utilisateur
 * Gère le profil, la sécurité, les mentions légales et la gestion du compte
 */

const SettingsModule = {
    data: {
        showSettingsModal: false,
        settingsTab: 'profile',

        // Profile form (réservé pour future utilisation)
        profileForm: {},
        isLoadingProfile: false,
        profileSuccess: false,

        // Password form
        passwordForm: {
            current_password: '',
            new_password: '',
            confirm_password: ''
        },
        isLoadingPassword: false,
        passwordSuccess: false,
        passwordError: '',

        // Account deletion
        deleteForm: {
            password: '',
            confirmation: false
        },
        showDeleteConfirmation: false,
        isLoadingDelete: false,
        deleteError: ''
    },

    methods: {
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

            // Validation
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
                    `${this.API_URL}/api/user/password`,
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

                console.log('Mot de passe mis à jour');
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
                    `${this.API_URL}/api/user/account`,
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

                // Déconnexion et redirection
                Alert.success('Votre compte a été supprimé définitivement. Conformément au RGPD, toutes vos données ont été effacées.', 'Compte supprimé');

                // Supprimer le token du localStorage
                localStorage.removeItem('authToken');

                // Recharger la page pour afficher le modal de login
                window.location.reload();
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
                    `${this.API_URL}/api/user/cancel-deletion`,
                    {},
                    {
                        headers: {
                            Authorization: `Bearer ${this.token}`
                        }
                    }
                );

                // Recharger les données utilisateur
                await this.loadCurrentUser();
                Alert.success('Demande de suppression annulée avec succès', 'Annulation réussie');
            } catch (error) {
                console.error('Erreur annulation suppression:', error);
                Alert.error(error.response?.data?.detail || 'Erreur inconnue', 'Erreur d\'annulation');
            }
        },

        viewPrivacyPolicy() {
            window.open('/privacy-policy.html', '_blank');
        },

        viewTermsOfUse() {
            window.open('/terms-of-use.html', '_blank');
        },

        formatDate(dateString) {
            if (!dateString) return 'Non disponible';
            const date = new Date(dateString);
            return date.toLocaleDateString('fr-FR', {
                day: 'numeric',
                month: 'long',
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
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

        async loadCurrentUser() {
            try {
                const response = await axios.get(
                    `${this.API_URL}/api/auth/me`,
                    {
                        headers: {
                            Authorization: `Bearer ${this.token}`
                        }
                    }
                );
                this.user = response.data.user;
            } catch (error) {
                console.error('Erreur chargement utilisateur:', error);
            }
        }
    }
};
