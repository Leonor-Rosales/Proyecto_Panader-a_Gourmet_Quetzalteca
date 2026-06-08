"""
controllers/auth_controller.py
Lógica de negocio para registro, verificación de correo e inicio de sesión.

CAMBIOS:
  - AÑADIDO: verificación de correo al registrar (token temporal, cuenta se crea al confirmar)
  - AÑADIDO: confirm_email para confirmar el token
  - AÑADIDO: google_login para autenticación con Google OAuth
"""

from werkzeug.security import generate_password_hash, check_password_hash
from database.conexion import db
from models.models import Usuario, Rol, Configuracion
from datetime import date, datetime, timedelta
import secrets
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
from controllers.security import crear_token_usuario

# Almacén temporal de registros pendientes (en memoria)
# Estructura: { token: { name, email, password_hash, telefono, expires_at } }
_pending_registrations: dict = {}


def _send_verification_email(to_email: str, name: str, token: str) -> bool:
    """Envía el correo de verificación. Retorna True si fue exitoso."""
    from controllers.config_controller import get_smtp_config
    smtp = get_smtp_config()
    smtp_host = smtp["host"]
    smtp_port = smtp["port"]
    smtp_user = smtp["user"]
    smtp_pass = smtp["password"]
    base_url  = os.getenv("BASE_URL", "http://localhost:5000")

    if not smtp_user or not smtp_pass:
        # Sin credenciales → imprime en consola (modo desarrollo)
        print(f"[DEV] Token de verificación para {to_email}: {token}")
        print(f"[DEV] URL: {base_url}/api/auth/confirm/{token}")
        return True

    verify_url = f"{base_url}/api/auth/confirm/{token}"

    negocio_nombre_row = Configuracion.query.get("negocio_nombre")
    negocio_nombre = negocio_nombre_row.valor if negocio_nombre_row and negocio_nombre_row.valor else "Panadería Gourmet Quetzalteca"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Confirma tu cuenta — Panadería Gourmet Quetzalteca"
    msg["From"]    = f"{negocio_nombre} <{smtp_user}>"
    msg["To"]      = to_email

    html = f"""
    <html><body style="font-family:'Segoe UI',sans-serif;background:#fdf6f8;margin:0;padding:0">
      <table width="100%" cellpadding="0" cellspacing="0"
             style="max-width:520px;margin:32px auto;background:#fff;border-radius:16px;
                    box-shadow:0 4px 24px rgba(100,30,50,.12);overflow:hidden">
        <tr><td style="background:#7a1f3d;padding:28px 32px;text-align:center">
          <h1 style="color:#fff;font-size:1.4rem;margin:0;font-style:italic">
            🥐 Panadería Gourmet Quetzalteca
          </h1>
        </td></tr>
        <tr><td style="padding:36px 32px">
          <h2 style="color:#7a1f3d;margin-top:0">¡Hola, {name}!</h2>
          <p style="color:#555;line-height:1.6">
            Gracias por registrarte. Solo falta un paso: confirma que este correo es tuyo.
          </p>
          <div style="text-align:center;margin:32px 0">
            <a href="{verify_url}"
               style="background:#7a1f3d;color:#fff;padding:14px 36px;border-radius:8px;
                      text-decoration:none;font-weight:600;font-size:1rem;display:inline-block">
              ✅ Confirmar mi cuenta
            </a>
          </div>
          <p style="color:#999;font-size:.82rem">
            Este enlace expira en <strong>24 horas</strong>.
            Si no te registraste tú, ignora este correo.
          </p>
        </td></tr>
        <tr><td style="background:#fdf0f4;padding:16px 32px;text-align:center">
          <p style="color:#bbb;font-size:.75rem;margin:0">
            © 2025 Panadería Gourmet Quetzalteca · Guatemala
          </p>
        </td></tr>
      </table>
    </body></html>
    """

    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, to_email, msg.as_string())
        return True
    except Exception as e:
        print(f"[EMAIL ERROR] {e}")
        return False


