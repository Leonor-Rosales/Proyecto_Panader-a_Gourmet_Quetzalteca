# 🥐 Integración Completa — Panadería Gourmet Quetzalteca
## Flask + PostgreSQL + Frontend HTML

> Guía generada **100% basada en tu proyecto real**:  
> `index.html`, `admin.html` y `script.sql` del ZIP analizado.

---

## 📋 Análisis del proyecto original

### Lo que encontré en tu ZIP

| Archivo | Contenido |
|---|---|
| `index.html` | SPA pública con 5 páginas: Inicio, Pastelería, Cursos (calendario), Banquetes, Contacto |
| `admin.html` | Panel admin con login, dashboard, cursos, inscripciones, pastelería, banquetes |
| `script.sql` | 14 tablas PostgreSQL con relaciones completas |

### Páginas del frontend (index.html)
- **Inicio** — hero, próximos cursos, strip banquetes, testimonios
- **Pastelería** — grid de productos (`DEMO_PASTELES` → API `/productos`)
- **Cursos** — calendario mensual (`CURSOS` array → API `/cursos`)
- **Detalle Curso** — vista individual al clic en el calendario
- **Banquetes** — formulario de cotización (→ API `/banquetes`)
- **Contacto** — formulario de contacto

### Secciones del panel admin (admin.html)
- **Dashboard** — 4 stats cards (→ API `/dashboard`)
- **Cursos** — tabla + modal CRUD (→ API `/cursos`)
- **Inscripciones** — tabla con filtros + confirmar/cancelar (→ API `/inscripciones`)
- **Pastelería** — tabla productos + modal CRUD (→ API `/productos`)
- **Banquetes** — solicitudes de catering + confirmar/rechazar (→ API `/banquetes`)
- **Ajustes** — configuración básica

### Tablas SQL identificadas

```
rol               → Roles: Cliente, Administrador, Docente
categoria         → Categorías de productos
usuario           → Usuarios del sistema (con FK a rol)
estudiante        → Extensión de usuario (carnet)
docente           → Extensión de usuario (teléfono)
curso             → Cursos/talleres
horario_curso     → Días y horas de cada curso
inscripcion       → Relación usuario ↔ curso (con estado_pago, nota_final)
asistencia        → Asistencia por inscripción
calificacion      → Notas por inscripción
diploma           → Diploma generado al completar
producto          → Pastelería / tienda (con FK a categoría)
pedido            → Pedidos web o catering
detalle_pedido    → Líneas del pedido (cantidad, precio, subtotal)
solicitudcatering → Formulario público de banquetes
solicitudcurso    → Solicitud de información sobre cursos
```

---

## 🏗 Estructura final del proyecto

```
PASTELERIA/
│
├── backend/
│   ├── app.py                        ← Punto de entrada Flask
│   ├── config.py                     ← Lee .env
│   ├── requirements.txt              ← Dependencias pip
│   ├── .env                          ← Credenciales (NO subir a Git)
│   │
│   ├── database/
│   │   ├── __init__.py
│   │   └── conexion.py               ← SQLAlchemy init
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   └── models.py                 ← 14 modelos de tus tablas reales
│   │
│   ├── controllers/
│   │   ├── __init__.py
│   │   ├── auth_controller.py        ← Login / Registro
│   │   ├── curso_controller.py       ← CRUD cursos
│   │   ├── producto_controller.py    ← CRUD productos
│   │   ├── inscripcion_controller.py ← CRUD inscripciones
│   │   └── banquete_controller.py    ← CRUD solicitudes catering
│   │
│   ├── routes/
│   │   ├── __init__.py
│   │   └── api_routes.py             ← Todos los endpoints REST
│   │
│   └── utils/                        ← Helpers futuros
│
├── frontend/
│   ├── pages/
│   │   ├── index.html                ← Tu index original (sin cambios)
│   │   └── admin.html                ← Tu admin original (sin cambios)
│   │
│   ├── js/
│   │   ├── cursos.js                 ← Carga cursos desde API
│   │   ├── admin.js                  ← Reemplaza localStorage por fetch()
│   │   └── banquetes.js              ← Envía formulario de cotización
│   │
│   ├── css/                          ← CSS adicional si necesitas
│   ├── assets/                       ← Imágenes locales
│   └── components/                   ← Componentes reutilizables HTML
│
├── database/
│   └── script.sql                    ← Tu SQL original
│
└── .gitignore
```

---

## ⚙️ PASO 1 — Instalar PostgreSQL y crear la base de datos

### 1.1 Instalar PostgreSQL (si no lo tienes)
Descarga desde: https://www.postgresql.org/download/windows/

Durante la instalación:
- Usuario: `postgres`
- Contraseña: `1234` (o la que prefieras, actualiza `.env`)
- Puerto: `5432`

### 1.2 Crear la base de datos

Abre **pgAdmin** o **SQL Shell (psql)**:

```sql
-- En psql como superusuario:
CREATE DATABASE pasteleria;
\c pasteleria
```

