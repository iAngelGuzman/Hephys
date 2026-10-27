import logging
import re

import pdfplumber

logger = logging.getLogger(__name__)


def extraer_materias_altas_bajas(pdf_file, tipo_modulo="bajas"):
    """
    Extrae las materias ignorando la tabla inferior de direcciones
    para evitar que se sobrescriban o pierdan los bloques reales.
    """
    try:
        if hasattr(pdf_file, "seek"):
            pdf_file.seek(0)

        materias_dict = {}

        with pdfplumber.open(pdf_file) as pdf:
            for pagina in pdf.pages:
                palabras = pagina.extract_words()
                if not palabras:
                    continue

                lineas_dict = {}
                for palabra in palabras:
                    top_key = round(palabra["top"] / 3) * 3
                    lineas_dict.setdefault(top_key, []).append(palabra)

                lineas_ordenadas = []
                for key in sorted(lineas_dict.keys()):
                    linea = sorted(lineas_dict[key], key=lambda p: p["x0"])
                    lineas_ordenadas.append(linea)

                bloques_nrc = []
                nrc_actual = None
                lineas_nrc = []

                for linea in lineas_ordenadas:
                    if not linea:
                        continue

                    texto_linea = " ".join([p["text"] for p in linea]).upper()

                    if "DIRECCIÓN" in texto_linea or "TOTAL DE CRÉDITOS" in texto_linea:
                        break

                    primer_token = linea[0]["text"].strip()

                    if (
                        primer_token.isdigit()
                        and len(primer_token) == 5
                        and linea[0]["x0"] < 50
                    ):
                        if nrc_actual:
                            bloques_nrc.append((nrc_actual, lineas_nrc))
                        nrc_actual = primer_token
                        lineas_nrc = [linea]
                    elif nrc_actual:
                        lineas_nrc.append(linea)

                if nrc_actual and lineas_nrc:
                    bloques_nrc.append((nrc_actual, lineas_nrc))

                for nrc, lineas_bloque in bloques_nrc:
                    palabras_bloque = [p for linea in lineas_bloque for p in linea]
                    texto_bloque_lista = [
                        " ".join([p["text"] for p in linea]) for linea in lineas_bloque
                    ]
                    texto_bloque = "\n".join(texto_bloque_lista).upper()

                    if tipo_modulo == "bajas":
                        if not _verificar_escuela(texto_bloque):
                            continue

                    materia = _extraer_nombre_materia(palabras_bloque)
                    maestro = _extraer_maestro(palabras_bloque)
                    creditos = _extraer_creditos(texto_bloque)
                    status_inscripcion = _extraer_status_inscripcion(texto_bloque)
                    horarios = _extraer_horarios(texto_bloque)

                    if not materia:
                        continue

                    if nrc not in materias_dict:
                        materias_dict[nrc] = {
                            "nrc": nrc,
                            "materia": materia,
                            "maestro": maestro,
                            "creditos": creditos,
                            "escuela": "FAC ESTADISTICA E INFORMATICA",
                            "status_inscripcion": status_inscripcion,
                            "horarios": horarios,
                        }

        return list(materias_dict.values())

    except Exception:
        # procesar_horario() convierte la lista vacía en un mensaje para el
        # alumno; aquí solo se deja el detalle en el log.
        logger.exception("Error al procesar horario de altas/bajas")
        return []


def _extraer_nombre_materia(palabras_fila):
    """
    Extrae el nombre de la materia filtrando las palabras
    que caen en la columna de materias (30 <= x0 < 160).
    """
    palabras_materia = []
    for palabra in palabras_fila:
        x0 = palabra["x0"]
        texto = palabra["text"].strip()
        if 30 <= x0 < 160:
            palabras_materia.append(texto)

    materia_bruta = " ".join(palabras_materia).strip()
    return _limpiar_texto_materia(materia_bruta)


def _extraer_maestro(palabras_fila):
    """
    Extrae el nombre completo del docente filtrando
    la columna de profesores (470 <= x0 < 555), ignorando correos y números.
    """
    palabras_docente = []
    for palabra in palabras_fila:
        x0 = palabra["x0"]
        texto = palabra["text"].strip()

        if 470 <= x0 < 555:
            if "@uv.mx" in texto.lower() or any(c.isdigit() for c in texto):
                continue
            palabras_docente.append(texto)

    docente_bruto = " ".join(palabras_docente).strip()
    docente_limpio = _limpiar_docente(docente_bruto)
    return docente_limpio if docente_limpio else "SIN ASIGNAR"


