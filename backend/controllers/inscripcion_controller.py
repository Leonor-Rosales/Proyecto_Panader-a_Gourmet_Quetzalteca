"""
controllers/inscripcion_controller.py
Inscripciones con cupo máximo, soft delete y estadísticas activas consistentes.
"""

from datetime import datetime

from database.conexion import db
from models.models import Inscripcion, Usuario, Curso
from controllers.curso_controller import sincronizar_estado_curso


def _query_activas():
    return Inscripcion.query.filter_by(is_active=True, estado="activa")


def obtener_inscripciones():
    inscripciones = Inscripcion.query.order_by(Inscripcion.fecha_inscripcion.desc()).all()
    return [i.to_dict() for i in inscripciones], 200


def obtener_inscripcion(id_inscripcion: int):
    i = Inscripcion.query.get(id_inscripcion)
    if not i:
        return {"message": "Inscripción no encontrada."}, 404
    return i.to_dict(), 200


def crear_inscripcion(data: dict):
    requeridos = ["id_usuario", "id_curso"]
    for campo in requeridos:
        if not data.get(campo):
            return {"message": f"El campo '{campo}' es obligatorio."}, 400

    id_usuario = int(data["id_usuario"])
    id_curso = int(data["id_curso"])
    usuario = Usuario.query.get(id_usuario)
    if not usuario:
        return {"message": "Usuario no encontrado."}, 404

    try:
        curso = Curso.query.filter_by(id_curso=id_curso, is_active=True).with_for_update().first()
    except Exception:
        curso = Curso.query.filter_by(id_curso=id_curso, is_active=True).first()
    if not curso:
        return {"message": "Curso no encontrado."}, 404

    existente = Inscripcion.query.filter_by(id_usuario=id_usuario, id_curso=id_curso).first()
    if existente and existente.is_active and existente.estado == "activa":
        return {"message": "El usuario ya está inscrito en este curso."}, 409

    inscritos = _query_activas().filter_by(id_curso=id_curso).count()
    if inscritos >= curso.cupo_maximo:
        curso.estado = "lleno"
        db.session.commit()
        return {"message": "El curso ya está lleno."}, 400

    if existente:
        existente.is_active = True
        existente.estado = "activa"
        existente.fecha_cancelacion = None
        existente.fecha_inscripcion = datetime.utcnow()
        existente.estado_pago = data.get("estado_pago", "Pendiente")
        nueva = existente
    else:
        nueva = Inscripcion(
            id_usuario=id_usuario,
            id_curso=id_curso,
            estado_pago=data.get("estado_pago", "Pendiente"),
            estado="activa",
            is_active=True,
        )
        db.session.add(nueva)

    db.session.flush()
    sincronizar_estado_curso(curso)
    db.session.commit()
    return {"message": "Inscripción creada.", "inscripcion": nueva.to_dict()}, 201


def actualizar_estado(id_inscripcion: int, data: dict):
    i = Inscripcion.query.get(id_inscripcion)
    if not i:
        return {"message": "Inscripción no encontrada."}, 404
    if not i.is_active or i.estado == "cancelada":
        return {"message": "No se puede modificar una inscripción cancelada."}, 409

    estado_valido = ["Pendiente", "Anticipo", "Pagado"]
    nuevo_estado = data.get("estado_pago")
    if nuevo_estado and nuevo_estado not in estado_valido:
        return {"message": f"Estado inválido. Valores: {estado_valido}"}, 400

    if nuevo_estado:
        i.estado_pago = nuevo_estado
    if "nota_final" in data:
        nota = float(data["nota_final"])
        if nota < 0 or nota > 100:
            return {"message": "La nota final debe estar entre 0 y 100."}, 400
        i.nota_final = nota

    db.session.commit()
    return {"message": "Inscripción actualizada.", "inscripcion": i.to_dict()}, 200


def inscripciones_por_usuario(id_usuario: int):
    usuario = Usuario.query.get(id_usuario)
    if not usuario:
        return {"message": "Usuario no encontrado."}, 404

    inscripciones = (
        Inscripcion.query
        .filter_by(id_usuario=id_usuario, is_active=True, estado="activa")
        .order_by(Inscripcion.fecha_inscripcion.desc())
        .all()
    )
    resultado = []
    for i in inscripciones:
        d = i.to_dict()
        if i.curso:
            d["nombre_curso"] = i.curso.nombre_curso
            d["imagen"] = i.curso.imagen
            d["fecha_inicio"] = str(i.curso.fecha_inicio)
        resultado.append(d)
    return resultado, 200


def cancelar_inscripcion_usuario(id_inscripcion: int, data: dict):
    id_usuario = data.get("id_usuario")
    if not id_usuario:
        return {"message": "Se requiere id_usuario para cancelar la inscripción."}, 400

    i = Inscripcion.query.get(id_inscripcion)
    if not i:
        return {"message": "Inscripción no encontrada."}, 404
    if i.id_usuario != int(id_usuario):
        return {"message": "No puedes cancelar una inscripción de otro usuario."}, 403
    if not i.is_active or i.estado == "cancelada":
        return {"message": "La inscripción ya estaba cancelada."}, 200

    i.is_active = False
    i.estado = "cancelada"
    i.fecha_cancelacion = datetime.utcnow()
    if i.curso:
        sincronizar_estado_curso(i.curso)

    db.session.commit()
    return {"message": "Te desuscribiste del curso correctamente."}, 200


def cancelar_inscripcion(id_inscripcion: int):
    i = Inscripcion.query.get(id_inscripcion)
    if not i:
        return {"message": "Inscripción no encontrada."}, 404
    if not i.is_active or i.estado == "cancelada":
        return {"message": "La inscripción ya estaba cancelada."}, 200

    i.is_active = False
    i.estado = "cancelada"
    i.fecha_cancelacion = datetime.utcnow()
    if i.curso:
        sincronizar_estado_curso(i.curso)

    db.session.commit()
    return {"message": "Inscripción cancelada."}, 200
