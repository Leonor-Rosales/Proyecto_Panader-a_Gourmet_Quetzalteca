"""
models.py — Modelos SQLAlchemy basados en script.sql del proyecto.

Tablas reales encontradas en script.sql:
  rol, categoria, usuario, estudiante, docente,
  curso, horario_curso, inscripcion, asistencia,
  calificacion, diploma, producto, pedido,
  detalle_pedido, solicitudcatering, solicitudcurso
"""

from database.conexion import db
from datetime import datetime, date


# ─────────────────────────────────────────
# ROL
# ─────────────────────────────────────────
class Rol(db.Model):
    __tablename__ = "rol"

    id_rol     = db.Column(db.Integer, primary_key=True)
    nombre_rol = db.Column(db.String(50), nullable=False, unique=True)

    usuarios = db.relationship("Usuario", back_populates="rol")

    def to_dict(self):
        return {"id_rol": self.id_rol, "nombre_rol": self.nombre_rol}


# ─────────────────────────────────────────
# CATEGORÍA (de productos)
# ─────────────────────────────────────────
class Categoria(db.Model):
    __tablename__ = "categoria"

    id_categoria     = db.Column(db.Integer, primary_key=True)
    nombre_categoria = db.Column(db.String(50), nullable=False, unique=True)

    productos = db.relationship("Producto", back_populates="categoria")

    def to_dict(self):
        return {"id_categoria": self.id_categoria,
                "nombre_categoria": self.nombre_categoria}


# ─────────────────────────────────────────
# USUARIO
# ─────────────────────────────────────────
class Usuario(db.Model):
    __tablename__ = "usuario"

    id_usuario      = db.Column(db.Integer, primary_key=True)
    nombre_completo = db.Column(db.String(150), nullable=False)
    fecha_nacimiento= db.Column(db.Date, nullable=False)
    username        = db.Column(db.String(50), nullable=False, unique=True)
    email           = db.Column(db.String(100), nullable=False, unique=True)
    password_hash   = db.Column(db.Text, nullable=False)
    id_rol          = db.Column(db.Integer, db.ForeignKey("rol.id_rol"), nullable=False)

    rol          = db.relationship("Rol", back_populates="usuarios")
    estudiante   = db.relationship("Estudiante", back_populates="usuario", uselist=False)
    docente      = db.relationship("Docente", back_populates="usuario", uselist=False)
    inscripciones= db.relationship("Inscripcion", back_populates="usuario")
    pedidos      = db.relationship("Pedido", back_populates="usuario")

    def to_dict(self):
        return {
            "id_usuario"      : self.id_usuario,
            "nombre_completo" : self.nombre_completo,
            "username"        : self.username,
            "email"           : self.email,
            "id_rol"          : self.id_rol,
            "rol"             : self.rol.nombre_rol if self.rol else None,
        }


# ─────────────────────────────────────────
# ESTUDIANTE
# ─────────────────────────────────────────
class Estudiante(db.Model):
    __tablename__ = "estudiante"

    carnet     = db.Column(db.String(20), primary_key=True)
    id_usuario = db.Column(db.Integer,
                           db.ForeignKey("usuario.id_usuario", ondelete="CASCADE"),
                           nullable=False, unique=True)

    usuario = db.relationship("Usuario", back_populates="estudiante")

    def to_dict(self):
        return {"carnet": self.carnet, "id_usuario": self.id_usuario}


# ─────────────────────────────────────────
# DOCENTE
# ─────────────────────────────────────────
class Docente(db.Model):
    __tablename__ = "docente"

    id_docente = db.Column(db.Integer, primary_key=True)
    telefono   = db.Column(db.String(20), nullable=False)
    id_usuario = db.Column(db.Integer,
                           db.ForeignKey("usuario.id_usuario", ondelete="CASCADE"),
                           nullable=False, unique=True)

    usuario = db.relationship("Usuario", back_populates="docente")
    cursos  = db.relationship("Curso", back_populates="docente")

    def to_dict(self):
        return {
            "id_docente": self.id_docente,
            "telefono"  : self.telefono,
            "id_usuario": self.id_usuario,
        }


