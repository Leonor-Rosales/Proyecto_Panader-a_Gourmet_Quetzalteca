"""
app.py — Punto de entrada principal de la aplicación Flask
Panadería Gourmet Quetzalteca
"""

import os
from flask import Flask, send_from_directory
from flask_cors import CORS
from config import Config
from database.conexion import init_db, db
from routes.api_routes import api


def create_app():
    app = Flask(
        __name__,
        # Servir el frontend desde ../frontend
        static_folder=os.path.join(os.path.dirname(__file__), "..", "frontend"),
        static_url_path="",
    )

    # ── Configuración ──────────────────────────────────────
    app.config.from_object(Config)

    # ── CORS: permite que el navegador llame a /api ────────
    # En producción reemplaza origins="*" por tu dominio real
    CORS(app, origins="*", supports_credentials=True)

    # ── Base de datos ──────────────────────────────────────
    init_db(app)

    # ── Blueprints (rutas API) ─────────────────────────────
    app.register_blueprint(api, url_prefix="/api")

    # ── Rutas para servir el frontend ─────────────────────
    @app.route("/")
    def index():
        return send_from_directory(
            os.path.join(app.static_folder, "pages"), "index.html"
        )

    @app.route("/admin")
    def admin():
        return send_from_directory(
            os.path.join(app.static_folder, "pages"), "admin.html"
        )

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
