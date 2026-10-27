"""
Lectores de PDF de la app administrador. Solo LEEN el PDF y regresan datos
de Python; guardar en la base de datos es trabajo de services.py.

- extraer_registros_calendario(): calendario de exámenes por carrera.
- extraer_ofertas_pdf():          oferta educativa (NRC, docente, horarios).
"""

import re
from datetime import datetime

import pdfplumber

from app.models.estudiante import Estudiante

from .excepciones_administracion import ErrorProcesandoCalendarioExamenes
from .normalizacion import normalizar_carrera

RE_HORA = re.compile(r"^\d{1,2}:\d{2}$")
RE_FECHA = re.compile(r"^\d{2}/\d{2}/\d{4}$")
RE_NRC = re.compile(r"^\d{4,6}$")

COL_BLOQUE_SECCION = (52, 95)
COL_NOMBRE_DOCENTE = (95, 283)
COL_SALON = (283, 332)
COL_EXAMEN_ORDINARIO = (366, 428)
COL_EXAMEN_EXTRAORDINARIO = (497, 562)
COL_EXAMEN_TITULO = (636, 701)


def _en_columna(x0, columna):
    return columna[0] <= x0 < columna[1]


def _agrupar_en_lineas(palabras):

    lineas = {}
    for palabra in palabras:
        clave = round(palabra["top"])
        clave_existente = next((k for k in lineas if abs(k - clave) <= 1.5), None)
        if clave_existente is None:
            lineas[clave] = []
            clave_existente = clave
        lineas[clave_existente].append(palabra)

    return [lineas[clave] for clave in sorted(lineas.keys())]


def _parsear_fecha(texto):
    if texto and RE_FECHA.match(texto):
        return datetime.strptime(texto, "%d/%m/%Y").date()
    return None


def _parsear_hora(texto):
    if texto and RE_HORA.match(texto):
        return datetime.strptime(texto, "%H:%M").time()
    return None


def _extraer_carrera_y_periodo(palabras):
    texto_unido = " ".join(p["text"] for p in palabras)
    match_carrera = re.search(
        r"(Ingeniería\s+de\s+\w+(?:\s+\([^)]+\))?)", texto_unido, re.IGNORECASE
    )
    carrera = (
        match_carrera.group(1).strip() if match_carrera else "Ingeniería de Software"
    )
    match_periodo = re.search(
        r"PERIODO:?\s*([A-ZÁÉÍÓÚÑ]+(?:\s+\d{4})?\s*-\s*[A-ZÁÉÍÓÚÑ]+\s+\d{4}(?:\s*\(\d{6}\))?)",
        texto_unido,
        re.IGNORECASE,
    )
    periodo = (
        re.sub(r"\s+", " ", match_periodo.group(1)).strip().upper()
        if match_periodo
        else "AGOSTO 2026 - ENERO 2027 (202701)"
    )

    return carrera, periodo


RE_TITULO_SECRETARIA = re.compile(r"^SECRETAR[IÍ]A:?$", re.IGNORECASE)
RE_PREFIJO_EE = re.compile(r"^EXPERIENCIA\s+EDUCATIVA\s*:\s*", re.IGNORECASE)
ETIQUETAS_TIPO_EXAMEN = {
    "ORDINARIO": "ordinario",
    "EXTRAORDINARIO": "extraordinario",
    "TÍTULO": "titulo",
    "TITULO": "titulo",
}


def _limpiar_nombre_ee(texto):
    if not texto:
        return texto
    return RE_PREFIJO_EE.sub("", texto).strip()


def _es_formato_con_actas(pdf):
    """
    El calendario "personalizado" (una tabla por materia, con la leyenda
    "SECRETARÍA:" junto al nombre y la fecha de entrega de acta como
    "Acta: dd/mm/aaaa" debajo de cada fecha) se lee con
    _extraer_registros_formato_actas. El formato anterior (columnas fijas)
    sigue usando el lector original.
    """
    for pagina in pdf.pages:
        for palabra in pagina.extract_words():
            texto = palabra["text"].strip()
            if texto == "Acta:" or RE_TITULO_SECRETARIA.match(texto):
                return True
    return False


