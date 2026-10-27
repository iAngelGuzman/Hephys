from app.models.estudiante import Estudiante

CARRERA_CODES = {
    "LINCID": Estudiante.ProgramaEducativo.LINCID,
    "LISTI": Estudiante.ProgramaEducativo.IT,
    "LIS": Estudiante.ProgramaEducativo.LIS,
    "LICIC": Estudiante.ProgramaEducativo.LICIC,
}

# Máximo de lugares que se pueden asignar a una experiencia educativa.
CUPO_MAXIMO = 20
