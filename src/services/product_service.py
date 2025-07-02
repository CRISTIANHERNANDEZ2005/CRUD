from firebase_admin import firestore
from .firestore_db import get_firestore_client
from typing import List, Dict, Optional
from datetime import datetime
import json
from google.cloud.firestore_v1 import SERVER_TIMESTAMP

class ProductService:
    _db = None

    @classmethod
    def _get_db(cls):
        if cls._db is None:
            cls._db = get_firestore_client()
        return cls._db

    @classmethod
    def _serialize_firestore_data(cls, data: Dict) -> Dict:
        """Convierte datos de Firestore a JSON serializable"""
        serialized = {}
        for key, value in data.items():
            if isinstance(value, (str, int, float, bool, list, dict)) or value is None:
                serialized[key] = value
            elif isinstance(value, datetime):
                serialized[key] = value.isoformat()
            elif hasattr(value, '_timestamp'):  # Para SERVER_TIMESTAMP
                serialized[key] = datetime.now().isoformat()
        return serialized

    @classmethod
    def validate_product_data(cls, data: Dict) -> Dict:
        required_fields = ["name", "price", "category_id"]
        
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Campo requerido faltante: {field}")
        
        if not isinstance(data["name"], str) or len(data["name"]) > 100:
            raise ValueError("Nombre debe ser string (max 100 caracteres)")
        
        if not isinstance(data["price"], (int, float)) or data["price"] <= 0:
            raise ValueError("Precio debe ser número positivo")
        
        # Verificar categoría existente o crear "uncategorized" si no existe
        category_ref = cls._get_db().collection("categories").document(data["category_id"])
        category_doc = category_ref.get()
        if not category_doc.exists:
            uncategorized_ref = cls._get_db().collection("categories").document("uncategorized")
            uncategorized_doc = uncategorized_ref.get()
            if not uncategorized_doc.exists:
                uncategorized_ref.set({
                    "name": "Uncategorized",
                    "description": "Productos sin categoría asignada",
                    "created_at": SERVER_TIMESTAMP,
                    "updated_at": SERVER_TIMESTAMP,
                    "estado": "activo"
                })
            data["category_id"] = "uncategorized"
        
        if "description" in data and (not isinstance(data["description"], str) or len(data["description"]) > 500):
            raise ValueError("Descripción debe ser string (max 500 caracteres)")
        
        validated_data = data.copy()
        validated_data["created_at"] = SERVER_TIMESTAMP
        validated_data["updated_at"] = SERVER_TIMESTAMP
        if "estado" not in validated_data:
            validated_data["estado"] = "activo"
        
        return validated_data

    @classmethod
    def create(cls, data: Dict) -> Dict:
        validated_data = cls.validate_product_data(data)
        doc_ref = cls._get_db().collection("products").document()
        doc_ref.set(validated_data)
        
        # Obtener datos serializables
        product_data = {"id": doc_ref.id, **cls._serialize_firestore_data(validated_data)}
        
        # Obtener categoría relacionada
        category = cls._get_db().collection("categories").document(validated_data["category_id"]).get()
        if category.exists:
            product_data["category"] = {"id": category.id, **cls._serialize_firestore_data(category.to_dict())}
        
        return product_data

    @classmethod
    def update(cls, product_id: str, data: Dict) -> Dict:
        """Actualizar un producto existente con validación de categoría"""
        doc_ref = cls._get_db().collection("products").document(product_id)
        
        doc = doc_ref.get()
        
        if not doc.exists:
            raise ValueError("Producto no encontrado")
        
        if doc.to_dict().get("estado") == "inactivo":
            raise ValueError("No se puede modificar un producto inactivo")
        
        validated_data = cls.validate_product_data(data)
        validated_data["updated_at"] = SERVER_TIMESTAMP
        
        doc_ref.update(validated_data)
        
        # Obtener datos actualizados con categoría
        updated_doc = doc_ref.get()
        product_data = {"id": updated_doc.id, **updated_doc.to_dict()}
        
        category = cls._get_db().collection("categories").document(validated_data["category_id"]).get()
        if category.exists:
            product_data["category"] = {"id": category.id, **category.to_dict()}
        
        return product_data

    @classmethod
    def get_by_category(cls, category_id: str) -> List[Dict]:
        """Obtener todos los productos de una categoría específica"""
        category_doc = cls._get_db().collection("categories").document(category_id).get()
        if not category_doc.exists:
            raise ValueError("Categoría no encontrada")
        
        products_ref = cls._get_db().collection("products")
        query = products_ref.where("category_id", "==", category_id).where("estado", "==", "activo")
        
        return [{"id": doc.id, **doc.to_dict()} for doc in query.stream()] 

    @classmethod
    def delete(cls, product_id: str) -> bool:
        """Eliminar un producto"""
        doc_ref = cls._get_db().collection("products").document(product_id)
        
        doc = doc_ref.get()
        
        if not doc.exists:
            raise ValueError("Producto no encontrado")
        
        doc_ref.delete()
        return True

    @classmethod
    def batch_create(cls, products_data: List[Dict]) -> List[Dict]:
        """Crear múltiples productos con validación de categorías"""
        if not isinstance(products_data, list):
            raise TypeError("Se esperaba una lista de productos")
        
        batch = cls._get_db().batch()
        created_products = []
        
        # Primero validar todos los productos
        validated_products = []
        for product_data in products_data:
            validated_products.append(cls.validate_product_data(product_data))
        
        # Luego crear en batch
        for validated_data in validated_products:
            doc_ref = cls._get_db().collection("products").document()
            batch.set(doc_ref, validated_data)
            created_products.append({"id": doc_ref.id, **validated_data})
        
        batch.commit()
        return created_products

    @classmethod
    def get_sample_products(cls) -> List[Dict]:
        """Devuelve datos de ejemplo para inicializar la base de datos"""
        return [
            {
                "name": "Laptop Gamer",
                "price": 1299.99,
                "category_id": "electronics",
                "description": "Laptop de alto rendimiento para gaming"
            },
            {
                "name": "Smartphone Pro",
                "price": 899.99,
                "category_id": "electronics",
                "description": "Último modelo con triple cámara"
            },
            {
                "name": "Zapatillas Running",
                "price": 89.99,
                "category_id": "sports",
                "description": "Zapatillas profesionales para correr"
            }
        ]

    @classmethod
    def get_all(cls, include_category: bool = False) -> List[Dict]:
        products_ref = cls._get_db().collection("products")
        products = []
        for doc in products_ref.where("estado", "==", "activo").stream():
            product_data = {"id": doc.id, **doc.to_dict()}
            if include_category:
                category = cls._get_db().collection("categories").document(product_data.get("category_id")).get()
                if category.exists:
                    product_data["category"] = {"id": category.id, **category.to_dict()}
            products.append(product_data)
        return products

    @classmethod
    def get_by_id(cls, product_id: str, include_category: bool = False) -> Optional[Dict]:
        doc_ref = cls._get_db().collection("products").document(product_id)
        doc = doc_ref.get()
        if not doc.exists or doc.to_dict().get("estado") != "activo":
            return None
        product_data = {"id": doc.id, **doc.to_dict()}
        if include_category:
            category = cls._get_db().collection("categories").document(product_data.get("category_id")).get()
            if category.exists:
                product_data["category"] = {"id": category.id, **category.to_dict()}
        return product_data

    @classmethod
    def set_status(cls, product_id: str, status: str) -> Dict:
        """Cambia el estado de un producto individual (solo actualiza el campo 'estado')"""
        doc_ref = cls._get_db().collection("products").document(product_id)
        doc = doc_ref.get()
        if not doc.exists:
            raise ValueError("Producto no encontrado")
        doc_ref.update({"estado": status, "updated_at": SERVER_TIMESTAMP})
        return {"id": product_id, "estado": status}