def extraer_registros_calendario(archivo_pdf):
    """Lee el calendario de exámenes y regresa (registros, carrera, periodo)."""
    try:
        pdf = pdfplumber.open(archivo_pdf)
    except Exception as exc:
        raise ErrorProcesandoCalendarioExamenes(
            "No se pudo abrir el PDF. Verifica que el archivo no esté dañado."
        ) from exc

    with pdf:
        if not pdf.pages:
            raise ErrorProcesandoCalendarioExamenes(
                "El archivo PDF no contiene páginas."
            )

        if _es_formato_con_actas(pdf):
            registros, carrera_nombre, periodo = _extraer_registros_formato_actas(pdf)
        else:
            registros, carrera_nombre, periodo = _extraer_registros_formato_anterior(
                pdf
            )

    for registro in registros:
        registro["ee_nombre"] = _limpiar_nombre_ee(registro.get("ee_nombre"))

    if not registros:
        raise ErrorProcesandoCalendarioExamenes(
            "No se encontraron NRC válidos en el calendario de exámenes."
        )

    return registros, carrera_nombre, periodo or "AGOSTO 2026 - ENERO 2027 (202701)"


def _extraer_registros_formato_actas(pdf):
    """
    Lee el calendario con una tabla por materia:

        NOMBRE DE LA MATERIA                    SECRETARÍA: NOMBRE
        NRC  BLOQ/SEC  CATEDRÁTICO  SALÓN/HORA  EXAMEN ORDINARIO | EXTRAORDINARIO | TÍTULO
        17802 B6/S1    PEREZ ...    ECONEX/CCI  04/12/2026       | 14/12/2026     | 11/01/2027
                                    09:00 hrs   Acta: 10/12/2026 | Acta: ...      | Acta: ...

    Las columnas se ubican a partir de los encabezados de cada tabla, así
    que no depende del tamaño de hoja ni de coordenadas fijas.
    """
    registros = []
    carrera_nombre = None
    periodo = None

    for pagina in pdf.pages:
        palabras = pagina.extract_words()
        if not palabras:
            continue

        if carrera_nombre is None:
            carrera_nombre, periodo = _extraer_carrera_y_periodo(palabras)

        etiquetas_examen = [
            p for p in palabras if p["text"].strip().upper() in ETIQUETAS_TIPO_EXAMEN
        ]
        lineas = [
            sorted(l, key=lambda p: p["x0"]) for l in _agrupar_en_lineas(palabras)
        ]

        secciones = [] 
        seccion = None

        for linea in lineas:
            texto_linea = " ".join(p["text"] for p in linea).strip().upper()
            if (
                "IMPORTANTE" in texto_linea
                or "RESPONSABILIDAD DEL ESTUDIANTE" in texto_linea
            ):
                break

            marca_secretaria = next(
                (p for p in linea if RE_TITULO_SECRETARIA.match(p["text"].strip())),
                None,
            )
            if marca_secretaria is not None:
                nombre = " ".join(
                    p["text"] for p in linea if p["x0"] < marca_secretaria["x0"]
                ).strip()
                seccion = {"ee": nombre.upper(), "encabezado": None, "palabras": []}
                secciones.append(seccion)
                continue

            if seccion is None:
                continue

            textos = {p["text"].strip().upper() for p in linea}
            if "NRC" in textos and ("CATEDRÁTICO" in textos or "BLOQ/SEC" in textos):
                top = linea[0]["top"]
                seccion["encabezado"] = {
                    "nrc": next(p for p in linea if p["text"].strip().upper() == "NRC"),
                    "bloque": next(
                        (p for p in linea if p["text"].strip().upper() == "BLOQ/SEC"),
                        None,
                    ),
                    "salon": next(
                        (
                            p
                            for p in linea
                            if p["text"].strip().upper().startswith("SAL")
                        ),
                        None,
                    ),
                    "examenes": [
                        (
                            ETIQUETAS_TIPO_EXAMEN[p["text"].strip().upper()],
                            (p["x0"] + p["x1"]) / 2,
                            p["x0"],
                        )
                        for p in etiquetas_examen
                        if abs(p["top"] - top) <= 10
                    ],
                }
                continue

            if seccion["encabezado"] is None:
                continue
            if textos <= {"EXAMEN", "ORDINARIO", "EXTRAORDINARIO", "TÍTULO", "TITULO"}:
                continue

            seccion["palabras"].extend(linea)

        for seccion in secciones:
            registros.extend(_registros_de_seccion(seccion))

    return registros, carrera_nombre, periodo


