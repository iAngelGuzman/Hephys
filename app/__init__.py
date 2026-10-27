"""
Sistema Hephys — app Django única con la estructura base documentada.

La app ``app`` contiene las tres capas del patrón MVC:

- ``app.models``       -> clases de persistencia (ORM de Django + MySQL).
- ``app.controllers``  -> lógica de negocio y transacciones atómicas.
- ``app.views``        -> vistas, formularios y validación visual.

Las plantillas están en ``templates/``, los estáticos en ``public/static/``,
los documentos sensibles fuera de la zona pública (``Papeles/`` y
``storage/secure_uploads/``) y las pruebas en ``tests/``. La configuración y
el enrutamiento viven en ``config/``.
"""
