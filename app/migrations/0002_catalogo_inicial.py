"""Catálogo inicial de trámites y requisitos (HU-03/HU-05)."""

from django.db import migrations

CATALOGO = [
    {
        "clave": "ingles",
        "nombre": "Acreditación de Inglés",
        "descripcion": (
            "Validación de constancias externas y certificaciones de inglés "
            "(EXAVER, CIX u otros centros reconocidos) para acreditar el "
            "requisito del programa educativo."
        ),
        "orden": 1,
        "requiere_pago": False,
        "requisitos": [
            "Constancia o certificación oficial en formato PDF.",
            "Documento legible, con firmas y sellos oficiales del centro expedidor.",
            "Certificación vigente a la fecha de la solicitud.",
            "Nivel o puntaje mínimo requerido por el programa educativo.",
            "Institución reconocida en la tabla de equivalencias de la UV.",
        ],
    },
    {
        "clave": "traspaso",
        "nombre": "Traspaso de Asignaturas Aprobadas",
        "descripcion": (
            "Transferencia y equivalencia crediticia de materias cursadas en "
            "otros programas educativos o instituciones."
        ),
        "orden": 2,
        "requiere_pago": False,
        "requisitos": [
            "Kárdex oficial de la institución de origen.",
            "Programa de estudios (syllabus) de cada materia de origen.",
            "Desglose de materias de origen y equivalencia propuesta en la FEI.",
            "Calificación mínima requerida para procesos de equivalencia.",
            "La materia no debe estar cursada o acreditada previamente.",
        ],
    },
    {
        "clave": "constancia",
        "nombre": "Constancia de Estudios",
        "descripcion": "Constancia que acredita la inscripción y los estudios del alumno.",
        "orden": 3,
        "requiere_pago": True,
        "requisitos": [
            "Papeleta de pago con folio.",
            "Motivo por el que se solicita la constancia.",
        ],
    },
    {
        "clave": "justificante",
        "nombre": "Justificante Médico",
        "descripcion": "Justificación de inasistencias por motivos de salud.",
        "orden": 4,
        "requiere_pago": False,
        "requisitos": [
            "Comprobante médico en formato PDF.",
            "Fechas de inicio y fin de la inasistencia.",
            "Solicitud presentada dentro de los 5 días hábiles posteriores.",
        ],
    },
    {
        "clave": "extraordinario",
        "nombre": "Examen Extraordinario",
        "descripcion": "Solicitud para presentar examen extraordinario de una experiencia educativa.",
        "orden": 5,
        "requiere_pago": True,
        "requisitos": [
            "Papeleta de pago por cada experiencia educativa.",
            "Horario de exámenes en formato PDF.",
            "Estar inscrito en la experiencia educativa.",
        ],
    },
    {
        "clave": "suficiencia",
        "nombre": "Título de Suficiencia",
        "descripcion": "Solicitud para acreditar una experiencia educativa por título de suficiencia.",
        "orden": 6,
        "requiere_pago": True,
        "requisitos": [
            "Papeleta de pago por cada experiencia educativa.",
            "Horario de exámenes en formato PDF.",
            "Estar inscrito en la experiencia educativa.",
        ],
    },
    {
        "clave": "alta",
        "nombre": "Alta de Experiencias Educativas",
        "descripcion": "Alta de una o varias experiencias educativas en el periodo vigente.",
        "orden": 7,
        "requiere_pago": False,
        "requisitos": [
            "Horario actual en formato PDF.",
            "Cumplir el mínimo de créditos del programa educativo.",
            "No exceder el límite de altas permitido.",
        ],
    },
    {
        "clave": "baja",
        "nombre": "Baja de Experiencias Educativas",
        "descripcion": "Baja de una o varias experiencias educativas del periodo vigente.",
        "orden": 8,
        "requiere_pago": False,
        "requisitos": [
            "Horario actual en formato PDF.",
            "Motivo de la baja.",
            "No exceder el límite de bajas ni el mínimo de créditos.",
        ],
    },
]


def cargar_datos(apps, schema_editor):
    Catalogo = apps.get_model("app", "CatalogoTramite")
    Requisito = apps.get_model("app", "RequisitoTramite")

    for datos in CATALOGO:
        requisitos = datos["requisitos"]
        tramite, _ = Catalogo.objects.get_or_create(
            clave=datos["clave"],
            defaults={
                "nombre": datos["nombre"],
                "descripcion": datos["descripcion"],
                "orden": datos["orden"],
                "requiere_pago": datos["requiere_pago"],
                "habilitado": True,
            },
        )
        for orden, descripcion in enumerate(requisitos, start=1):
            Requisito.objects.get_or_create(
                tramite=tramite,
                descripcion=descripcion,
                defaults={"obligatorio": True, "orden": orden},
            )


def revertir(apps, schema_editor):
    Catalogo = apps.get_model("app", "CatalogoTramite")
    Catalogo.objects.filter(clave__in=[d["clave"] for d in CATALOGO]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("app", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(cargar_datos, revertir),
    ]