def _registros_de_seccion(seccion):
    encabezado = seccion["encabezado"]
    if not encabezado or not encabezado["examenes"]:
        return []

    x_nrc = encabezado["nrc"]["x0"]
    palabras_nrc = [
        p
        for p in seccion["palabras"]
        if RE_NRC.match(p["text"].strip()) and abs(p["x0"] - x_nrc) <= 20
    ]
    if not palabras_nrc:
        return []

    limite_bloque = (
        encabezado["bloque"]["x1"] + 5 if encabezado["bloque"] else x_nrc + 70
    )
    inicio_salon = encabezado["salon"]["x0"] - 8 if encabezado["salon"] else None
    inicio_fechas = min(x0 for _, _, x0 in encabezado["examenes"]) - 8
    por_nrc = {id(p): [] for p in palabras_nrc}
    for palabra in seccion["palabras"]:
        if any(palabra is p for p in palabras_nrc):
            continue
        dueno = min(palabras_nrc, key=lambda n: abs(n["top"] - palabra["top"]))
        por_nrc[id(dueno)].append(palabra)

    registros = []
    for palabra_nrc in palabras_nrc:
        datos = {
            "ee_nombre": seccion["ee"],
            "nrc": palabra_nrc["text"].strip(),
            "bloque_seccion": None,
            "profesor": "",
            "salon": None,
            "hora": None,
            "fecha_ordinario": None,
            "fecha_extraordinario": None,
            "fecha_titulo": None,
            "acta_ordinario": None,
            "acta_extraordinario": None,
            "acta_titulo": None,
        }
        profesor, salon, bloque = [], [], []
        palabras = sorted(
            por_nrc[id(palabra_nrc)], key=lambda p: (round(p["top"]), p["x0"])
        )

        for i, palabra in enumerate(palabras):
            texto = palabra["text"].strip()
            x0 = palabra["x0"]
            if not texto or texto == "Acta:" or texto.lower() == "hrs":
                continue

            if RE_FECHA.match(texto):
                tipo = min(
                    encabezado["examenes"],
                    key=lambda e: abs(e[1] - (x0 + palabra["x1"]) / 2),
                )[0]
                anterior = palabras[i - 1] if i > 0 else None
                es_acta = (
                    anterior is not None
                    and anterior["text"].strip() == "Acta:"
                    and abs(anterior["top"] - palabra["top"]) <= 2
                ) or datos[f"fecha_{tipo}"] is not None
                campo = f"acta_{tipo}" if es_acta else f"fecha_{tipo}"
                if datos[campo] is None:
                    datos[campo] = _parsear_fecha(texto)
                continue

            if RE_HORA.match(texto):
                datos["hora"] = _parsear_hora(texto)
                continue

            if x0 >= inicio_fechas:
                continue
            if x0 < limite_bloque:
                bloque.append(texto)
            elif inicio_salon is not None and x0 >= inicio_salon:
                salon.append(texto)
            else:
                profesor.append(texto)

        datos["bloque_seccion"] = "".join(bloque) or None
        datos["profesor"] = " ".join(profesor).strip()
        datos["salon"] = " ".join(salon).strip() or None
        registros.append(datos)

    return registros