# ─────────────────────────────────────────
# CURSO
# ─────────────────────────────────────────
class Curso(db.Model):
    __tablename__ = "curso"

    id_curso       = db.Column(db.Integer, primary_key=True)
    nombre_curso   = db.Column(db.String(100), nullable=False)
    descripcion    = db.Column(db.Text, nullable=False)
    duracion_horas = db.Column(db.Integer, nullable=False)
    modalidad      = db.Column(db.String(50), nullable=False)   # 'Presencial' | 'Virtual'
    cupo_maximo    = db.Column(db.Integer, nullable=False)
    id_docente     = db.Column(db.Integer, db.ForeignKey("docente.id_docente"), nullable=False)
    fecha_inicio   = db.Column(db.Date, nullable=False)
    precio_curso   = db.Column(db.Numeric(10, 2), nullable=False)

    # Campos extra usados en el frontend (imagen, nivel, hora, extras)
    imagen = db.Column(db.Text)
    hora   = db.Column(db.String(50))
    nivel  = db.Column(db.String(50))
    extras = db.Column(db.String(100))
    estado    = db.Column(db.String(20), default="disponible")   # disponible | lleno
    is_active = db.Column(db.Boolean, default=True, nullable=False)  # False = borrado lógico

    docente      = db.relationship("Docente", back_populates="cursos")
    horarios     = db.relationship("HorarioCurso", back_populates="curso",
                                   cascade="all, delete-orphan")
    inscripciones= db.relationship("Inscripcion", back_populates="curso")

    def to_dict(self):
        return {
            "id_curso"      : self.id_curso,
            "nombre_curso"  : self.nombre_curso,
            "descripcion"   : self.descripcion,
            "duracion_horas": self.duracion_horas,
            "modalidad"     : self.modalidad,
            "cupo_maximo"   : self.cupo_maximo,
            "fecha_inicio"  : str(self.fecha_inicio),
            "precio_curso"  : float(self.precio_curso),
            "imagen"        : self.imagen,
            "hora"          : self.hora,
            "nivel"         : self.nivel,
            "extras"        : self.extras,
            "estado"        : self.estado,
            "id_docente"    : self.id_docente,
            "is_active"     : self.is_active,
        }


# ─────────────────────────────────────────
# HORARIO CURSO
# ─────────────────────────────────────────
class HorarioCurso(db.Model):
    __tablename__ = "horario_curso"

    id_horario  = db.Column(db.Integer, primary_key=True)
    id_curso    = db.Column(db.Integer,
                            db.ForeignKey("curso.id_curso", ondelete="CASCADE"),
                            nullable=False)
    dia_semana  = db.Column(db.String(20), nullable=False)
    hora_inicio = db.Column(db.Time, nullable=False)
    hora_fin    = db.Column(db.Time, nullable=False)

    curso = db.relationship("Curso", back_populates="horarios")

    def to_dict(self):
        return {
            "id_horario" : self.id_horario,
            "id_curso"   : self.id_curso,
            "dia_semana" : self.dia_semana,
            "hora_inicio": str(self.hora_inicio),
            "hora_fin"   : str(self.hora_fin),
        }


# ─────────────────────────────────────────
# INSCRIPCIÓN
# ─────────────────────────────────────────
class Inscripcion(db.Model):
    __tablename__ = "inscripcion"

    id_inscripcion    = db.Column(db.Integer, primary_key=True)
    id_usuario        = db.Column(db.Integer, db.ForeignKey("usuario.id_usuario"), nullable=False)
    id_curso          = db.Column(db.Integer, db.ForeignKey("curso.id_curso"), nullable=False)
    fecha_inscripcion = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    estado_pago       = db.Column(db.String(20), default="Pendiente", nullable=False)
    nota_final        = db.Column(db.Numeric(5, 2), default=0)

    usuario       = db.relationship("Usuario", back_populates="inscripciones")
    curso         = db.relationship("Curso", back_populates="inscripciones")
    asistencias   = db.relationship("Asistencia", back_populates="inscripcion",
                                    cascade="all, delete-orphan")
    calificaciones= db.relationship("Calificacion", back_populates="inscripcion",
                                    cascade="all, delete-orphan")
    diploma       = db.relationship("Diploma", back_populates="inscripcion", uselist=False)

    def to_dict(self):
        return {
            "id_inscripcion"   : self.id_inscripcion,
            "id_usuario"       : self.id_usuario,
            "alumno"           : self.usuario.nombre_completo if self.usuario else None,
            "email"            : self.usuario.email if self.usuario else None,
            "id_curso"         : self.id_curso,
            "curso"            : self.curso.nombre_curso if self.curso else None,
            "fecha_inscripcion": str(self.fecha_inscripcion),
            "estado_pago"      : self.estado_pago,
            "nota_final"       : float(self.nota_final) if self.nota_final else 0,
        }


