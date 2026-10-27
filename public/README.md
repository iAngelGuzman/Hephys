# `public/` — raíz pública del sistema

En la estructura documentada (Semana 1 y 2, tabla 2), `public` es el
directorio raíz que guarda los archivos de entrada y los recursos estáticos.

En un proyecto Django el arranque real lo hacen estos archivos, que están en
la raíz del repositorio:

| Archivo | Función |
|---|---|
| `manage.py` | Punto de entrada de comandos (`runserver`, `migrate`, `test`). |
| `config/wsgi.py` | Punto de entrada para servidores WSGI (gunicorn, Render). |
| `config/asgi.py` | Punto de entrada para servidores ASGI. |
| `config/urls/` | Enrutamiento general del sistema (un módulo por área). |

Los recursos estáticos compartidos y los de cada módulo viven en
`public/static/` (por ejemplo `public/static/solicitud/`), y Django los
publica bajo `/static/`:

```python
STATICFILES_DIRS = [BASE_DIR / "public" / "static"]
```

`collectstatic` los copia a `staticfiles/` para servirlos en producción.

> Los documentos de alumnos **no** se guardan aquí. Van a `Papeles/` o
> `storage/secure_uploads/`, fuera de la zona pública, y solo se descargan a
> través de una vista que valida el rol y la propiedad del archivo.
