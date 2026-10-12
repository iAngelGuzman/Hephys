"""
Lectores de PDF de la app solicitud (horarios de clase que sube el alumno).

Aquí solo se LEE el PDF y se regresan listas/dicts de Python: nada toca la
base de datos ni la sesión (eso vive en services.py y en las vistas).

- extraer_materias_horario_examen(): horario para extraordinario/suficiencia.
- extraer_materias_altas_bajas():    horario para altas y bajas (con créditos
                                     y horarios por día).
- limpiar_materias_examen():         limpieza extra de nombres de docente.
"""

import logging
import re

import pdfplumber

from .exceptions import HorarioSinMateriasError

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Horario para exámenes (extraordinario / título de suficiencia)
# ---------------------------------------------------------------------------

PATRONES_SEGUNDA_INSCRIPCION = ["2DA INSCR", "2IN", "SEGUNDA", "2A INSCR"]
DIAS_SEMANA = {"LUN", "MAR", "MIE", "MIÉ", "JUE", "VIE", "SAB", "SÁB"}
TOLERANCIA_LINEA_ARRIBA_NRC = 10


def _agrupar_lineas_horario(palabras, tolerancia=2.5):
    lineas = []
    for palabra in sorted(palabras, key=lambda p: p["top"]):
        if lineas and abs(lineas[-1][0]["top"] - palabra["top"]) <= tolerancia:
            lineas[-1].append(palabra)
        else:
            lineas.append([palabra])
    return [sorted(l, key=lambda p: p["x0"]) for l in lineas]


def _columnas_horario(linea_encabezado, palabras_pagina):
    """Ubica las columnas a partir del encabezado de la tabla."""
    top = linea_encabezado[0]["top"]
    cercanas = [p for p in palabras_pagina if abs(p["top"] - top) <= 8]
    texto = lambda p: p["text"].strip().upper()

    experiencia = next(p for p in cercanas if texto(p).startswith("EXPERIENCIA"))
    creditos = next(
        (
            p
            for p in cercanas
            if texto(p).startswith("CR") and p["x0"] > experiencia["x0"]
        ),
        None,
    )
    academico = next((p for p in cercanas if texto(p).startswith("ACAD")), None)
    dias = [p for p in cercanas if texto(p) in DIAS_SEMANA]

    return {
        "top": top,
        "limite_nrc": experiencia["x0"],
        "fin_materia": (creditos["x0"] - 2) if creditos else experiencia["x1"] + 80,
        "inicio_docente": (academico["x0"] - 30) if academico else None,
        "fin_docente": (min(p["x0"] for p in dias) - 4) if dias else None,
    }


