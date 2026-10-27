# Guía de desarrollo — Hephys

Esta guía es para quien continúa la tesis. Explica qué ya está hecho, qué
falta, cómo está organizado el código y qué reglas seguir para que el proyecto
no se desordene. Primero instala el proyecto siguiendo el [README](README.md).

---

## 1. Dónde se quedó el proyecto

**Ya funciona:**

- Inicio de sesión con límite de intentos, registro de alumnos y cierre de sesión.
- Acceso por rol: alumno, secretaria de grupo y Secretaría Académica.
- Panel de la Secretaría Académica: periodos de altas y bajas por matrícula,
  oferta educativa (se sube en PDF), calendario de exámenes, cupos y alta de
  secretarias.
- Panel de la secretaria de grupo: solicitudes pendientes, aprobar o rechazar,
  e historial.
- Del lado del alumno: la pantalla **Trámites Escolares** (las tarjetas con
  buscador), "Mis solicitudes" y el historial.

**Lo que falta (tu trabajo):** las pantallas de cada trámite. Hoy cada tarjeta
tiene su botón **Solicitar**, pero el botón todavía no lleva a ningún lado. Los cuatro trámites son:

| Trámite | Tipo en `Solicitud.TipoTramite` | Quién revisa |
|---|---|---|
| Justificante médico | `justificante` | Secretaría Académica autoriza los días → secretaria de grupo |
| Constancia de estudios | `constancia` | Secretaria de grupo la elabora → Secretaría Académica la firma |
| Examen extraordinario / título de suficiencia | `extraordinario`, `suficiencia` | Secretaria de grupo |
| Altas / bajas de experiencias educativas | `alta`, `baja` | Secretaría Académica → secretaria de grupo |

**Lo que ya existe y puedes reutilizar.** La lógica de negocio de los trámites
se dejó en el proyecto; solo se quitaron las vistas, URLs y plantillas.

- `app/models/solicitud.py`: el modelo `Solicitud` ya tiene todos los campos y
  estados (fechas de inasistencia, motivo de constancia, motivo de baja,
  documento médico, etc.).
- `app/controllers/reglas.py`: reglas para saber si el periodo está abierto,
  el límite de bajas, los créditos mínimos, los cruces de horario y el plazo
  del justificante.
- `app/controllers/servicios_solicitud.py`: funciones que crean las solicitudes
  (`crear_solicitudes_examen`, `crear_solicitudes_alta`,
  `crear_solicitudes_baja`, `crear_solicitud_constancia`,
  `crear_solicitud_justificante`) y que procesan el horario y las papeletas.
- `app/views/forms/solicitud.py`: formularios de horario, papeleta, constancia
  y justificante.
- `app/controllers/utils_solicitud.py` y `app/controllers/lectores_pdf.py`:
  lectura del horario en PDF.

Lee esos archivos antes de escribir lógica nueva: es probable que lo que
necesitas ya esté ahí.

---

## 2. Cómo está organizado el código

Hephys tiene **una sola app de Django** llamada `app`. Dentro de ella se
separan las tres capas documentadas:

```text
app/
├── models/         # Tablas de la base de datos
│   ├── usuario.py
│   ├── estudiante.py
│   ├── secretaria.py
│   ├── solicitud.py
│   └── administrador.py
├── controllers/    # Operaciones que guardan o modifican datos
│   ├── servicios_solicitud.py
│   ├── servicios_administracion.py
│   ├── reglas.py
│   ├── auditoria.py
│   ├── validadores.py
│   ├── lectores_pdf.py
│   ├── decoradores.py
│   ├── limite_intentos.py
│   ├── middleware.py
│   └── signals.py
└── views/          # Reciben la petición y devuelven una página
    ├── autenticacion.py
    ├── estudiante.py
    ├── secretaria.py
    ├── administracion.py
    ├── tramites.py
    └── forms/      # Validación de lo que el usuario envía
```

Las plantillas están en `templates/` y los estáticos en `public/static/`.
Las rutas se reparten en `config/urls/` y las pruebas en `tests/`.

**Regla de capas:** la vista debe ser delgada.

> **Estructura base documentada (Semana 1 y 2).** `app/controllers`,
> `app/models` y `app/views` son carpetas reales, no fachadas. `config/`
> centraliza la conexión MySQL y el enrutamiento, `public/static/` guarda los
> estáticos, `storage/secure_uploads/` queda reservada para documentos
> sensibles y `tests/` contiene las pruebas. El mapeo completo está en
> [`ESTRUCTURA.md`](ESTRUCTURA.md).

1. La **vista** recibe la petición, usa un **form** para validar y llama a
   **services** para guardar.
