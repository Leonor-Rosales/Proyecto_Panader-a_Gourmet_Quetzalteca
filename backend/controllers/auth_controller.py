"""
controllers/auth_controller.py
Lógica de negocio para registro e inicio de sesión de usuarios.
"""

from werkzeug.security import generate_password_hash, check_password_hash
from database.conexion import db
from models.models import Usuario, Rol
from datetime import date


def registrar_usuario(data: dict):
    """
    Recibe: { name, email, password }
    Devuelve: (dict_respuesta, codigo_http)
    """
    name     = (data.get("name") or "").strip()
    email    = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    # ── Validaciones ──
    if not name or not email or not password:
        return {"message": "Todos los campos son obligatorios."}, 400
    if len(password) < 8:
        return {"message": "La contraseña debe tener al menos 8 caracteres."}, 400
    if Usuario.query.filter_by(email=email).first():
        return {"message": "Este correo ya está registrado."}, 409

    # ── Rol por defecto: Cliente (id_rol=1) ──
    rol_cliente = Rol.query.filter_by(nombre_rol="Cliente").first()
    if not rol_cliente:
        return {"message": "Error de configuración: rol 'Cliente' no existe."}, 500

    nuevo = Usuario(
        nombre_completo = name,
        fecha_nacimiento= date(2000, 1, 1),   # valor por defecto; el perfil lo actualiza
        username        = email.split("@")[0],
        email           = email,
        password_hash   = generate_password_hash(password),
        id_rol          = rol_cliente.id_rol,
    )
    db.session.add(nuevo)
    db.session.commit()
    return {"message": "Cuenta creada correctamente.", "usuario": nuevo.to_dict()}, 201


def actualizar_usuario(id_usuario: int, data: dict):
    """
    Actualiza el perfil de un usuario.
    Recibe: { nombre_completo, telefono, fecha_nacimiento, password (opcional) }
    """
    usuario = Usuario.query.get(id_usuario)
    if not usuario:
        return {"message": "Usuario no encontrado."}, 404

    nombre = (data.get("nombre_completo") or "").strip()
    if not nombre:
        return {"message": "El nombre no puede estar vacío."}, 400

    usuario.nombre_completo = nombre

    fecha = data.get("fecha_nacimiento")
    if fecha:
        try:
            from datetime import date as date_type
            usuario.fecha_nacimiento = date_type.fromisoformat(fecha)
        except ValueError:
            return {"message": "Formato de fecha inválido (YYYY-MM-DD)."}, 400

    password = data.get("password")
    if password:
        if len(password) < 8:
            return {"message": "La contraseña debe tener al menos 8 caracteres."}, 400
        usuario.password_hash = generate_password_hash(password)

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return {"message": f"Error al guardar: {str(e)}"}, 500

    return {"message": "Perfil actualizado correctamente.", "usuario": usuario.to_dict()}, 200


def login_usuario(data: dict):
    """
    Recibe: { email, password }
    Devuelve: (dict_respuesta, codigo_http)
    En producción aquí emitirías un JWT; aquí devolvemos los datos básicos.
    """
    email    = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return {"message": "Correo y contraseña son obligatorios."}, 400

    usuario = Usuario.query.filter_by(email=email).first()
    if not usuario or not check_password_hash(usuario.password_hash, password):
        return {"message": "Correo o contraseña incorrectos."}, 401

    return {
        "message": "Inicio de sesión exitoso.",
        "usuario": usuario.to_dict(),
    }, 200