def _extraer_registros_formato_anterior(pdf):
    registros = []
    carrera_nombre = None
    periodo = None

    for pagina in pdf.pages:
        palabras = pagina.extract_words()
        if not palabras:
            continue

        if carrera_nombre is None:
            carrera_nombre, periodo = _extraer_carrera_y_periodo(palabras)

        lineas = _agrupar_en_lineas(palabras)

        ee_actual = None
        nrcs_del_bloque = []
        horario_del_bloque = {}
        en_pie_de_pagina = False

        def cerrar_bloque():
            for entrada in nrcs_del_bloque:
                registros.append(
                    {
                        "ee_nombre": ee_actual,
                        "nrc": entrada["nrc"],
                        "bloque_seccion": entrada["bloque_seccion"],
                        "profesor": " ".join(entrada["profesor_tokens"]).strip(),
                        "salon": entrada["salon"],
                        "hora": horario_del_bloque.get("hora"),
                        "fecha_ordinario": horario_del_bloque.get("ordinario"),
                        "fecha_extraordinario": horario_del_bloque.get(
                            "extraordinario"
                        ),
                        "fecha_titulo": horario_del_bloque.get("titulo"),
                    }
                )

        for linea in lineas:
            if not linea:
                continue

            linea = sorted(linea, key=lambda p: p["x0"])
            texto_linea = " ".join(p["text"] for p in linea).strip().upper()

            if (
                "IMPORTANTE" in texto_linea
                or "RESPONSABILIDAD DEL ESTUDIANTE" in texto_linea
            ):
                en_pie_de_pagina = True
            if en_pie_de_pagina:
                continue

            primer_texto = linea[0]["text"].strip()

            if RE_NRC.match(primer_texto) and len(primer_texto) == 5:
                nueva_nrc = primer_texto
                entrada = {
                    "nrc": nueva_nrc,
                    "bloque_seccion": None,
                    "profesor_tokens": [],
                    "salon": None,
                }
                nrcs_del_bloque.append(entrada)
            else:
                nueva_nrc = None
                entrada = nrcs_del_bloque[-1] if nrcs_del_bloque else None
            if (
                not nueva_nrc
                and primer_texto
                not in (
                    "NRC",
                    "BLOQ/SEC",
                    "CATEDRÁTICO",
                    "PROGRAMA",
                    "CAMPUS/MÓDULO",
                    "UNIVERSIDAD",
                )
                and not primer_texto.startswith("SECRETARÍA")
                and not primer_texto.startswith("SECRETARIA")
                and not RE_FECHA.match(primer_texto)
                and not RE_HORA.match(primer_texto)
                and len(texto_linea) > 4
                and not any(
                    k in texto_linea
                    for k in [
                        "EXAMEN",
                        "ORDINARIO",
                        "EXTRAORDINARIO",
                        "TITULO",
                        "TÍTULO",
                        "ACTA:",
                    ]
                )
            ):
                if nrcs_del_bloque:
                    cerrar_bloque()
                    nrcs_del_bloque = []
                    horario_del_bloque = {}
                ee_actual = texto_linea
                continue

            for palabra in linea:
                if nueva_nrc and palabra is linea[0]:
                    continue

                x0 = palabra["x0"]
                texto = palabra["text"].strip()
                if not texto or texto.startswith("Acta:"):
                    continue

                if entrada is not None and _en_columna(x0, COL_BLOQUE_SECCION):
                    entrada["bloque_seccion"] = (
                        entrada["bloque_seccion"] or ""
                    ) + texto
                    continue

                if RE_HORA.match(texto) or "hrs" in texto.lower():
                    if RE_HORA.match(texto):
                        horario_del_bloque["hora"] = _parsear_hora(texto)
                    continue

                if RE_FECHA.match(texto):
                    fecha_parsed = _parsear_fecha(texto)
                    if _en_columna(x0, COL_EXAMEN_ORDINARIO):
                        horario_del_bloque["ordinario"] = fecha_parsed
                    elif _en_columna(x0, COL_EXAMEN_EXTRAORDINARIO):
                        horario_del_bloque["extraordinario"] = fecha_parsed
                    elif _en_columna(x0, COL_EXAMEN_TITULO):
                        horario_del_bloque["titulo"] = fecha_parsed
                    continue

                if entrada is None:
                    continue

                if _en_columna(x0, COL_NOMBRE_DOCENTE):
                    entrada["profesor_tokens"].append(texto)
                    continue

                if _en_columna(x0, COL_SALON):
                    entrada["salon"] = (
                        f"{entrada['salon']} {texto}" if entrada["salon"] else texto
                    )
                    continue
        if nrcs_del_bloque:
            cerrar_bloque()
            nrcs_del_bloque = []
            horario_del_bloque = {}

    return registros, carrera_nombre, periodo