2. Las **reglas** deciden si algo está permitido y lanzan
   `TramiteNoPermitidoError` con el mensaje para el alumno.
3. Las **plantillas** solo muestran datos. El JavaScript puede avisar antes de
   enviar, pero **toda validación importante se repite en el servidor**.

Las plantillas compartidas están en `templates/` en la raíz: `base.html`,
`topbar.html`, `stepper.html` (los pasos 1-2-3 de un trámite) y
`boton_regresar.html`.

---

## 3. Cómo agregar un trámite (paso a paso)

Ejemplo: activar **Constancia de estudios**.

### 3.1 La vista

Crea `app/views/constancias.py`:

```python
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from app.models.estudiante import Estudiante
from app.controllers.decoradores import rol_requerido
from app.models.usuario import User
from app.controllers.excepciones_solicitud import TramiteNoPermitidoError
from app.views.forms.solicitud import SolicitudConstanciaForm


@rol_requerido(User.Rol.ALUMNO)
def informacion_constancia(request):
    return render(request, "solicitud/constancias/informacion_constancia.html")


@rol_requerido(User.Rol.ALUMNO)
def solicitar_constancia(request):
    estudiante = get_object_or_404(Estudiante, user=request.user)
    form = SolicitudConstanciaForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        try:
            # Llama aquí a la función de servicios_solicitud.py que crea la solicitud.
            ...
        except TramiteNoPermitidoError as error:
            messages.error(request, str(error))
        else:
            return redirect("solicitud:lista_tramites")
    return render(
        request,
        "solicitud/constancias/solicitar_constancia.html",
        {"form": form, "paso_actual": 1},
    )
```

**Siempre** pon `@rol_requerido(...)` en cada vista. Sin él, cualquiera
podría entrar escribiendo la URL.

### 3.2 Registrarla en las rutas

En `config/urls/solicitud.py`:

```python
from app.views.constancias import informacion_constancia, solicitar_constancia
```

Y agrega los `path(...)` correspondientes. Si prefieres exponerla desde el
paquete, agrega el nombre al `_MAPA` de `app/views/__init__.py`.

### 3.3 La URL

En `config/urls/solicitud.py`:

```python
from app.views.constancias import informacion_constancia, solicitar_constancia

path("constancia-estudios/", informacion_constancia, name="informacion_constancia"),
path("constancia-estudios/solicitar/", solicitar_constancia, name="solicitar_constancia"),
```

### 3.4 La plantilla

Créala en `templates/solicitud/constancias/` y extiende la base:

```django
{% extends "base.html" %}
{% load static %}
{% block title %}Constancia de Estudios{% endblock %}
{% block content %}
  {% include "stepper.html" %}
  ...
{% endblock %}
```

Los archivos CSS y JS de esa pantalla van en `public/static/solicitud/`.

### 3.5 Activar el botón "Solicitar"

En `app/views/tramites.py`, agrega `"url"` a la tarjeta del trámite:

```python
{
    "titulo": "Constancia de Estudios",
    ...
    "url": "informacion_constancia",
},
```

En `tramites.html` el botón hoy es un `<button>` sin destino. Cámbialo para
que, si la tarjeta tiene `url`, sea un enlace:

```django
{% if t.url %}
  <a href="{% url 'solicitud:'|add:t.url %}" class="btn-solicitar">Solicitar</a>
{% else %}
  <button type="button" class="btn-solicitar">Solicitar</button>
{% endif %}
```

Los estilos de `.btn-solicitar` ya están en `tramites.css`.

### 3.6 Pruebas

Agrega pruebas en `tests/test_solicitud.py`. La clase `BaseTramites` ya crea
una secretaria y un alumno con sesión iniciada. Prueba por lo menos:

- que la pantalla responde 200 para el alumno;
- que otro rol recibe 403;
- que una solicitud válida se crea y una inválida muestra el error.

Hay una prueba, `test_no_se_puede_entrar_a_los_tramites`, que verifica que
los botones no lleven a ningún trámite. **Actualízala** cuando actives el
primero.

---

## 4. Reglas del proyecto

**Seguridad**

- Cada vista lleva `@rol_requerido`.
- Filtra siempre por el usuario conectado. Por ejemplo,
  `Solicitud.objects.filter(estudiante__user=request.user)` y no
  `Solicitud.objects.get(pk=id)` a secas. Si no, un alumno podría ver las
  solicitudes de otro cambiando el número en la URL.
- No confíes en campos ocultos ni en rutas de archivos que vengan del
  formulario; valida que pertenezcan al alumno (por ejemplo, guárdalas en
  `request.session`).
- Los archivos subidos se validan con `validadores.py` o con los `clean_*` de
  los formularios.
