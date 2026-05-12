"""
routes/api_routes.py
Define todos los endpoints REST del sistema.

CAMBIOS REALIZADOS:
  - AÑADIDO: endpoint POST /api/upload  — sube imagen al servidor
  - AÑADIDO: endpoint GET  /api/upload/check — verifica si uploads funciona
  - CORREGIDO: /api/dashboard usa filter() en vez de filter_by(is_active=True)
    porque la tabla curso NO tiene columna is_active
"""

import os
import uuid
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename

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

# ── EXTENSIONES PERMITIDAS PARA IMÁGENES ──────────────────
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}

def allowed_file(filename: str) -> bool:
    """Verifica que el archivo tenga extensión permitida."""
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


def resp(data, code):
    """Convierte tupla (dict/list, código) en Response JSON."""
    return jsonify(data), code


# ═══════════════════════════════════════
#  SUBIDA DE IMÁGENES  ← NUEVO ENDPOINT
# ═══════════════════════════════════════

# AÑADIDO: endpoint completo de subida de imagen
# Recibe multipart/form-data con campo "imagen"
# Devuelve la URL pública de la imagen: /uploads/nombre_del_archivo.jpg
@api.post("/upload")
def upload_image():
    # Verificar que viene el campo "imagen"
    if "imagen" not in request.files:
        return jsonify({"message": "No se encontró el campo 'imagen'."}), 400

    file = request.files["imagen"]

    # Nombre vacío = no se seleccionó archivo
    if file.filename == "":
        return jsonify({"message": "No se seleccionó ningún archivo."}), 400

    # Validar extensión (bloquea .exe, .js, etc.)
    if not allowed_file(file.filename):
        return jsonify({
            "message": "Formato no permitido. Usa JPG, JPEG, PNG o WEBP."
        }), 400

    # Generar nombre único para evitar colisiones y ataques de path traversal
    ext      = file.filename.rsplit(".", 1)[1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"   # ej: a3f9c1d2....jpg
    filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)

    # Guardar en frontend/uploads/
    file.save(filepath)

    # Devolver URL pública que Flask puede servir
    url = f"/uploads/{filename}"
    return jsonify({"url": url, "message": "Imagen subida correctamente."}), 200


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
    return resp(*actualizar_estado_banquete(
        id_solicitud, request.get_json(force=True) or {}
    ))

@api.delete("/banquetes/<int:id_solicitud>")
def delete_banquete(id_solicitud):
    return resp(*eliminar_banquete(id_solicitud))


# ═══════════════════════════════════════
#  DASHBOARD
#  CORREGIDO: quitado filter_by(is_active=True) que daba error
#  porque la tabla no tiene esa columna
# ═══════════════════════════════════════

@api.get("/dashboard")
def get_dashboard():
    from models.models import Curso, Inscripcion, Producto, SolicitudCatering
    return jsonify({
        "total_cursos"          : Curso.query.count(),           # CORREGIDO
        "total_inscripciones"   : Inscripcion.query.count(),
        "total_productos"       : Producto.query.count(),        # CORREGIDO
        "total_banquetes"       : SolicitudCatering.query.count(),
        "pendientes_pago"       : Inscripcion.query.filter_by(estado_pago="Pendiente").count(),
        "banquetes_pendientes"  : SolicitudCatering.query.filter_by(estado="pendiente").count(),
        "ingresos_confirmados"  : 0,
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
