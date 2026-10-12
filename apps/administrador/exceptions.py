class ErrorProcesandoCalendarioExamenes(Exception):

    def __init__(self, mensaje="No se pudo leer el calendario de exámenes."):
        self.mensaje = mensaje
        super().__init__(self.mensaje)
