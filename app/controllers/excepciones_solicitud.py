"""Errores de negocio de la app solicitud (se muestran al alumno)."""


class HorarioSinMateriasError(Exception):
    def __init__(self, mensaje="No se encontraron materias válidas en el horario."):
        self.mensaje = mensaje
        super().__init__(self.mensaje)


class ErrorProcesandoHorario(Exception):
    def __init__(self, mensaje="Ocurrió un error al procesar el horario."):
        self.mensaje = mensaje
        super().__init__(self.mensaje)


class PapeletaInvalidaError(Exception):
    def __init__(self, mensaje, archivos_guardados=None):
        self.mensaje = mensaje
        self.archivos_guardados = archivos_guardados or {}
        super().__init__(self.mensaje)


class TramiteNoPermitidoError(Exception):
    """
    El alumno no cumple una regla del trámite (periodo cerrado, límite de
    bajas, mínimo de créditos, cruce de horario...). El mensaje se le
    muestra tal cual.
    """

    def __init__(self, mensaje):
        self.mensaje = mensaje
        super().__init__(self.mensaje)