def extraer_ofertas_pdf(archivo_pdf):
    """
    Lee el PDF de oferta educativa (puede traer varias carreras) y regresa
    (ofertas, carreras_no_reconocidas). Cada oferta es un dict con
    nombre_ee, carrera, nrc, docente, horarios y bloque_seccion.
    No toca la base de datos.
    """
    ofertas = []
    carreras_no_reconocidas = set()

    with pdfplumber.open(archivo_pdf) as pdf:
        bloque_seccion_actual = ""
        carrera_canonica = None

        for page in pdf.pages:
            elementos = []

            for linea in page.extract_text_lines():
                texto_linea = linea["text"].strip()
                texto_upper = texto_linea.upper()
                if any(
                    k in texto_upper
                    for k in [
                        "CARRERA:",
                        "PROGRAMA EDUCATIVO:",
                        "LICENCIATURA:",
                        "INGENIERÍA:",
                    ]
                ):
                    if ":" in texto_linea:
                        partes = texto_linea.split(":")
                        carrera_detectada = (
                            partes[1].strip() if len(partes) > 1 else partes[0].strip()
                        )
                    else:
                        carrera_detectada = texto_linea

                    carrera_resuelta = normalizar_carrera(carrera_detectada)
                    if carrera_resuelta:
                        carrera_canonica = carrera_resuelta
                    else:
                        carreras_no_reconocidas.add(carrera_detectada)
                elementos.append(
                    {
                        "tipo": "texto",
                        "top": linea["top"],
                        "texto": texto_linea,
                    }
                )

            for tabla in page.find_tables():
                elementos.append(
                    {
                        "tipo": "tabla",
                        "top": tabla.bbox[1],
                        "rows": tabla.extract(),
                    }
                )

            elementos.sort(key=lambda x: x["top"])

            for el in elementos:
                if el["tipo"] == "texto":
                    texto_linea = el["texto"]
                    if any(
                        palabra in texto_linea.upper()
                        for palabra in ["BLOQUE", "SECCIÓN", "SECCION"]
                    ):
                        bloque_seccion_actual = texto_linea

                elif el["tipo"] == "tabla":
                    for row in el["rows"]:
                        row_limpio = [cell.strip() if cell else "" for cell in row]

                        if (
                            not row_limpio
                            or "EXPERIENCIA EDUCATIVA" in row_limpio[0]
                            or "NRC" in row_limpio
                        ):
                            continue

                        if len(row_limpio) >= 13:
                            nombre_ee = row_limpio[0].replace("\n", " ").strip()
                            nrc_str = row_limpio[1].strip()

                            if not nrc_str.isdigit():
                                continue

                            nrc = int(nrc_str)

                            horarios_dict = {
                                "Lunes": row_limpio[2],
                                "Martes": row_limpio[4],
                                "Miércoles": row_limpio[6],
                                "Jueves": row_limpio[8],
                                "Viernes": row_limpio[10],
                            }

                            horarios_lista = [
                                {"dia": dia, "hora": hora}
                                for dia, hora in horarios_dict.items()
                                if hora
                            ]

                            catedratico = row_limpio[12].replace("\n", " ").strip()
                            bloque_limpio = bloque_seccion_actual.rstrip(":").strip()

                            ofertas.append(
                                {
                                    "nombre_ee": nombre_ee,
                                    "carrera": carrera_canonica,
                                    "nrc": nrc,
                                    "docente": catedratico,
                                    "horarios": horarios_lista,
                                    "bloque_seccion": bloque_limpio,
                                }
                            )

    return ofertas, carreras_no_reconocidas