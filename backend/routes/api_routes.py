"""Rutas REST del sistema."""

from flask import Blueprint, jsonify, redirect, request

from controllers.auth_controller import (
    accept_docente,
    actualizar_usuario,
    confirm_email,
    google_login,
    google_userinfo,
    invitar_docente,
    login_usuario,
    registrar_usuario,
    verificar_correo_usuario,
)
from controllers.banquete_controller import (
    actualizar_estado_banquete,
    crear_banquete,
    eliminar_banquete,
    obtener_banquete,
    obtener_banquetes,
)
from controllers.config_controller import (
    actualizar_valor,
    inicializar_config,
    obtener_config,
    obtener_valor,
)
from controllers.curso_controller import (
    actualizar_curso,
    crear_curso,
    eliminar_curso,
    obtener_curso,
    obtener_cursos,
    obtener_inscritos_curso,
)
from controllers.dashboard_controller import obtener_dashboard_stats
from controllers.inscripcion_controller import (
    actualizar_estado,
    cancelar_inscripcion,
    cancelar_inscripcion_usuario,
    crear_inscripcion,
    inscripciones_por_usuario,
    obtener_inscripcion,
    obtener_inscripciones,
)
from controllers.pedido_controller import (
    actualizar_estado_pedido,
    cancelar_pedido,
    crear_pedido,
    obtener_pedido,
    obtener_pedidos,
    pedidos_por_usuario,
)
from controllers.producto_controller import (
    actualizar_producto,
    crear_producto,
    eliminar_producto,
    obtener_producto,
    obtener_productos,
)
from controllers.security import admin_required

api = Blueprint("api", __name__)


def resp(data, code):
    return jsonify(data), code


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
    result, code = confirm_email(token)
    if code == 201:
        return redirect("/?verified=1", code=302)
    import urllib.parse
    msg = urllib.parse.quote(result.get("message", "Error."))
    return redirect(f"/?verified=0&msg={msg}", code=302)


@api.post("/auth/google")
def google():
    return resp(*google_login(request.get_json(force=True) or {}))


@api.post("/auth/google-userinfo")
def google_userinfo_route():
    return resp(*google_userinfo(request.get_json(force=True) or {}))


@api.post("/auth/check-email")
def check_email():
    return resp(*verificar_correo_usuario(request.get_json(force=True) or {}))


@api.post("/auth/invitar-docente")
@admin_required
def post_invitar_docente():
    return resp(*invitar_docente(request.get_json(force=True) or {}))


@api.get("/auth/accept-docente/<string:token>")
def get_accept_docente(token):
    result, code = accept_docente(token)
    import urllib.parse
    if code == 200:
        return redirect("/?docente=1", code=302)
    if result.get("needs_account"):
        return redirect("/?docente=needs_account", code=302)
    msg = urllib.parse.quote(result.get("message", "Error."))
    return redirect(f"/?docente=error&msg={msg}", code=302)


@api.get("/cursos")
def get_cursos():
    data, code = obtener_cursos(request.args.to_dict())
    if code == 200 and request.args.get("format") != "paginated":
        return resp(data["items"], code)
    return resp(data, code)


@api.get("/cursos/<int:id_curso>")
def get_curso(id_curso):
    return resp(*obtener_curso(id_curso))


@api.get("/cursos/<int:id_curso>/inscritos")
@admin_required
def get_curso_inscritos(id_curso):
    return resp(*obtener_inscritos_curso(id_curso))


@api.post("/cursos")
@admin_required
def post_curso():
    return resp(*crear_curso(request.get_json(force=True) or {}))


@api.put("/cursos/<int:id_curso>")
@admin_required
def put_curso(id_curso):
    return resp(*actualizar_curso(id_curso, request.get_json(force=True) or {}))


@api.delete("/cursos/<int:id_curso>")
@admin_required
def delete_curso(id_curso):
    return resp(*eliminar_curso(id_curso))


@api.get("/productos")
def get_productos():
    return resp(*obtener_productos())


@api.get("/productos/<int:id_producto>")
def get_producto(id_producto):
    return resp(*obtener_producto(id_producto))


