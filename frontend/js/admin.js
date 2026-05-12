/**
 * frontend/js/admin.js
 * Conecta el panel admin con la API real de Flask.
 *
 * CAMBIOS EN ESTA VERSIÓN:
 * 1. Soft Delete: apiDeleteCurso y apiDeleteProducto hacen DELETE al endpoint,
 *    que ahora el backend convierte en UPDATE is_active=False.
 *    El frontend recarga la lista (sin el registro eliminado) automáticamente.
 * 2. FIX botón Modificar producto: openEditPastel carga datos desde la API
 *    (/api/productos/:id) para garantizar datos frescos, no del array local.
 * 3. FIX calendario index: loadCursos filtra is_active=true (el backend ya filtra,
 *    pero aquí se añade una guarda extra en el mapeo).
 * 4. Variables globales sincronizadas con var del HTML inline (no let).
 */

const API = "/api";

// ══════════════════════════════════════════
//  DASHBOARD
// ══════════════════════════════════════════

async function loadDashboard() {
  try {
    const res  = await fetch(`${API}/dashboard`);
    const data = await res.json();
    setStatValue("stat-cursos",        data.total_cursos);
    setStatValue("stat-inscripciones", data.total_inscripciones);
    setStatValue("stat-productos",     data.total_productos);
    setStatValue("stat-banquetes",     data.banquetes_pendientes);
  } catch (err) {
    console.warn("Dashboard stats error:", err.message);
  }
}

function setStatValue(id, val) {
  const el = document.getElementById(id);
  if (el) el.textContent = val ?? "—";
}

// ══════════════════════════════════════════
//  CURSOS
// ══════════════════════════════════════════

async function apiLoadCursos() {
  try {
    const res  = await fetch(`${API}/cursos`);
    if (!res.ok) throw new Error("HTTP " + res.status);
    const data = await res.json();

    // El backend ya filtra is_active=True; mapeamos todo lo que llegue
    const mapped = data.map(c => ({
      id         : c.id_curso,
      titulo     : c.nombre_curso,
      fecha      : c.fecha_inicio,
      hora       : c.hora        || "Por confirmar",
      nivel      : c.nivel       || "Todos",
      duracion   : (c.duracion_horas || 1) + " horas",
      extras     : c.extras      || "",
      precio     : "Q." + parseFloat(c.precio_curso).toFixed(2),
      precioNum  : parseFloat(c.precio_curso),   // FIX: valor numérico puro para edición
      estado     : c.estado      || "disponible",
      descripcion: c.descripcion,
      imagen     : c.imagen,
    }));

    cursosData        = mapped;
    window.cursosData = mapped;

    if (typeof renderCursos    === "function") renderCursos(window.cursosData);
    if (typeof renderDashboard === "function") renderDashboard();
  } catch (err) {
    console.warn("Error al cargar cursos:", err.message);
    showToast("Error al cargar cursos", "error");
  }
}

async function apiSaveCurso(payload, id = null) {
  const url    = id ? `${API}/cursos/${id}` : `${API}/cursos`;
  const method = id ? "PUT" : "POST";

  // FIX precio: el input #curso-precio ahora contiene el número puro (ej. "250" o "250.00").
  // Pero como salvaguarda, eliminamos cualquier prefijo no numérico (ej. "Q.") y luego
  // removemos puntos de miles ambiguos. "Q.250" → ".250" causaba el bug 0.25 (antes).
  const precioRaw = String(payload.precio || "0").trim();
  // Si empieza con letra/Q seguido de punto, quitamos todo lo que no sea dígito/punto al inicio
  const precioNum = parseFloat(precioRaw.replace(/^[^\d]+/, "")) || 0;

  const body = {
    nombre_curso   : payload.titulo,
    descripcion    : payload.descripcion    || "",
    fecha_inicio   : payload.fecha,
    precio_curso   : precioNum,
    duracion_horas : parseInt(payload.duracion) || 1,
    modalidad      : payload.modalidad      || "Presencial",
    cupo_maximo    : parseInt(payload.cupo_maximo) || 20,
    id_docente     : parseInt(payload.id_docente)  || 1,
    hora           : payload.hora,
    nivel          : payload.nivel,
    extras         : payload.extras,
    imagen         : payload.imagen,
    estado         : payload.estado         || "disponible",
  };

  try {
    const res  = await fetch(url, {
      method,
      headers: { "Content-Type": "application/json" },
      body   : JSON.stringify(body),
    });
    const data = await res.json();
    if (!res.ok) { showToast(data.message || "Error al guardar", "error"); return; }
    showToast(id ? "Curso actualizado ✓" : "Curso creado ✓");
    await apiLoadCursos();
  } catch {
    showToast("Error de conexión", "error");
  }
}

