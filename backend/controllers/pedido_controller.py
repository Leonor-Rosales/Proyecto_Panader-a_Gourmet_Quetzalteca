"""
controllers/pedido_controller.py

Lógica de negocio para el carrito de compras y pedidos.

Flujo completo:
  1. El frontend acumula ítems en memoria (JS).
  2. Al "Finalizar pedido" hace POST /api/pedidos  →  se guarda en BD.
  3. El backend responde con el no_pedido creado + URL de WhatsApp prellenada.
  4. El frontend abre esa URL en una nueva pestaña.

Endpoints que maneja este controlador:
  POST   /api/pedidos                    → crear_pedido()
  GET    /api/pedidos                    → obtener_pedidos()        (admin)
  GET    /api/pedidos/usuario/<id>       → pedidos_por_usuario()    (cliente)
  GET    /api/pedidos/<no_pedido>        → obtener_pedido()
  PUT    /api/pedidos/<no_pedido>/estado → actualizar_estado_pedido()  (admin)
  DELETE /api/pedidos/<no_pedido>        → cancelar_pedido()
"""

from urllib.parse import quote
from datetime import date, timedelta

from database.conexion import db
from models.models import Pedido, DetallePedido, Producto, Usuario
from controllers.config_controller import get_wa_number


# ─────────────────────────────────────────────────────────────────────────────
# CREAR PEDIDO  (el más importante)
# ─────────────────────────────────────────────────────────────────────────────
def crear_pedido(data: dict):
    """
    Body esperado:
    {
      "id_usuario"       : 3,
      "ubicacion_entrega": "Zona 1, Xela",       ← dirección de entrega
      "fecha_entrega"    : "2026-06-01",          ← opcional; default: hoy + 3 días
      "items": [
        { "id_producto": 1, "cantidad": 2 },
        { "id_producto": 4, "cantidad": 1 }
      ]
    }

    Respuesta exitosa (201):
    {
      "message"    : "Pedido creado correctamente.",
      "no_pedido"  : 12,
      "monto_total": 380.00,
      "whatsapp_url": "https://wa.me/502...?text=..."
    }
    """

    # ── 1. Validar campos obligatorios ────────────────────────────────────────
    id_usuario = data.get("id_usuario")
    items      = data.get("items") or []
    ubicacion  = (data.get("ubicacion_entrega") or "").strip()

    if not id_usuario:
        return {"message": "Se requiere id_usuario."}, 400
    if not items:
        return {"message": "El carrito está vacío."}, 400
    if not ubicacion:
        return {"message": "Se requiere la dirección de entrega."}, 400

    # ── 2. Verificar que el usuario existe ────────────────────────────────────
    usuario = Usuario.query.get(id_usuario)
    if not usuario:
        return {"message": "Usuario no encontrado."}, 404

    # ── 3. Procesar cada ítem: validar producto, calcular subtotales ──────────
    detalles_a_crear = []
    monto_total      = 0.0

    for item in items:
        id_producto = item.get("id_producto")
        cantidad    = int(item.get("cantidad") or 0)

        if not id_producto or cantidad <= 0:
            return {"message": f"Ítem inválido: {item}"}, 400

        producto = Producto.query.filter_by(
            id_producto=id_producto, is_active=True
        ).first()

        # Fallback: si viene nombre en el ítem y no se encontró por ID, buscar por nombre
        if not producto:
            nombre_fallback = (item.get("nombre") or "").strip()
            if nombre_fallback:
                producto = Producto.query.filter(
                    Producto.nombre_producto.ilike(f"%{nombre_fallback}%"),
                    Producto.is_active == True
                ).first()

        if not producto:
            return {
                "message": f"Producto id={id_producto} no existe o está inactivo. "
                           f"Verifica que el producto esté registrado en la BD."
            }, 404

        precio_momento = float(producto.precio_unitario)
        subtotal       = round(precio_momento * cantidad, 2)
        monto_total   += subtotal

        detalles_a_crear.append({
            "id_producto"   : id_producto,
            "cantidad"      : cantidad,
            "precio_momento": precio_momento,
            "subtotal"      : subtotal,
            "nombre"        : producto.nombre_producto,   # solo para el mensaje WA
        })

    monto_total = round(monto_total, 2)

    # ── 4. Fecha de entrega ───────────────────────────────────────────────────
    fecha_entrega_raw = data.get("fecha_entrega")
    if fecha_entrega_raw:
        try:
            fecha_entrega = date.fromisoformat(fecha_entrega_raw)
        except ValueError:
            return {"message": "Formato de fecha_entrega inválido (YYYY-MM-DD)."}, 400
    else:
        fecha_entrega = date.today() + timedelta(days=3)   # default: 3 días

    # ── 5. Insertar Pedido + Detalles en una transacción ─────────────────────
    try:
        nuevo_pedido = Pedido(
            id_usuario       = id_usuario,
            tipo_pedido      = "Web",
            fecha_entrega    = fecha_entrega,
            monto_anticipo   = 0,
            monto_total      = monto_total,
            estado_pedido    = "Pendiente",
            ubicacion_entrega= ubicacion,
        )
        db.session.add(nuevo_pedido)
        db.session.flush()   # obtiene no_pedido sin hacer commit aún

        for d in detalles_a_crear:
            detalle = DetallePedido(
                no_pedido      = nuevo_pedido.no_pedido,
                id_producto    = d["id_producto"],
                cantidad       = d["cantidad"],
                precio_momento = d["precio_momento"],
                subtotal       = d["subtotal"],
            )
            db.session.add(detalle)

        db.session.commit()

    except Exception as e:
        db.session.rollback()
        return {"message": f"Error al guardar el pedido: {str(e)}"}, 500

    # ── 6. Construir mensaje de WhatsApp ─────────────────────────────────────
    telefono = ""  # Usuario base no tiene telefono; se omite en el mensaje

    wa_url = _construir_url_whatsapp(
        no_pedido     = nuevo_pedido.no_pedido,
        cliente       = usuario.nombre_completo,
        telefono      = telefono,
        detalles      = detalles_a_crear,
        monto_total   = monto_total,
        fecha_entrega = str(fecha_entrega),
        ubicacion     = ubicacion,
    )

    # ── 7. Respuesta ──────────────────────────────────────────────────────────
    return {
        "message"     : "Pedido creado correctamente.",
        "no_pedido"   : nuevo_pedido.no_pedido,
        "monto_total" : monto_total,
        "whatsapp_url": wa_url,
    }, 201