@api.post("/productos")
@admin_required
def post_producto():
    return resp(*crear_producto(request.get_json(force=True) or {}))


@api.put("/productos/<int:id_producto>")
@admin_required
def put_producto(id_producto):
    return resp(*actualizar_producto(id_producto, request.get_json(force=True) or {}))


@api.delete("/productos/<int:id_producto>")
@admin_required
def delete_producto(id_producto):
    return resp(*eliminar_producto(id_producto))


@api.get("/inscripciones")
@admin_required
def get_inscripciones():
    return resp(*obtener_inscripciones())


@api.get("/inscripciones/usuario/<int:id_usuario>")
def get_inscripciones_usuario(id_usuario):
    return resp(*inscripciones_por_usuario(id_usuario))


@api.get("/inscripciones/<int:id_inscripcion>")
@admin_required
def get_inscripcion(id_inscripcion):
    return resp(*obtener_inscripcion(id_inscripcion))


@api.post("/inscripciones")
def post_inscripcion():
    return resp(*crear_inscripcion(request.get_json(force=True) or {}))


@api.put("/inscripciones/<int:id_inscripcion>")
@admin_required
def put_inscripcion(id_inscripcion):
    return resp(*actualizar_estado(id_inscripcion, request.get_json(force=True) or {}))


@api.delete("/inscripciones/<int:id_inscripcion>")
@admin_required
def delete_inscripcion(id_inscripcion):
    return resp(*cancelar_inscripcion(id_inscripcion))


@api.post("/inscripciones/<int:id_inscripcion>/desuscribir")
def post_desuscribir_inscripcion(id_inscripcion):
    return resp(*cancelar_inscripcion_usuario(id_inscripcion, request.get_json(force=True) or {}))


@api.get("/banquetes")
@admin_required
def get_banquetes():
    return resp(*obtener_banquetes())


@api.get("/banquetes/<int:id_solicitud>")
@admin_required
def get_banquete(id_solicitud):
    return resp(*obtener_banquete(id_solicitud))


@api.post("/banquetes")
def post_banquete():
    return resp(*crear_banquete(request.get_json(force=True) or {}))


@api.put("/banquetes/<int:id_solicitud>")
@admin_required
def put_banquete(id_solicitud):
    return resp(*actualizar_estado_banquete(id_solicitud, request.get_json(force=True) or {}))


@api.delete("/banquetes/<int:id_solicitud>")
@admin_required
def delete_banquete(id_solicitud):
    return resp(*eliminar_banquete(id_solicitud))


@api.get("/dashboard")
@admin_required
def get_dashboard():
    return resp(*obtener_dashboard_stats())


@api.get("/dashboard/stats")
@admin_required
def get_dashboard_stats():
    return resp(*obtener_dashboard_stats())


@api.post("/pedidos")
def post_pedido():
    return resp(*crear_pedido(request.get_json(force=True) or {}))


@api.get("/pedidos")
@admin_required
def get_pedidos():
    return resp(*obtener_pedidos())


@api.get("/pedidos/usuario/<int:id_usuario>")
def get_pedidos_usuario(id_usuario):
    return resp(*pedidos_por_usuario(id_usuario))


@api.get("/pedidos/<int:no_pedido>")
def get_pedido(no_pedido):
    return resp(*obtener_pedido(no_pedido))


@api.put("/pedidos/<int:no_pedido>/estado")
@admin_required
def put_pedido_estado(no_pedido):
    return resp(*actualizar_estado_pedido(no_pedido, request.get_json(force=True) or {}))


@api.delete("/pedidos/<int:no_pedido>")
def delete_pedido(no_pedido):
    return resp(*cancelar_pedido(no_pedido))


@api.get("/config")
def get_config():
    return resp(*obtener_config())


@api.get("/config/<string:clave>")
def get_config_valor(clave):
    return resp(*obtener_valor(clave))


@api.put("/config/<string:clave>")
@admin_required
def put_config(clave):
    return resp(*actualizar_valor(clave, request.get_json(force=True) or {}))


@api.post("/config/init")
@admin_required
def post_config_init():
    return resp(*inicializar_config())