class CategoryService:
    _db = None

    @classmethod
    def _get_db(cls):
        """Obtiene la instancia de Firestore (singleton)"""
        if cls._db is None:
            cls._db = get_firestore_client()
        return cls._db

    @classmethod
    def validate_category_data(cls, data: Dict) -> Dict:
        """Validación de datos de categoría"""
        if "name" not in data:
            raise ValueError("El campo 'name' es obligatorio")
        
        if not isinstance(data["name"], str) or len(data["name"]) > 50:
            raise ValueError("Nombre debe ser string (max 50 caracteres)")
        
        if "description" in data and (not isinstance(data["description"], str) or len(data["description"]) > 200):
            raise ValueError("Descripción debe ser string (max 200 caracteres)")
        
        validated_data = data.copy()
        validated_data["created_at"] = SERVER_TIMESTAMP
        validated_data["updated_at"] = SERVER_TIMESTAMP
        if "estado" not in validated_data:
            validated_data["estado"] = "activo"
        
        return validated_data

    @classmethod
    def create(cls, data: Dict) -> Dict:
        """Crear una nueva categoría"""
        validated_data = cls.validate_category_data(data)
        doc_ref = cls._get_db().collection("categories").document()
        doc_ref.set(validated_data)
        # Obtener los datos ya guardados (con los timestamps reales)
        doc = doc_ref.get()
        return {"id": doc.id, **doc.to_dict()}

    @classmethod
    def get_all(cls, include_products: bool = False) -> List[Dict]:
        """
        Obtener todas las categorías
        Args:
            include_products: Si True, incluye lista de productos en cada categoría
        """
        categories_ref = cls._get_db().collection("categories")
        categories = []
        
        for doc in categories_ref.stream():
            category_data = {"id": doc.id, **doc.to_dict()}
            
            if include_products:
                products = ProductService.get_by_category(doc.id)
                category_data["products"] = products
                category_data["products_count"] = len(products)
            
            categories.append(category_data)
        
        return categories

    @classmethod
    def get_by_id(cls, category_id: str, include_products: bool = False) -> Optional[Dict]:
        """Obtener una categoría por ID con opción de incluir productos"""
        doc_ref = cls._get_db().collection("categories").document(category_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            return None
            
        category_data = {"id": doc.id, **doc.to_dict()}
        
        if include_products:
            products = ProductService.get_by_category(doc.id)
            category_data["products"] = products
            category_data["products_count"] = len(products)
        
        return category_data

    @classmethod
    def update(cls, category_id: str, data: Dict) -> Dict:
        """Actualizar una categoría existente"""
        doc_ref = cls._get_db().collection("categories").document(category_id)
        
        doc = doc_ref.get()
        
        if not doc.exists:
            raise ValueError("Categoría no encontrada")
        
        if doc.to_dict().get("estado") == "inactivo":
            raise ValueError("No se puede modificar una categoría inactiva")
        
        validated_data = cls.validate_category_data(data)
        validated_data["updated_at"] = SERVER_TIMESTAMP
        
        doc_ref.update(validated_data)
        return {"id": doc_ref.id, **doc_ref.get().to_dict()}

    @classmethod
    def delete(cls, category_id: str) -> Dict:
        """
        Eliminar una categoría y reasignar sus productos a 'uncategorized'
        Retorna estadísticas de la operación
        """
        category_ref = cls._get_db().collection("categories").document(category_id)
        products_ref = cls._get_db().collection("products")
        
        doc = category_ref.get()
        
        if not doc.exists:
            raise ValueError("Categoría no encontrada")
        
        # Crear categoría uncategorized si no existe
        uncategorized = cls._get_db().collection("categories").document("uncategorized")
        uncategorized_doc = uncategorized.get()
        if not uncategorized_doc.exists:
            uncategorized.set({
                "name": "Uncategorized",
                "description": "Productos sin categoría asignada",
                "created_at": SERVER_TIMESTAMP,
                "updated_at": SERVER_TIMESTAMP,
                "estado": "activo"
            })
        
        # Reasignar productos y contar
        query = products_ref.where("category_id", "==", category_id)
        products = list(query.stream())
        products_reassigned = 0
        batch = cls._get_db().batch()
        for doc in products:
            batch.update(doc.reference, {"category_id": "uncategorized"})
            products_reassigned += 1
        batch.delete(category_ref)
        batch.commit()
        
        return {
            "message": f"Categoría eliminada y {products_reassigned} productos reasignados",
            "products_reassigned": products_reassigned,
            "uncategorized_id": "uncategorized"
        }

    @classmethod
    def get_sample_categories(cls) -> List[Dict]:
        """Devuelve categorías de ejemplo para inicializar la base de datos"""
        return [
            {
                "id": "electronics",
                "name": "Electrónicos",
                "description": "Dispositivos electrónicos y gadgets"
            },
            {
                "id": "sports",
                "name": "Deportes",
                "description": "Artículos deportivos y fitness"
            },
            {
                "id": "home",
                "name": "Hogar",
                "description": "Productos para el hogar"
            }
        ]

    @classmethod
    def set_status(cls, category_id: str, status: str) -> Dict:
        """Cambia el estado de una categoría (solo actualiza el campo 'estado')"""
        doc_ref = cls._get_db().collection("categories").document(category_id)
        doc = doc_ref.get()
        if not doc.exists:
            raise ValueError("Categoría no encontrada")
        doc_ref.update({"estado": status, "updated_at": SERVER_TIMESTAMP})
        return {"id": category_id, "estado": status}