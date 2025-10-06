-- Script de inicialização do PostgreSQL
-- Este arquivo é executado automaticamente quando o container é criado pela primeira vez

-- Habilitar extensões úteis
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Configurar timezone
SET timezone = 'UTC';

-- Criar schema se necessário
-- CREATE SCHEMA IF NOT EXISTS app_schema;

-- Log de inicialização
DO $$
BEGIN
    RAISE NOTICE '✅ Database initialized successfully';
    RAISE NOTICE '📅 Timestamp: %', NOW();
END $$;
