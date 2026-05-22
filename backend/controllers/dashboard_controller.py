"""Estadísticas del dashboard calculadas en backend."""

from datetime import date, datetime, time, timedelta

from sqlalchemy import func

from database.conexion import db
from models.models import Curso, Inscripcion, Producto, SolicitudCatering


def obtener_dashboard_stats():
    hoy = date.today()
    inicio_mes = datetime.combine(hoy.replace(day=1), time.min)
    if hoy.month == 12:
        siguiente_mes = date(hoy.year + 1, 1, 1)
    else:
        siguiente_mes = date(hoy.year, hoy.month + 1, 1)
    fin_mes = datetime.combine(siguiente_mes, time.min)
    inicio_semana = datetime.combine(hoy - timedelta(days=hoy.weekday()), time.min)

    inscripciones_mes_query = Inscripcion.query.filter(
        Inscripcion.is_active == True,
        Inscripcion.estado == "activa",
        Inscripcion.fecha_inscripcion >= inicio_mes,
        Inscripcion.fecha_inscripcion < fin_mes,
    )

    ingresos_mes = db.session.query(
        func.coalesce(func.sum(Curso.precio_curso), 0)
    ).join(Inscripcion, Inscripcion.id_curso == Curso.id_curso).filter(
        Inscripcion.is_active == True,
        Inscripcion.estado == "activa",
        Inscripcion.estado_pago == "Pagado",
        Inscripcion.fecha_inscripcion >= inicio_mes,
        Inscripcion.fecha_inscripcion < fin_mes,
    ).scalar() or 0

    inscripciones_semana = Inscripcion.query.filter(
        Inscripcion.is_active == True,
        Inscripcion.estado == "activa",
        Inscripcion.fecha_inscripcion >= inicio_semana,
    ).count()

    return {
        "total_cursos_activos": Curso.query.filter_by(is_active=True).count(),
        "total_cursos": Curso.query.filter_by(is_active=True).count(),
        "total_inscripciones_mes": inscripciones_mes_query.count(),
        "total_inscripciones": inscripciones_mes_query.count(),
        "inscripciones_semana": inscripciones_semana,
        "ingresos_mes_actual": float(ingresos_mes),
        "ingresos_mes": float(ingresos_mes),
        "total_productos": Producto.query.filter_by(is_active=True).count(),
        "total_banquetes": SolicitudCatering.query.count(),
        "banquetes_pendientes": SolicitudCatering.query.filter_by(estado="pendiente").count(),
        "pendientes_pago": Inscripcion.query.filter_by(
            is_active=True,
            estado="activa",
            estado_pago="Pendiente",
        ).count(),
        "mes": hoy.month,
        "anio": hoy.year,
    }, 200