# ─────────────────────────────────────────────────────────────────────────────
# LISTAR TODOS (admin)
# ─────────────────────────────────────────────────────────────────────────────
def obtener_pedidos():
    """Devuelve todos los pedidos con sus detalles. Solo para admin."""
    pedidos = Pedido.query.order_by(Pedido.fecha_solicitud.desc()).all()
    resultado = []
    for p in pedidos:
        d = p.to_dict()
        d["detalles"] = [det.to_dict() for det in p.detalles]
        resultado.append(d)
    return resultado, 200


# ─────────────────────────────────────────────────────────────────────────────
# PEDIDOS DE UN USUARIO
# ─────────────────────────────────────────────────────────────────────────────
def pedidos_por_usuario(id_usuario: int):
    """Devuelve el historial de pedidos de un usuario específico."""
    usuario = Usuario.query.get(id_usuario)
    if not usuario:
        return {"message": "Usuario no encontrado."}, 404

    pedidos = (
        Pedido.query
        .filter_by(id_usuario=id_usuario)
        .order_by(Pedido.fecha_solicitud.desc())
        .all()
    )
    resultado = []
    for p in pedidos:
        d = p.to_dict()
        d["detalles"] = [det.to_dict() for det in p.detalles]
        resultado.append(d)
    return resultado, 200


