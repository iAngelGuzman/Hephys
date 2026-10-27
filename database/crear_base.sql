-- ===========================================================================
-- HEPHYS - Creación de la base de datos MySQL
-- ===========================================================================
-- Ejecutar UNA VEZ con un usuario administrador (root) en MySQL Workbench o
-- en la terminal:
--
--   mysql -u root -p < database/crear_base.sql
--
-- Después, desde la carpeta del proyecto:
--
--   python manage.py migrate
--   python manage.py createcachetable
--   python manage.py verificar_bd
--
-- El archivo database/hephys_db.sql contiene la estructura completa ya
-- generada (solo como referencia o para revisión); el camino recomendado es
-- `migrate`, porque mantiene el esquema sincronizado con los modelos.
-- ===========================================================================

CREATE DATABASE IF NOT EXISTS `hephys_db`
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------------
-- Usuario dedicado de la aplicación (recomendado para producción).
-- Cambia la contraseña antes de usarlo y colócala en el .env.
-- Para desarrollo local también se puede usar root (ver .env.example).
-- ---------------------------------------------------------------------------
CREATE USER IF NOT EXISTS 'hephys_user'@'localhost'
  IDENTIFIED BY 'CAMBIA_ESTA_CONTRASENA';

ALTER USER 'hephys_user'@'localhost'
  IDENTIFIED BY 'CAMBIA_ESTA_CONTRASENA';

-- Solo puede operar sobre hephys_db: no ve otras bases del servidor.
GRANT ALL PRIVILEGES ON `hephys_db`.* TO 'hephys_user'@'localhost';

FLUSH PRIVILEGES;

SELECT SCHEMA_NAME AS base,
       DEFAULT_CHARACTER_SET_NAME AS charset,
       DEFAULT_COLLATION_NAME AS collation
FROM information_schema.SCHEMATA
WHERE SCHEMA_NAME = 'hephys_db';