- Si creas varias solicitudes a la vez, usa `transaction.atomic()` para que
  no se guarden a medias.

**Nombres y estilo**

- Código en español, en minúsculas con guion bajo: `crear_solicitud_constancia`,
  `fecha_inicio_inasistencia`.
- Nombres de archivos de plantillas **en minúsculas**. En Windows
  `Stepper.html` y `stepper.html` son lo mismo, pero en el servidor (Linux)
  no, y la página truena.
- Los números y textos fijos van en `constants.py`, no sueltos en el código.

**Base de datos**

- La conexión vive en `config/database.py`; no abras conexiones a MySQL en
  vistas ni servicios. Las credenciales van en `.env`.
- La fuente de verdad del esquema son los modelos: si cambias uno,
  `python manage.py makemigrations`, luego `migrate`, y sube la migración
  junto con el cambio. No edites a mano las tablas de MySQL.
- Después de migrar, `python manage.py verificar_bd` comprueba la conexión,
  `utf8mb4`, el modo estricto y que todo sea InnoDB.
- Nunca borres ni edites migraciones que ya están en el repositorio.
- Las tablas principales usan los nombres del modelo relacional documentado:
  `usuarios`, `estudiantes`, `secretarias`, `tramites`,
  `bitacora_transaccional` y `comprobantes_pago`. Las tablas de apoyo
  (`app_periodotramite`, `app_calendariomatricula`,
  `app_experienciaeducativa`, `app_experienciaeducativaoferta`, `app_carrera`
  y `app_horarioexamen`) se crean desde los modelos. El esquema final tiene 18
  tablas (ver `database/README.md`).
- La bitácora **no se edita ni se borra**: se llena sola con la señal
  `post_save` de `Solicitud` y el `AuditoriaMiddleware`. Si necesitas registrar
  un movimiento manual, usa `app.controllers.auditoria.registrar_movimiento()`.
- Los archivos sensibles se guardan fuera de `public/`, `static/` y `media/`:
  los justificantes en `CARPETA_JUSTIFICANTES`, las papeletas en
  `CARPETA_COMPROBANTES_PAGO` y las resoluciones en `CARPETA_RESOLUCIONES`.
  Se descargan mediante una vista con control de rol y propiedad.
- Los cambios de estado deben hacerse con `transaction.atomic()`; la bitácora
  se escribe en la misma transacción.

**Lo que nunca se sube a git** (ya está en `.gitignore`)

- `.env` (contiene contraseñas), `venv/`, `Papeles/` (documentos de alumnos) y
  `staticfiles/`.
- Si por error se sube una contraseña, **cámbiala** de inmediato; borrar el
  archivo no basta, porque queda en el historial.

---

## 5. Flujo de trabajo con Git

1. Antes de empezar, actualiza tu copia:
   ```bash
   git pull
   ```
2. Trabaja en tu propia rama, una por trámite o funcionalidad:
   ```bash
   git checkout -b constancia-estudios
   ```
3. Antes de subir, comprueba que todo esté bien:
   ```bash
   python manage.py check
   python manage.py test
   ```
4. Sube los cambios con un mensaje que diga **qué** hiciste:
   ```bash
   git add .
   git commit -m "Agrega la pantalla para solicitar constancia de estudios"
   git push -u origin constancia-estudios
   ```
5. En GitHub abre un *Pull Request* hacia `main` para que lo revisen antes de
   unirlo.

Revisa siempre `git status` antes de `git add .`: si aparece `.env` o algo de
`Papeles/`, no lo subas.

---

## 6. Problemas comunes

| Error | Solución |
|---|---|
| `venv\Scripts\activate` → "no se encuentra la ruta" | El entorno no existe todavía: `python -m venv venv`. |
| `ModuleNotFoundError: No module named 'django'` | No activaste el entorno virtual o falta `pip install -r requirements.txt`. |
| Falla la instalación de `mysqlclient` | Instala MySQL Connector/C (librerías de desarrollo) y reinstala con `pip install -r requirements.txt`. |
| `SECRET_KEY not found` | Falta el archivo `.env` (cópialo de `.env.example`). |
| `Unknown database 'hephys_db'` | Crea la base con `mysql -u root -p < database/crear_base.sql` antes de `migrate`. |
| `TemplateDoesNotExist` | Revisa la ruta y que el nombre esté en minúsculas. |
| `NoReverseMatch` | Usaste en `{% url %}` o `redirect()` un nombre de URL que no existe en `urls.py`. |
| 403 al entrar a una página | El usuario no tiene el rol que pide `@rol_requerido`. |
| No aparece el CSS en producción | Corre `python manage.py collectstatic`. |
