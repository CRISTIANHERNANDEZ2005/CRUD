from flask import Blueprint, request, jsonify
from src.services.product_service import ProductService
from werkzeug.exceptions import BadRequest
from src.services.auth import require_jwt
from typing import List, Dict

products_bp = Blueprint('products', __name__)

@products_bp.route('/', methods=['GET'])
@require_jwt
def get_products():
    try:
        include_category = request.args.get('include_category', 'false').lower() == 'true'
        products = ProductService.get_all(include_category=include_category)
        return jsonify(products), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@products_bp.route('/', methods=['POST'])
@require_jwt
def create_product():
    try:
        if not request.is_json:
            return jsonify({"error": "Se esperaba un JSON"}), 400

        data = request.get_json()
        if not data or not isinstance(data, dict):
            return jsonify({"error": "Datos vacíos o formato incorrecto"}), 400

        # Validar campos requeridos antes de pasar al servicio
        required_fields = ["name", "price", "category_id"]
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({"error": f"Faltan campos requeridos: {', '.join(missing_fields)}"}), 400

        # Validaciones básicas de tipos y longitudes
        if not isinstance(data["name"], str) or len(data["name"]) > 100:
            return jsonify({"error": "El nombre debe ser un string de máximo 100 caracteres"}), 400
        if not isinstance(data["price"], (int, float)) or data["price"] <= 0:
            return jsonify({"error": "El precio debe ser un número positivo"}), 400
        if "description" in data and (not isinstance(data["description"], str) or len(data["description"]) > 500):
            return jsonify({"error": "La descripción debe ser un string de máximo 500 caracteres"}), 400

        category_ref = ProductService._get_db().collection("categories").document(data["category_id"])
        if not category_ref.get().exists:
            raise ValueError(f"La categoría '{data['category_id']}' no existe. Por favor, crea la categoría antes de asignarla a un producto.")

        new_product = ProductService.create(data)
        return jsonify(new_product), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except BadRequest as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@products_bp.route('/<product_id>', methods=['GET'])
@require_jwt
def get_product_by_id(product_id):
    try:
        include_category = request.args.get('include_category', 'false').lower() == 'true'
        product = ProductService.get_by_id(product_id, include_category=include_category)
        if not product:
            return jsonify({"error": "Producto no encontrado"}), 404
        return jsonify(product), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@products_bp.route('/<product_id>', methods=['PUT'])
@require_jwt
def update_product(product_id):
    try:
        if not request.is_json:
            return jsonify({"error": "Se esperaba un JSON en la solicitud"}), 400

        data = request.get_json()
        if not data or not isinstance(data, dict):
            return jsonify({"error": "Datos vacíos o formato incorrecto, se esperaba un objeto JSON"}), 400

        # Validar campos requeridos
        required_fields = ["name", "price", "category_id"]
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({"error": f"Faltan campos requeridos: {', '.join(missing_fields)}"}), 400

        # Validaciones de tipos y longitudes
        if not isinstance(data["name"], str) or len(data["name"]) > 100:
            return jsonify({"error": "El nombre debe ser un string de máximo 100 caracteres"}), 400
        if not isinstance(data["price"], (int, float)) or data["price"] <= 0:
            return jsonify({"error": "El precio debe ser un número positivo"}), 400
        if "description" in data and (not isinstance(data["description"], str) or len(data["description"]) > 500):
            return jsonify({"error": "La descripción debe ser un string de máximo 500 caracteres"}), 400

        updated_product = ProductService.update(product_id, data)
        return jsonify(updated_product), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except BadRequest as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@products_bp.route('/<product_id>', methods=['DELETE'])
@require_jwt
def delete_product(product_id):
    try:
        result = ProductService.delete(product_id)
        return jsonify({"message": "Producto eliminado"}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@products_bp.route('/seed', methods=['POST'])
def seed_products():
    """Endpoint para poblar la base de datos con productos de ejemplo"""
    try:
        sample_products = ProductService.get_sample_products()
        created_products = ProductService.batch_create(sample_products)
        return jsonify({
            "message": f"{len(created_products)} productos creados",
            "products": created_products
        }), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@products_bp.route('/batch', methods=['POST'])
@require_jwt
def create_batch_products():
    """Endpoint para crear múltiples productos"""
    try:
        products_data = request.get_json()
        if not isinstance(products_data, list):
            raise BadRequest("Se esperaba una lista de productos")
        
        created_products = ProductService.batch_create(products_data)
        return jsonify({
            "message": f"{len(created_products)} productos creados",
            "products": created_products
        }), 201
    except BadRequest as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@products_bp.route('/<product_id>/estado', methods=['PATCH'])
@require_jwt
def set_product_status(product_id):
    try:
        data = request.get_json()
        status = data.get('estado')
        if status not in ['activo', 'inactivo']:
            return jsonify({'error': 'Estado inválido, debe ser "activo" o "inactivo"'}), 400
        result = ProductService.set_status(product_id, status)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500