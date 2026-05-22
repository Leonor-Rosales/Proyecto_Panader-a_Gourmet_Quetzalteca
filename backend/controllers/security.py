"""Autenticación simple con token firmado para endpoints administrativos."""

from functools import wraps

from flask import current_app, jsonify, request
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from models.models import Usuario

ADMIN_ROLES = {2, 3}


def _serializer():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"] or "dev-secret")


def crear_token_usuario(usuario: Usuario) -> str:
    return _serializer().dumps({
        "id_usuario": usuario.id_usuario,
        "id_rol": usuario.id_rol,
    }, salt="admin-auth")


def validar_admin_token(token: str):
    if not token:
        return None
    try:
        data = _serializer().loads(token, salt="admin-auth", max_age=60 * 60 * 12)
    except (BadSignature, SignatureExpired):
        return None
    usuario = Usuario.query.get(data.get("id_usuario"))
    if not usuario or usuario.id_rol not in ADMIN_ROLES:
        return None
    return usuario


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        token = auth.replace("Bearer ", "", 1).strip() if auth.startswith("Bearer ") else ""
        token = token or request.headers.get("X-Admin-Token", "")
        if not validar_admin_token(token):
            return jsonify({"message": "No autorizado."}), 401
        return fn(*args, **kwargs)
    return wrapper