def extraer_materias_horario_examen(archivo_pdf):
    """
    Lee el horario de clases del alumno y regresa sus materias
    (NRC, nombre, docente y si está en 2da inscripción).

    No usa coordenadas fijas: toma la posición de las columnas del
    encabezado de la tabla (NRC / EXPERIENCIA EDUCATIVA / CRÉD / ACADÉMICO /
    LUN...), por lo que funciona tanto con el horario horizontal del SIIU
    como con el comprobante vertical tamaño carta.
    """
    if hasattr(archivo_pdf, "seek"):
        archivo_pdf.seek(0)

    materias = []
    with pdfplumber.open(archivo_pdf) as pdf:
        if not pdf.pages:
            raise HorarioSinMateriasError("El archivo PDF no contiene páginas.")

        columnas = None
        actual = None

        fin_de_tabla = False

        for pagina in pdf.pages:
            if fin_de_tabla:
                break
            palabras = pagina.extract_words()
            if not palabras:
                continue
            lineas = _agrupar_lineas_horario(palabras)

            indice_inicio = 0
            for i, linea in enumerate(lineas):
                textos = [p["text"].strip().upper() for p in linea]
                if "NRC" in textos and any(t.startswith("EXPERIENCIA") for t in textos):
                    columnas = _columnas_horario(linea, palabras)
                    indice_inicio = i + 1
                    break
            if columnas is None:
                continue

            lineas_tabla = []
            for linea in lineas[indice_inicio:]:
                if linea[0]["top"] <= columnas["top"] + 8:
                    continue
                texto_linea = " ".join(p["text"] for p in linea).upper()
                if "TOTAL DE CR" in texto_linea:
                    fin_de_tabla = True
                    break
                if (
                    "UBICACI" in texto_linea
                    or "FIRMA DEL" in texto_linea
                    or texto_linea.startswith("LOS DATOS")
                ):
                    break
                lineas_tabla.append(linea)

            def nrc_de(linea):
                primera = linea[0]
                texto = primera["text"].strip()
                if (
                    texto.isdigit()
                    and len(texto) == 5
                    and primera["x0"] < columnas["limite_nrc"]
                ):
                    return primera
                return None

            correos = [p for l in lineas_tabla for p in l if "@" in p["text"]]
            inicio_docente = (
                min(p["x0"] for p in correos) - 2
                if correos
                else columnas["inicio_docente"]
            )
            fin_docente = columnas["fin_docente"]

            tops_nrc = [l[0]["top"] for l in lineas_tabla if nrc_de(l)]
            pendientes_por_top = {}

            for linea in lineas_tabla:
                palabra_nrc = nrc_de(linea)
                top = linea[0]["top"]

                if palabra_nrc is None and any(
                    0 < t - top <= TOLERANCIA_LINEA_ARRIBA_NRC for t in tops_nrc
                ):
                    siguiente = min(t for t in tops_nrc if t > top)
                    pendientes = pendientes_por_top.setdefault(siguiente, [])
                    pendientes.append(linea)
                    continue

                if palabra_nrc is not None:
                    if actual:
                        materias.append(actual)
                    actual = {
                        "nrc": palabra_nrc["text"].strip(),
                        "_materia": [],
                        "_docente": [],
                        "es_segunda_inscripcion": False,
                    }
                    lineas_fila = pendientes_por_top.pop(top, []) + [linea]
                else:
                    if actual is None:
                        continue
                    lineas_fila = [linea]

                for l in lineas_fila:
                    texto_linea = " ".join(p["text"] for p in l).upper()
                    if any(pat in texto_linea for pat in PATRONES_SEGUNDA_INSCRIPCION):
                        actual["es_segunda_inscripcion"] = True
                    for p in l:
                        if p is palabra_nrc:
                            continue
                        texto = p["text"].strip()
                        x0 = p["x0"]
                        if columnas["limite_nrc"] - 15 <= x0 < columnas["fin_materia"]:
                            actual["_materia"].append(texto)
                        elif (
                            inicio_docente is not None
                            and x0 >= inicio_docente
                            and (fin_docente is None or x0 < fin_docente)
                            and "@" not in texto
                            and not any(c.isdigit() for c in texto)
                            and texto not in ("-", "—", "/")
                        ):
                            actual["_docente"].append(texto)

        if actual:
            materias.append(actual)

    resultado = []
    for m in materias:
        resultado.append(
            {
                "nrc": m["nrc"],
                "materia": " ".join(m["_materia"]).strip(),
                "maestro": " ".join(m["_docente"]).strip(),
                "es_segunda_inscripcion": m["es_segunda_inscripcion"],
            }
        )
    return resultado


def limpiar_materias_examen(lista_materias):
    """Quita la leyenda "Firma del ..." y repeticiones del nombre del docente."""
    for item in lista_materias:
        docente = item.get("maestro", "")
        if docente:
            docente = re.sub(
                r"(?i)Firma\s+del\s+(?:Secretario|Alumno).*", "", docente
            ).strip()
            palabras = docente.split()
            unicas = []
            for p in palabras:
                if not unicas or unicas[-1] != p:
                    unicas.append(p)
            total = len(unicas)
            for div in (3, 2):
                if total >= div and total % div == 0:
                    sub = total // div
                    if unicas[:sub] * div == unicas:
                        unicas = unicas[:sub]
                        break
            item["maestro"] = " ".join(unicas)
        materia = item.get("materia", "")
        if materia:
            materia = re.sub(
                r"(?i)Firma\s+del\s+(?:Secretario|Alumno).*", "", materia
            ).strip()
            item["materia"] = materia

    return lista_materias


# ---------------------------------------------------------------------------
# Horario para altas y bajas
# ---------------------------------------------------------------------------


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
