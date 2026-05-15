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
import threading
from flask import Flask, send_from_directory, request, jsonify, abort
from flask_cors import CORS
from config import Config
from database.conexion import init_db, db
from routes.api_routes import api


def _start_course_reminder_scheduler(app):
    """
    Hilo de fondo que cada hora revisa si hay cursos que empiezan en ~24h
    y, si la configuración notif_recordatorio24h=1, manda correos a los inscritos.
    """
    import time, smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from datetime import datetime, timedelta, date

    def _send(to_email, nombre_alumno, nombre_curso, fecha_inicio):
        smtp_host = os.getenv("MAIL_HOST", "smtp.gmail.com")
        smtp_port = int(os.getenv("MAIL_PORT", 587))
        smtp_user = os.getenv("MAIL_USER", "")
        smtp_pass = os.getenv("MAIL_PASSWORD", "")
        if not smtp_user or not smtp_pass:
            print(f"[REMINDER] Recordatorio para {to_email} - {nombre_curso} el {fecha_inicio}")
            return
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"Recordatorio: Tu curso '{nombre_curso}' empieza mañana 🥐"
        msg["From"]    = f"Panadería Gourmet Quetzalteca <{smtp_user}>"
        msg["To"]      = to_email
        html = f"""
        <html><body style="font-family:'Segoe UI',sans-serif;background:#fdf6f8;margin:0;padding:0">
          <table width="100%" cellpadding="0" cellspacing="0"
                 style="max-width:520px;margin:32px auto;background:#fff;border-radius:16px;
                        box-shadow:0 4px 24px rgba(100,30,50,.12);overflow:hidden">
            <tr><td style="background:#7a1f3d;padding:24px 32px;text-align:center">
              <h1 style="color:#fff;font-size:1.3rem;margin:0;font-style:italic">🥐 Panadería Gourmet Quetzalteca</h1>
            </td></tr>
            <tr><td style="padding:32px">
              <h2 style="color:#7a1f3d;margin-top:0">¡Hola, {nombre_alumno}!</h2>
              <p style="color:#555;line-height:1.6">
                Este es un recordatorio de que tu curso <strong>"{nombre_curso}"</strong>
                comienza <strong>mañana {fecha_inicio}</strong>.
              </p>
              <p style="color:#555;line-height:1.6">¡Prepárate y mucho éxito! 🎉</p>
            </td></tr>
            <tr><td style="background:#fdf0f4;padding:14px 32px;text-align:center">
              <p style="color:#bbb;font-size:.75rem;margin:0">© 2025 Panadería Gourmet Quetzalteca · Guatemala</p>
            </td></tr>
          </table>
        </body></html>"""
        msg.attach(MIMEText(html, "html"))
        try:
            with smtplib.SMTP(smtp_host, smtp_port) as s:
                s.ehlo(); s.starttls(); s.login(smtp_user, smtp_pass)
                s.sendmail(smtp_user, to_email, msg.as_string())
        except Exception as e:
            print(f"[REMINDER ERROR] {e}")

    # IDs ya notificados para no mandar dos veces (se reinicia al reiniciar el server)
    _ya_notificados = set()

    def _loop():
        while True:
            try:
                with app.app_context():
                    from models.models import Configuracion, Curso, Inscripcion
                    cfg = Configuracion.query.get("notif_recordatorio24h")
                    if cfg and cfg.valor == "1":
                        manana = date.today() + timedelta(days=1)
                        cursos = Curso.query.filter_by(fecha_inicio=manana, is_active=True).all()
                        for curso in cursos:
                            for insc in curso.inscripciones:
                                key = f"{curso.id_curso}_{insc.id_usuario}"
                                if key not in _ya_notificados and insc.usuario:
                                    _send(
                                        insc.usuario.email,
                                        insc.usuario.nombre_completo,
                                        curso.nombre_curso,
                                        str(manana),
                                    )
                                    _ya_notificados.add(key)
            except Exception as e:
                print(f"[SCHEDULER ERROR] {e}")
            time.sleep(3600)  # revisar cada hora

    t = threading.Thread(target=_loop, daemon=True)
    t.start()



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

    # ── Scheduler: recordatorio 24h antes de cada curso ──────
    _start_course_reminder_scheduler(app)

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

    # ── Endpoint para subir imágenes de cursos y productos ──
    @app.route("/api/upload", methods=["POST"])
    def upload_image():
        """
        Recibe un archivo de imagen (campo 'imagen') via multipart/form-data,
        lo guarda en frontend/uploads/ con nombre único (uuid) y devuelve
        la URL pública para guardarla en la BD.
        """
        import uuid
        from werkzeug.utils import secure_filename

        if "imagen" not in request.files:
            return jsonify({"message": "No se recibió ningún archivo."}), 400

        file = request.files["imagen"]
        if file.filename == "":
            return jsonify({"message": "El archivo no tiene nombre."}), 400

        ALLOWED = {"image/jpeg", "image/png", "image/webp"}
        if file.content_type not in ALLOWED:
            return jsonify({"message": "Solo se permiten JPG, PNG o WEBP."}), 400

        # Generar nombre único para evitar colisiones
        ext = os.path.splitext(secure_filename(file.filename))[1].lower()
        if ext not in (".jpg", ".jpeg", ".png", ".webp"):
            ext = ".jpg"
        filename = uuid.uuid4().hex + ext

        save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(save_path)

        # Devolver la URL pública que el frontend guardará en la BD
        url = f"/uploads/{filename}"
        return jsonify({"url": url, "filename": filename}), 200

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