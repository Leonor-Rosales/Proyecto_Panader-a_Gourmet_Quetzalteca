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
    
    # Notificar al administrador por correo
    _notificar_banquete_admin(nueva)

    return {"message": "Solicitud enviada. Te contactaremos pronto.",
            "solicitud": nueva.to_dict()}, 201


def _notificar_banquete_admin(solicitud):
    try:
        from models.models import Configuracion
        cfg = Configuracion.query.get("notif_banquete")
        if not cfg or cfg.valor != "1":
            return

        from controllers.config_controller import get_smtp_config, get_admin_email
        smtp = get_smtp_config()
        smtp_host = smtp["host"]
        smtp_port = smtp["port"]
        smtp_user = smtp["user"]
        smtp_pass = smtp["password"]
        admin_email = get_admin_email()

        if not smtp_user or not smtp_pass or not admin_email:
            return

        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText

        negocio_nombre_row = Configuracion.query.get("negocio_nombre")
        negocio_nombre = negocio_nombre_row.valor if negocio_nombre_row and negocio_nombre_row.valor else "Panadería Gourmet Quetzalteca"

        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"Nueva Solicitud de Catering: {solicitud.nombre_cliente} - {solicitud.tipo_evento} 🥐"
        msg["From"]    = f"{negocio_nombre} <{smtp_user}>"
        msg["To"]      = admin_email

        html = f"""
        <html><body style="font-family:'Segoe UI',sans-serif;background:#fdf6f8;margin:0;padding:0">
          <table width="100%" cellpadding="0" cellspacing="0"
                 style="max-width:520px;margin:32px auto;background:#fff;border-radius:16px;
                        box-shadow:0 4px 24px rgba(100,30,50,.12);overflow:hidden">
            <tr><td style="background:#7a1f3d;padding:24px 32px;text-align:center">
              <h1 style="color:#fff;font-size:1.3rem;margin:0;font-style:italic">🥐 Panadería Gourmet Quetzalteca</h1>
            </td></tr>
            <tr><td style="padding:32px">
              <h2 style="color:#7a1f3d;margin-top:0">¡Nueva solicitud de catering/banquete!</h2>
              <p style="color:#555;line-height:1.6">
                Se ha recibido una solicitud de banquete de <strong>{solicitud.nombre_cliente}</strong> ({solicitud.email_cliente}).
              </p>
              <p style="color:#555;line-height:1.6">
                <strong>Tipo de evento:</strong> {solicitud.tipo_evento}<br>
                <strong>Fecha del evento:</strong> {str(solicitud.fecha_evento)}<br>
                <strong>Personas:</strong> {solicitud.personas or 'No especificado'}<br>
                <strong>Mensaje/Detalles:</strong> {solicitud.descripcion or 'Ninguno'}
              </p>
              <p style="color:#555;line-height:1.6">Por favor revisa el panel de administración para responder a esta solicitud.</p>
            </td></tr>
            <tr><td style="background:#fdf0f4;padding:14px 32px;text-align:center">
              <p style="color:#bbb;font-size:.75rem;margin:0">© 2025 Panadería Gourmet Quetzalteca · Guatemala</p>
            </td></tr>
          </table>
        </body></html>"""
        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, admin_email, msg.as_string())
    except Exception as e:
        print(f"[MAIL ADMIN BANQUETE ERROR] {e}")


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
