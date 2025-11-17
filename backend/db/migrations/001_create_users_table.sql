-- Migration: Create users table
-- Description: Initial users table with authentication and role management
-- Date: 2025-10-22

CREATE TABLE IF NOT EXISTS users (
    -- Identifiant unique
    id SERIAL PRIMARY KEY,

    -- Authentification
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,

    -- Gestion des permissions et validation
    role INTEGER NOT NULL DEFAULT 0 CHECK (role IN (0, 1, 2)),
    -- 0 = En attente de validation
    -- 1 = Utilisateur accepté
    -- 2 = Admin

    -- Métadonnées
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index pour optimiser les recherches
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- Commentaires sur les colonnes
COMMENT ON TABLE users IS 'Table des utilisateurs avec système de validation par admin';
COMMENT ON COLUMN users.role IS '0=En attente, 1=Accepté, 2=Admin';
