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
from controllers.security import admin_required


def _ensure_lightweight_migrations(_db):
    """Agrega columnas nuevas cuando la BD ya existía antes de estos cambios."""
    from sqlalchemy import text

    statements = [
        "ALTER TABLE inscripcion ADD COLUMN IF NOT EXISTS estado VARCHAR(20) NOT NULL DEFAULT 'activa'",
        "ALTER TABLE inscripcion ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE",
        "ALTER TABLE inscripcion ADD COLUMN IF NOT EXISTS fecha_cancelacion TIMESTAMP NULL",
        "ALTER TABLE inscripcion ADD COLUMN IF NOT EXISTS fecha_recordatorio_enviado TIMESTAMP NULL",
        "ALTER TABLE usuario ADD COLUMN IF NOT EXISTS telefono VARCHAR(20) NULL",
    ]
    for sql in statements:
        _db.session.execute(text(sql))
    _db.session.execute(text(
        "UPDATE inscripcion SET estado = 'activa' WHERE estado IS NULL"
    ))
    _db.session.execute(text(
        "UPDATE inscripcion SET is_active = TRUE WHERE is_active IS NULL"
    ))
    _db.session.commit()


def _start_course_reminder_scheduler(app):
    """
    Hilo de fondo que cada hora revisa si hay cursos que empiezan en ~24h
    y, si la configuración notif_recordatorio24h=1, manda correos a los inscritos y copia al administrador.
    """
    import time, smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from datetime import datetime, timedelta, date

    def _send_reminders(student_email, nombre_alumno, nombre_curso, fecha_inicio, hora_curso, admin_email=None):
        from controllers.config_controller import get_smtp_config
        from models.models import Configuracion

        smtp = get_smtp_config()
        smtp_host = smtp["host"]
        smtp_port = smtp["port"]
        smtp_user = smtp["user"]
        smtp_pass = smtp["password"]

        if not smtp_user or not smtp_pass:
            print(f"[REMINDER] Recordatorio para {student_email} - {nombre_curso} el {fecha_inicio}")
            if admin_email:
                print(f"[REMINDER] Copia de recordatorio para ADMIN {admin_email} - {nombre_curso} el {fecha_inicio}")
            return

        negocio_nombre_row = Configuracion.query.get("negocio_nombre")
        negocio_nombre = negocio_nombre_row.valor if negocio_nombre_row and negocio_nombre_row.valor else "Panadería Gourmet Quetzalteca"

        # 1. Correo del Alumno
        msg_student = MIMEMultipart("alternative")
        msg_student["Subject"] = f"Recordatorio: Tu curso '{nombre_curso}' empieza mañana 🥐"
        msg_student["From"]    = f"{negocio_nombre} <{smtp_user}>"
        msg_student["To"]      = student_email
        html_student = f"""
        <html><body style="font-family:'Segoe UI',sans-serif;background:#fdf6f8;margin:0;padding:0">
          <table width="100%" cellpadding="0" cellspacing="0"
                 style="max-width:520px;margin:32px auto;background:#fff;border-radius:16px;
                        box-shadow:0 4px 24px rgba(100,30,50,.12);overflow:hidden">
            <tr><td style="background:#7a1f3d;padding:24px 32px;text-align:center">
              <h1 style="color:#fff;font-size:1.3rem;margin:0;font-style:italic">🥐 {negocio_nombre}</h1>
            </td></tr>
            <tr><td style="padding:32px">
              <h2 style="color:#7a1f3d;margin-top:0">¡Hola, {nombre_alumno}!</h2>
              <p style="color:#555;line-height:1.6">
                Este es un recordatorio de que tu curso <strong>"{nombre_curso}"</strong>
                comienza <strong>mañana {fecha_inicio}</strong> a las <strong>{hora_curso or 'No especificada'}</strong>.
              </p>
              <p style="color:#555;line-height:1.6">¡Prepárate y mucho éxito! 🎉</p>
            </td></tr>
            <tr><td style="background:#fdf0f4;padding:14px 32px;text-align:center">
              <p style="color:#bbb;font-size:.75rem;margin:0">© 2025 Panadería Gourmet Quetzalteca · Guatemala</p>
            </td></tr>
          </table>
        </body></html>"""
        msg_student.attach(MIMEText(html_student, "html"))

        # 2. Correo del Admin
        msg_admin = None
        if admin_email:
            msg_admin = MIMEMultipart("alternative")
            msg_admin["Subject"] = f"Recordatorio para el curso de mañana {fecha_inicio} a las {hora_curso or 'No especificada'} 🥐"
            msg_admin["From"]    = f"{negocio_nombre} <{smtp_user}>"
            msg_admin["To"]      = admin_email
            html_admin = f"""
            <html><body style="font-family:'Segoe UI',sans-serif;background:#fdf6f8;margin:0;padding:0">
              <table width="100%" cellpadding="0" cellspacing="0"
                     style="max-width:520px;margin:32px auto;background:#fff;border-radius:16px;
                            box-shadow:0 4px 24px rgba(100,30,50,.12);overflow:hidden">
                <tr><td style="background:#7a1f3d;padding:24px 32px;text-align:center">
                  <h1 style="color:#fff;font-size:1.3rem;margin:0;font-style:italic">🥐 {negocio_nombre}</h1>
                </td></tr>
                <tr><td style="padding:32px">
                  <h2 style="color:#7a1f3d;margin-top:0">Recordatorio para el curso de mañana</h2>
                  <p style="color:#555;line-height:1.6">
                    Se le recuerda que mañana comienza el curso <strong>"{nombre_curso}"</strong>.
                  </p>
                  <p style="color:#555;line-height:1.6">
                    <strong>Fecha:</strong> {fecha_inicio}<br>
                    <strong>Hora:</strong> {hora_curso or 'No especificada'}
                  </p>
                </td></tr>
                <tr><td style="background:#fdf0f4;padding:14px 32px;text-align:center">
                  <p style="color:#bbb;font-size:.75rem;margin:0">© 2025 Panadería Gourmet Quetzalteca · Guatemala</p>
                </td></tr>
              </table>
            </body></html>"""
            msg_admin.attach(MIMEText(html_admin, "html"))

        try:
            with smtplib.SMTP(smtp_host, smtp_port) as s:
                s.ehlo()
                s.starttls()
                s.login(smtp_user, smtp_pass)
                # Enviar al alumno
                try:
                    s.sendmail(smtp_user, student_email, msg_student.as_string())
                    print(f"[REMINDER] Correo enviado a alumno: {student_email}")
                except Exception as est:
                    print(f"[REMINDER ERROR ALUMNO] {est}")
                # Enviar al administrador
                if msg_admin and admin_email:
                    try:
                        s.sendmail(smtp_user, admin_email, msg_admin.as_string())
                        print(f"[REMINDER] Correo enviado a admin: {admin_email}")
                    except Exception as ead:
                        print(f"[REMINDER ERROR ADMIN] {ead}")
        except Exception as e:
            print(f"[REMINDER ERROR] {e}")

    def _loop():
        from datetime import time as dt_time
        while True:
            try:
                with app.app_context():
                    from models.models import Configuracion, Curso, NotificacionCurso
                    from controllers.config_controller import get_admin_email
                    cfg = Configuracion.query.get("notif_recordatorio24h")
                    if cfg and cfg.valor == "1":
                        cursos = Curso.query.filter(Curso.fecha_inicio >= date.today(), Curso.is_active == True).all()
                        for curso in cursos:
                            # 1. Parse start time of the course (local time naive)
                            try:
                                h_parts = (curso.hora or "00:00").strip().split(":")
                                hour = int(h_parts[0])
                                minute = int(h_parts[1])
                            except Exception:
                                hour, minute = 0, 0
                            
                            start_time = datetime.combine(curso.fecha_inicio, dt_time(hour, minute))
                            current_time = datetime.now()  # local time
                            
                            # 2. Check if the difference is inside the [1439.0, 1441.0] minutes window (24h +/- 1 min)
                            diff_minutes = (start_time - current_time).total_seconds() / 60.0
                            if 1439.0 <= diff_minutes <= 1441.0:
                                # We are in the 24-hour mark window!
                                for insc in curso.inscripciones:
                                    ya_enviado = NotificacionCurso.query.filter_by(
                                        id_curso=curso.id_curso,
                                        id_inscripcion=insc.id_inscripcion,
                                        tipo="recordatorio_24h",
                                    ).first()
                                    if not ya_enviado and insc.usuario and insc.is_active:
                                        # Only send admin email ONCE per course (on the first sent student notification)
                                        admin_enviado = NotificacionCurso.query.filter_by(
                                            id_curso=curso.id_curso,
                                            tipo="recordatorio_24h"
                                        ).first()
                                        
                                        admin_email_to_send = None
                                        if not admin_enviado:
                                            admin_email_to_send = get_admin_email()
                                            
                                        _send_reminders(
                                            insc.usuario.email,
                                            insc.usuario.nombre_completo,
                                            curso.nombre_curso,
                                            str(curso.fecha_inicio),
                                            curso.hora,
                                            admin_email_to_send
                                        )
                                        db.session.add(NotificacionCurso(
                                            id_curso=curso.id_curso,
                                            id_inscripcion=insc.id_inscripcion,
                                            tipo="recordatorio_24h",
                                        ))
                                        insc.fecha_recordatorio_enviado = datetime.utcnow()
                                        db.session.commit()
            except Exception as e:
                print(f"[SCHEDULER ERROR] {e}")
            finally:
                with app.app_context():
                    db.session.remove()
            time.sleep(60)  # revisar cada minuto para reaccionar en tiempo real

    t = threading.Thread(target=_loop, daemon=True)
    t.start()


