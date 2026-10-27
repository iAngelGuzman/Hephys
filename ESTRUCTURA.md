# Estructura base del proyecto

La estructura solicitada en la **Semana 1 y 2 (tabla 2)** está implementada
físicamente en este repositorio. Hephys es una sola app de Django llamada
`app`; las tres capas documentadas son paquetes dentro de ella.

## Mapeo de carpetas

| Ubicación documentada | Implementación | Contenido |
|---|---|---|
| `app/controllers` | `app/controllers/` | Lógica de negocio: servicios de trámites y administración, reglas académicas, auditoría, validación de PDF, límite de intentos y middleware. |
| `app/models` | `app/models/` | Clases de persistencia del ORM sobre MySQL: `usuario.py`, `estudiante.py`, `secretaria.py`, `solicitud.py` y `administrador.py`. |
| `app/views` | `app/views/` | Vistas por rol (`autenticacion`, `estudiante`, `secretaria`, `administracion`, `tramites`), la sonda de salud (`salud.py` → `/health`) y formularios en `app/views/forms/`. |
| `config` | `config/` | `settings.py`, `database.py` (conexión MySQL centralizada), `urls/` (enrutamiento por módulo), `wsgi.py` y `asgi.py`. |
| `storage/secure_uploads` | `storage/secure_uploads/` | Carpeta reservada para documentos sensibles, fuera de `public/`, `static/` y `media/`. Los justificantes médicos y comprobantes se guardan en `Papeles/` y solo se descargan por una vista con control de rol y propiedad. |
| `public` | `public/` | Raíz pública: `public/static/` con CSS, JS e íconos compartidos y por módulo. Los puntos de entrada son `manage.py` y `config/wsgi.py`. |
| `tests` | `tests/` | Pruebas de estructura, seguridad, autenticación, trámites, administración y plantillas. |
| `postman` | `postman/` | Colección de Postman (`Hephys.postman_collection.json`) con 30 peticiones para probar los endpoints reales con sesión y CSRF, más su guía de uso. |

## Modelos y tablas

| Archivo | Modelos | Tablas |
|---|---|---|
| `app/models/usuario.py` | `User` | `usuarios` |
| `app/models/estudiante.py` | `Estudiante` | `estudiantes` |
| `app/models/secretaria.py` | `Secretaria` | `secretarias` |
| `app/models/solicitud.py` | `Solicitud`, `BitacoraTransaccional`, `ComprobantePago`, `PeriodoTramite`, `CalendarioMatricula`, `ExperienciaEducativa`, `ExperienciaEducativaOferta` | `tramites`, `bitacora_transaccional`, `comprobantes_pago`, `app_periodotramite`, `app_calendariomatricula`, `app_experienciaeducativa`, `app_experienciaeducativaoferta` |
| `app/models/administrador.py` | `Carrera`, `HorarioExamen` | `app_carrera`, `app_horarioexamen` |

Las tablas `catalogo_tramites`, `requisitos_tramite`, `detalle_traspasos`,
`certificados_ingles`, `observaciones_solicitud` y `documentos_solicitud`
fueron eliminadas en `app.0003_limpieza_tablas` por no usarse en ningún flujo.
También se eliminaron `auth_group`, `auth_group_permissions`,
`usuarios_groups` y `usuarios_user_permissions`: la autorización usa el campo
`rol`, no los grupos/permisos de Django.

## Uso de las capas

```python
# Persistencia
from app.models import ComprobantePago, Solicitud, User

# Lógica de negocio
from app.controllers import crear_solicitud_constancia, registrar_movimiento

# Interfaz
from app.views import login_usuario, aprobar_solicitud_secretaria
```

También se puede importar el módulo completo cuando se necesita una función
concreta:

```python
from app.controllers import reglas
from app.views import administracion
```

## Reglas de la estructura

- **Una sola app Django**: `app` está en `INSTALLED_APPS`; no hay paquetes
  `apps/*` paralelos.
- **Sin duplicar lógica**: los modelos, servicios y vistas viven una sola vez
  en la capa que les corresponde.
- **Documentos sensibles**: nunca dentro de `public/`, `static/` ni `media/`.
  Las rutas se configuran en `config/settings.py`
  (`CARPETA_JUSTIFICANTES`, `CARPETA_COMPROBANTES_PAGO` y
  `CARPETA_RESOLUCIONES`).
- **Base de datos**: la conexión se arma solo en `config/database.py`. No
  abras conexiones sueltas en vistas ni servicios.
- **Pruebas**: cualquier cambio de seguridad debe venir con una prueba en
  `tests/`.

## Comandos de verificación

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py verificar_bd
python manage.py test
```

`python manage.py test` descubre automáticamente los archivos `test_*.py` de
`tests/`.
