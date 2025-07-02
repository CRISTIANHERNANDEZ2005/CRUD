import os
import sys
from dotenv import load_dotenv

# Configura el path para importar módulos correctamente
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.firestore_db import get_firestore_client
from src.services.product_service import ProductService, CategoryService

def seed_database():
    print("Inicializando base de datos...")
    db = get_firestore_client()  # Esto ejecutará las migraciones
    
    try:
        # 1. Primero crear las categorías
        print("\nCreando categorías de ejemplo...")
        sample_categories = CategoryService.get_sample_categories()
        
        # Crear categorías asegurando los IDs específicos
        for category in sample_categories:
            category_id = category.pop("id")  # Extraemos el ID del diccionario
            doc_ref = db.collection("categories").document(category_id)
            doc_ref.set(category)
            print(f"- Categoría creada: {category_id}")

        # 2. Luego crear los productos
        print("\nCreando productos de ejemplo...")
        sample_products = ProductService.get_sample_products()
        result = ProductService.batch_create(sample_products)
        
        print(f"\n✅ Se insertaron {len(result)} productos:")
        for product in result:
            print(f"- {product['name']} (Categoría: {product['category_id']})")

        print("\n🎉 Base de datos inicializada exitosamente!")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        # Opcional: imprimir traza completa para debugging
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    load_dotenv()
    seed_database()