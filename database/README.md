# Base de datos MySQL de Hephys

Este directorio contiene todo lo necesario para crear y revisar la base de
datos `hephys_db`. La fuente de verdad del esquema son los modelos de Django:
`python manage.py migrate` crea las tablas a partir de ellos. Los archivos
`.sql` son para crear la base y para documentar la estructura en la tesis.

| Archivo | Para qué sirve |
|---|---|
| `crear_base.sql` | Crea `hephys_db` y el usuario `hephys_user` con permisos solo sobre esa base. |
| `hephys_db.sql` | Estructura completa generada con `mysqldump --no-data`. Es de referencia: incluye `DROP TABLE`, así que **no** debe ejecutarse sobre una base con datos. |

## Puesta en marcha

```bash
# 1. Crear la base (una sola vez)
mysql -u root -p < database/crear_base.sql

# 2. Configurar .env (copia de .env.example)
#    DB_NAME=hephys_db
#    DB_USER=hephys_user
#    DB_PASSWORD=...

# 3. Crear las tablas desde los modelos
python manage.py migrate
python manage.py createcachetable

# 4. Comprobar conexión, charset, modo estricto e InnoDB
python manage.py verificar_bd
```

## Modelo relacional (documentado en las semanas 9, 10 y 12)

| Tabla | Modelo Django | Contenido |
|---|---|---|
| `usuarios` | `app.models.usuario.User` | Cuentas, rol (`alumno`, `secretaria_grupo`, `coordinador`, `administrador`) y estado (`is_active`). |
| `estudiantes` | `app.models.estudiante.Estudiante` | Datos académicos del alumno y secretaria asignada. |
| `secretarias` | `app.models.secretaria.Secretaria` | Perfil de la secretaria de grupo. |
| `tramites` | `app.models.solicitud.Solicitud` | Solicitud general: folio único, tipo, estado, fechas, revisor y resolución. |
| `bitacora_transaccional` | `app.models.solicitud.BitacoraTransaccional` | Trazabilidad de cada alta y cambio de estatus. |
| `comprobantes_pago` | `app.models.solicitud.ComprobantePago` | Papeletas de pago con folio. |

### Tablas de apoyo

| Tabla | Modelo Django | Contenido |
|---|---|---|
| `app_periodotramite` | `app.models.solicitud.PeriodoTramite` | Ventanas de apertura y cierre por tipo de trámite. |
| `app_calendariomatricula` | `app.models.solicitud.CalendarioMatricula` | Fechas de matrícula por prefijo de matrícula. |
| `app_experienciaeducativa` | `app.models.solicitud.ExperienciaEducativa` | Catálogo de experiencias educativas y créditos. |
| `app_experienciaeducativaoferta` | `app.models.solicitud.ExperienciaEducativaOferta` | Oferta por NRC, docente, horario y cupo. |
| `app_carrera` | `app.models.administrador.Carrera` | Catálogo de carreras de la FEI. |
| `app_horarioexamen` | `app.models.administrador.HorarioExamen` | Horarios de examen por carrera y periodo. |

### Tablas eliminadas por estar en desuso

`catalogo_tramites`, `requisitos_tramite`, `detalle_traspasos`,
`certificados_ingles`, `observaciones_solicitud`, `documentos_solicitud`,
`auth_group`, `auth_group_permissions`, `usuarios_groups` y
`usuarios_user_permissions`. La migración `app.0003_limpieza_tablas` las
elimina y el comando `verificar_bd` avisa si alguna reaparece.

## Decisiones de seguridad reflejadas en el esquema

- **InnoDB + transacciones**: las altas y los cambios de estado usan
  `transaction.atomic()`; la bitácora se escribe en la misma transacción.
- **Sentencias preparadas**: Django usa el ORM/mysqlclient con
  `EMULATE_PREPARES` desactivado por defecto; no se concatenan cadenas SQL.
- **Folio único**: `tramites.folio` es `UNIQUE` y se genera en el servidor con
  `secrets`, nunca se recibe del formulario.
- **Bitácora append-only**: la aplicación no edita ni borra
  `bitacora_transaccional`; el FK usa `PROTECT` para conservar la evidencia.
- **Archivos**: los comprobantes médicos y las papeletas se guardan fuera de
  `static/` y solo se descargan mediante una vista con control de rol y
  propiedad.
- **Modo estricto**: `STRICT_TRANS_TABLES` rechaza datos truncados o
  inválidos en lugar de guardarlos a medias.