### 1.3 Importar el script SQL

```bash
# Desde PowerShell o CMD:
psql -U postgres -d pasteleria -f "C:\ruta\PASTELERIA\database\script.sql"
```

O en pgAdmin: clic derecho en `pasteleria` → `Query Tool` → pegar y ejecutar `script.sql`.

### 1.4 Verificar tablas

```sql
\dt                          -- listar tablas
SELECT * FROM rol;           -- debe mostrar: Cliente, Administrador, Docente
SELECT * FROM categoria;     -- vacío, debes insertar tus categorías
```

### 1.5 Insertar datos base necesarios

```sql
-- Categorías de productos (pastelería)
INSERT INTO categoria (nombre_categoria) VALUES
  ('Pasteles'),
  ('Cupcakes'),
  ('Pan Artesanal'),
  ('Macarons'),
  ('Cheesecake');

-- Usuario administrador de prueba
-- (la contraseña se hashea desde Flask; este es solo el hash de "admin2024")
-- Créalo desde el endpoint /api/auth/register o usa pgAdmin.
```

---

## ⚙️ PASO 2 — Configurar el entorno Python

### 2.1 Crear entorno virtual

```powershell
cd C:\ruta\PASTELERIA\backend
python -m venv venv
```

### 2.2 Activar (PowerShell)

```powershell
.\venv\Scripts\Activate
```

Verás `(venv)` al inicio del prompt.

### 2.3 Instalar dependencias

```bash
pip install -r requirements.txt
```

Las librerías instaladas y para qué sirven:

| Librería | Para qué |
|---|---|
| `flask` | Framework web Python |
| `flask-cors` | Permite que el navegador llame a la API sin bloqueos |
| `flask-sqlalchemy` | ORM para PostgreSQL desde Python |
| `psycopg2-binary` | Driver de conexión Python → PostgreSQL |
| `python-dotenv` | Lee el archivo `.env` con credenciales |
| `werkzeug` | Hash de contraseñas (`generate_password_hash`) |

---

## ⚙️ PASO 3 — Configurar credenciales

Edita `backend/.env` con tus datos reales:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=pasteleria
DB_USER=postgres
DB_PASSWORD=1234          ← tu contraseña real de PostgreSQL
SECRET_KEY=clave-larga-aleatoria-aqui
FLASK_ENV=development
FLASK_DEBUG=True
```

> ⚠️ **Nunca subas `.env` a GitHub.** Ya está en `.gitignore`.

---

## ⚙️ PASO 4 — Conectar los archivos JS al frontend

### 4.1 Modificar `index.html`

Agrega estas líneas **antes de `</body>`** en `frontend/pages/index.html`:

```html
<!-- Conectar cursos con la API -->
<script src="../js/cursos.js"></script>
<!-- Conectar formulario de banquetes con la API -->
<script src="../js/banquetes.js"></script>
```

El archivo `cursos.js` sobrescribirá automáticamente el array `CURSOS` con datos reales de PostgreSQL.

### 4.2 Modificar `admin.html`

Agrega estas líneas **antes de `</body>`** en `frontend/pages/admin.html`:

```html
<!-- Conectar panel admin con la API (reemplaza localStorage) -->
<script src="../js/admin.js"></script>
```

El archivo `admin.js` sobrescribirá `initApp()` para usar `fetch()` en lugar de `localStorage`.

> **Importante:** los `<script>` de `admin.js` y `cursos.js` deben ir **después** del script inline existente.

---

## ▶️ PASO 5 — Ejecutar el proyecto

### 5.1 Iniciar Flask

```powershell
# Dentro de backend/ con el venv activo:
cd C:\ruta\PASTELERIA\backend
python app.py
```

Deberías ver:
```
✅  Conexión a PostgreSQL exitosa.
 * Running on http://0.0.0.0:5000
```

### 5.2 Abrir el frontend

Flask sirve el frontend directamente:

| URL | Página |
|---|---|
| `http://localhost:5000/` | index.html (sitio público) |
| `http://localhost:5000/admin` | admin.html (panel administrativo) |

---

## 🔌 APIs REST disponibles

### Autenticación
```
POST /api/auth/register   { name, email, password }
POST /api/auth/login      { email, password }
```

### Cursos
```
GET    /api/cursos
GET    /api/cursos/<id>
POST   /api/cursos         { nombre_curso, descripcion, fecha_inicio, precio_curso,
                             duracion_horas, modalidad, cupo_maximo, id_docente,
                             hora, nivel, extras, imagen, estado }
PUT    /api/cursos/<id>    (mismos campos, todos opcionales)
DELETE /api/cursos/<id>
```

### Productos (Pastelería)
```
GET    /api/productos
GET    /api/productos/<id>
POST   /api/productos      { nombre_producto, descripcion, precio_unitario,
                             id_categoria, imagen }
PUT    /api/productos/<id>
DELETE /api/productos/<id>
```

