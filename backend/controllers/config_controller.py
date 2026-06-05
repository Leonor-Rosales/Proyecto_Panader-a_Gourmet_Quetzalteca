"""
controllers/config_controller.py

Ajustes globales del sistema almacenados en la tabla `configuracion`.

Endpoints:
  GET  /api/config              → obtener toda la config (solo admin)
  GET  /api/config/<clave>      → obtener un valor específico (público, usado por el frontend)
  PUT  /api/config/<clave>      → actualizar un valor (solo admin)
  POST /api/config/init         → insertar valores por defecto si no existen
"""

import os
from database.conexion import db
from models.models import Configuracion, Usuario

# Valores por defecto que se crean en /api/config/init
DEFAULTS = {
    "whatsapp_numero"      : "50212345678",
    "negocio_nombre"       : "Panadería Gourmet Quetzalteca",
    "negocio_email"        : "panaderiaGourmetQuetzalteca@gmail.com",
    # Notificaciones (1=activo, 0=inactivo)
    "notif_inscripcion"    : "1",
    "notif_banquete"       : "1",
    "notif_recordatorio24h": "0",
    "notif_reporte_semanal": "1",
    # Credenciales de correo (SMTP)
    "mail_host"            : os.getenv("MAIL_HOST", "smtp.gmail.com"),
    "mail_port"            : os.getenv("MAIL_PORT", "587"),
    "mail_user"            : os.getenv("MAIL_USER", ""),
    "mail_password"        : os.getenv("MAIL_PASSWORD", ""),
}


def obtener_config():
    """Devuelve todas las claves de configuración."""
    rows = Configuracion.query.all()
    return {r.clave: r.valor for r in rows}, 200


def obtener_valor(clave: str):
    """Devuelve el valor de una clave específica."""
    row = Configuracion.query.get(clave)
    if not row:
        return {"message": f"Clave '{clave}' no encontrada."}, 404
    return {"clave": row.clave, "valor": row.valor}, 200


def actualizar_valor(clave: str, data: dict):
    """Crea o actualiza una clave de configuración."""
    valor = (data.get("valor") or "").strip()
    if not valor:
        return {"message": "El campo 'valor' es obligatorio."}, 400

    # Validación especial para el número de WhatsApp
    if clave == "whatsapp_numero":
        limpio = valor.replace("+", "").replace(" ", "").replace("-", "")
        if not limpio.isdigit() or len(limpio) < 8:
            return {"message": "Número de WhatsApp inválido. Usa formato: 50212345678"}, 400
        valor = limpio  # guardar siempre sin +, sin espacios

    row = Configuracion.query.get(clave)
    if row:
        row.valor = valor
    else:
        row = Configuracion(clave=clave, valor=valor)
        db.session.add(row)

    db.session.commit()
    return {"message": "Configuración actualizada.", "clave": clave, "valor": valor}, 200


def inicializar_config():
    """Inserta los valores por defecto solo si no existen aún."""
    creados = []
    for clave, valor in DEFAULTS.items():
        if not Configuracion.query.get(clave):
            db.session.add(Configuracion(clave=clave, valor=valor))
            creados.append(clave)
    db.session.commit()
    return {"message": "Init OK.", "creados": creados}, 200


# ── Helper para leer el número WA desde cualquier controlador ────────────────
def get_wa_number() -> str:
    """
    Lee el número de WhatsApp desde la BD.
    Si no existe aún la tabla o la fila, devuelve el default hardcodeado
    para no romper el sistema en el primer arranque.
    """
    try:
        row = Configuracion.query.get("whatsapp_numero")
        return row.valor if row else DEFAULTS["whatsapp_numero"]
    except Exception:
        return DEFAULTS["whatsapp_numero"]


# ── Helper para obtener credenciales SMTP desde la BD ────────────────────────
def get_smtp_config() -> dict:
    """
    Lee las credenciales SMTP de la base de datos.
    Si no existen, usa variables de entorno como fallback.
    """
    try:
        host_row = Configuracion.query.get("mail_host")
        port_row = Configuracion.query.get("mail_port")
        user_row = Configuracion.query.get("mail_user")
        pass_row = Configuracion.query.get("mail_password")

        host = host_row.valor if host_row and host_row.valor else os.getenv("MAIL_HOST", "smtp.gmail.com")
        port = int(port_row.valor) if port_row and port_row.valor.isdigit() else int(os.getenv("MAIL_PORT", 587))
        user = user_row.valor if user_row and user_row.valor else os.getenv("MAIL_USER", "")
        password = pass_row.valor if pass_row and pass_row.valor else os.getenv("MAIL_PASSWORD", "")

        return {
            "host": host,
            "port": port,
            "user": user,
            "password": password
        }
    except Exception:
        return {
            "host": os.getenv("MAIL_HOST", "smtp.gmail.com"),
            "port": int(os.getenv("MAIL_PORT", 587)),
            "user": os.getenv("MAIL_USER", ""),
            "password": os.getenv("MAIL_PASSWORD", "")
        }


# ── Helper para obtener el correo del administrador ─────────────────────────
def get_admin_email() -> str:
    """
    Retorna el correo de notificaciones (negocio_email) configurado.
    Si no está configurado, busca como fallback el correo del usuario con rol de Administrador (id_rol = 2) en la BD.
    """
    try:
        # 1. Obtener correo de notificaciones configurado en la BD
        email_row = Configuracion.query.get("negocio_email")
        if email_row and email_row.valor:
            return email_row.valor

        # 2. Fallback al correo de la cuenta de administrador principal
        admin = Usuario.query.filter_by(id_rol=2).first()
        if admin and admin.email:
            return admin.email
            
        return DEFAULTS["negocio_email"]
    except Exception:
        return DEFAULTS["negocio_email"]