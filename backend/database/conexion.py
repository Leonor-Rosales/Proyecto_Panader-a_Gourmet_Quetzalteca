from flask_sqlalchemy import SQLAlchemy

# Instancia única de SQLAlchemy — se comparte con todos los modelos
db = SQLAlchemy()


def init_db(app):
    """
    Inicializa la extensión SQLAlchemy con la aplicación Flask.
    Llamar desde app.py después de configurar app.config.
    """
    db.init_app(app)
    with app.app_context():
        try:
            db.engine.connect()
            print("✅  Conexión a MySQL exitosa.")
        except Exception as e:
            print(f"Error al conectar con MySQL: {e}")
            raise