### Inscripciones
```
GET    /api/inscripciones
GET    /api/inscripciones/<id>
POST   /api/inscripciones  { id_usuario, id_curso, estado_pago }
PUT    /api/inscripciones/<id>  { estado_pago: "Pendiente"|"Anticipo"|"Pagado" }
DELETE /api/inscripciones/<id>
```

### Banquetes / Catering
```
GET    /api/banquetes
GET    /api/banquetes/<id>
POST   /api/banquetes      { nombre_cliente, email_cliente, telefono,
                             tipo_evento, personas, fecha_evento, descripcion }
PUT    /api/banquetes/<id> { estado: "pendiente"|"confirmada"|"rechazada" }
DELETE /api/banquetes/<id>
```

### Dashboard
```
GET    /api/dashboard      → { total_cursos, total_inscripciones,
                               total_productos, total_banquetes,
                               pendientes_pago, banquetes_pendientes }
```

---

## 🧪 PASO 6 — Probar las APIs

Puedes usar **Postman**, **Thunder Client** (VS Code) o el navegador.

### Probar login
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@panaderia.com","password":"admin2024"}'
```

### Probar GET cursos
```
http://localhost:5000/api/cursos
```

### Probar crear un curso
```bash
curl -X POST http://localhost:5000/api/cursos \
  -H "Content-Type: application/json" \
  -d '{
    "nombre_curso": "Taller de Panadería",
    "descripcion": "Aprende pan artesanal desde cero.",
    "fecha_inicio": "2026-05-10",
    "precio_curso": 200,
    "duracion_horas": 4,
    "modalidad": "Presencial",
    "cupo_maximo": 15,
    "id_docente": 1,
    "hora": "9:00 am – 1:00 pm",
    "nivel": "Principiantes",
    "estado": "disponible"
  }'
```

---

## 🔐 Flujo completo del sistema

```
Usuario abre http://localhost:5000/
        ↓
Flask sirve index.html
        ↓
JS (cursos.js) llama GET /api/cursos
        ↓
Flask → curso_controller → Curso.query.all() → PostgreSQL
        ↓
Flask responde JSON con los cursos
        ↓
JS renderiza el calendario con datos reales
        ↓
Usuario rellena formulario de banquetes
        ↓
JS (banquetes.js) llama POST /api/banquetes
        ↓
Flask → banquete_controller → INSERT en solicitudcatering
        ↓
PostgreSQL guarda la solicitud
        ↓
Admin abre http://localhost:5000/admin
        ↓
JS (admin.js) llama GET /api/banquetes
        ↓
Admin ve la solicitud y puede confirmar o rechazar
```

---

## 🚀 Para GitHub

```bash
cd C:\ruta\PASTELERIA
git init
git add .
git commit -m "Panadería Gourmet Quetzalteca — Flask + PostgreSQL integrado"

# Verifica que NO se subió .env:
git status  # no debe aparecer backend/.env
```

---

## ❓ Errores comunes y soluciones

| Error | Causa | Solución |
|---|---|---|
| `psycopg2.OperationalError` | PostgreSQL no está corriendo o credenciales incorrectas | Verifica que PostgreSQL está activo; revisa `.env` |
| `ModuleNotFoundError: flask` | Entorno virtual no activado | Ejecuta `.\venv\Scripts\Activate` |
| `CORS error` en el navegador | Flask no configurado con CORS | Ya está en `app.py` con `CORS(app)` |
| `404 /api/cursos` | Flask no inició o URL incorrecta | Verifica que `python app.py` corre en puerto 5000 |
| `relation does not exist` | Script SQL no importado | Ejecuta `script.sql` en PostgreSQL |
| Calendario vacío | No hay cursos en la BD | Usa `POST /api/cursos` para crear uno |

---

## 📁 Archivos creados en esta integración

| Archivo | Descripción |
|---|---|
| `backend/app.py` | Flask + CORS + Blueprints + rutas estáticas |
| `backend/config.py` | Lee `.env` y configura SQLAlchemy |
| `backend/requirements.txt` | Dependencias pip |
| `backend/.env` | Credenciales DB (no subir a Git) |
| `backend/database/conexion.py` | Inicialización SQLAlchemy |
| `backend/models/models.py` | 14 modelos basados en tu SQL real |
| `backend/controllers/auth_controller.py` | Login / Registro con hash |
| `backend/controllers/curso_controller.py` | CRUD cursos |
| `backend/controllers/producto_controller.py` | CRUD productos |
| `backend/controllers/inscripcion_controller.py` | CRUD inscripciones |
| `backend/controllers/banquete_controller.py` | CRUD solicitudes catering |
| `backend/routes/api_routes.py` | Todos los endpoints REST |
| `frontend/js/cursos.js` | Conecta calendario con API |
| `frontend/js/admin.js` | Reemplaza localStorage por API |
| `frontend/js/banquetes.js` | Envía formulario público a API |
| `.gitignore` | Excluye venv, .env, __pycache__ |
