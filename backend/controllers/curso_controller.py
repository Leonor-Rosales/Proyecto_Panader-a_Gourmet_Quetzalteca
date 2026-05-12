"""
controllers/curso_controller.py
CRUD completo para la tabla 'curso'.

CAMBIOS:
- obtener_cursos()  → filtra solo is_active=True (fix calendario index)
- obtener_curso()   → verifica is_active
- eliminar_curso()  → SOFT DELETE: pone is_active=False en lugar de DELETE
- crear_curso()     → sets is_active=True por defecto
"""

from database.conexion import db
from models.models import Curso
from datetime import date as date_type


def obtener_cursos():
    """
    Devuelve solo cursos activos (is_active=True).
    FIX calendario index: el frontend solo recibe cursos visibles.
    """
    cursos = (Curso.query
              .filter_by(is_active=True)
              .order_by(Curso.fecha_inicio.asc())
              .all())
    return [c.to_dict() for c in cursos], 200


def obtener_curso(id_curso: int):
    curso = Curso.query.get(id_curso)
    if not curso or not curso.is_active:
        return {"message": "Curso no encontrado."}, 404
    return curso.to_dict(), 200


def crear_curso(data: dict):
    """
    Campos requeridos: nombre_curso, descripcion, fecha_inicio, precio_curso,
                       duracion_horas, modalidad, cupo_maximo, id_docente
    Campos opcionales: hora, nivel, extras, imagen, estado
    """
    requeridos = ["nombre_curso", "descripcion", "fecha_inicio",
                  "precio_curso", "duracion_horas", "modalidad",
                  "cupo_maximo", "id_docente"]
    for campo in requeridos:
        if not data.get(campo):
            return {"message": f"El campo '{campo}' es obligatorio."}, 400

    try:
        fecha = date_type.fromisoformat(data["fecha_inicio"])
    except ValueError:
        return {"message": "Formato de fecha inválido. Use YYYY-MM-DD."}, 400

    nuevo = Curso(
        nombre_curso   = data["nombre_curso"],
        descripcion    = data["descripcion"],
        fecha_inicio   = fecha,
        precio_curso   = float(data["precio_curso"]),
        duracion_horas = int(data["duracion_horas"]),
        modalidad      = data["modalidad"],
        cupo_maximo    = int(data["cupo_maximo"]),
        id_docente     = int(data["id_docente"]),
        hora           = data.get("hora"),
        nivel          = data.get("nivel"),
        extras         = data.get("extras"),
        imagen         = data.get("imagen"),
        estado         = data.get("estado", "disponible"),
        is_active      = True,
    )
    db.session.add(nuevo)
    db.session.commit()
    return {"message": "Curso creado.", "curso": nuevo.to_dict()}, 201


def actualizar_curso(id_curso: int, data: dict):
    curso = Curso.query.get(id_curso)
    if not curso or not curso.is_active:
        return {"message": "Curso no encontrado."}, 404

    if "nombre_curso"   in data: curso.nombre_curso    = data["nombre_curso"]
    if "descripcion"    in data: curso.descripcion     = data["descripcion"]
    if "precio_curso"   in data: curso.precio_curso    = float(data["precio_curso"])
    if "duracion_horas" in data: curso.duracion_horas  = int(data["duracion_horas"])
    if "modalidad"      in data: curso.modalidad       = data["modalidad"]
    if "cupo_maximo"    in data: curso.cupo_maximo     = int(data["cupo_maximo"])
    if "id_docente"     in data: curso.id_docente      = int(data["id_docente"])
    if "hora"           in data: curso.hora            = data["hora"]
    if "nivel"          in data: curso.nivel           = data["nivel"]
    if "extras"         in data: curso.extras          = data["extras"]
    if "imagen"         in data: curso.imagen          = data["imagen"]
    if "estado"         in data: curso.estado          = data["estado"]
    if "fecha_inicio"   in data:
        try:
            curso.fecha_inicio = date_type.fromisoformat(data["fecha_inicio"])
        except ValueError:
            return {"message": "Formato de fecha inválido."}, 400

    db.session.commit()
    return {"message": "Curso actualizado.", "curso": curso.to_dict()}, 200


def eliminar_curso(id_curso: int):
    """
    SOFT DELETE: marca el curso como inactivo.
    Las inscripciones históricas permanecen intactas.
    """
    curso = Curso.query.get(id_curso)
    if not curso or not curso.is_active:
        return {"message": "Curso no encontrado."}, 404

    curso.is_active = False       # ← UPDATE en lugar de DELETE
    db.session.commit()
    return {"message": "Curso desactivado correctamente."}, 200
