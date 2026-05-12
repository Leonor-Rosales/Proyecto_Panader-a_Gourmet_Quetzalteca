/**
 * frontend/js/banquetes.js
 * Envía el formulario público de cotización de banquetes a Flask.
 *
 * CORRECCIONES:
 * 1. Incluye id_usuario desde sessionStorage si hay sesión activa.
 * 2. Selección de campos por ID (más robusto que por placeholder).
 * 3. URL relativa en vez de localhost hardcodeado.
 */

const API_BASE_B = "/api";

async function enviarCotizacion(event) {
  if (event) event.preventDefault();

  const nombre   = document.getElementById("cotizar-nombre")?.value?.trim()
                || document.querySelector(".cotizar-form [placeholder='Tu nombre']")?.value?.trim();
  const telefono = document.getElementById("cotizar-telefono")?.value?.trim()
                || document.querySelector(".cotizar-form [placeholder='+502 ---- ----']")?.value?.trim();
  const email    = document.getElementById("cotizar-email")?.value?.trim()
                || document.querySelector(".cotizar-form [type='email']")?.value?.trim();
  const tipoEv   = document.getElementById("cotizar-tipo")?.value
                || document.querySelector(".cotizar-form select")?.value;
  const personas = document.getElementById("cotizar-personas")?.value
                || document.querySelector(".cotizar-form [type='number']")?.value;
  const fecha    = document.getElementById("cotizar-fecha")?.value
                || document.querySelector(".cotizar-form [type='date']")?.value;
  const mensaje  = document.getElementById("cotizar-mensaje")?.value?.trim()
                || document.querySelector(".cotizar-form textarea")?.value?.trim();

  if (!nombre || !fecha) {
    alert("Por favor completa al menos tu nombre y la fecha del evento.");
    return;
  }

  // CORRECCIÓN: obtener usuario de sesión para asociar la solicitud
  const usuario = JSON.parse(sessionStorage.getItem("usuario_sesion") || "null");

  const btnEnviar = document.querySelector(".cotizar-form .btn-submit");
  const original  = btnEnviar?.textContent;

  if (btnEnviar) {
    btnEnviar.textContent = "Enviando…";
    btnEnviar.disabled    = true;
  }

  try {
    const body = {
      nombre_cliente: nombre,
      email_cliente : email    || "",
      telefono      : telefono || "",
      tipo_evento   : tipoEv   || "",
      personas      : parseInt(personas) || null,
      fecha_evento  : fecha,
      descripcion   : mensaje  || "",
    };

    // Asociar al usuario autenticado si existe sesión
    if (usuario && usuario.id_usuario) {
      body.id_usuario = usuario.id_usuario;
    }

    const res  = await fetch(`${API_BASE_B}/banquetes`, {
      method : "POST",
      headers: { "Content-Type": "application/json" },
      body   : JSON.stringify(body),
    });

    const data = await res.json();
    if (res.ok) {
      alert("✅ " + data.message);
      document.querySelectorAll(".cotizar-form input, .cotizar-form select, .cotizar-form textarea")
        .forEach(el => el.value = "");
    } else {
      alert("❌ " + (data.message || "No se pudo enviar la solicitud."));
    }
  } catch {
    alert("❌ Error de conexión. Verifica que el servidor esté corriendo.");
  } finally {
    if (btnEnviar) {
      btnEnviar.textContent = original;
      btnEnviar.disabled    = false;
    }
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const btn = document.querySelector(".cotizar-form .btn-submit");
  if (btn) btn.addEventListener("click", enviarCotizacion);
});
