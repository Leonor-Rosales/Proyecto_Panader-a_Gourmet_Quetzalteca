"""
controllers/config_controller.py

Ajustes globales del sistema almacenados en la tabla `configuracion`.

Endpoints:
  GET  /api/config              → obtener toda la config (solo admin)
  GET  /api/config/<clave>      → obtener un valor específico (público, usado por el frontend)
  PUT  /api/config/<clave>      → actualizar un valor (solo admin)
  POST /api/config/init         → insertar valores por defecto si no existen
"""

from database.conexion import db
from models.models import Configuracion

# Valores por defecto que se crean en /api/config/init
DEFAULTS = {
    "whatsapp_numero" : "50212345678",
    "negocio_nombre"  : "Panadería Gourmet Quetzalteca",
    "negocio_email"   : "panaderiaGourmetQuetzalteca@gmail.com",
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
