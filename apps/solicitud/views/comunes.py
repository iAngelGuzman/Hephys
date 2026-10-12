from django.shortcuts import render

from apps.usuario.decorators import rol_requerido
from apps.usuario.models import User


@rol_requerido(User.Rol.ALUMNO)
def lista_tramites(request):
    tramites = [
        {
            "titulo": "Justificante Médico",
            "descripcion": "Documento que certifica una inasistencia por motivos de salud.",
            "icono": "Justificantes.jpg",
        },
        {
            "titulo": "Constancia de Estudios",
            "descripcion": (
                "Documento oficial que acredita tu inscripción en la Universidad "
                "y que estás cursando un programa educativo."
            ),
            "icono": "certificate.jpg",
        },
        {
            "titulo": "Examen Extraordinario y Título de Suficiencia",
            "descripcion": "Solicitud para presentar evaluaciones extraordinarias o de título de suficiencia.",
            "icono": "Exam.jpg",
        },
        {
            "titulo": "Altas / Bajas de Experiencias Educativas",
            "descripcion": "Solicitud para dar de alta o baja materias inscritas.",
            "icono": "course.jpg",
        },
    ]
    return render(request, "solicitud/tramites.html", {"tramites": tramites})
