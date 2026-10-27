# `storage/` — documentos sensibles

Este directorio aísla los archivos oficiales de los alumnos. **No** está
dentro de `public/`, `static/` ni `media/`, así que el servidor web no los
expone por URL: solo se descargan mediante las vistas que comprueban rol y
propiedad (`CA-04`).

## Carpetas de este directorio

| Carpeta | Contenido | Configuración |
|---|---|---|
| `secure_uploads/` | Zona reservada para documentos sensibles. | `CARPETA_DOCUMENTOS_SEGUROS` |
| `resoluciones/` | Resoluciones y constancias generadas por la institución. | `CARPETA_RESOLUCIONES` |

## Archivos que usa el sistema

Los documentos que hoy sube el alumno se guardan en `Papeles/`, también fuera
de la zona pública:

| Carpeta | Contenido | Configuración |
|---|---|---|
| `Papeles/justificantes/` | Comprobantes médicos de los justificantes. | `CARPETA_JUSTIFICANTES` |
| `Papeles/comprobantes_pago/` | Papeletas de pago de los trámites. | `CARPETA_COMPROBANTES_PAGO` |

Cada archivo se registra en la base de datos (`comprobantes_pago` o el campo
`documento_medico` de `tramites`) y se sirve solo a través de una vista que
verifica el rol y la propiedad de la solicitud.

## Reglas

- Los archivos subidos **nunca** se versionan en git (ver `.gitignore`); solo
  se versionan las carpetas y este README.
- No cambies los nombres de las carpetas: en Linux distinguen mayúsculas y
  `config/settings.py` apunta a estas rutas exactas.
- En producción, respalda este directorio y limita los permisos del usuario
  que ejecuta Django.