def _verificar_escuela(bloque):
    bloque_upper = bloque.upper()
    return "ESTADISTICA" in bloque_upper and "INFORMATICA" in bloque_upper


def _extraer_creditos(bloque):
    patron = re.search(
        r"""
        (?:CRED\.?)?      
        \s*
        \b(\d{1,2})\b      
        \s+
        (?:ORDINARIO|EXTRAORDINARIO|EXTRAORDINARIA|REGULAR|1RA|2DA|3RA)
        \b
        """,
        bloque,
        re.IGNORECASE | re.VERBOSE | re.DOTALL,
    )
    if patron:
        try:
            return int(patron.group(1))
        except ValueError:
            pass

    match_alternativo = re.search(r"\b([4689]|10|12)\b", bloque)
    if match_alternativo:
        try:
            return int(match_alternativo.group(1))
        except ValueError:
            pass

    return 0


def _extraer_status_inscripcion(bloque):
    bloque_upper = bloque.upper()
    if "2DA" in bloque_upper or "SEGUNDA" in bloque_upper:
        return "2DA INSCRIPCIÓN"
    return "1RA INSCRIPCIÓN"


def _extraer_horarios(bloque):
    dias_mapa = {
        "LUN": "Lunes",
        "MAR": "Martes",
        "MIE": "Miércoles",
        "JUE": "Jueves",
        "VIE": "Viernes",
        "SAB": "Sábado",
    }
    horarios = []
    lineas = bloque.split("\n")
    for linea in lineas:
        tokens = linea.strip().split()
        if len(tokens) >= 6:
            ultimos_6 = tokens[-6:]
            tiene_horario = any(
                re.search(r"\d{2}:\d{2}\s*-\s*\d{2}:\d{2}", t) for t in ultimos_6
            )
            if tiene_horario:
                for idx, token in enumerate(ultimos_6):
                    match_hora = re.search(r"(\d{2}:\d{2})\s*-\s*(\d{2}:\d{2})", token)
                    if match_hora:
                        dia_abr = ["LUN", "MAR", "MIE", "JUE", "VIE", "SAB"][idx]
                        horarios.append(
                            {
                                "dia": dias_mapa[dia_abr],
                                "inicio": match_hora.group(1),
                                "fin": match_hora.group(2),
                            }
                        )
    return horarios


def _limpiar_texto_materia(texto):
    if not texto:
        return ""
    texto = re.sub(r"(?i)Firma\s+del\s+(?:Secretario|Alumno).*", "", texto).strip()
    if (
        texto.isdigit()
        or "@" in texto
        or any(
            h in texto.upper()
            for h in [
                "EXP.",
                "STATUS",
                "DIRECCIÓN",
                "PERIODO",
                "NRC",
                "ACADÉMICO",
                "UNIVERSIDAD",
            ]
        )
    ):
        return ""
    palabras = texto.split()
    palabras_unicas = []
    for p in palabras:
        if not palabras_unicas or palabras_unicas[-1] != p:
            palabras_unicas.append(p)

    return " ".join(palabras_unicas).strip()


def _limpiar_docente(texto):
    if not texto:
        return ""
    texto = re.sub(r"(?i)Firma\s+del\s+(?:Secretario|Alumno).*", "", texto).strip()
    palabras = [p for p in texto.split() if "@" not in p]

    if not palabras:
        return ""
    palabras_unicas = []
    for p in palabras:
        if not palabras_unicas or palabras_unicas[-1] != p:
            palabras_unicas.append(p)
    total = len(palabras_unicas)
    for division in (3, 2):
        if total >= division and total % division == 0:
            tamano = total // division
            bloques = [
                palabras_unicas[i * tamano : (i + 1) * tamano] for i in range(division)
            ]
            if all(b == bloques[0] for b in bloques):
                return " ".join(bloques[0])

    return " ".join(palabras_unicas).strip()
