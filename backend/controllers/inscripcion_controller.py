"""
controllers/inscripcion_controller.py
CRUD para la tabla 'inscripcion'.
El admin puede confirmar, cancelar y ver inscripciones.
"""

from database.conexion import db
from models.models import Inscripcion, Usuario, Curso


def obtener_inscripciones():
    inscripciones = Inscripcion.query.order_by(
        Inscripcion.fecha_inscripcion.desc()
    ).all()
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

    # Evitar duplicados
    existe = Inscripcion.query.filter_by(
        id_usuario=int(data["id_usuario"]),
        id_curso=int(data["id_curso"])
    ).first()
    if existe:
        return {"message": "El usuario ya está inscrito en este curso."}, 409

    nueva = Inscripcion(
        id_usuario  = int(data["id_usuario"]),
        id_curso    = int(data["id_curso"]),
        estado_pago = data.get("estado_pago", "Pendiente"),
    )
    db.session.add(nueva)
    db.session.commit()
    return {"message": "Inscripción creada.", "inscripcion": nueva.to_dict()}, 201


def actualizar_estado(id_inscripcion: int, data: dict):
    """Confirmar o cancelar una inscripción desde el panel admin."""
    i = Inscripcion.query.get(id_inscripcion)
    if not i:
        return {"message": "Inscripción no encontrada."}, 404

    estado_valido = ["Pendiente", "Anticipo", "Pagado"]
    nuevo_estado  = data.get("estado_pago")
    if nuevo_estado and nuevo_estado not in estado_valido:
        return {"message": f"Estado inválido. Valores: {estado_valido}"}, 400

    if nuevo_estado:
        i.estado_pago = nuevo_estado
    if "nota_final" in data:
        i.nota_final = float(data["nota_final"])

    db.session.commit()
    return {"message": "Inscripción actualizada.", "inscripcion": i.to_dict()}, 200


def cancelar_inscripcion(id_inscripcion: int):
    i = Inscripcion.query.get(id_inscripcion)
    if not i:
        return {"message": "Inscripción no encontrada."}, 404
    db.session.delete(i)
    db.session.commit()
    return {"message": "Inscripción cancelada."}, 200