def registrar_usuario(data: dict):
    """
    Recibe: { name, email, password, telefono? }
    NO crea la cuenta de inmediato.
    Guarda registro temporal y envía correo de verificación.
    """
    name     = (data.get("name") or "").strip()
    email    = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    telefono = (data.get("telefono") or "").strip()

    if not name or not email or not password:
        return {"message": "Todos los campos son obligatorios."}, 400
    if len(password) < 8:
        return {"message": "La contraseña debe tener al menos 8 caracteres."}, 400

    # Correo ya registrado en la BD
    if Usuario.query.filter_by(email=email).first():
        return {"message": "Este correo ya está registrado."}, 409

    # Correo con verificación pendiente
    for tok, info in list(_pending_registrations.items()):
        if info["email"] == email:
            if datetime.utcnow() < info["expires_at"]:
                return {
                    "message": "Ya enviamos un correo de verificación a esa dirección. "
                               "Revisa tu bandeja (o spam). Expira en 24 h."
                }, 409
            else:
                del _pending_registrations[tok]

    token = secrets.token_urlsafe(32)
    _pending_registrations[token] = {
        "name"         : name,
        "email"        : email,
        "password_hash": generate_password_hash(password),
        "telefono"     : telefono,
        "expires_at"   : datetime.utcnow() + timedelta(hours=24),
    }

    sent = _send_verification_email(email, name, token)
    if not sent:
        del _pending_registrations[token]
        return {"message": "No se pudo enviar el correo de verificación. Intenta más tarde."}, 500

    return {
        "message": f"Te enviamos un correo a {email}. "
                   "Haz clic en el enlace para activar tu cuenta. Revisa también el spam."
    }, 200


def confirm_email(token: str):
    """
    Confirma el token y crea la cuenta en la BD.
    """
    info = _pending_registrations.get(token)
    if not info:
        return {"message": "Enlace inválido o ya utilizado."}, 400

    if datetime.utcnow() > info["expires_at"]:
        del _pending_registrations[token]
        return {"message": "El enlace expiró. Regístrate de nuevo."}, 400

    if Usuario.query.filter_by(email=info["email"]).first():
        del _pending_registrations[token]
        return {"message": "Este correo ya fue registrado."}, 409

    rol_cliente = Rol.query.filter_by(nombre_rol="Cliente").first()
    if not rol_cliente:
        return {"message": "Error de configuración: rol 'Cliente' no existe."}, 500

    nuevo = Usuario(
        nombre_completo  = info["name"],
        fecha_nacimiento = date(2000, 1, 1),
        username         = info["email"].split("@")[0],
        email            = info["email"],
        password_hash    = info["password_hash"],
        id_rol           = rol_cliente.id_rol,
        telefono         = info.get("telefono"),
    )
    db.session.add(nuevo)
    db.session.commit()
    del _pending_registrations[token]

    return {
        "message" : "¡Cuenta verificada y activada! Ya puedes iniciar sesión.",
        "verified": True,
    }, 201


def google_login(data: dict):
    """
    Recibe: { credential } — el id_token JWT de Google Sign-In.
    Verifica con Google, busca/crea el usuario y devuelve la sesión.
    """
    try:
        from google.oauth2 import id_token
        from google.auth.transport import requests as google_requests
    except ImportError:
        return {"message": "Librería google-auth no instalada. Ejecuta: pip install google-auth"}, 500

    credential = data.get("credential") or ""
    if not credential:
        return {"message": "Token de Google no recibido."}, 400

    client_id = os.getenv("GOOGLE_CLIENT_ID", "")
    if not client_id:
        return {"message": "GOOGLE_CLIENT_ID no configurado en el servidor."}, 500

    try:
        id_info = id_token.verify_oauth2_token(
            credential,
            google_requests.Request(),
            client_id,
        )
    except ValueError as e:
        return {"message": f"Token de Google inválido: {str(e)}"}, 401

    email = id_info.get("email", "").lower()
    name  = id_info.get("name", email.split("@")[0])

    if not email:
        return {"message": "No se pudo obtener el correo de Google."}, 400

    usuario = Usuario.query.filter_by(email=email).first()
    if usuario: # Refresh the user object to get the latest role from DB
        db.session.refresh(usuario)
    if not usuario:
        rol_cliente = Rol.query.filter_by(nombre_rol="Cliente").first()
        if not rol_cliente:
            return {"message": "Error de configuración: rol 'Cliente' no existe."}, 500

        usuario = Usuario(
            nombre_completo  = name,
            fecha_nacimiento = date(2000, 1, 1),
            username         = email.split("@")[0],
            email            = email,
            password_hash    = generate_password_hash(secrets.token_hex(24)),
            id_rol           = rol_cliente.id_rol,
        )
        db.session.add(usuario)
        db.session.commit()

    usuario_dict = usuario.to_dict()
    usuario_dict["auth_token"] = crear_token_usuario(usuario)
    return {
        "message": "Inicio de sesión con Google exitoso.",
        "usuario": usuario_dict,
        "token": usuario_dict["auth_token"],
    }, 200