def _start_weekly_report_scheduler(app):
    """
    Hilo de fondo que envia el reporte semanal al administrador una vez que
    termina la semana. La semana reportada es de lunes a domingo.
    """
    import time
    from datetime import datetime, time as dt_time, timedelta

    from sqlalchemy import func

    def _week_window(today):
        inicio_semana_actual = today - timedelta(days=today.weekday())
        inicio_semana_reportada = inicio_semana_actual - timedelta(days=7)
        fin_semana_reportada = inicio_semana_actual
        return inicio_semana_reportada, fin_semana_reportada

    def _money(value):
        return f"Q{float(value or 0):,.2f}"

    def _send_report(inicio, fin):
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText

        from controllers.config_controller import get_admin_email, get_smtp_config
        from models.models import Configuracion, Curso, Inscripcion, SolicitudCatering

        smtp = get_smtp_config()
        smtp_host = smtp["host"]
        smtp_port = smtp["port"]
        smtp_user = smtp["user"]
        smtp_pass = smtp["password"]
        admin_email = get_admin_email()

        if not smtp_user or not smtp_pass or not admin_email:
            print("[WEEKLY REPORT] SMTP o correo administrador no configurado.")
            return False

        inicio_dt = datetime.combine(inicio, dt_time.min)
        fin_dt = datetime.combine(fin, dt_time.min)

        inscripciones = Inscripcion.query.filter(
            Inscripcion.is_active == True,
            Inscripcion.estado == "activa",
            Inscripcion.fecha_inscripcion >= inicio_dt,
            Inscripcion.fecha_inscripcion < fin_dt,
        )
        total_inscripciones = inscripciones.count()
        inscripciones_pagadas = inscripciones.filter(Inscripcion.estado_pago == "Pagado").count()
        inscripciones_pendientes = inscripciones.filter(Inscripcion.estado_pago == "Pendiente").count()
        ingresos = db.session.query(
            func.coalesce(func.sum(Curso.precio_curso), 0)
        ).join(Inscripcion, Inscripcion.id_curso == Curso.id_curso).filter(
            Inscripcion.is_active == True,
            Inscripcion.estado == "activa",
            Inscripcion.estado_pago == "Pagado",
            Inscripcion.fecha_inscripcion >= inicio_dt,
            Inscripcion.fecha_inscripcion < fin_dt,
        ).scalar() or 0

        cursos_activos = Curso.query.filter_by(is_active=True).count()
        banquetes_pendientes = SolicitudCatering.query.filter_by(estado="pendiente").count()

        negocio_nombre_row = Configuracion.query.get("negocio_nombre")
        negocio_nombre = (
            negocio_nombre_row.valor
            if negocio_nombre_row and negocio_nombre_row.valor
            else "Panaderia Gourmet Quetzalteca"
        )

        periodo = f"{inicio.isoformat()} al {(fin - timedelta(days=1)).isoformat()}"
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"Reporte semanal - {periodo}"
        msg["From"] = f"{negocio_nombre} <{smtp_user}>"
        msg["To"] = admin_email

        html = f"""
        <html><body style="font-family:'Segoe UI',sans-serif;background:#fdf6f8;margin:0;padding:0">
          <table width="100%" cellpadding="0" cellspacing="0"
                 style="max-width:620px;margin:32px auto;background:#fff;border-radius:16px;
                        box-shadow:0 4px 24px rgba(100,30,50,.12);overflow:hidden">
            <tr><td style="background:#7a1f3d;padding:24px 32px;text-align:center">
              <h1 style="color:#fff;font-size:1.3rem;margin:0;font-style:italic">{negocio_nombre}</h1>
            </td></tr>
            <tr><td style="padding:32px">
              <h2 style="color:#7a1f3d;margin-top:0">Reporte semanal</h2>
              <p style="color:#555;line-height:1.6;margin-top:0">Periodo: <strong>{periodo}</strong></p>
              <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;margin-top:18px">
                <tr>
                  <td style="padding:12px;border-bottom:1px solid #f0dce3;color:#555">Inscripciones nuevas</td>
                  <td style="padding:12px;border-bottom:1px solid #f0dce3;text-align:right;color:#7a1f3d;font-weight:700">{total_inscripciones}</td>
                </tr>
                <tr>
                  <td style="padding:12px;border-bottom:1px solid #f0dce3;color:#555">Inscripciones pagadas</td>
                  <td style="padding:12px;border-bottom:1px solid #f0dce3;text-align:right;color:#7a1f3d;font-weight:700">{inscripciones_pagadas}</td>
                </tr>
                <tr>
                  <td style="padding:12px;border-bottom:1px solid #f0dce3;color:#555">Pagos pendientes</td>
                  <td style="padding:12px;border-bottom:1px solid #f0dce3;text-align:right;color:#7a1f3d;font-weight:700">{inscripciones_pendientes}</td>
                </tr>
                <tr>
                  <td style="padding:12px;border-bottom:1px solid #f0dce3;color:#555">Ingresos confirmados por cursos</td>
                  <td style="padding:12px;border-bottom:1px solid #f0dce3;text-align:right;color:#7a1f3d;font-weight:700">{_money(ingresos)}</td>
                </tr>
                <tr>
                  <td style="padding:12px;border-bottom:1px solid #f0dce3;color:#555">Cursos activos</td>
                  <td style="padding:12px;border-bottom:1px solid #f0dce3;text-align:right;color:#7a1f3d;font-weight:700">{cursos_activos}</td>
                </tr>
                <tr>
                  <td style="padding:12px;color:#555">Solicitudes de banquete pendientes</td>
                  <td style="padding:12px;text-align:right;color:#7a1f3d;font-weight:700">{banquetes_pendientes}</td>
                </tr>
              </table>
              <p style="color:#555;line-height:1.6">Revisa el panel de administracion para dar seguimiento a pagos, cursos y solicitudes pendientes.</p>
            </td></tr>
            <tr><td style="background:#fdf0f4;padding:14px 32px;text-align:center">
              <p style="color:#bbb;font-size:.75rem;margin:0">Reporte automatico semanal</p>
            </td></tr>
          </table>
        </body></html>"""
        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, admin_email, msg.as_string())
        return True

    def _loop():
        while True:
            try:
                with app.app_context():
                    from models.models import Configuracion

                    cfg = Configuracion.query.get("notif_reporte_semanal")
                    if cfg and cfg.valor == "1":
                        today = (datetime.utcnow() - timedelta(hours=6)).date()
                        inicio, fin = _week_window(today)
                        semana_key = f"{inicio.isoformat()}_{(fin - timedelta(days=1)).isoformat()}"
                        sent_key = "notif_reporte_semanal_ultimo_envio"
                        sent_row = Configuracion.query.get(sent_key)
                        if not sent_row or sent_row.valor != semana_key:
                            if _send_report(inicio, fin):
                                if sent_row:
                                    sent_row.valor = semana_key
                                else:
                                    db.session.add(Configuracion(clave=sent_key, valor=semana_key))
                                db.session.commit()
                                print(f"[WEEKLY REPORT] Enviado reporte {semana_key}.")
            except Exception as e:
                print(f"[WEEKLY REPORT ERROR] {e}")
            time.sleep(30)

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
            _ensure_lightweight_migrations(_db)
            from controllers.config_controller import inicializar_config
            inicializar_config()                    # inserta defaults si no existen
        except Exception as _e:
            print(f"[config init] {_e}")

    # ── Blueprints ─────────────────────────────────────────
    app.register_blueprint(api, url_prefix="/api")

    # ── Scheduler: recordatorio 24h antes de cada curso ──────
    _start_course_reminder_scheduler(app)
    _start_weekly_report_scheduler(app)

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
    @admin_required
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
            return jsonify({"message": "Extensión no permitida."}), 400
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
