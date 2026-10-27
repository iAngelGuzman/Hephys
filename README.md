# Hephys — Sistema Web para la Gestión de Trámites Escolares en la FEI

Sistema web para automatizar los trámites académicos de la Facultad de
Estadística e Informática (FEI) de la Universidad Veracruzana.

> **Estado de esta versión.** Están terminados el inicio de sesión, el registro
> de alumnos, los paneles de la Secretaría Académica y de la secretaria de
> grupo, y la pantalla **Trámites Escolares**. Cada tarjeta tiene su botón
> **Solicitar**, pero **las pantallas de cada trámite aún no están incluidas**:
> construirlas es el trabajo que sigue. La lógica de negocio de esos trámites ya
> existe en `app/controllers/servicios_solicitud.py`. Antes de empezar, lee
> [`GUIA_DESARROLLO.md`](GUIA_DESARROLLO.md).

## Roles

| Rol | Qué puede hacer en esta versión |
|---|---|
| **Alumno** | Registrarse, iniciar sesión, ver la lista de trámites, consultar "Mis solicitudes" e historial y descargar sus comprobantes. |
| **Secretaría Académica** (`administrador`) | Configurar periodos de altas y bajas, subir la oferta educativa y el calendario de exámenes, gestionar cupos, administrar usuarios y secretarias, y revisar solicitudes. |
| **Secretaria de grupo** | Aprobar o rechazar las solicitudes de sus alumnos y consultar su historial. |
| **Coordinación académica** (`coordinador`) | Rol definido en el modelo `User`, todavía sin vistas propias. |

La autorización se resuelve con el campo `rol` de `usuarios`, no con grupos ni
permisos individuales de Django.

## Tecnologías

| Componente | Versión / uso |
|---|---|
| Python | 3.12 o superior |
| Django | 6.0.5 |
| Base de datos | MySQL 8 (`utf8mb4`, InnoDB, modo estricto) |
| Driver | `mysqlclient` 2.2.8 |
| PDF | `pdfplumber` (horarios, oferta educativa y calendarios de exámenes) |
| Imágenes | `Pillow` |
| Estáticos | WhiteNoise |
| Producción | Gunicorn |
| Configuración | `python-decouple` (`.env`) |
| Frontend | HTML, CSS y JavaScript sin frameworks |

El proyecto usa **solo MySQL**; no hay soporte para SQLite.

## Estructura del proyecto

