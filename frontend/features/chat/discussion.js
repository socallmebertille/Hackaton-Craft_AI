/**
 * Module de discussion/chat
 * Gère les conversations, débats juridiques, polling et export PDF
 */

// Utilisation de la configuration globale

const DiscussionModule = {
    data: {
        question: '',
        currentDebate: null,
        messages: [],
        isProcessing: false,
        isTyping: false,
        typingText: '',
        typingAvatar: '🤖',
        pollInterval: null,
        debateGenerated: false // Indique si un débat a déjà été généré
        // typingIntervals: {} // Pour gérer l'affichage progressif de chaque message
    },

    computed: {
        statusText() {
            if (!this.currentDebate) return '';
            const statusMap = {
                'processing': 'En cours de traitement',
                'completed': 'Terminé',
                'error': 'Erreur'
            };
            return statusMap[this.currentDebate.status] || this.currentDebate.status;
        },

        decodedQuestion() {
            if (!this.currentDebate?.question) return '';
            return DOMPurify.sanitize(this.currentDebate.question, {
                ALLOWED_TAGS: [],
                KEEP_CONTENT: true
            });
        },

        isInputDisabled() {
            // Désactiver l'input si l'utilisateur est en attente de validation (role=0)
            // OU si un débat a déjà été généré (nécessite de cliquer sur "Nouveau")
            return (this.user && this.user.role === 0) || this.debateGenerated;
        },

        inputPlaceholder() {
            if (this.user && this.user.role === 0) {
                return 'Compte en attente de validation...';
            } else if (this.debateGenerated) {
                return 'Cliquez sur "Nouveau" pour poser une nouvelle question...';
            } else {
                return 'Posez votre question juridique...';
            }
        }
    },

    methods: {
        renderMarkdown(text) {
            if (!text) return '';

            marked.setOptions(AppConfig.MARKDOWN_OPTIONS);
            const html = marked.parse(text);
            return DOMPurify.sanitize(html, AppConfig.DOMPURIFY_CONFIG);
        },

        addMessage(message) {
            const messageId = Date.now() + Math.random();
            const newMessage = {
                id: messageId,
                timestamp: new Date(),
                ...message,
                // Pour l'instant, afficher directement le contenu (pas d'animation progressive)
                displayedContent: message.content,
                isTyping: false
            };
            this.messages.push(newMessage);

            this.$nextTick(() => {
                this.scrollToBottom();
            });
        },

        // typeMessage(messageId, fullContent) {
        //     const message = this.messages.find(msg => msg.id === messageId);
        //     if (!message) return;

        //     const speed = 20; // Vitesse en ms par caractère
        //     let charIndex = 0;

        //     // Nettoyer l'interval précédent s'il existe
        //     if (this.typingIntervals[messageId]) {
        //         clearInterval(this.typingIntervals[messageId]);
        //     }

        //     this.typingIntervals[messageId] = setInterval(() => {
        //         if (charIndex < fullContent.length) {
        //             message.displayedContent = fullContent.substring(0, charIndex + 1);
        //             charIndex++;
        //             this.$nextTick(() => {
        //                 this.scrollToBottom();
        //             });
        //         } else {
        //             clearInterval(this.typingIntervals[messageId]);
        //             delete this.typingIntervals[messageId];
        //             message.isTyping = false;
        //         }
        //     }, speed);
        // },

        async submitQuestion() {
            const question = this.question.trim();
            if (!question || this.isProcessing) return;

            if (question.length < AppConfig.MIN_QUESTION_LENGTH) {
                Alert.warning(`La question doit contenir au moins ${AppConfig.MIN_QUESTION_LENGTH} caractères.`, 'Question trop courte');
                return;
            }

            if (question.length > AppConfig.MAX_QUESTION_LENGTH) {
                Alert.warning(`La question ne peut pas dépasser ${AppConfig.MAX_QUESTION_LENGTH} caractères.`, 'Question trop longue');
                return;
            }

            this.addMessage({
                type: 'user',
                content: question,
                sender: '👤 Vous'
            });

            this.question = '';
            this.isProcessing = true;
            this.isTyping = true;
            this.typingText = 'Recherche en cours';
            this.debateGenerated = true; // Marquer qu'un débat a été généré

            try {
                const response = await axios.post(`${this.API_URL}/api/debate/submit`, {
                    question: question
                });

                const debateId = response.data.debate_id;
                console.log(`[API] Débat créé avec ID: ${debateId}`);

                this.currentDebate = {
                    id: debateId,
                    question: question,
                    status: 'processing'
                };

                this.startPolling(debateId);

            } catch (error) {
                console.error('[API] Erreur lors de la soumission:', error);
                this.addMessage({
                    type: 'assistant',
                    content: 'Désolé, une erreur est survenue lors du traitement de votre question. Veuillez réessayer.',
                    sender: '🤖 Assistant'
                });
                this.isProcessing = false;
                this.debateGenerated = false; // Réactiver l'input en cas d'erreur
            }
        },

        async startPolling(debateId) {
            console.log(`[Polling] Démarrage du polling pour le débat ${debateId}`);
            
            this.pollInterval = setInterval(async () => {
                try {
                    const response = await axios.get(`${this.API_URL}/api/debate/${debateId}`);
                    const debate = response.data;
                    
                    this.updateDebateDisplay(debate);
                    
                    if (debate.status === 'completed' || debate.status === 'error') {
                        console.log(`[Polling] Débat terminé avec le statut: ${debate.status}`);
                        this.stopPolling();
                        this.isProcessing = false;
                        this.isTyping = false;

                        if (debate.status === 'completed') {
                            this.addMessage({
                                type: 'export',
                                content: 'Le débat est terminé ! Vous pouvez maintenant exporter la conversation en PDF.',
                                sender: '🤖 Export',
                                showExportButton: true
                            });
                        }
                    }
                } catch (error) {
                    console.error('[Polling] Erreur:', error);
                    this.stopPolling();
                    this.isProcessing = false;
                    this.isTyping = false;
                }
            }, 2000);
        },

        updateDebateDisplay(debate) {
            this.currentDebate = debate;

            // Afficher le contexte légal
            if (debate.legal_context && !this.hasMessageType('context')) {
                const contextText = debate.legal_context.summary ||
                                  (debate.legal_context.texts && debate.legal_context.texts.length > 0
                                    ? `${debate.legal_context.texts.length} texte(s) juridique(s) trouvé(s)`
                                    : 'Contexte juridique collecté');
            }

            // Afficher les rounds du débat progressivement
            if (debate.debate_rounds && Array.isArray(debate.debate_rounds)) {
                debate.debate_rounds.forEach((round, index) => {
                    const messageKey = `round_${round.position}_${round.round}`;
                    if (!this.hasMessage(messageKey)) {
                        this.addMessage({
                            type: round.position, // 'pour' ou 'contre'
                            content: round.argument,
                            sender: round.position === 'pour' ? '✅ Avocat POUR' : '❌ Avocat CONTRE',
                            messageKey: messageKey,
                            roundNumber: round.round
                        });
                    }
                });
            }

            // Afficher le résumé final
            if (debate.summary && !this.hasMessageType('summary')) {
                this.addMessage({
                    type: 'summary',
                    content: debate.summary,
                    sender: '📄 Synthèse'
                });
            }

            this.typingText = AppConfig.STATUS_MESSAGES[debate.status] || debate.status;
        },

        hasMessageType(type) {
            return this.messages.some(msg => msg.type === type);
        },

        hasMessage(messageKey) {
            return this.messages.some(msg => msg.messageKey === messageKey);
        },

        stopPolling() {
            if (this.pollInterval) {
                clearInterval(this.pollInterval);
                this.pollInterval = null;
                console.log('[Polling] Arrêté');
            }
        },

        resetChat() {
            // Nettoyer tous les intervals de typing
            // Object.keys(this.typingIntervals).forEach(key => {
            //     clearInterval(this.typingIntervals[key]);
            // });
            // this.typingIntervals = {};

            this.messages = [];
            this.currentDebate = null;
            this.question = '';
            this.isProcessing = false;
            this.isTyping = false;
            this.debateGenerated = false; // Réactiver l'input
            this.stopPolling();

            // Ajouter le message de bienvenue approprié
            // Utiliser la fonction centralisée d'AuthModule pour éviter les doublons
            if (this.addWelcomeMessage) {
                this.addWelcomeMessage();
            } else {
                // Fallback si la fonction n'est pas disponible
                console.warn('[Chat] addWelcomeMessage non disponible, ajout manuel');
                if (this.user && this.user.role === 0) {
                    this.addMessage({
                        type: 'assistant',
                        content: AppConfig.PENDING_MESSAGE,
                        sender: '🤖 Assistant Juridique'
                    });
                } else {
                    this.addMessage({
                        type: 'assistant',
                        content: AppConfig.WELCOME_MESSAGE,
                        sender: '🤖 Assistant Juridique'
                    });
                }
            }

            console.log('[Chat] Remis à zéro');
        },

        scrollToBottom() {
            if (this.$refs.chatContainer) {
                const chatMessages = this.$refs.chatContainer.querySelector('.chat-messages');
                if (chatMessages) {
                    chatMessages.scrollTop = chatMessages.scrollHeight;
                }
            }
        },

        handleEnterKey(event) {
            if (event.shiftKey) return;
            if (this.question.trim() && !this.isProcessing) {
                this.submitQuestion();
            }
        },

        getAvatarIcon(messageType) {
            return AppConfig.AVATAR_MAP[messageType] || '🤖';
        },

        formatTime(timestamp) {
            if (!timestamp) return '';
            const date = new Date(timestamp);
            return date.toLocaleTimeString('fr-FR', {
                hour: '2-digit',
                minute: '2-digit'
            });
        },

        async exportToPDF() {
            if (!this.currentDebate || !this.currentDebate.debate_id) {
                Alert.warning('Vous devez d\'abord créer un débat avant de l\'exporter', 'Aucun débat');
                return;
            }

            try {
                console.log('[Export] Téléchargement du PDF pour le débat:', this.currentDebate.debate_id);
                const response = await axios.get(
                    `${this.API_URL}/api/debate/${this.currentDebate.debate_id}/export-pdf`,
                    { responseType: 'blob' }
                );

                const blob = new Blob([response.data], { type: 'application/pdf' });
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;

                // Générer un nom de fichier avec la date
                const date = new Date().toISOString().split('T')[0];
                a.download = `debat-juridique-${date}.pdf`;

                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);

                console.log('[Export] PDF téléchargé avec succès');
            } catch (error) {
                console.error('[Export] Erreur:', error);
                Alert.error('Une erreur est survenue lors de l\'export PDF', 'Erreur d\'export');
            }
        }
    }
};