"""
routes/api_routes.py
Define todos los endpoints REST del sistema.
Se registra como Blueprint en app.py con prefijo /api
"""

from flask import Blueprint, request, jsonify, redirect
from controllers.auth_controller import (registrar_usuario, login_usuario,
                                         actualizar_usuario, confirm_email,
                                         google_login, google_userinfo,
                                         invitar_docente, accept_docente,
                                         verificar_correo_usuario)
from controllers.curso_controller      import (obtener_cursos, obtener_curso,
                                               crear_curso, actualizar_curso,
                                               eliminar_curso)
from controllers.producto_controller   import (obtener_productos, obtener_producto,
                                               crear_producto, actualizar_producto,
                                               eliminar_producto)
from controllers.inscripcion_controller import (obtener_inscripciones,
                                                obtener_inscripcion,
                                                crear_inscripcion,
                                                actualizar_estado,
                                                cancelar_inscripcion,
                                                inscripciones_por_usuario)
from controllers.banquete_controller   import (obtener_banquetes, obtener_banquete,
                                               crear_banquete,
                                               actualizar_estado_banquete,
                                               eliminar_banquete)

api = Blueprint("api", __name__)


def resp(data, code):
    """Convierte tupla (dict/list, código) en Response JSON."""
    return jsonify(data), code


# ═══════════════════════════════════════
#  AUTH
# ═══════════════════════════════════════

@api.post("/auth/register")
def register():
    return resp(*registrar_usuario(request.get_json(force=True) or {}))


@api.post("/auth/login")
def login():
    return resp(*login_usuario(request.get_json(force=True) or {}))


@api.put("/auth/usuario/<int:id_usuario>")
def put_usuario(id_usuario):
    return resp(*actualizar_usuario(id_usuario, request.get_json(force=True) or {}))


@api.get("/auth/confirm/<string:token>")
def confirm(token):
    """Confirma el correo y crea la cuenta. Redirige al frontend con resultado."""
    from flask import redirect
    result, code = confirm_email(token)
    if code == 201:
        return redirect("/?verified=1", code=302)
    else:
        import urllib.parse
        msg = urllib.parse.quote(result.get("message", "Error."))
        return redirect(f"/?verified=0&msg={msg}", code=302)


@api.post("/auth/google")
def google():
    """Recibe el id_token de Google Sign-In (One Tap) y devuelve la sesión."""
    return resp(*google_login(request.get_json(force=True) or {}))


@api.post("/auth/google-userinfo")
def google_userinfo_route():
    """Recibe email/name del flujo popup OAuth2 y devuelve la sesión."""
    return resp(*google_userinfo(request.get_json(force=True) or {}))


@api.post("/auth/check-email")
def check_email():
    """Verifica si un correo existe como usuario registrado."""
    return resp(*verificar_correo_usuario(request.get_json(force=True) or {}))


@api.post("/auth/invitar-docente")
def post_invitar_docente():
    """Verifica que exista el correo y envía invitación de rol docente."""
    return resp(*invitar_docente(request.get_json(force=True) or {}))


@api.get("/auth/accept-docente/<string:token>")
def get_accept_docente(token):
    """Acepta la invitación de docente y cambia el rol. Redirige al frontend."""
    result, code = accept_docente(token)
    import urllib.parse
    if code == 200:
        return redirect("/?docente=1", code=302)
    elif result.get("needs_account"):
        return redirect("/?docente=needs_account", code=302)
    else:
        msg = urllib.parse.quote(result.get("message", "Error."))
        return redirect(f"/?docente=error&msg={msg}", code=302)


# ═══════════════════════════════════════
#  CURSOS
# ═══════════════════════════════════════

@api.get("/cursos")
def get_cursos():
    return resp(*obtener_cursos())


@api.get("/cursos/<int:id_curso>")
def get_curso(id_curso):
    return resp(*obtener_curso(id_curso))


@api.post("/cursos")
def post_curso():
    return resp(*crear_curso(request.get_json(force=True) or {}))


@api.put("/cursos/<int:id_curso>")
def put_curso(id_curso):
    return resp(*actualizar_curso(id_curso, request.get_json(force=True) or {}))


@api.delete("/cursos/<int:id_curso>")
def delete_curso(id_curso):
    return resp(*eliminar_curso(id_curso))


# ═══════════════════════════════════════
#  PRODUCTOS  (pastelería)
# ═══════════════════════════════════════

@api.get("/productos")
def get_productos():
    return resp(*obtener_productos())


@api.get("/productos/<int:id_producto>")
def get_producto(id_producto):
    return resp(*obtener_producto(id_producto))


@api.post("/productos")
def post_producto():
    return resp(*crear_producto(request.get_json(force=True) or {}))


@api.put("/productos/<int:id_producto>")
def put_producto(id_producto):
    return resp(*actualizar_producto(id_producto, request.get_json(force=True) or {}))


@api.delete("/productos/<int:id_producto>")
def delete_producto(id_producto):
    return resp(*eliminar_producto(id_producto))


# ═══════════════════════════════════════
#  INSCRIPCIONES
# ═══════════════════════════════════════

@api.get("/inscripciones")
def get_inscripciones():
    return resp(*obtener_inscripciones())