def actualizar_usuario(id_usuario: int, data: dict):
    usuario = Usuario.query.get(id_usuario)
    if not usuario:
        return {"message": "Usuario no encontrado."}, 404

    nombre = (data.get("nombre_completo") or "").strip()
    if not nombre:
        return {"message": "El nombre no puede estar vacío."}, 400

    usuario.nombre_completo = nombre

    telefono = data.get("telefono")
    if telefono is not None:
        usuario.telefono = telefono.strip()

    email = (data.get("email") or "").strip().lower()
    if email and email != usuario.email:
        existente = Usuario.query.filter_by(email=email).first()
        if existente:
            return {"message": "Este correo ya está registrado por otro usuario."}, 409
        usuario.email = email
        
        # Actualizar username para evitar colisiones
        new_username = email.split("@")[0]
        count = 1
        temp_username = new_username
        while Usuario.query.filter(Usuario.username == temp_username, Usuario.id_usuario != id_usuario).first():
            temp_username = f"{new_username}{count}"
            count += 1
        usuario.username = temp_username

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
    email    = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return {"message": "Correo y contraseña son obligatorios."}, 400

    usuario = Usuario.query.filter_by(email=email).first()
    if not usuario or not check_password_hash(usuario.password_hash, password):
        return {"message": "Correo o contraseña incorrectos."}, 401

    usuario_dict = usuario.to_dict()
    usuario_dict["auth_token"] = crear_token_usuario(usuario)
    return {
        "message": "Inicio de sesión exitoso.",
        "usuario": usuario_dict,
        "token": usuario_dict["auth_token"],
    }, 200


def google_userinfo(data: dict):
    """
    Recibe: { email, name, sub } — datos del usuario de Google userinfo.
    No necesita verificar token, ya viene del endpoint seguro de Google.
    Busca/crea el usuario y devuelve la sesión.
    """
    email = (data.get("email") or "").strip().lower()
    name  = (data.get("name") or email.split("@")[0]).strip()

    if not email:
        return {"message": "No se recibió el correo de Google."}, 400

    usuario = Usuario.query.filter_by(email=email).first()
    if usuario: # Refresh the user object to get the latest role from DB
        db.session.refresh(usuario)
    if not usuario:
        rol_cliente = Rol.query.filter_by(nombre_rol="Cliente").first()
        if not rol_cliente:
            return {"message": "Error de configuración: rol 'Cliente' no existe."}, 500

        usuario = Usuario(
            nombre_completo  = name,
            fecha_nacimiento = date(2000, 1, 1),
            username         = email.split("@")[0],
            email            = email,
            password_hash    = generate_password_hash(secrets.token_hex(24)),
            id_rol           = rol_cliente.id_rol,
        )
        db.session.add(usuario)
        db.session.commit()

    usuario_dict = usuario.to_dict()
    usuario_dict["auth_token"] = crear_token_usuario(usuario)
    return {
        "message": "Inicio de sesión con Google exitoso.",
        "usuario": usuario_dict,
        "token": usuario_dict["auth_token"],
    }, 200


# ── Almacén temporal de invitaciones de docente (en memoria) ─────────────────
# Estructura: { token: { email, invitado_por, expires_at } }
_pending_invitations: dict = {}


