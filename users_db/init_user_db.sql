CREATE TABLE IF NOT EXISTS progreso_usuarios (
    user_id VARCHAR(36) PRIMARY KEY,
    datos_progreso JSONB,
    fecha TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_user_id ON progreso_usuarios(user_id);