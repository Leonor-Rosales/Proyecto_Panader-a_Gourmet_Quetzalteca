/**
 * frontend/js/cursos.js
 * Carga cursos activos desde la API y los renderiza en:
 *  - El calendario de la página Cursos (renderCalendar)
 *  - La sección "Próximos Cursos" del inicio (.calendar-container)
 *
 * CAMBIOS:
 * 1. FIX calendario: filtra is_active=true en el mapeo (doble seguridad además del backend).
 * 2. FIX fecha: usa c.fecha + "T12:00:00" para evitar desfase de zona horaria (UTC-6 GT).
 * 3. renderCalendar usa CURSOS filtrados por estado !== 'inactivo' para el display.
 */

const API_BASE = "/api";

async function loadCursos() {
  try {
    const res = await fetch(`${API_BASE}/cursos`);
    if (!res.ok) throw new Error("HTTP " + res.status);
    const data = await res.json();

    if (!data || data.length === 0) return; // sin datos: deja demo intacto

    // FIX: filtrar is_active como doble seguridad (el backend ya filtra,
    // pero si la BD aún no tiene la columna, no rompemos nada)
    const activos = data.filter(c => c.is_active !== false);

    const mapped = activos.map(c => ({
      id         : c.id_curso,
      titulo     : c.nombre_curso,
      fecha      : c.fecha_inicio,          // formato YYYY-MM-DD del backend
      hora       : c.hora   || "Por confirmar",
      nivel      : c.nivel  || "Todos",
      duracion   : (c.duracion_horas || 1) + " horas",
      extras     : c.extras || "",
      // FIX precio: usar toFixed(2) para que el número quede bien formateado
      precio     : "Q." + parseFloat(c.precio_curso).toFixed(2),
      descripcion: c.descripcion,
      imagen     : c.imagen || "https://images.unsplash.com/photo-1509440159596-0249088772ff?w=800&q=80",
      estado     : c.estado || "disponible",
    }));

    // FIX sincronización: mutar window.CURSOS en lugar de reasignarlo,
    // para que var CURSOS del script inline siga apuntando al mismo objeto.
    window.CURSOS.length = 0;
    mapped.forEach(c => window.CURSOS.push(c));

    // También actualizar var CURSOS si por alguna razón es un objeto distinto
    if (typeof CURSOS !== "undefined" && CURSOS !== window.CURSOS) {
      CURSOS.length = 0;
      mapped.forEach(c => CURSOS.push(c));
    }

    // Re-renderizar el calendario con los datos reales
    if (typeof renderCalendar === "function") renderCalendar();

    // Actualizar la sección "Próximos Cursos" en el inicio
    renderProximosCursos();

  } catch (err) {
    console.warn("loadCursos:", err.message);
    // Si falla la API, el calendario sigue mostrando los datos demo del HTML
  }
}

/**
 * Renderiza hasta 3 próximos cursos activos en .calendar-container (página inicio).
 * FIX fecha: añade T12:00:00 para evitar que UTC-0 desplace el día en zona GMT-6 (Guatemala).
 * FIX calendario: si no hay cursos futuros, muestra los más recientes activos como fallback.
 */
function renderProximosCursos() {
  const container = document.querySelector(".calendar-container");
  if (!container || !window.CURSOS || window.CURSOS.length === 0) return;

  const hoy = new Date();
  hoy.setHours(0, 0, 0, 0); // comparar solo por fecha, no por hora

  // Intentar mostrar cursos futuros; si no hay, mostrar todos ordenados por fecha
  let proximos = window.CURSOS
    .filter(c => new Date(c.fecha + "T12:00:00") >= hoy)
    .sort((a, b) => new Date(a.fecha) - new Date(b.fecha))
    .slice(0, 3);

  // Fallback: si no hay cursos futuros, mostrar los últimos activos disponibles
  if (!proximos.length) {
    proximos = window.CURSOS
      .filter(c => c.estado !== "cancelado")
      .sort((a, b) => new Date(b.fecha) - new Date(a.fecha))
      .slice(0, 3);
  }

  if (!proximos.length) {
    container.innerHTML = `
      <div class="event-row">
        <div class="date-box" style="opacity:.5">—</div>
        <div class="event-info"><h4>Sin cursos próximos</h4><p>Vuelve pronto para ver nuevas fechas.</p></div>
        <div class="event-divider"></div>
        <div class="price"></div>
      </div>`;
    return;
  }

  const meses = ["ENE","FEB","MAR","ABR","MAY","JUN",
                  "JUL","AGO","SEP","OCT","NOV","DIC"];

  container.innerHTML = proximos.map(c => {
    const d = new Date(c.fecha + "T12:00:00");
    const estadoLabel = c.estado === "disponible" ? "DISPONIBLE" :
                        c.estado === "lleno"       ? "LLENO"      :
                        c.estado.toUpperCase();
    return `
      <div class="event-row">
        <div class="date-box">${d.getDate()}<span>${meses[d.getMonth()]}</span></div>
        <div class="event-info">
          <h4>${c.titulo}</h4>
          <p>${estadoLabel}</p>
        </div>
        <div class="event-divider"></div>
        <div class="price">${c.precio}</div>
      </div>`;
  }).join("");
}

document.addEventListener("DOMContentLoaded", loadCursos);
