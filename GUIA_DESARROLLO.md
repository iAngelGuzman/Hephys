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

- `apps/solicitud/models.py`: el modelo `Solicitud` ya tiene todos los campos y
  estados (fechas de inasistencia, motivo de constancia, motivo de baja,
  documento médico, etc.). **No hace falta crear migraciones para empezar.**
- `apps/solicitud/reglas.py`: reglas para saber si el periodo está abierto,
  el límite de bajas, los créditos mínimos, los cruces de horario y el plazo
  del justificante.
- `apps/solicitud/services.py`: funciones que crean las solicitudes
  (`crear_solicitudes_examen`, `crear_solicitudes_alta`,
  `crear_solicitudes_baja`, `crear_solicitud_constancia`,
  `crear_solicitud_justificante`) y que procesan el horario y las papeletas.
- `apps/solicitud/forms.py`: formularios de horario, papeleta, constancia y
  justificante.
- `apps/solicitud/utils.py` y `lectores_pdf.py`: lectura del horario en PDF.

Lee esos archivos antes de escribir lógica nueva: es probable que lo que
necesitas ya esté ahí.

---

## 2. Cómo está organizado el código

Cada carpeta dentro de `apps/` es una app de Django con la misma forma:

```text
apps/<app>/
├── models.py       # Tablas de la base de datos
├── views.py        # o views/<archivo>.py: reciben la petición y devuelven una página
├── urls.py         # Rutas de la app
├── forms.py        # Validación de lo que el usuario envía
├── services.py     # Operaciones que guardan o modifican datos
├── reglas.py       # Reglas de negocio (solo consultan y validan, no guardan)
├── constants.py    # Números y textos fijos (límites, motivos, etc.)
├── templates/<app>/...
└── static/<app>/css|js|img/...
```

**Regla de capas:** la vista debe ser delgada.

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

Crea `apps/solicitud/views/constancias.py`:

```python
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from apps.estudiante.models import Estudiante
from apps.usuario.decorators import rol_requerido
from apps.usuario.models import User

from ..exceptions import TramiteNoPermitidoError
from ..forms import SolicitudConstanciaForm


@rol_requerido(User.Rol.ALUMNO)
def informacion_constancia(request):
    return render(request, "solicitud/constancias/informacion_constancia.html")


@rol_requerido(User.Rol.ALUMNO)
def solicitar_constancia(request):
    estudiante = get_object_or_404(Estudiante, user=request.user)
    form = SolicitudConstanciaForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        try:
            # Llama aquí a la función de services.py que crea la solicitud.
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

### 3.2 Exportarla

En `apps/solicitud/views/__init__.py`:

```python
from .comunes import lista_tramites
from .constancias import informacion_constancia, solicitar_constancia
```

### 3.3 La URL

En `apps/solicitud/urls.py`:

```python
path("constancia-estudios/", views.informacion_constancia, name="informacion_constancia"),
path("constancia-estudios/solicitar/", views.solicitar_constancia, name="solicitar_constancia"),
```

### 3.4 La plantilla

Créala en `apps/solicitud/templates/solicitud/constancias/` y extiende la base:

```django
{% extends "base.html" %}
{% load static %}
{% block title %}Constancia de Estudios{% endblock %}
{% block content %}
  {% include "stepper.html" %}
  ...
{% endblock %}
```

Los archivos CSS y JS de esa pantalla van en `apps/solicitud/static/solicitud/`.

### 3.5 Activar el botón "Solicitar"

En `apps/solicitud/views/comunes.py`, agrega `"url"` a la tarjeta del trámite:

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

Agrega pruebas en `apps/solicitud/tests.py`. La clase `BaseTramites` ya crea
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

- Si cambias un modelo: `python manage.py makemigrations` y luego `migrate`,
  y sube la migración junto con el cambio.
- Nunca borres ni edites migraciones que ya están en el repositorio.

**Lo que nunca se sube a git** (ya está en `.gitignore`)

- `.env` (contiene contraseñas), `venv/`, `db.sqlite3`, `Papeles/` (documentos
  de alumnos) y `staticfiles/`.
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

Revisa siempre `git status` antes de `git add .`: si aparece `.env`,
`db.sqlite3` o algo de `Papeles/`, no lo subas.

---

## 6. Problemas comunes

| Error | Solución |
|---|---|
| `venv\Scripts\activate` → "no se encuentra la ruta" | El entorno no existe todavía: `python -m venv venv`. |
| `ModuleNotFoundError: No module named 'django'` | No activaste el entorno virtual o falta `pip install -r requirements.txt`. |
| Falla la instalación de `mysqlclient` | Usa SQLite (`USE_SQLITE=True`) o instala MySQL Connector/C. |
| `SECRET_KEY not found` | Falta el archivo `.env` (cópialo de `.env.example`). |
| `Unknown database 'sistema'` | Crea la base en MySQL Workbench antes de `migrate`. |
| `TemplateDoesNotExist` | Revisa la ruta y que el nombre esté en minúsculas. |
| `NoReverseMatch` | Usaste en `{% url %}` o `redirect()` un nombre de URL que no existe en `urls.py`. |
| 403 al entrar a una página | El usuario no tiene el rol que pide `@rol_requerido`. |
| No aparece el CSS en producción | Corre `python manage.py collectstatic`. |
