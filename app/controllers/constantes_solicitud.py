MINIMO_CREDITOS = 20

MAXIMO_BAJAS = 5

PRIMERA_INSCRIPCION = "1ra Inscripción"
SEGUNDA_INSCRIPCION = "2da Inscripción"
VECES_INSCRIPCION = (PRIMERA_INSCRIPCION, SEGUNDA_INSCRIPCION)

MOTIVO_CONSTANCIA_OTRO = "Otro"
MOTIVOS_CONSTANCIA = (
    "Beca",
    "Trámite ante el IMSS o seguro médico",
    "Trabajo",
    "Descuento de transporte",
    "Servicio social o prácticas profesionales",
    MOTIVO_CONSTANCIA_OTRO,
)

# Justificante médico: se solicita dentro de los primeros 5 días hábiles
# (lunes a viernes) después del último día de inasistencia.
PLAZO_JUSTIFICANTE_DIAS_HABILES = 5