def _send_invitation_email(to_email: str, nombre_usuario: str, token: str) -> bool:
    """Envía el correo de invitación para ser docente."""
    from controllers.config_controller import get_smtp_config
    smtp = get_smtp_config()
    smtp_host = smtp["host"]
    smtp_port = smtp["port"]
    smtp_user = smtp["user"]
    smtp_pass = smtp["password"]
    base_url  = os.getenv("BASE_URL", "http://localhost:5000")

    accept_url = f"{base_url}/api/auth/accept-docente/{token}"

    if not smtp_user or not smtp_pass:
        print(f"[DEV] Invitación docente para {to_email}")
        print(f"[DEV] URL aceptar: {accept_url}")
        return True

    negocio_nombre_row = Configuracion.query.get("negocio_nombre")
    negocio_nombre = negocio_nombre_row.valor if negocio_nombre_row and negocio_nombre_row.valor else "Panadería Gourmet Quetzalteca"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Invitación para ser Docente — Panadería Gourmet Quetzalteca"
    msg["From"]    = f"{negocio_nombre} <{smtp_user}>"
    msg["To"]      = to_email

    html = f"""
    <html><body style="font-family:'Segoe UI',sans-serif;background:#fdf6f8;margin:0;padding:0">
      <table width="100%" cellpadding="0" cellspacing="0"
             style="max-width:540px;margin:32px auto;background:#fff;border-radius:16px;
                    box-shadow:0 4px 24px rgba(100,30,50,.12);overflow:hidden">
        <tr><td style="background:#7a1f3d;padding:28px 32px;text-align:center">
          <h1 style="color:#fff;font-size:1.4rem;margin:0;font-style:italic">
            🥐 Panadería Gourmet Quetzalteca
          </h1>
        </td></tr>
        <tr><td style="padding:36px 32px">
          <h2 style="color:#7a1f3d;margin-top:0">¡Hola, {nombre_usuario}!</h2>
          <p style="color:#555;line-height:1.6">
            El equipo de la <strong>Panadería Gourmet Quetzalteca</strong> te invita a ser
            <strong>Docente</strong> en nuestra plataforma.
          </p>
          <div style="background:#fff8e1;border:1.5px solid #f9c02a;border-radius:8px;
                      padding:14px 16px;margin:20px 0">
            <p style="margin:0;font-size:.85rem;color:#7a5800;line-height:1.5">
              ⚠️ Para aceptar esta invitación debes tener una cuenta de usuario ya creada
              y confirmada en nuestra plataforma.<br>
              <strong>Si aún no tienes cuenta, créala primero en el sitio web.</strong>
            </p>
          </div>
          <div style="text-align:center;margin:28px 0">
            <a href="{accept_url}"
               style="background:#7a1f3d;color:#fff;padding:14px 36px;border-radius:8px;
                      text-decoration:none;font-weight:600;font-size:1rem;display:inline-block">
              ✅ Aceptar rol de Docente
            </a>
          </div>
          <p style="color:#999;font-size:.82rem">
            Este enlace expira en <strong>48 horas</strong>.
            Si no esperabas esta invitación, ignora este correo.
          </p>
        </td></tr>
        <tr><td style="background:#fdf0f4;padding:16px 32px;text-align:center">
          <p style="color:#bbb;font-size:.75rem;margin:0">
            © 2025 Panadería Gourmet Quetzalteca · Guatemala
          </p>
        </td></tr>
      </table>
    </body></html>
    """
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, to_email, msg.as_string())
        return True
    except Exception as e:
        print(f"[EMAIL ERROR invitación] {e}")
        return False


def invitar_docente(data: dict):
    """
    Verifica que el correo exista como usuario registrado,
    luego manda una invitación para ser docente.
    Recibe: { email }
    """
    email = (data.get("email") or "").strip().lower()
    if not email:
        return {"message": "El correo es obligatorio."}, 400

    usuario = Usuario.query.filter_by(email=email).first()
    if not usuario:
        return {"message": "Correo no encontrado. El usuario debe tener cuenta registrada.", "found": False}, 404

    # Verificar si ya es docente
    rol_docente = Rol.query.filter_by(nombre_rol="Docente").first()
    if rol_docente and usuario.id_rol == rol_docente.id_rol:
        return {"message": f"{email} ya tiene rol de Docente.", "found": True}, 409

    # Verificar si ya tiene invitación pendiente
    for tok, info in list(_pending_invitations.items()):
        if info["email"] == email:
            if datetime.utcnow() < info["expires_at"]:
                return {
                    "message": "Ya se envió una invitación a ese correo. Expira en 48 h.",
                    "found": True
                }, 409
            else:
                del _pending_invitations[tok]

    token = secrets.token_urlsafe(32)
    _pending_invitations[token] = {
        "email"    : email,
        "expires_at": datetime.utcnow() + timedelta(hours=48),
    }

    sent = _send_invitation_email(email, usuario.nombre_completo, token)
    if not sent:
        del _pending_invitations[token]
        return {"message": "No se pudo enviar la invitación. Intenta más tarde.", "found": True}, 500

    return {
        "message": f"Invitación enviada a {email} ({usuario.nombre_completo}).",
        "nombre" : usuario.nombre_completo,
        "found"  : True,
    }, 200