```text
Hephys/
├── app/                          # App Django única con las capas documentadas
│   ├── admin/                    # Registro de modelos en el panel de Django
│   ├── controllers/              # Lógica de negocio y transacciones
│   │   ├── servicios_solicitud.py          # Altas, bajas, constancias, pagos
│   │   ├── servicios_administracion.py     # Periodos, oferta y exámenes
│   │   ├── reglas.py                       # Reglas académicas
│   │   ├── auditoria.py                    # Bitácora transaccional
│   │   ├── validadores.py                  # Validación de archivos PDF
│   │   ├── lectores_pdf.py                 # Horarios y papeletas
│   │   ├── lectores_pdf_administracion.py  # Oferta y calendarios
│   │   ├── normalizacion.py                # Texto de carreras y materias
│   │   ├── utils_solicitud.py              # Utilidades de trámites
│   │   ├── decoradores.py                  # Control de roles
│   │   ├── limite_intentos.py              # Protección contra fuerza bruta
│   │   ├── middleware.py / signals.py      # Auditoría automática
│   │   └── constantes_*.py / excepciones_*.py
│   ├── migrations/               # 0001_initial, 0002_catalogo_inicial, 0003_limpieza_tablas
│   ├── management/commands/      # verificar_bd
│   ├── models/                   # Persistencia (ORM sobre MySQL)
│   │   ├── usuario.py            # User, roles y estado de la cuenta
│   │   ├── estudiante.py         # Estudiante
│   │   ├── secretaria.py         # Secretaria de grupo
│   │   ├── solicitud.py          # Solicitud, bitácora, comprobantes y periodos
│   │   └── administrador.py      # Carrera y horarios de examen
│   ├── templatetags/             # Filtros de plantillas
│   └── views/                    # Vistas y formularios por rol
│       ├── autenticacion.py      # Login, logout y registro
│       ├── estudiante.py         # Mis solicitudes, historial y documentos
│       ├── secretaria.py         # Panel y revisión de solicitudes
│       ├── administracion.py     # Panel de la Secretaría Académica
│       ├── tramites.py           # Lista de trámites del alumno
│       ├── salud.py              # Sonda /health
│       └── forms/                # Formularios y validación
├── config/                       # Configuración y enrutamiento
│   ├── database.py               # Conexión MySQL centralizada
│   ├── settings.py
│   ├── urls/                     # Rutas por módulo
│   ├── asgi.py
│   └── wsgi.py
├── database/                     # crear_base.sql, hephys_db.sql y README
├── public/                       # Raíz pública
│   ├── static/                   # CSS, JS e imágenes compartidas y por módulo
│   └── README.md
├── storage/                      # Documentos fuera de la zona pública
│   ├── secure_uploads/           # Zona reservada para documentos sensibles
│   └── resoluciones/             # Resoluciones y constancias emitidas
├── templates/                    # Plantillas compartidas y por módulo
├── tests/                        # Pruebas automatizadas
├── postman/                      # Colección de pruebas manuales de los endpoints
├── Papeles/                      # Archivos subidos (se crea al ejecutar; no se versiona)
├── .env.example                  # Plantilla de variables de entorno
├── ESTRUCTURA.md                 # Mapeo detallado de la estructura
├── GUIA_DESARROLLO.md            # Cómo continuar el proyecto
├── manage.py
└── requirements.txt
```

## Base de datos

La fuente de verdad del esquema son los modelos de Django. El esquema actual
tiene **18 tablas**:

| Grupo | Tablas |
|---|---|
| Modelo relacional | `usuarios`, `estudiantes`, `secretarias`, `tramites`, `bitacora_transaccional`, `comprobantes_pago` |
| Apoyo | `app_periodotramite`, `app_calendariomatricula`, `app_experienciaeducativa`, `app_experienciaeducativaoferta`, `app_carrera`, `app_horarioexamen` |
| Infraestructura Django | `auth_permission`, `django_admin_log`, `django_content_type`, `django_migrations`, `django_session`, `cache_sistema` |

Características de la conexión:

- MySQL 8 con `utf8mb4` / `utf8mb4_unicode_ci`.
- Todas las tablas usan **InnoDB** (transacciones ACID).
- `sql_mode` estricto: rechaza datos truncados o inválidos.
- Aislamiento `READ COMMITTED` y reutilización de conexiones (`CONN_MAX_AGE`).
- Credenciales solo en `.env`.

El detalle de cada tabla, las decisiones de seguridad y las tablas eliminadas
están en [`database/README.md`](database/README.md).

## Rutas principales

| Ruta | Quién entra | Función |
|---|---|---|
| `/` | Público | Redirige al login |
| `/login/`, `/logout/` | Público | Inicio y cierre de sesión |
| `/registro/` | Público | Registro de alumnos |
| `/solicitudes/lista-tramites/` | Alumno | Tarjetas de trámites |
| `/estudiante/mis-solicitudes/` | Alumno | Solicitudes en trámite |
| `/estudiante/historial/` | Alumno | Historial de solicitudes |
| `/estudiante/ver-comprobante/` | Alumno, secretaria, administrador | Descarga de papeleta |
| `/estudiante/ver-horario/<id>/` | Alumno, secretaria, administrador | Descarga del horario PDF |
| `/estudiante/ver-documento-medico/<id>/` | Alumno, secretaria, administrador | Descarga de justificante |
| `/secretaria/` | Secretaria de grupo | Panel de revisión |
| `/administrador/` | Secretaría Académica | Panel de configuración |
| `/administrador/usuarios/` | Secretaría Académica | Alta y edición de usuarios |
| `/admin/` | Superusuario | Admin de Django |
| `/health` y `/health/` | Público | Sonda de salud (JSON) |

