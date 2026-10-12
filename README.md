# Hephys — Sistema Web para la Automatización de Trámites Académicos

Sistema web para gestionar los trámites académicos de la Facultad de
Estadística e Informática (FEI-UV).

> **Estado de esta versión.** Este repositorio es el punto de partida para la
> siguiente persona que continúe la tesis. Están terminados el inicio de sesión,
> el registro de alumnos, los paneles de la Secretaría Académica y de la
> secretaria de grupo, y la pantalla **Trámites Escolares**, donde el alumno ve
> los trámites disponibles. Cada tarjeta tiene su botón **Solicitar**, pero
> **las pantallas de cada trámite no están incluidas: construirlas es el
> trabajo que sigue.** Antes de empezar, lee
> [`GUIA_DESARROLLO.md`](GUIA_DESARROLLO.md).

## Roles

| Rol | Qué puede hacer en esta versión |
|---|---|
| **Alumno** | Registrarse, iniciar sesión, ver la lista de trámites, ver "Mis solicitudes" y su historial. |
| **Secretaría Académica** (administrador) | Configurar periodos de altas y bajas, subir la oferta educativa y el calendario de exámenes, gestionar cupos, dar de alta secretarias y revisar solicitudes. |
| **Secretaria de grupo** | Aprobar o rechazar las solicitudes de sus alumnos y consultar su historial. |

## Tecnologías

- Python 3.12 o superior y Django 6.0
- MySQL (producción y desarrollo con MySQL Workbench) o SQLite (desarrollo rápido)
- pdfplumber para leer horarios, la oferta educativa y los calendarios de exámenes
- WhiteNoise para servir los archivos estáticos
- HTML, CSS y JavaScript sin frameworks de frontend

## Estructura del proyecto

```text
Hephys/
├── apps/
│   ├── usuario/        # Modelo User (con rol), login, registro, límite de intentos, @rol_requerido
│   ├── estudiante/     # Modelo Estudiante, "Mis solicitudes" e historial del alumno
│   ├── secretaria/     # Modelo Secretaria, dashboard e historial de la secretaria de grupo
│   ├── administrador/  # Panel de la Secretaría Académica (periodos, oferta, cupos, usuarios)
│   └── solicitud/      # Modelo Solicitud, catálogo de EE, periodos y la lista de trámites
│       ├── views/comunes.py   # Vista lista_tramites (pantalla "Trámites Escolares")
│       ├── reglas.py          # Reglas de negocio (periodos, límites de bajas, cruces de horario…)
│       ├── services.py        # Creación de solicitudes y manejo de archivos
│       ├── forms.py           # Formularios de los trámites
│       ├── utils.py / lectores_pdf.py  # Lectura de horarios en PDF
│       ├── validadores.py     # Validación de archivos subidos
│       └── templates/solicitud/
│           ├── tramites.html      # Pantalla con las tarjetas de trámites
│           └── componentes/       # Modales compartidos con secretaría y administrador
├── config/             # settings.py, urls.py, wsgi.py
├── templates/          # Plantillas compartidas (base, topbar, stepper, botón regresar)
├── static/             # CSS, JS e íconos compartidos
├── .env.example        # Plantilla de variables de entorno
├── GUIA_DESARROLLO.md  # Cómo trabajar en el proyecto (léela primero)
├── manage.py
└── requirements.txt
```

## Instalación local

### 1. Obtener el proyecto

Si recibiste el proyecto como **zip**: descomprímelo y abre una terminal (CMD)
dentro de la carpeta `Hephys`, la que contiene `manage.py`:

```bat
cd ruta\donde\lo\descomprimiste\Hephys
```

Si está en GitHub:

```bash
git clone <URL-de-este-repositorio>
cd Hephys
```

### 2. Crear y activar el entorno virtual

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

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

Si en Windows falla la instalación de `mysqlclient` y vas a usar SQLite,
puedes instalar lo demás con:

```bash
pip install Django==6.0.5 python-decouple pdfplumber pillow whitenoise
```

### 4. Crear el archivo `.env`

Copia `.env.example` como `.env` (en Windows: `copy .env.example .env`) y
ajusta los valores. Para empezar rápido con SQLite basta con:

```env
SECRET_KEY=una-clave-larga-y-aleatoria
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
USE_SQLITE=True
```

Para usar MySQL pon `USE_SQLITE=False` y llena `DB_NAME`, `DB_USER`,
`DB_PASSWORD`, `DB_HOST` y `DB_PORT`. La base de datos tiene que existir antes
(créala en MySQL Workbench con `CREATE DATABASE sistema CHARACTER SET utf8mb4;`).

> El archivo `.env` **nunca** se sube a git.

### 5. Crear las tablas

```bash
python manage.py migrate
python manage.py createcachetable
```

### 6. Crear el usuario de la Secretaría Académica

```bash
python manage.py createsuperuser
```

Entra a `http://127.0.0.1:8000/admin/`, abre ese usuario y cambia su **Rol** a
*Secretaría Académica*. Desde el sistema ese usuario puede dar de alta a las
secretarias de grupo. Los alumnos se registran solos en `/registro/` (necesitan
que exista al menos una secretaria de grupo).

### 7. Ejecutar

```bash
python manage.py runserver
```

Abre `http://127.0.0.1:8000/`.

### 8. Correr las pruebas

```bash
python manage.py test
```

Todas deben pasar antes de subir cambios.

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
| `USE_SQLITE` | `False` |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | datos del servidor MySQL |
| `DB_SSL` | `True` si el proveedor exige conexión cifrada (por ejemplo Aiven) |

## Seguridad (resumen)

- Acceso por rol con el decorador `@rol_requerido`; cada usuario solo ve los
  documentos de las solicitudes que le corresponden.
- Contraseñas validadas con los validadores de Django.
- Máximo 5 intentos fallidos de inicio de sesión por usuario e IP, y 20 por
  usuario desde cualquier IP (bloqueo de 15 minutos).
- Credenciales solo en variables de entorno; cookies seguras y HTTPS con
  `DEBUG=False`.

## Autoras

Proyecto desarrollado como parte de la tesis universitaria por:

- Karen Esperanza López Yoval
- Norma Isabel Torales Quintana