# ─────────────────────────────────────────
# ASISTENCIA
# ─────────────────────────────────────────
class Asistencia(db.Model):
    __tablename__ = "asistencia"

    id_asistencia  = db.Column(db.Integer, primary_key=True)
    id_inscripcion = db.Column(db.Integer,
                               db.ForeignKey("inscripcion.id_inscripcion", ondelete="CASCADE"),
                               nullable=False)
    fecha          = db.Column(db.Date, default=date.today, nullable=False)
    presente       = db.Column(db.Boolean, default=False, nullable=False)

    inscripcion = db.relationship("Inscripcion", back_populates="asistencias")

    def to_dict(self):
        return {
            "id_asistencia" : self.id_asistencia,
            "id_inscripcion": self.id_inscripcion,
            "fecha"         : str(self.fecha),
            "presente"      : self.presente,
        }


# ─────────────────────────────────────────
# CALIFICACIÓN
# ─────────────────────────────────────────
class Calificacion(db.Model):
    __tablename__ = "calificacion"

    id_calificacion= db.Column(db.Integer, primary_key=True)
    id_inscripcion = db.Column(db.Integer,
                               db.ForeignKey("inscripcion.id_inscripcion", ondelete="CASCADE"),
                               nullable=False)
    descripcion    = db.Column(db.String(100), nullable=False)
    nota           = db.Column(db.Numeric(5, 2), nullable=False)

    inscripcion = db.relationship("Inscripcion", back_populates="calificaciones")

    def to_dict(self):
        return {
            "id_calificacion": self.id_calificacion,
            "id_inscripcion" : self.id_inscripcion,
            "descripcion"    : self.descripcion,
            "nota"           : float(self.nota),
        }


# ─────────────────────────────────────────
# DIPLOMA
# ─────────────────────────────────────────
class Diploma(db.Model):
    __tablename__ = "diploma"

    id_diploma           = db.Column(db.Integer, primary_key=True)
    id_inscripcion       = db.Column(db.Integer,
                                     db.ForeignKey("inscripcion.id_inscripcion"),
                                     nullable=False, unique=True)
    fecha_emision        = db.Column(db.Date, default=date.today, nullable=False)
    codigo_verificacion  = db.Column(db.String(100), nullable=False, unique=True)

    inscripcion = db.relationship("Inscripcion", back_populates="diploma")

    def to_dict(self):
        return {
            "id_diploma"          : self.id_diploma,
            "id_inscripcion"      : self.id_inscripcion,
            "fecha_emision"       : str(self.fecha_emision),
            "codigo_verificacion" : self.codigo_verificacion,
        }


# ─────────────────────────────────────────
# PRODUCTO  (pastelería / tienda)
# ─────────────────────────────────────────
class Producto(db.Model):
    __tablename__ = "producto"

    id_producto     = db.Column(db.Integer, primary_key=True)
    nombre_producto = db.Column(db.String(100), nullable=False)
    descripcion     = db.Column(db.Text, nullable=False)
    precio_unitario = db.Column(db.Numeric(10, 2), nullable=False)
    id_categoria    = db.Column(db.Integer, db.ForeignKey("categoria.id_categoria"), nullable=False)

    # Campo extra para el frontend
    imagen    = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True, nullable=False)  # False = borrado lógico

    categoria     = db.relationship("Categoria", back_populates="productos")
    detalles      = db.relationship("DetallePedido", back_populates="producto")

    def to_dict(self):
        return {
            "id_producto"    : self.id_producto,
            "nombre_producto": self.nombre_producto,
            "descripcion"    : self.descripcion,
            "precio_unitario": float(self.precio_unitario),
            "id_categoria"   : self.id_categoria,
            "categoria"      : self.categoria.nombre_categoria if self.categoria else None,
            "imagen"         : self.imagen,
            "is_active"      : self.is_active,
        }


