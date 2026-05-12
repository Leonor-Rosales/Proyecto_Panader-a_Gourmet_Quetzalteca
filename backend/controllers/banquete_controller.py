"""
controllers/banquete_controller.py
Gestión de solicitudes de catering / banquetes.
El formulario en banquetes (index.html) envía:
  nombre, telefono, email, tipo_evento, personas, fecha_evento, descripcion
El admin confirma o rechaza desde panel-banquetes.
"""

from database.conexion import db
from models.models import SolicitudCatering
from datetime import date as date_type


def obtener_banquetes():
    solicitudes = SolicitudCatering.query.order_by(
        SolicitudCatering.id_solicitud.desc()
    ).all()
    return [s.to_dict() for s in solicitudes], 200


def obtener_banquete(id_solicitud: int):
    s = SolicitudCatering.query.get(id_solicitud)
    if not s:
        return {"message": "Solicitud no encontrada."}, 404
    return s.to_dict(), 200


def crear_banquete(data: dict):
    """Llamado desde el formulario público de banquetes en index.html."""
    requeridos = ["nombre_cliente", "email_cliente", "fecha_evento"]
    for campo in requeridos:
        if not data.get(campo):
            return {"message": f"El campo '{campo}' es obligatorio."}, 400

    try:
        fecha = date_type.fromisoformat(data["fecha_evento"])
    except (ValueError, TypeError):
        return {"message": "Formato de fecha inválido. Use YYYY-MM-DD."}, 400

    nueva = SolicitudCatering(
        id_usuario     = int(data["id_usuario"]) if data.get("id_usuario") else None,
        nombre_cliente = data.get("nombre_cliente"),
        email_cliente  = data.get("email_cliente"),
        telefono       = data.get("telefono"),
        tipo_evento    = data.get("tipo_evento"),
        personas       = int(data["personas"]) if data.get("personas") else None,
        descripcion    = data.get("descripcion"),
        fecha_evento   = fecha,
        estado         = "pendiente",
    )
    db.session.add(nueva)
    db.session.commit()
    return {"message": "Solicitud enviada. Te contactaremos pronto.",
            "solicitud": nueva.to_dict()}, 201


def actualizar_estado_banquete(id_solicitud: int, data: dict):
    """Admin confirma o rechaza."""
    s = SolicitudCatering.query.get(id_solicitud)
    if not s:
        return {"message": "Solicitud no encontrada."}, 404

    estados_validos = ["pendiente", "confirmada", "rechazada"]
    nuevo = data.get("estado")
    if nuevo and nuevo not in estados_validos:
        return {"message": f"Estado inválido. Valores: {estados_validos}"}, 400
    if nuevo:
        s.estado = nuevo

    db.session.commit()
    return {"message": "Solicitud actualizada.", "solicitud": s.to_dict()}, 200


def eliminar_banquete(id_solicitud: int):
    s = SolicitudCatering.query.get(id_solicitud)
    if not s:
        return {"message": "Solicitud no encontrada."}, 404
    db.session.delete(s)
    db.session.commit()
    return {"message": "Solicitud eliminada."}, 200