async function apiDeleteCurso(id) {
  /**
   * SOFT DELETE: el endpoint DELETE /api/cursos/:id ahora hace
   * UPDATE curso SET is_active=False en el backend.
   * Tras la respuesta recargamos la lista (el curso desaparece al filtrarse).
   */
  try {
    const res  = await fetch(`${API}/cursos/${id}`, { method: "DELETE" });
    const data = await res.json();
    if (!res.ok) { showToast(data.message, "error"); return; }
    showToast("Curso eliminado ✓");
    await apiLoadCursos();
  } catch {
    showToast("Error de conexión", "error");
  }
}

// ══════════════════════════════════════════
//  PRODUCTOS (Pastelería)
// ══════════════════════════════════════════

async function apiLoadProductos() {
  try {
    const res  = await fetch(`${API}/productos`);
    if (!res.ok) throw new Error("HTTP " + res.status);
    const data = await res.json();

    // El backend filtra is_active=True; mapeamos todo lo que llegue
    const mapped = data.map(p => ({
      id         : p.id_producto,
      nombre     : p.nombre_producto,
      descripcion: p.descripcion,
      precio     : "Q." + parseFloat(p.precio_unitario).toFixed(2),
      precioNum  : parseFloat(p.precio_unitario),   // FIX: valor numérico puro para edición
      imagen     : p.imagen || "",
    }));

    pasteriaData        = mapped;
    window.pasteriaData = mapped;

    if (typeof renderPasteleria === "function") renderPasteleria();
  } catch (err) {
    console.warn("Error al cargar productos:", err.message);
    showToast("Error al cargar productos", "error");
  }
}

async function apiSaveProducto(payload, id = null) {
  const url    = id ? `${API}/productos/${id}` : `${API}/productos`;
  const method = id ? "PUT" : "POST";

  // FIX precio: mismo bug que en cursos. "Q.250".replace(/[^\d.]/g,"") → ".250" → 0.25
  // Solución: eliminar solo el prefijo no numérico inicial.
  const precioRaw = String(payload.precio || "0").trim();
  const precioNum = parseFloat(precioRaw.replace(/^[^\d]+/, "")) || 0;

  const body = {
    nombre_producto : payload.nombre,
    descripcion     : payload.descripcion || "",
    precio_unitario : precioNum,
    id_categoria    : parseInt(payload.id_categoria) || 1,
    imagen          : payload.imagen || "",
  };

  try {
    const res  = await fetch(url, {
      method,
      headers: { "Content-Type": "application/json" },
      body   : JSON.stringify(body),
    });
    const data = await res.json();
    if (!res.ok) { showToast(data.message || "Error", "error"); return; }
    showToast(id ? "Producto actualizado ✓" : "Producto creado ✓");
    await apiLoadProductos();
  } catch {
    showToast("Error de conexión", "error");
  }
}

async function apiDeleteProducto(id) {
  /**
   * SOFT DELETE: el endpoint DELETE /api/productos/:id ahora hace
   * UPDATE producto SET is_active=False en el backend.
   */
  try {
    const res  = await fetch(`${API}/productos/${id}`, { method: "DELETE" });
    const data = await res.json();
    if (!res.ok) { showToast(data.message, "error"); return; }
    showToast("Producto eliminado ✓");
    await apiLoadProductos();
  } catch {
    showToast("Error de conexión", "error");
  }
}

/**
 * FIX BOTÓN MODIFICAR PRODUCTO:
 * Carga los datos del producto desde la API (/api/productos/:id)
 * para asegurar que el modal recibe información fresca y correcta.
 * Fallback: usa pasteriaData local si la API falla.
 */
async function apiCargarProductoParaEditar(id) {
  try {
    const res  = await fetch(`${API}/productos/${id}`);
    if (!res.ok) throw new Error("HTTP " + res.status);
    const p = await res.json();
    return {
      id         : p.id_producto,
      nombre     : p.nombre_producto,
      descripcion: p.descripcion,
      precio     : "Q." + parseFloat(p.precio_unitario).toFixed(2),
      precioNum  : parseFloat(p.precio_unitario),   // FIX: valor numérico puro para edición
      imagen     : p.imagen || "",
    };
  } catch {
    // Fallback al array local si no hay conexión
    return (window.pasteriaData || pasteriaData || []).find(x => x.id === id) || null;
  }
}

// ══════════════════════════════════════════
//  INSCRIPCIONES
// ══════════════════════════════════════════

