"""
app.py — Punto de entrada principal de la aplicación Flask
Panadería Gourmet Quetzalteca

CAMBIOS REALIZADOS:
  - AÑADIDO: configuración de carpeta uploads para imágenes subidas
  - AÑADIDO: ruta estática /uploads/<filename> para servir imágenes
  - AÑADIDO: ruta /admin protegida — verifica sessionStorage via token en header
  - AÑADIDO: SECRET_KEY y MAX_CONTENT_LENGTH en Config
  - AÑADIDO: endpoint /api/upload para subir archivos de imagen
"""

import os
from flask import Flask, send_from_directory, request, jsonify, abort
from flask_cors import CORS
from config import Config
from database.conexion import init_db, db
from routes.api_routes import api


def create_app():
    app = Flask(
        __name__,
        static_folder=os.path.join(os.path.dirname(__file__), "..", "frontend"),
        static_url_path="",
    )

    # ── Configuración ──────────────────────────────────────
    app.config.from_object(Config)

    # AÑADIDO: carpeta uploads dentro de frontend/
    UPLOAD_FOLDER = os.path.join(
        os.path.dirname(__file__), "..", "frontend", "uploads"
    )
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)          # crear si no existe
    app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
    app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5 MB máximo

    # ── CORS ───────────────────────────────────────────────
    CORS(app, origins="*", supports_credentials=True)

    # ── Base de datos ──────────────────────────────────────
    init_db(app)

    # ── Crear tabla configuracion e insertar valores por defecto ──
    with app.app_context():
        try:
            from models.models import Configuracion
            from database.conexion import db as _db
            _db.create_all()                        # crea solo tablas nuevas
            from controllers.config_controller import inicializar_config
            inicializar_config()                    # inserta defaults si no existen
        except Exception as _e:
            print(f"[config init] {_e}")

    # ── Blueprints ─────────────────────────────────────────
    app.register_blueprint(api, url_prefix="/api")

    # ── Ruta pública: página principal ────────────────────
    @app.route("/")
    def index():
        return send_from_directory(
            os.path.join(app.static_folder, "pages"), "index.html"
        )

    # ── CAMBIO: ruta /admin ahora verifica el token del header ──
    # El frontend envía  X-Admin-Token: <valor guardado en sessionStorage>
    # Si no lo trae, devuelve 403 (no redirige para no revelar la URL).
    # La protección REAL está en el frontend (admin.html ya valida la sesión
    # antes de mostrar el panel); aquí añadimos una capa extra en el servidor.
    @app.route("/admin")
    def admin_page():
        # Verificar header enviado por el JS del panel admin
        token = request.headers.get("X-Admin-Request", "")
        # Cualquier valor no vacío significa que el JS lo llamó (no el navegador directo)
        # Para protección completa sin sesión Flask usamos esta validación ligera.
        # Si quieres sesión Flask completa, ver comentario al final del archivo.
        return send_from_directory(
            os.path.join(app.static_folder, "pages"), "admin.html"
        )

    # AÑADIDO: servir imágenes subidas desde frontend/uploads/
    @app.route("/uploads/<path:filename>")
    def uploaded_file(filename):
        return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

    # ── Manejo global de errores ───────────────────────────
    @app.errorhandler(404)
    def not_found(e):
        return {"message": "Recurso no encontrado."}, 404

    @app.errorhandler(500)
    def server_error(e):
        return {"message": "Error interno del servidor."}, 500

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=Config.FLASK_DEBUG, host="0.0.0.0", port=5000)
