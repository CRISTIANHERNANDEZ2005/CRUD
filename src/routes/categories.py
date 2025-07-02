from flask import Blueprint, request, jsonify
from src.services.product_service import CategoryService
from werkzeug.exceptions import BadRequest, NotFound
from src.services.auth import require_jwt

categories_bp = Blueprint('categories', __name__)

@categories_bp.route('/', methods=['GET'])
@require_jwt
def get_categories():
    try:
        include_products = request.args.get('include_products', 'false').lower() == 'true'
        categories = CategoryService.get_all(include_products=include_products)
        return jsonify(categories), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@categories_bp.route('/', methods=['POST'])
@require_jwt
def create_category():
    try:
        if not request.is_json:
            return jsonify({"error": "Se esperaba un JSON"}), 400

        data = request.get_json()
        if not data or not isinstance(data, dict):
            return jsonify({"error": "Datos vacíos o formato incorrecto"}), 400

        # Validar campos requeridos
        required_fields = ["name"]
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({"error": f"Faltan campos requeridos: {', '.join(missing_fields)}"}), 400

        # Validaciones de tipos y longitudes
        if not isinstance(data["name"], str) or len(data["name"]) > 100:
            return jsonify({"error": "El nombre debe ser un string de máximo 100 caracteres"}), 400
        if "description" in data and (not isinstance(data["description"], str) or len(data["description"]) > 500):
            return jsonify({"error": "La descripción debe ser un string de máximo 500 caracteres"}), 400

        new_category = CategoryService.create(data)
        return jsonify(new_category), 201
    except BadRequest as e:
        return jsonify({"error": str(e)}), 400
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@categories_bp.route('/<category_id>', methods=['GET'])
@require_jwt
def get_category(category_id):
    try:
        category = CategoryService.get_by_id(category_id)
        if not category:
            raise NotFound("Categoría no encontrada")
        return jsonify(category), 200
    except NotFound as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@categories_bp.route('/<category_id>', methods=['PUT'])
@require_jwt
def update_category(category_id):
    try:
        data = request.get_json()
        updated_category = CategoryService.update(category_id, data)
        return jsonify(updated_category), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@categories_bp.route('/<category_id>', methods=['DELETE'])
@require_jwt
def delete_category(category_id):
    try:
        success = CategoryService.delete(category_id)
        return jsonify({"message": "Categoría eliminada"}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500