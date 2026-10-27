# Pruebas manuales con Postman

Hephys **no es una API REST**: es una aplicación Django que devuelve HTML y
mantiene la sesión en cookies. Por eso la colección no usa tokens Bearer, sino
el flujo real del navegador:

1. `GET /login/` para obtener la cookie `csrftoken`.
2. `POST /login/` con `matricula`, `password` y `csrfmiddlewaretoken`.
3. Postman guarda la cookie `sessionid` y las peticiones siguientes viajan ya
   autenticadas.
4. `POST /logout/` al terminar cada bloque (Django 6 solo acepta POST).

## Archivos

| Archivo | Uso |
|---|---|
| `Hephys.postman_collection.json` | Colección v2.1 con 33 peticiones en 6 carpetas. |

## Importar

1. Abre Postman → **Import** → **File**.
2. Selecciona `postman/Hephys.postman_collection.json`.
3. La colección aparece como **Hephys — Pruebas funcionales**.

## Variables a editar

Antes de ejecutar, abre la colección → pestaña **Variables** y ajusta:

| Variable | Valor por defecto | Qué poner |
|---|---|---|
| `baseUrl` | `http://127.0.0.1:8000` | URL local o la de Render, sin `/` final |
| `matriculaAlumno` | `S24000001` | Matrícula de un alumno ya registrado |
| `passwordAlumno` | `CAMBIAR` | Su contraseña |
| `usuarioSecretaria` | `secretaria` | Nómina/usuario de una secretaria de grupo activa |
| `passwordSecretaria` | `CAMBIAR` | Su contraseña |
| `usuarioAdministrador` | `admin` | Usuario con rol **Secretaría Académica** |
| `passwordAdministrador` | `CAMBIAR` | Su contraseña |
| `usuarioSuper` | `admin` | Superusuario de Django |
| `passwordSuper` | `CAMBIAR` | Su contraseña |
| `csrfToken` | *(vacío)* | **No se toca**: lo llena la colección |

> `csrfToken` se actualiza solo en cada petición: un script de *pre-request*
> copia la cookie `csrftoken` a la variable y la envía en el cuerpo y en el
> encabezado `X-CSRFToken`. Django rota el token al iniciar sesión, por eso cada
> carpeta vuelve a abrir `/login/` antes de autenticarse.

## Orden de ejecución

Las carpetas están numeradas y **deben ejecutarse en orden** (o con
**Run collection**), porque cada login cambia el usuario de la sesión:

| Carpeta | Peticiones | Qué valida |
|---|---|---|
| `00 · Sin sesión` | 1 | Sin sesión, una vista privada redirige al login |
| `01 · Salud` | 2 | `/health` y `/health/` responden 200 con MySQL operativo |
| `02 · Sesión alumno` | 8 | Limpieza de sesión, login, trámites, mis solicitudes, historial y **403** al intentar entrar al panel administrativo |
| `03 · Sesión secretaría` | 6 | Limpieza de sesión, login, panel de revisión e historial |
| `04 · Sesión administración` | 12 | Limpieza de sesión, login, panel, usuarios, pendientes, altas/bajas, exámenes, cupos, oferta e historial |
| `05 · Admin de Django` | 4 | Login del admin, índice y cierre de sesión |

Cada petición incluye pruebas (`pm.test`) que verifican el código HTTP y un
texto propio de la página, para detectar si el HTML cambió. La petición
**0. Cerrar sesión previa** de las carpetas 02 a 04 permite reejecutar cualquier
bloque sin que quede abierta la sesión de otro rol.

## Requisitos de datos

- Al menos una **secretaria de grupo** activa (los alumnos la eligen al
  registrarse y las solicitudes se asignan a ella).
- Un **alumno** registrado.
- Un usuario con rol **administrador** y un **superusuario** para `/admin/`.

Si faltan, créalos así:

```bash
python manage.py createsuperuser
```

Después entra a `http://127.0.0.1:8000/admin/`, abre el usuario y cambia su
**Rol** a *Secretaría Académica*; desde `/administrador/usuarios/crear/` das de
alta a la secretaria de grupo.

## Bloqueo por intentos fallidos

El login permite **5 intentos fallidos por usuario + IP** y **20 por usuario**
desde cualquier IP; al pasarse, la cuenta queda bloqueada **15 minutos**. Si
ejecutas la colección muchas veces con contraseñas incorrectas verás `429` o el
mensaje de bloqueo: espera o limpia la caché (`cache_sistema`).

## Ejecución por línea de comandos (opcional)

Con [Newman](https://www.npmjs.com/package/newman):

```bash
npm install -g newman
newman run postman/Hephys.postman_collection.json \
  --env-var "baseUrl=http://127.0.0.1:8000" \
  --env-var "matriculaAlumno=S24000001" \
  --env-var "passwordAlumno=tu-password" \
  --env-var "usuarioSecretaria=secretaria" \
  --env-var "passwordSecretaria=tu-password" \
  --env-var "usuarioAdministrador=admin" \
  --env-var "passwordAdministrador=tu-password" \
  --env-var "usuarioSuper=admin" \
  --env-var "passwordSuper=tu-password" \
  --reporters cli
```

Newman mantiene las cookies entre peticiones igual que Postman, así que el orden
de carpetas también aplica.

## Notas

- No ejecutes la colección contra producción con datos reales: crea solicitudes
  y modifica el estado de la sesión.
- Los `GET` de configuración solo comprueban que la pantalla carga; no suben
  PDFs ni guardan periodos.
- El panel `/admin/` usa el campo `username`, no la matrícula.
