from datetime import datetime
import logging
from firebase_admin import firestore
import bcrypt

logger = logging.getLogger(__name__)

def run_migrations(db):  # <-- Recibir db como parámetro
    """Ejecuta todas las migraciones pendientes"""
    try:
        migrations_ref = db.collection("_migrations")
        executed = [doc.id for doc in migrations_ref.stream()]
        
        all_migrations = sorted(_get_migrations(), key=lambda x: x["version"])
        
        for migration in all_migrations:
            if migration["version"] not in executed:
                _execute_migration(migration, db)  # <-- Pasar db
                migrations_ref.document(migration["version"]).set({
                    "executed_at": datetime.now(),
                    "description": migration["description"]
                })
                logger.info(f"Migración ejecutada: {migration['version']}")
                
    except Exception as e:
        logger.error(f"Error en migraciones: {str(e)}")
        raise

def _get_migrations():
    return [
        {
            "version": "1.0-initial-schema",
            "description": "Creación de colecciones base",
            "up": _initial_schema
        },
        {
            "version": "1.1-add-product-fields",
            "description": "Agrega campos requeridos a productos",
            "up": _add_product_fields
        },
        {
            "version": "1.2-create-users-collection",
            "description": "Crea la colección de usuarios y un usuario admin de ejemplo",
            "up": _create_users_collection
        }
    ]

def _add_product_fields(db):
    """Migración para agregar campos a productos"""
    products = db.collection("products").stream()
    
    for product in products:
        data = product.to_dict()
        updates = {}
        
        if "description" not in data:
            updates["description"] = ""
        
        if "created_at" not in data:
            updates["created_at"] = firestore.SERVER_TIMESTAMP
        
        if updates:
            product.reference.update(updates)

def _execute_migration(migration, db):  # <-- Recibir db
    try:
        migration["up"](db)  # <-- Pasar db
    except Exception as e:
        logger.error(f"Fallo en migración {migration['version']}: {str(e)}")
        raise

def _initial_schema(db):  # <-- Recibir db como parámetro
    """Migración inicial"""
    collections = ["products", "categories"]
    
    for collection in collections:
        if not db.collection(collection).limit(1).get():
            db.collection(collection).document("_init").set({
                "description": f"Colección inicial para {collection}",
                "created_at": datetime.now()
            })

    sample_categories = [
        {"name": "Electrónicos", "description": "Dispositivos electrónicos"},
        {"name": "Ropa", "description": "Prendas de vestir"}
    ]
    
    for category in sample_categories:
        if not db.collection("categories").where("name", "==", category["name"]).get():
            db.collection("categories").add(category)

def _create_users_collection(db):
    users_ref = db.collection("users")
    # Si la colección está vacía, crear usuario admin
    if not users_ref.limit(1).get():
        password = "admin123"
        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        admin_data = {
            "email": "admin@admin.com",
            "password": hashed.decode("utf-8"),
            "created_at": datetime.now().isoformat(),
            "role": "admin"
        }
        users_ref.document().set(admin_data)