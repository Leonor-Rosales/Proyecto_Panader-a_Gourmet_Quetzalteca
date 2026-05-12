"""
controllers/producto_controller.py
CRUD para la tabla 'producto' (pastelería — panel admin).

CAMBIOS:
- obtener_productos()  → filtra solo is_active=True
- obtener_producto()   → verifica is_active
- eliminar_producto()  → SOFT DELETE: pone is_active=False en lugar de DELETE
- actualizar_producto() → permite editar todos los campos (fix botón Modificar)
"""

from database.conexion import db
from models.models import Producto, Categoria


def obtener_productos():
    """Devuelve solo productos activos (is_active=True)."""
    productos = (Producto.query
                 .filter_by(is_active=True)
                 .order_by(Producto.id_producto)
                 .all())
    return [p.to_dict() for p in productos], 200


def obtener_producto(id_producto: int):
    p = Producto.query.get(id_producto)
    if not p or not p.is_active:
        return {"message": "Producto no encontrado."}, 404
    return p.to_dict(), 200


def crear_producto(data: dict):
    requeridos = ["nombre_producto", "descripcion", "precio_unitario", "id_categoria"]
    for campo in requeridos:
        if not data.get(campo):
            return {"message": f"El campo '{campo}' es obligatorio."}, 400

    nuevo = Producto(
        nombre_producto = data["nombre_producto"],
        descripcion     = data["descripcion"],
        precio_unitario = float(data["precio_unitario"]),
        id_categoria    = int(data["id_categoria"]),
        imagen          = data.get("imagen"),
        is_active       = True,
    )
    db.session.add(nuevo)
    db.session.commit()
    return {"message": "Producto creado.", "producto": nuevo.to_dict()}, 201


def actualizar_producto(id_producto: int, data: dict):
    """
    FIX botón Modificar: acepta y actualiza todos los campos del formulario.
    Solo modifica los campos que vienen en el payload (PATCH semántico con PUT).
    """
    p = Producto.query.get(id_producto)
    if not p or not p.is_active:
        return {"message": "Producto no encontrado."}, 404

    if "nombre_producto" in data: p.nombre_producto = data["nombre_producto"]
    if "descripcion"     in data: p.descripcion     = data["descripcion"]
    if "precio_unitario" in data: p.precio_unitario = float(data["precio_unitario"])
    if "id_categoria"    in data: p.id_categoria    = int(data["id_categoria"])
    if "imagen"          in data: p.imagen          = data["imagen"]

    db.session.commit()
    return {"message": "Producto actualizado.", "producto": p.to_dict()}, 200


def eliminar_producto(id_producto: int):
    """
    SOFT DELETE: marca el producto como inactivo en lugar de borrarlo físicamente.
    Preserva la integridad referencial con detalle_pedido.
    """
    p = Producto.query.get(id_producto)
    if not p or not p.is_active:
        return {"message": "Producto no encontrado."}, 404

    p.is_active = False          # ← UPDATE en lugar de DELETE
    db.session.commit()
    return {"message": "Producto desactivado correctamente."}, 200
