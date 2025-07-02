from src.services.firestore_db import get_firestore_client
from src.services.migrations import run_migrations

if __name__ == "__main__":
    print("Ejecutando migraciones...")
    db = get_firestore_client()
    run_migrations(db)
    print("Migraciones completadas")