@api.get("/inscripciones/usuario/<int:id_usuario>")
def get_inscripciones_usuario(id_usuario):
    return resp(*inscripciones_por_usuario(id_usuario))


@api.get("/inscripciones/<int:id_inscripcion>")
def get_inscripcion(id_inscripcion):
    return resp(*obtener_inscripcion(id_inscripcion))


@api.post("/inscripciones")
def post_inscripcion():
    return resp(*crear_inscripcion(request.get_json(force=True) or {}))


@api.put("/inscripciones/<int:id_inscripcion>")
def put_inscripcion(id_inscripcion):
    return resp(*actualizar_estado(id_inscripcion, request.get_json(force=True) or {}))


@api.delete("/inscripciones/<int:id_inscripcion>")
def delete_inscripcion(id_inscripcion):
    return resp(*cancelar_inscripcion(id_inscripcion))


# ═══════════════════════════════════════
#  BANQUETES / CATERING
# ═══════════════════════════════════════

@api.get("/banquetes")
def get_banquetes():
    return resp(*obtener_banquetes())


@api.get("/banquetes/<int:id_solicitud>")
def get_banquete(id_solicitud):
    return resp(*obtener_banquete(id_solicitud))


@api.post("/banquetes")
def post_banquete():
    return resp(*crear_banquete(request.get_json(force=True) or {}))


@api.put("/banquetes/<int:id_solicitud>")
def put_banquete(id_solicitud):
    return resp(*actualizar_estado_banquete(id_solicitud,
                request.get_json(force=True) or {}))


@api.delete("/banquetes/<int:id_solicitud>")
def delete_banquete(id_solicitud):
    return resp(*eliminar_banquete(id_solicitud))


# ═══════════════════════════════════════
#  DASHBOARD  (estadísticas rápidas)
# ═══════════════════════════════════════

@api.get("/dashboard")
def get_dashboard():
    from models.models import (Curso, Inscripcion, Producto, SolicitudCatering)
    from sqlalchemy import func
    from datetime import date, timedelta

    hoy = date.today()
    inicio_mes    = hoy.replace(day=1)
    inicio_semana = hoy - timedelta(days=hoy.weekday())

    # Ingresos del mes: solo inscripciones pagadas (precio del curso)
    ingresos_mes = db.session.query(
        func.coalesce(func.sum(Curso.precio_curso), 0)
    ).join(Inscripcion, Inscripcion.id_curso == Curso.id_curso).filter(
        Inscripcion.estado_pago == "Pagado",
        func.date(Inscripcion.fecha_inscripcion) >= inicio_mes,
    ).scalar() or 0

    # ── Inscripciones esta semana ─────────────────────────────────────
    inscripciones_semana = Inscripcion.query.filter(
        func.date(Inscripcion.fecha_inscripcion) >= inicio_semana
    ).count()

    return jsonify({
        "total_cursos"         : Curso.query.filter_by(is_active=True).count(),
        "total_inscripciones"  : Inscripcion.query.count(),
        "inscripciones_semana" : inscripciones_semana,
        "total_productos"      : Producto.query.filter_by(is_active=True).count(),
        "total_banquetes"      : SolicitudCatering.query.count(),
        "pendientes_pago"      : Inscripcion.query.filter_by(estado_pago="Pendiente").count(),
        "banquetes_pendientes" : SolicitudCatering.query.filter_by(estado="pendiente").count(),
        "ingresos_mes"         : float(ingresos_mes),
    }), 200


# ═══════════════════════════════════════
#  PEDIDOS (carrito)
# ═══════════════════════════════════════
from controllers.pedido_controller import (crear_pedido, obtener_pedidos,
                                           obtener_pedido, pedidos_por_usuario,
                                           actualizar_estado_pedido, cancelar_pedido)

@api.post("/pedidos")
def post_pedido():
    return resp(*crear_pedido(request.get_json(force=True) or {}))

@api.get("/pedidos")
def get_pedidos():
    return resp(*obtener_pedidos())

@api.get("/pedidos/usuario/<int:id_usuario>")
def get_pedidos_usuario(id_usuario):
    return resp(*pedidos_por_usuario(id_usuario))

@api.get("/pedidos/<int:no_pedido>")
def get_pedido(no_pedido):
    return resp(*obtener_pedido(no_pedido))

@api.put("/pedidos/<int:no_pedido>/estado")
def put_pedido_estado(no_pedido):
    return resp(*actualizar_estado_pedido(no_pedido, request.get_json(force=True) or {}))

@api.delete("/pedidos/<int:no_pedido>")
def delete_pedido(no_pedido):
    return resp(*cancelar_pedido(no_pedido))


# ═══════════════════════════════════════
#  CONFIGURACIÓN DEL SISTEMA
# ═══════════════════════════════════════
from controllers.config_controller import (obtener_config, obtener_valor,
                                            actualizar_valor, inicializar_config)

@api.get("/config")
def get_config():
    return resp(*obtener_config())

@api.get("/config/<string:clave>")
def get_config_valor(clave):
    return resp(*obtener_valor(clave))

@api.put("/config/<string:clave>")
def put_config(clave):
    return resp(*actualizar_valor(clave, request.get_json(force=True) or {}))

@api.post("/config/init")
def post_config_init():
    return resp(*inicializar_config())