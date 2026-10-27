"""Validaciones de archivos que suben alumnos y administradores."""

from django.core.exceptions import ValidationError

TAMANO_MAXIMO_PDF_MB = 10


def validar_archivo_pdf(archivo, tamano_maximo_mb=TAMANO_MAXIMO_PDF_MB):
    """
    Revisa que el archivo sea realmente un PDF y no pese demasiado.

    No se confía en la extensión ni en el tipo que manda el navegador (los
    dos se pueden falsificar): se leen los primeros bytes, que en todo PDF
    empiezan con "%PDF-".
    """
    if not archivo.name.lower().endswith(".pdf"):
        raise ValidationError("El archivo debe ser un documento PDF.")

    if archivo.size > tamano_maximo_mb * 1024 * 1024:
        raise ValidationError(f"El archivo no debe pesar más de {tamano_maximo_mb} MB.")

    archivo.seek(0)
    encabezado = archivo.read(5)
    archivo.seek(0)
    if encabezado != b"%PDF-":
        raise ValidationError("El archivo no es un PDF válido o está dañado.")

    return archivo
