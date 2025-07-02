from datetime import datetime
from typing import Dict, Any
from firebase_admin import firestore

SCHEMAS = {
    "products": {
        "required_fields": ["name", "price", "category_id"],
        "fields": {
            "name": {"type": str, "max_length": 100},
            "price": {"type": (int, float), "min_value": 0},
            "category_id": {"type": str},
            "description": {"type": str, "required": False, "max_length": 500},
            "created_at": {"type": datetime, "auto": True},
            "updated_at": {"type": datetime, "auto": True}
        }
    },
    "categories": {
        "required_fields": ["name"],
        "fields": {
            "name": {"type": str, "max_length": 50},
            "description": {"type": str, "required": False},
            "created_at": {"type": datetime, "auto": True},
            "updated_at": {"type": datetime, "auto": True}
        }
    }
}

def validate_document(collection: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Valida un documento según el esquema definido"""
    if collection not in SCHEMAS:
        raise ValueError(f"Colección {collection} no tiene esquema definido")
    
    schema = SCHEMAS[collection]
    validated_data = {}
    
    # Validar campos requeridos
    for field in schema["required_fields"]:
        if field not in data:
            raise ValueError(f"Campo requerido faltante: {field}")
    
    # Validar cada campo
    for field, config in schema["fields"].items():
        if field in data:
            value = data[field]
            
            # Validar tipo
            if not isinstance(value, config["type"]):
                if not (isinstance(config["type"], tuple) and isinstance(value, config["type"])):
                    raise TypeError(f"Campo {field} debe ser de tipo {config['type']}")
            
            # Validar longitud máxima
            if "max_length" in config and len(str(value)) > config["max_length"]:
                raise ValueError(f"Campo {field} excede el máximo de {config['max_length']} caracteres")
            
            # Validar valor mínimo
            if "min_value" in config and value < config["min_value"]:
                raise ValueError(f"Campo {field} debe ser mayor o igual a {config['min_value']}")
            
            validated_data[field] = value
        elif config.get("required", True):
            raise ValueError(f"Campo requerido faltante: {field}")
    
    # Campos automáticos
    now = firestore.SERVER_TIMESTAMP
    if "created_at" in schema["fields"] and "created_at" not in validated_data:
        validated_data["created_at"] = now
    if "updated_at" in schema["fields"]:
        validated_data["updated_at"] = now
    
    return validated_data