def verificar_correo_usuario(data: dict):
    """
    Verifica si un correo existe como usuario registrado.
    Recibe: { email }
    Devuelve found: true/false y el nombre si existe.
    """
    email = (data.get("email") or "").strip().lower()
    if not email:
        return {"found": False, "message": ""}, 200

    usuario = Usuario.query.filter_by(email=email).first()
    if not usuario:
        return {"found": False, "message": "Correo no encontrado."}, 200

    return {"found": True, "nombre": usuario.nombre_completo, "id_usuario": usuario.id_usuario}, 200


def accept_docente(token: str):
    """
    Acepta la invitación de docente y cambia el rol del usuario.
    """
    info = _pending_invitations.get(token)
    if not info:
        return {"message": "Enlace inválido o ya utilizado."}, 400

    if datetime.utcnow() > info["expires_at"]:
        del _pending_invitations[token]
        return {"message": "El enlace expiró. Pide al admin que envíe una nueva invitación."}, 400

    usuario = Usuario.query.filter_by(email=info["email"]).first()
    if not usuario:
        del _pending_invitations[token]
        return {
            "message": "No se encontró una cuenta con ese correo. "
                       "Primero crea tu cuenta en el sitio web y luego usa este enlace.",
            "needs_account": True,
        }, 404

    rol_docente = Rol.query.filter_by(nombre_rol="Docente").first()
    if not rol_docente:
        return {"message": "Error de configuración: rol 'Docente' no existe en la BD."}, 500

    usuario.id_rol = rol_docente.id_rol
    db.session.commit()
    del _pending_invitations[token]

    usuario_dict = usuario.to_dict()
    usuario_dict["auth_token"] = crear_token_usuario(usuario)

    return {
        "message"  : f"¡Listo! {usuario.nombre_completo} ahora tiene rol de Docente.",
        "accepted" : True,
        "id_usuario": usuario.id_usuario,
        "usuario": usuario_dict,
        "token": usuario_dict["auth_token"],
    }, 200


def listar_docentes():
    """
    Retorna todos los usuarios con rol Administrador o Docente.
    Usado por el panel de admin para mostrar la lista de docentes autorizados.
    """
    rol_admin = Rol.query.filter_by(nombre_rol="Administrador").first()
    rol_docente = Rol.query.filter_by(nombre_rol="Docente").first()

    ids_roles = []
    if rol_admin:
        ids_roles.append(rol_admin.id_rol)
    if rol_docente:
        ids_roles.append(rol_docente.id_rol)

    if not ids_roles:
        return [], 200

    usuarios = Usuario.query.filter(Usuario.id_rol.in_(ids_roles)).all()

    result = []
    for u in usuarios:
        result.append({
            "id_usuario"     : u.id_usuario,
            "nombre_completo": u.nombre_completo,
            "email"          : u.email,
            "rol"            : u.rol.nombre_rol if u.rol else "Desconocido",
        })

    return result, 200


def quitar_docente(id_usuario: int):
    """
    Devuelve al usuario con rol Docente al rol Cliente.
    """
    usuario = Usuario.query.get(id_usuario)
    if not usuario:
        return {"message": "Usuario no encontrado."}, 404

    rol_docente = Rol.query.filter_by(nombre_rol="Docente").first()
    if not rol_docente or usuario.id_rol != rol_docente.id_rol:
        return {"message": "Este usuario no tiene rol de Docente."}, 409

    rol_cliente = Rol.query.filter_by(nombre_rol="Cliente").first()
    if not rol_cliente:
        return {"message": "Error de configuración: rol 'Cliente' no existe."}, 500

    usuario.id_rol = rol_cliente.id_rol
    db.session.commit()

    return {
        "message": f"El rol de {usuario.nombre_completo} fue cambiado a Cliente.",
        "id_usuario": usuario.id_usuario,
    }, 200