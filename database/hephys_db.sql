-- ===========================================================================
-- HEPHYS - Estructura de la base de datos MySQL (hephys_db)
-- ===========================================================================
-- Generado con: mysqldump --no-data --skip-comments hephys_db
-- Servidor: MySQL 8.0.46
-- Motor: InnoDB | Charset: utf8mb4 | Collation: utf8mb4_unicode_ci
--
-- ADVERTENCIA: este archivo incluye DROP TABLE IF EXISTS. Sirve como
-- referencia/documentacion de la estructura, NO para ejecutarlo sobre una
-- base que ya tenga datos. Para crear las tablas usa:
--
--     python manage.py migrate
--
-- ===========================================================================

CREATE DATABASE IF NOT EXISTS hephys_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE hephys_db;


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;
DROP TABLE IF EXISTS `app_calendariomatricula`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `app_calendariomatricula` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `tipo_tramite` varchar(10) COLLATE utf8mb4_unicode_ci NOT NULL,
  `prefijo_matricula` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `fecha_apertura` datetime(6) NOT NULL,
  `fecha_cierre` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `app_carrera`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `app_carrera` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `nombre` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `clave` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `nombre` (`nombre`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `app_experienciaeducativa`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `app_experienciaeducativa` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `nombre` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `carrera` varchar(150) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `creditos` int unsigned NOT NULL,
  `tiene_prerequisito` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  CONSTRAINT `app_experienciaeducativa_chk_1` CHECK ((`creditos` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `app_experienciaeducativaoferta`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `app_experienciaeducativaoferta` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `nrc` varchar(10) COLLATE utf8mb4_unicode_ci NOT NULL,
  `docente` varchar(200) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `horarios` json NOT NULL,
  `bloque_seccion` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `cupo` int NOT NULL,
  `experiencia_educativa_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `nrc` (`nrc`),
  KEY `app_experienciaeduca_experiencia_educativ_b23da6ac_fk_app_exper` (`experiencia_educativa_id`),
  CONSTRAINT `app_experienciaeduca_experiencia_educativ_b23da6ac_fk_app_exper` FOREIGN KEY (`experiencia_educativa_id`) REFERENCES `app_experienciaeducativa` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `app_horarioexamen`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `app_horarioexamen` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `nrc` varchar(10) COLLATE utf8mb4_unicode_ci NOT NULL,
  `ee_nombre` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `profesor` varchar(200) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `bloque_seccion` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `salon` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `hora` time(6) DEFAULT NULL,
  `tipo_examen` varchar(3) COLLATE utf8mb4_unicode_ci NOT NULL,
  `fecha_examen` date NOT NULL,
  `fecha_entrega_acta` date DEFAULT NULL,
  `periodo` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `carrera_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `app_horarioexamen_carrera_id_nrc_tipo_exam_205b5dc0_uniq` (`carrera_id`,`nrc`,`tipo_examen`,`periodo`),
  CONSTRAINT `app_horarioexamen_carrera_id_25f8ade9_fk_app_carrera_id` FOREIGN KEY (`carrera_id`) REFERENCES `app_carrera` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `app_periodotramite`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `app_periodotramite` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `tipo_tramite` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `fecha_apertura` datetime(6) NOT NULL,
  `fecha_cierre` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `tipo_tramite` (`tipo_tramite`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `auth_permission`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_permission` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `content_type_id` int NOT NULL,
  `codename` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_permission_content_type_id_codename_01ab375a_uniq` (`content_type_id`,`codename`),
  CONSTRAINT `auth_permission_content_type_id_2f476e4b_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=93 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `bitacora_transaccional`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `bitacora_transaccional` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `estatus_anterior` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `estatus_nuevo` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `comentarios` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `fecha_movimiento` datetime(6) NOT NULL,
  `id_usuario_responsable` bigint DEFAULT NULL,
  `id_tramite` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_bitacora_sol_fecha` (`id_tramite`,`fecha_movimiento`),
  KEY `bitacora_transaccion_id_usuario_responsab_83bebc55_fk_usuarios_` (`id_usuario_responsable`),
  CONSTRAINT `bitacora_transaccion_id_usuario_responsab_83bebc55_fk_usuarios_` FOREIGN KEY (`id_usuario_responsable`) REFERENCES `usuarios` (`id`),
  CONSTRAINT `bitacora_transaccional_id_tramite_8b5f2bab_fk_tramites_id` FOREIGN KEY (`id_tramite`) REFERENCES `tramites` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `cache_sistema`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `cache_sistema` (
  `cache_key` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `value` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `expires` datetime(6) NOT NULL,
  PRIMARY KEY (`cache_key`),
  KEY `cache_sistema_expires` (`expires`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `comprobantes_pago`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `comprobantes_pago` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `folio` varchar(7) COLLATE utf8mb4_unicode_ci NOT NULL,
  `archivo` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `fecha_subida` datetime(6) NOT NULL,
  `solicitud_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `comprobantes_pago_solicitud_id_312295d9_fk_tramites_id` (`solicitud_id`),
  CONSTRAINT `comprobantes_pago_solicitud_id_312295d9_fk_tramites_id` FOREIGN KEY (`solicitud_id`) REFERENCES `tramites` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `django_admin_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_admin_log` (
  `id` int NOT NULL AUTO_INCREMENT,
  `action_time` datetime(6) NOT NULL,
  `object_id` longtext COLLATE utf8mb4_unicode_ci,
  `object_repr` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `action_flag` smallint unsigned NOT NULL,
  `change_message` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `content_type_id` int DEFAULT NULL,
  `user_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `django_admin_log_content_type_id_c4bce8eb_fk_django_co` (`content_type_id`),
  KEY `django_admin_log_user_id_c564eba6_fk_usuarios_id` (`user_id`),
  CONSTRAINT `django_admin_log_content_type_id_c4bce8eb_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  CONSTRAINT `django_admin_log_user_id_c564eba6_fk_usuarios_id` FOREIGN KEY (`user_id`) REFERENCES `usuarios` (`id`),
  CONSTRAINT `django_admin_log_chk_1` CHECK ((`action_flag` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `django_content_type`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_content_type` (
  `id` int NOT NULL AUTO_INCREMENT,
  `app_label` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `model` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `django_content_type_app_label_model_76bd3d3b_uniq` (`app_label`,`model`)
) ENGINE=InnoDB AUTO_INCREMENT=24 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `django_migrations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_migrations` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `app` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `applied` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=22 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `django_session`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_session` (
  `session_key` varchar(40) COLLATE utf8mb4_unicode_ci NOT NULL,
  `session_data` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `expire_date` datetime(6) NOT NULL,
  PRIMARY KEY (`session_key`),
  KEY `django_session_expire_date_a5c62663` (`expire_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `estudiantes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `estudiantes` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `nombres` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `apellido_paterno` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `apellido_materno` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `matricula` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `carrera` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `semestre` int unsigned NOT NULL,
  `numero_bajas` int DEFAULT NULL,
  `user_id` bigint NOT NULL,
  `secretaria_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `matricula` (`matricula`),
  UNIQUE KEY `user_id` (`user_id`),
  KEY `estudiantes_secretaria_id_556d827d_fk_secretarias_id` (`secretaria_id`),
  CONSTRAINT `estudiantes_secretaria_id_556d827d_fk_secretarias_id` FOREIGN KEY (`secretaria_id`) REFERENCES `secretarias` (`id`),
  CONSTRAINT `estudiantes_user_id_ad5af51c_fk_usuarios_id` FOREIGN KEY (`user_id`) REFERENCES `usuarios` (`id`),
  CONSTRAINT `estudiantes_chk_1` CHECK ((`semestre` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `secretarias`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `secretarias` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`),
  CONSTRAINT `secretarias_user_id_23a181a7_fk_usuarios_id` FOREIGN KEY (`user_id`) REFERENCES `usuarios` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `tramites`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tramites` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `tipo_tramite` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `estado` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `folio` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `fecha_solicitud` datetime(6) NOT NULL,
  `fecha_actualizacion` datetime(6) DEFAULT NULL,
  `fecha_dictamen` datetime(6) DEFAULT NULL,
  `motivo_rechazo` longtext COLLATE utf8mb4_unicode_ci,
  `documento_resolucion` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `status_inscripcion` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `observaciones` longtext COLLATE utf8mb4_unicode_ci,
  `motivo_baja` longtext COLLATE utf8mb4_unicode_ci,
  `motivo_constancia` longtext COLLATE utf8mb4_unicode_ci,
  `fecha_inicio_inasistencia` date DEFAULT NULL,
  `fecha_fin_inasistencia` date DEFAULT NULL,
  `fecha_inicio_autorizada` date DEFAULT NULL,
  `fecha_fin_autorizada` date DEFAULT NULL,
  `motivo_justificante` longtext COLLATE utf8mb4_unicode_ci,
  `documento_medico` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `lote_id` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `materia_nrc` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `materia_nombre` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `materia_maestro` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `ruta_horario` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `estudiante_id` bigint NOT NULL,
  `revisor_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `folio` (`folio`),
  KEY `idx_tramites_estado` (`estado`),
  KEY `idx_tramites_tipo` (`tipo_tramite`),
  KEY `idx_tramites_folio` (`folio`),
  KEY `tramites_estudiante_id_4c58e80e_fk_estudiantes_id` (`estudiante_id`),
  KEY `tramites_revisor_id_4cac7b52_fk_usuarios_id` (`revisor_id`),
  KEY `tramites_lote_id_58898532` (`lote_id`),
  CONSTRAINT `tramites_estudiante_id_4c58e80e_fk_estudiantes_id` FOREIGN KEY (`estudiante_id`) REFERENCES `estudiantes` (`id`),
  CONSTRAINT `tramites_revisor_id_4cac7b52_fk_usuarios_id` FOREIGN KEY (`revisor_id`) REFERENCES `usuarios` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `usuarios`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `usuarios` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `password` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `last_login` datetime(6) DEFAULT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `username` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `first_name` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `last_name` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `email` varchar(254) COLLATE utf8mb4_unicode_ci NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `date_joined` datetime(6) NOT NULL,
  `rol` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