## Instalación local

### 1. Requisitos previos

- Python 3.12 o superior.
- MySQL 8 en ejecución (servicio `MySQL80` en Windows).
- MySQL Connector/C, necesario para compilar `mysqlclient` en Windows.

### 2. Obtener el proyecto

Si lo recibiste como **zip**, descomprímelo y abre una terminal en la carpeta
que contiene `manage.py`:

```bat
cd ruta\donde\lo\descomprimiste\Hephys
```

Si está en GitHub:

```bash
git clone <URL-de-este-repositorio>
cd Hephys
```

### 3. Crear y activar el entorno virtual

```bash
python -m venv venv
```

Windows (CMD):

```bat
venv\Scripts\activate
```

Linux / macOS:

```bash
source venv/bin/activate
```

Sabes que está activo cuando la línea de la terminal empieza con `(venv)`.

### 4. Instalar dependencias

```bash
pip install -r requirements.txt
```

Si falla `mysqlclient`, instala MySQL Connector/C (incluye las librerías de
desarrollo) y vuelve a ejecutar el comando. El proyecto solo soporta MySQL,
así que `mysqlclient` es obligatorio.

### 5. Crear la base de datos

```bash
mysql -u root -p < database/crear_base.sql
```

El script crea `hephys_db` con `utf8mb4`, un usuario `hephys_user` con permisos
solo sobre esa base y muestra el charset resultante. También puedes crearla
desde MySQL Workbench:

```sql
CREATE DATABASE hephys_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 6. Configurar el `.env`

Copia `.env.example` como `.env` (en Windows: `copy .env.example .env`) y
ajusta los valores:

```env
SECRET_KEY=una-clave-larga-y-aleatoria
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=

DB_NAME=hephys_db
DB_USER=root
DB_PASSWORD=tu-password
DB_HOST=localhost
DB_PORT=3306
DB_CONN_MAX_AGE=60
DB_SSL=False
```

Genera la `SECRET_KEY` con:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

> El archivo `.env` **nunca** se sube a git.

### 7. Crear las tablas y verificar la conexión

```bash
python manage.py migrate
python manage.py createcachetable
python manage.py verificar_bd
```

`verificar_bd` muestra motor, versión de MySQL, charset, `sql_mode`, número de
tablas y confirma que todas usan InnoDB y que no quedan tablas en desuso.

### 8. Crear el primer usuario

```bash
python manage.py createsuperuser
```

Entra a `http://127.0.0.1:8000/admin/`, abre ese usuario y cambia su **Rol** a
*Secretaría Académica*. Con esa cuenta puedes dar de alta secretarias de grupo
desde `/administrador/usuarios/crear/`. Los alumnos se registran solos en
`/registro/` y deben elegir una secretaria activa, así que **primero debe
existir al menos una secretaria de grupo**.

### 9. Ejecutar

```bash
python manage.py runserver
```

Abre `http://127.0.0.1:8000/`.

## Pruebas

```bash
python manage.py test
```

El comando descubre los archivos `test_*.py` de `tests/`:

| Archivo | Cubre |
|---|---|
| `test_estructura.py` | Carpetas documentadas, estáticos, esquema y tablas eliminadas |
| `test_seguridad.py` | Folio generado en servidor y bitácora append-only |
| `test_usuario.py` | Login y bloqueo por intentos (por IP y por usuario) |
| `test_solicitud.py` | Pantallas del alumno, historial y modelo relacional |
| `test_administrador.py` | Validaciones del panel: periodos, calendario, oferta, exámenes y cupos |
| `test_plantillas.py` | HTML de las plantillas (etiquetas y atributos bien formados) |
| `test_salud.py` | Sonda `/health` (200 y 503) |

Estado actual: **39 pruebas en verde**.

### Pruebas manuales con Postman

La carpeta [`postman/`](postman/README.md) contiene
`Hephys.postman_collection.json`, una colección v2.1 con **33 peticiones en 6
carpetas** que recorre los endpoints reales:

| Carpeta | Qué prueba |
|---|---|
| `00 · Sin sesión` | Redirección al login en una vista privada |
| `01 · Salud` | `/health` y `/health/` |
| `02 · Sesión alumno` | Login, trámites, mis solicitudes, historial y 403 por rol |
| `03 · Sesión secretaría` | Panel de revisión e historial |
| `04 · Sesión administración` | Panel, usuarios, pendientes y pantallas de configuración |
| `05 · Admin de Django` | Login del admin, índice y logout |

La colección obtiene el token CSRF, inicia sesión y conserva las cookies; cada
carpeta cierra la sesión anterior y vuelve a autenticarse porque el login cambia
el usuario. Ajusta las variables (`baseUrl`, matrículas y contraseñas) antes de
ejecutarla. Los detalles están en [`postman/README.md`](postman/README.md).

## Despliegue en Render

**Build Command**

```bash
pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate && python manage.py createcachetable
```

**Start Command**

```bash
gunicorn config.wsgi:application
```

**Variables de entorno**

| Variable | Valor |
|---|---|
| `SECRET_KEY` | clave larga y aleatoria |
| `DEBUG` | `False` |
| `ALLOWED_HOSTS` | `tu-app.onrender.com` |
| `CSRF_TRUSTED_ORIGINS` | `https://tu-app.onrender.com` |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | datos del servidor MySQL |
| `DB_SSL` | `True` si el proveedor exige conexión cifrada (por ejemplo Aiven) |
| `DB_SSL_CA` | ruta al certificado CA, solo si el proveedor la pide |
| `DB_CONN_MAX_AGE` | segundos de reutilización de la conexión (`60` por defecto) |
| `SECURE_SSL_REDIRECT` | `True` por defecto con `DEBUG=False` |
| `SECURE_HSTS_SECONDS` | `0` hasta que el dominio sea definitivo |

**Health check**

Configura la ruta `/health` en Render. Responde `200` con
`{"status": "ok", "database": "ok"}` cuando Django y MySQL están operativos, y
`503` si la base de datos no responde, para que el balanceador no envíe tráfico
a una instancia rota.

## Seguridad (resumen)

- **Autorización por rol**: cada vista lleva `@rol_requerido`; no se usan
  grupos ni permisos individuales de Django.
- **Propiedad de los datos**: las consultas filtran por el usuario conectado,
  de modo que un alumno no puede ver solicitudes de otro cambiando el id.
- **Contraseñas** con los cuatro validadores de Django.
- **Fuerza bruta**: 5 intentos fallidos por usuario + IP y 20 por usuario desde
  cualquier IP; bloqueo de 15 minutos en la caché compartida.
- **CSRF** activo, cookies `Secure` y HTTPS con `DEBUG=False`.
- **SQL**: ORM de Django con sentencias preparadas; no se concatenan cadenas.
- **Bitácora append-only**: `bitacora_transaccional` no se edita ni se borra y
  su llave foránea usa `PROTECT`.
- **Archivos**: justificantes, papeletas y resoluciones se guardan fuera de
  `public/`, `static/` y `media/`, y solo se descargan mediante vistas con
  control de rol y propiedad.
- **Secretos**: credenciales únicamente en `.env`; nunca en el código ni en git.

## Documentación relacionada

- [`ESTRUCTURA.md`](ESTRUCTURA.md) — mapeo de carpetas y capas.
- [`GUIA_DESARROLLO.md`](GUIA_DESARROLLO.md) — cómo continuar y agregar trámites.
- [`database/README.md`](database/README.md) — esquema, tablas y seguridad.
- [`postman/README.md`](postman/README.md) — cómo ejecutar la colección de Postman.
- [`storage/README.md`](storage/README.md) — manejo de documentos sensibles.
- [`public/README.md`](public/README.md) — recursos estáticos.

## Autoras

Proyecto desarrollado como parte de la tesis universitaria por:

- Karen Esperanza López Yoval
- Norma Isabel Torales Quintana