# ─────────────────────────────────────────
# PEDIDO
# ─────────────────────────────────────────
class Pedido(db.Model):
    __tablename__ = "pedido"

    no_pedido        = db.Column(db.Integer, primary_key=True)
    id_usuario       = db.Column(db.Integer, db.ForeignKey("usuario.id_usuario"), nullable=False)
    tipo_pedido      = db.Column(db.String(50), nullable=False)       # 'Web' | 'Catering'
    fecha_solicitud  = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    fecha_entrega    = db.Column(db.Date, nullable=False)
    monto_anticipo   = db.Column(db.Numeric(10, 2), default=0, nullable=False)
    monto_total      = db.Column(db.Numeric(10, 2), default=0, nullable=False)
    estado_pedido    = db.Column(db.String(30), default="Pendiente", nullable=False)
    ubicacion_entrega= db.Column(db.Text, nullable=False)

    usuario  = db.relationship("Usuario", back_populates="pedidos")
    detalles = db.relationship("DetallePedido", back_populates="pedido",
                               cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "no_pedido"        : self.no_pedido,
            "id_usuario"       : self.id_usuario,
            "cliente"          : self.usuario.nombre_completo if self.usuario else None,
            "tipo_pedido"      : self.tipo_pedido,
            "fecha_solicitud"  : str(self.fecha_solicitud),
            "fecha_entrega"    : str(self.fecha_entrega),
            "monto_anticipo"   : float(self.monto_anticipo),
            "monto_total"      : float(self.monto_total),
            "estado_pedido"    : self.estado_pedido,
            "ubicacion_entrega": self.ubicacion_entrega,
        }


# ─────────────────────────────────────────
# DETALLE PEDIDO
# ─────────────────────────────────────────
class DetallePedido(db.Model):
    __tablename__ = "detalle_pedido"

    id_detalle    = db.Column(db.Integer, primary_key=True)
    no_pedido     = db.Column(db.Integer,
                              db.ForeignKey("pedido.no_pedido", ondelete="CASCADE"),
                              nullable=False)
    id_producto   = db.Column(db.Integer, db.ForeignKey("producto.id_producto"), nullable=False)
    cantidad      = db.Column(db.Integer, nullable=False)
    precio_momento= db.Column(db.Numeric(10, 2), nullable=False)
    subtotal      = db.Column(db.Numeric(10, 2), nullable=False)

    pedido   = db.relationship("Pedido", back_populates="detalles")
    producto = db.relationship("Producto", back_populates="detalles")

    def to_dict(self):
        return {
            "id_detalle"    : self.id_detalle,
            "no_pedido"     : self.no_pedido,
            "id_producto"   : self.id_producto,
            "producto"      : self.producto.nombre_producto if self.producto else None,
            "cantidad"      : self.cantidad,
            "precio_momento": float(self.precio_momento),
            "subtotal"      : float(self.subtotal),
        }


# ─────────────────────────────────────────
# SOLICITUD CATERING  (banquetes)
# ─────────────────────────────────────────
class SolicitudCatering(db.Model):
    __tablename__ = "solicitudcatering"

    id_solicitud = db.Column(db.Integer, primary_key=True)
    id_usuario   = db.Column(db.Integer, db.ForeignKey("usuario.id_usuario"), nullable=True)
    descripcion  = db.Column(db.Text)
    fecha_evento = db.Column(db.Date)
    estado       = db.Column(db.String(20), default="pendiente")

    # Campos extra del formulario del frontend
    nombre_cliente = db.Column(db.String(150))
    email_cliente  = db.Column(db.String(100))
    telefono       = db.Column(db.String(20))
    tipo_evento    = db.Column(db.String(80))
    personas       = db.Column(db.Integer)

    def to_dict(self):
        return {
            "id_solicitud" : self.id_solicitud,
            "nombre_cliente": self.nombre_cliente,
            "email_cliente" : self.email_cliente,
            "telefono"      : self.telefono,
            "tipo_evento"   : self.tipo_evento,
            "personas"      : self.personas,
            "descripcion"   : self.descripcion,
            "fecha_evento"  : str(self.fecha_evento) if self.fecha_evento else None,
            "estado"        : self.estado,
        }


# ─────────────────────────────────────────
# SOLICITUD CURSO  (interés público)
# ─────────────────────────────────────────
class SolicitudCurso(db.Model):
    __tablename__ = "solicitudcurso"

    id_solicitud = db.Column(db.Integer, primary_key=True)
    id_usuario   = db.Column(db.Integer, db.ForeignKey("usuario.id_usuario"), nullable=True)
    descripcion  = db.Column(db.Text)
    fecha        = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id_solicitud": self.id_solicitud,
            "id_usuario"  : self.id_usuario,
            "descripcion" : self.descripcion,
            "fecha"       : str(self.fecha),
        }