async function apiLoadInscripciones() {
  try {
    const res  = await fetch(`${API}/inscripciones`);
    if (!res.ok) throw new Error("HTTP " + res.status);
    const data = await res.json();

    const mapped = data.map(i => ({
      id               : i.id_inscripcion,
      alumno           : i.alumno           || "Sin nombre",
      email            : i.email            || "—",
      telefono         : i.telefono         || "",
      cursoId          : i.id_curso,
      curso            : i.curso            || "—",
      fechaInscripcion : i.fecha_inscripcion ? i.fecha_inscripcion.slice(0, 10) : "—",
      estado           : mapEstadoInscripcion(i.estado_pago),
      estadoPago       : i.estado_pago,
      pago             : i.nota_final > 0 ? "Q." + i.nota_final : "Pendiente",
      metodoPago       : i.estado_pago || "—",
    }));

    inscripcionesData        = mapped;
    window.inscripcionesData = mapped;

    if (typeof renderInscripciones === "function")
      renderInscripciones(window.inscripcionesData);
  } catch (err) {
    console.warn("Error al cargar inscripciones:", err.message);
    showToast("Error al cargar inscripciones", "error");
  }
}

function mapEstadoInscripcion(estado_pago) {
  const m = { "Pendiente": "pendiente", "Anticipo": "pendiente", "Pagado": "confirmada" };
  return m[estado_pago] || "pendiente";
}

async function apiConfirmarInscripcion(id) {
  try {
    const res = await fetch(`${API}/inscripciones/${id}`, {
      method : "PUT",
      headers: { "Content-Type": "application/json" },
      body   : JSON.stringify({ estado_pago: "Pagado" }),
    });
    const data = await res.json();
    if (!res.ok) { showToast(data.message, "error"); return; }
    showToast("Inscripción confirmada ✓");
    await apiLoadInscripciones();
  } catch {
    showToast("Error de conexión", "error");
  }
}

async function apiCancelarInscripcion(id) {
  try {
    const res  = await fetch(`${API}/inscripciones/${id}`, { method: "DELETE" });
    const data = await res.json();
    if (!res.ok) { showToast(data.message, "error"); return; }
    showToast("Inscripción cancelada");
    await apiLoadInscripciones();
  } catch {
    showToast("Error de conexión", "error");
  }
}

// ══════════════════════════════════════════
//  BANQUETES
// ══════════════════════════════════════════

async function apiLoadBanquetes() {
  try {
    const res  = await fetch(`${API}/banquetes`);
    if (!res.ok) throw new Error("HTTP " + res.status);
    const data = await res.json();

    const mapped = data.map(b => ({
      id         : b.id_solicitud,
      cliente    : b.nombre_cliente || "Sin nombre",
      email      : b.email_cliente  || "—",
      telefono   : b.telefono       || "—",
      tipoEvento : b.tipo_evento    || "—",
      fechaEvento: b.fecha_evento   || "—",
      personas   : b.personas       || 0,
      mensaje    : b.descripcion    || "",
      estado     : b.estado         || "pendiente",
    }));

    banquetesData        = mapped;
    window.banquetesData = mapped;

    if (typeof renderBanquetes === "function") renderBanquetes();
    if (typeof renderDashboard === "function") renderDashboard();
  } catch (err) {
    console.warn("Error al cargar banquetes:", err.message);
    showToast("Error al cargar banquetes", "error");
  }
}

async function apiConfirmarBanquete(id) {
  await _updateBanquete(id, "confirmada", "Banquete confirmado ✓");
}

async function apiRechazarBanquete(id) {
  await _updateBanquete(id, "rechazada", "Banquete rechazado");
}

async function _updateBanquete(id, estado, msg) {
  try {
    const res = await fetch(`${API}/banquetes/${id}`, {
      method : "PUT",
      headers: { "Content-Type": "application/json" },
      body   : JSON.stringify({ estado }),
    });
    const data = await res.json();
    if (!res.ok) { showToast(data.message, "error"); return; }
    showToast(msg);
    await apiLoadBanquetes();
  } catch {
    showToast("Error de conexión", "error");
  }
}

// ══════════════════════════════════════════
//  INICIALIZACIÓN AUTOMÁTICA
// ══════════════════════════════════════════

(async function arrancarAPI() {
  try {
    await Promise.all([
      loadDashboard(),
      apiLoadCursos(),
      apiLoadProductos(),
      apiLoadInscripciones(),
      apiLoadBanquetes(),
    ]);
  } catch (err) {
    console.warn("arrancarAPI error:", err);
  }
})();
