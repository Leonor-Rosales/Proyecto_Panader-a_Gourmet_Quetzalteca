"""
routes/api_routes.py
Define todos los endpoints REST del sistema.
Se registra como Blueprint en app.py con prefijo /api
"""

from flask import Blueprint, request, jsonify
from controllers.auth_controller       import registrar_usuario, login_usuario
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
                                                cancelar_inscripcion)
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
    return jsonify({
        "total_cursos"        : Curso.query.filter_by(is_active=True).count(),
        "total_inscripciones" : Inscripcion.query.count(),
        "total_productos"     : Producto.query.filter_by(is_active=True).count(),
        "total_banquetes"     : SolicitudCatering.query.count(),
        "pendientes_pago"     : Inscripcion.query.filter_by(estado_pago="Pendiente").count(),
        "banquetes_pendientes": SolicitudCatering.query.filter_by(estado="pendiente").count(),
    }), 200
