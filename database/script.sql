CREATE TABLE rol (
    id_rol SERIAL PRIMARY KEY,
    nombre_rol VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE categoria (
    id_categoria SERIAL PRIMARY KEY,
    nombre_categoria VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE usuario (
    id_usuario SERIAL PRIMARY KEY,
    nombre_completo VARCHAR(150) NOT NULL,
    fecha_nacimiento DATE NOT NULL,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    id_rol INT NOT NULL REFERENCES rol(id_rol)
);

CREATE TABLE estudiante (
    carnet VARCHAR(20) PRIMARY KEY,
    id_usuario INT NOT NULL UNIQUE REFERENCES usuario(id_usuario) ON DELETE CASCADE
);

CREATE TABLE docente (
    id_docente SERIAL PRIMARY KEY,
    telefono VARCHAR(20) NOT NULL,
    id_usuario INT NOT NULL UNIQUE REFERENCES usuario(id_usuario) ON DELETE CASCADE
);

CREATE TABLE curso (
    id_curso SERIAL PRIMARY KEY,
    nombre_curso VARCHAR(100) NOT NULL,
    descripcion TEXT NOT NULL,
    duracion_horas INT NOT NULL CHECK (duracion_horas > 0),
    modalidad VARCHAR(50) NOT NULL CHECK (modalidad IN ('Presencial', 'Virtual')),
    cupo_maximo INT NOT NULL CHECK (cupo_maximo > 0),
    id_docente INT NOT NULL REFERENCES docente(id_docente),
    fecha_inicio DATE NOT NULL,
    precio_curso DECIMAL(10,2) NOT NULL CHECK (precio_curso >= 0),
    -- Campos extra para el frontend
    imagen TEXT,
    hora VARCHAR(50),
    nivel VARCHAR(50),
    extras VARCHAR(100),
    estado VARCHAR(20) DEFAULT 'disponible',
    is_active BOOLEAN NOT NULL DEFAULT TRUE  -- Soft delete: FALSE = eliminado lógicamente
);

CREATE TABLE horario_curso (
    id_horario SERIAL PRIMARY KEY,
    id_curso INT NOT NULL REFERENCES curso(id_curso) ON DELETE CASCADE,
    dia_semana VARCHAR(20) NOT NULL CHECK (dia_semana IN ('Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo')),
    hora_inicio TIME NOT NULL,
    hora_fin TIME NOT NULL,
    CONSTRAINT ck_horas CHECK (hora_fin > hora_inicio),
    CONSTRAINT uq_horario_unico UNIQUE (id_curso, dia_semana, hora_inicio)
);

CREATE TABLE inscripcion (
    id_inscripcion SERIAL PRIMARY KEY,
    id_usuario INT NOT NULL REFERENCES usuario(id_usuario),
    id_curso INT NOT NULL REFERENCES curso(id_curso),
    fecha_inscripcion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    estado_pago VARCHAR(20) NOT NULL DEFAULT 'Pendiente'
        CHECK (estado_pago IN ('Pendiente', 'Anticipo', 'Pagado')),
    nota_final DECIMAL(5,2) DEFAULT 0 CHECK (nota_final BETWEEN 0 AND 100),
    CONSTRAINT uq_usuario_curso UNIQUE (id_usuario, id_curso)
);

CREATE TABLE asistencia (
    id_asistencia SERIAL PRIMARY KEY,
    id_inscripcion INT NOT NULL REFERENCES inscripcion(id_inscripcion) ON DELETE CASCADE,
    fecha DATE NOT NULL DEFAULT CURRENT_DATE,
    presente BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT uq_asistencia_dia UNIQUE (id_inscripcion, fecha)
);

CREATE TABLE calificacion (
    id_calificacion SERIAL PRIMARY KEY,
    id_inscripcion INT NOT NULL REFERENCES inscripcion(id_inscripcion) ON DELETE CASCADE,
    descripcion VARCHAR(100) NOT NULL,
    nota DECIMAL(5,2) NOT NULL CHECK (nota BETWEEN 0 AND 100)
);

CREATE TABLE diploma (
    id_diploma SERIAL PRIMARY KEY,
    id_inscripcion INT NOT NULL UNIQUE REFERENCES inscripcion(id_inscripcion),
    fecha_emision DATE NOT NULL DEFAULT CURRENT_DATE,
    codigo_verificacion VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE producto (
    id_producto SERIAL PRIMARY KEY,
    nombre_producto VARCHAR(100) NOT NULL,
    descripcion TEXT NOT NULL,
    precio_unitario DECIMAL(10,2) NOT NULL CHECK (precio_unitario > 0),
    id_categoria INT NOT NULL REFERENCES categoria(id_categoria),
    -- Campo extra para el frontend
    imagen TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE  -- Soft delete: FALSE = eliminado lógicamente
);

CREATE TABLE pedido (
    no_pedido SERIAL PRIMARY KEY,
    id_usuario INT NOT NULL REFERENCES usuario(id_usuario),
    tipo_pedido VARCHAR(50) NOT NULL CHECK (tipo_pedido IN ('Web', 'Catering')),
    fecha_solicitud TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_entrega DATE NOT NULL,
    monto_anticipo DECIMAL(10,2) NOT NULL DEFAULT 0 CHECK (monto_anticipo >= 0),
    monto_total DECIMAL(10,2) NOT NULL DEFAULT 0 CHECK (monto_total >= 0),
    estado_pedido VARCHAR(30) NOT NULL DEFAULT 'Pendiente'
        CHECK (estado_pedido IN ('Pendiente', 'En Preparación', 'Pagado', 'Entregado', 'Cancelado')),
    ubicacion_entrega TEXT NOT NULL
);

CREATE TABLE detalle_pedido (
    id_detalle SERIAL PRIMARY KEY,
    no_pedido INT NOT NULL REFERENCES pedido(no_pedido) ON DELETE CASCADE,
    id_producto INT NOT NULL REFERENCES producto(id_producto),
    cantidad INT NOT NULL CHECK (cantidad > 0),
    precio_momento DECIMAL(10,2) NOT NULL CHECK (precio_momento > 0),
    subtotal DECIMAL(10,2) NOT NULL,
    CONSTRAINT ck_subtotal_calculado CHECK (subtotal = (cantidad * precio_momento))
);

-- CORRECCIÓN: SolicitudCatering ahora incluye TODAS las columnas que usa el backend/frontend
CREATE TABLE solicitudcatering (
    id_solicitud SERIAL PRIMARY KEY,
    id_usuario INT REFERENCES usuario(id_usuario),
    nombre_cliente VARCHAR(150),
    email_cliente VARCHAR(100),
    telefono VARCHAR(20),
    tipo_evento VARCHAR(80),
    personas INT,
    descripcion TEXT,
    fecha_evento DATE,
    estado VARCHAR(20) DEFAULT 'pendiente'
);

CREATE TABLE solicitudcurso (
    id_solicitud SERIAL PRIMARY KEY,
    id_usuario INT REFERENCES usuario(id_usuario),
    descripcion TEXT,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices
CREATE INDEX idx_inscripcion_usuario ON inscripcion(id_usuario);
CREATE INDEX idx_pedido_usuario ON pedido(id_usuario);
CREATE INDEX idx_detalle_pedido ON detalle_pedido(no_pedido);
CREATE INDEX idx_producto_categoria ON producto(id_categoria);

-- Datos iniciales de roles
INSERT INTO rol (nombre_rol) VALUES ('Cliente');
INSERT INTO rol (nombre_rol) VALUES ('Administrador');
INSERT INTO rol (nombre_rol) VALUES ('Docente');

-- Categorías iniciales de productos
INSERT INTO categoria (nombre_categoria) VALUES ('Pasteles');
INSERT INTO categoria (nombre_categoria) VALUES ('Cupcakes');
INSERT INTO categoria (nombre_categoria) VALUES ('Pan');
INSERT INTO categoria (nombre_categoria) VALUES ('Macarons');
INSERT INTO categoria (nombre_categoria) VALUES ('Otros');

-- ══════════════════════════════════════════════════
-- MIGRACIÓN: Soft Delete — ejecutar si la BD ya existe
-- ══════════════════════════════════════════════════
-- ALTER TABLE curso    ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE;
-- ALTER TABLE producto ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE;
-- UPDATE curso    SET is_active = TRUE WHERE is_active IS NULL;
-- UPDATE producto SET is_active = TRUE WHERE is_active IS NULL;
