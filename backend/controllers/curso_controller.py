"""
controllers/curso_controller.py
CRUD de cursos con validaciones de fechas, cupos, filtros y vista de inscritos.
"""

from datetime import date as date_type

from sqlalchemy import or_

from database.conexion import db
from models.models import Curso, Inscripcion


def _conteo_inscritos_activos(id_curso: int) -> int:
    return Inscripcion.query.filter_by(
        id_curso=id_curso,
        is_active=True,
        estado="activa",
    ).count()


def sincronizar_estado_curso(curso: Curso):
    if not curso:
        return
    inscritos = _conteo_inscritos_activos(curso.id_curso)
    curso.estado = "lleno" if inscritos >= curso.cupo_maximo else "disponible"


def obtener_cursos(filtros=None):
    filtros = filtros or {}
    query = Curso.query.filter_by(is_active=True)

    busqueda = (filtros.get("search") or "").strip()
    if busqueda:
        like = f"%{busqueda}%"
        query = query.filter(or_(Curso.nombre_curso.ilike(like), Curso.descripcion.ilike(like)))

    estado = (filtros.get("estado") or "").strip()
    if estado:
        query = query.filter(Curso.estado == estado)

    try:
        if filtros.get("desde"):
            query = query.filter(Curso.fecha_inicio >= date_type.fromisoformat(filtros["desde"]))
        if filtros.get("hasta"):
            query = query.filter(Curso.fecha_inicio <= date_type.fromisoformat(filtros["hasta"]))
    except ValueError:
        return {"message": "Formato de fecha inválido. Use YYYY-MM-DD."}, 400

    page = max(int(filtros.get("page") or 1), 1)
    per_page = min(max(int(filtros.get("per_page") or 50), 1), 100)
    pagination = query.order_by(Curso.fecha_inicio.asc()).paginate(
        page=page,
        per_page=per_page,
        error_out=False,
    )

    return {
        "items": [c.to_dict() for c in pagination.items],
        "total": pagination.total,
        "page": pagination.page,
        "per_page": pagination.per_page,
        "pages": pagination.pages,
    }, 200


def obtener_curso(id_curso: int):
    curso = Curso.query.get(id_curso)
    if not curso or not curso.is_active:
        return {"message": "Curso no encontrado."}, 404
    return curso.to_dict(), 200


def _validar_payload_curso(data: dict, parcial=False):
    requeridos = [
        "nombre_curso", "descripcion", "fecha_inicio", "precio_curso",
        "duracion_horas", "modalidad", "cupo_maximo", "id_docente",
    ]
    if not parcial:
        for campo in requeridos:
            if not data.get(campo):
                return None, {"message": f"El campo '{campo}' es obligatorio."}, 400

    valores = {}
    if "fecha_inicio" in data:
        try:
            valores["fecha_inicio"] = date_type.fromisoformat(data["fecha_inicio"])
        except ValueError:
            return None, {"message": "Formato de fecha inválido. Use YYYY-MM-DD."}, 400
        if valores["fecha_inicio"] < date_type.today():
            return None, {"message": "No se permiten cursos con fecha pasada."}, 400

    try:
        if "precio_curso" in data:
            valores["precio_curso"] = float(data["precio_curso"])
            if valores["precio_curso"] < 0:
                return None, {"message": "El precio no puede ser negativo."}, 400
        if "duracion_horas" in data:
            valores["duracion_horas"] = int(data["duracion_horas"])
            if valores["duracion_horas"] <= 0:
                return None, {"message": "La duración debe ser mayor que cero."}, 400
        if "cupo_maximo" in data:
            valores["cupo_maximo"] = int(data["cupo_maximo"])
            if valores["cupo_maximo"] <= 0:
                return None, {"message": "El cupo máximo debe ser mayor que cero."}, 400
        if "id_docente" in data:
            valores["id_docente"] = int(data["id_docente"])
    except (TypeError, ValueError):
        return None, {"message": "Precio, duración, cupo y docente deben ser válidos."}, 400

    return valores, None, None


def crear_curso(data: dict):
    valores, error, code = _validar_payload_curso(data)
    if error:
        return error, code

    nuevo = Curso(
        nombre_curso=data["nombre_curso"].strip(),
        descripcion=data["descripcion"].strip(),
        fecha_inicio=valores["fecha_inicio"],
        precio_curso=valores["precio_curso"],
        duracion_horas=valores["duracion_horas"],
        modalidad=data["modalidad"],
        cupo_maximo=valores["cupo_maximo"],
        id_docente=valores["id_docente"],
        hora=data.get("hora"),
        nivel=data.get("nivel"),
        extras=data.get("extras"),
        imagen=data.get("imagen"),
        estado=data.get("estado", "disponible"),
        is_active=True,
    )
    db.session.add(nuevo)
    db.session.commit()
    return {"message": "Curso creado.", "curso": nuevo.to_dict()}, 201


def actualizar_curso(id_curso: int, data: dict):
    curso = Curso.query.get(id_curso)
    if not curso or not curso.is_active:
        return {"message": "Curso no encontrado."}, 404

    valores, error, code = _validar_payload_curso(data, parcial=True)
    if error:
        return error, code

    if "cupo_maximo" in valores and valores["cupo_maximo"] < _conteo_inscritos_activos(id_curso):
        return {"message": "El cupo no puede ser menor que las inscripciones activas."}, 400

    for campo in ("nombre_curso", "descripcion", "modalidad", "hora", "nivel", "extras", "imagen", "estado"):
        if campo in data:
            setattr(curso, campo, data[campo])
    for campo, valor in valores.items():
        setattr(curso, campo, valor)

    sincronizar_estado_curso(curso)
    db.session.commit()
    return {"message": "Curso actualizado.", "curso": curso.to_dict()}, 200


def eliminar_curso(id_curso: int):
    curso = Curso.query.get(id_curso)
    if not curso or not curso.is_active:
        return {"message": "Curso no encontrado."}, 404

    curso.is_active = False
    db.session.commit()
    return {"message": "Curso desactivado correctamente."}, 200


def obtener_inscritos_curso(id_curso: int):
    curso = Curso.query.get(id_curso)
    if not curso or not curso.is_active:
        return {"message": "Curso no encontrado."}, 404

    inscripciones = (
        Inscripcion.query
        .filter_by(id_curso=id_curso, is_active=True, estado="activa")
        .order_by(Inscripcion.fecha_inscripcion.desc())
        .all()
    )
    total = len(inscripciones)
    return {
        "curso": curso.to_dict(),
        "inscritos": [i.to_dict() for i in inscripciones],
        "total_inscritos": total,
        "cupos_disponibles": max(curso.cupo_maximo - total, 0),
    }, 200