# ─────────────────────────────────────────────────────────────────────────────
# OBTENER UN PEDIDO
# ─────────────────────────────────────────────────────────────────────────────
def obtener_pedido(no_pedido: int):
    pedido = Pedido.query.get(no_pedido)
    if not pedido:
        return {"message": "Pedido no encontrado."}, 404

    resultado = pedido.to_dict()
    resultado["detalles"] = [d.to_dict() for d in pedido.detalles]
    return resultado, 200


# ─────────────────────────────────────────────────────────────────────────────
# ACTUALIZAR ESTADO (admin: Pendiente → En preparación → Listo → Entregado)
# ─────────────────────────────────────────────────────────────────────────────
ESTADOS_VALIDOS = {"Pendiente", "En preparación", "Listo", "Entregado", "Cancelado"}

def actualizar_estado_pedido(no_pedido: int, data: dict):
    pedido = Pedido.query.get(no_pedido)
    if not pedido:
        return {"message": "Pedido no encontrado."}, 404

    nuevo_estado = (data.get("estado_pedido") or "").strip()
    if nuevo_estado not in ESTADOS_VALIDOS:
        return {
            "message": f"Estado inválido. Opciones: {', '.join(ESTADOS_VALIDOS)}"
        }, 400

    # Anticipo opcional
    anticipo = data.get("monto_anticipo")
    if anticipo is not None:
        try:
            pedido.monto_anticipo = float(anticipo)
        except (TypeError, ValueError):
            return {"message": "monto_anticipo debe ser numérico."}, 400

    pedido.estado_pedido = nuevo_estado
    db.session.commit()
    return {"message": "Estado actualizado.", "pedido": pedido.to_dict()}, 200


# ─────────────────────────────────────────────────────────────────────────────
# CANCELAR PEDIDO
# ─────────────────────────────────────────────────────────────────────────────
def cancelar_pedido(no_pedido: int):
    pedido = Pedido.query.get(no_pedido)
    if not pedido:
        return {"message": "Pedido no encontrado."}, 404
    if pedido.estado_pedido == "Entregado":
        return {"message": "No se puede cancelar un pedido ya entregado."}, 409

    # Borrado lógico: marcamos como Cancelado en lugar de DELETE
    pedido.estado_pedido = "Cancelado"
    db.session.commit()
    return {"message": "Pedido cancelado."}, 200


# ─────────────────────────────────────────────────────────────────────────────
# HELPER: construir URL de WhatsApp
# ─────────────────────────────────────────────────────────────────────────────
def _construir_url_whatsapp(
    no_pedido, cliente, telefono, detalles, monto_total, fecha_entrega, ubicacion
) -> str:
    """
    Construye la URL wa.me con el mensaje del pedido ya codificado.
    El mensaje se ve así en WhatsApp:

        🥐 *Nuevo Pedido #12 - Panadería Gourmet Quetzalteca*

        👤 Cliente: María García
        📱 Teléfono: +502 5555 1234

        🧾 Detalle:
          • Pastel de Bodas x1 = Q.800.00
          • Macarons Franceses x4 = Q.120.00

        💰 *Total: Q.920.00*
        📅 Fecha de entrega solicitada: 2026-06-01
        📍 Dirección: Zona 1, Xela

        Por favor confirmar disponibilidad y forma de pago.
    """
    lineas = [
        f"🥐 *Nuevo Pedido #{no_pedido} - Panadería Gourmet Quetzalteca*\n",
        f"👤 Cliente: {cliente}",
    ]
    if telefono:
        lineas.append(f"📱 Teléfono: {telefono}")

    lineas.append("\n🧾 Detalle:")
    for d in detalles:
        lineas.append(
            f"  • {d['nombre']} x{d['cantidad']} = Q.{d['subtotal']:.2f}"
        )

    lineas += [
        f"\n💰 *Total: Q.{monto_total:.2f}*",
        f"📅 Entrega solicitada: {fecha_entrega}",
        f"📍 Dirección: {ubicacion}",
        "\nPor favor confirmar disponibilidad y forma de pago. ¡Gracias!",
    ]

    mensaje = "\n".join(lineas)
    return f"https://wa.me/{get_wa_number()}?text={quote(mensaje)}"
