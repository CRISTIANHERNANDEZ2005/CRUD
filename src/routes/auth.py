from flask import Blueprint, request, jsonify
from ..services.auth import AuthService

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json(force=True)
        if not data:
            return jsonify({'error': 'No se proporcionaron datos'}), 400

        email = data.get('email')
        password = data.get('password')
        if not email or not password:
            return jsonify({'error': 'Email y password requeridos'}), 400

        user = AuthService.register(email, password)
        return jsonify({'message': 'Usuario registrado', 'user': user}), 201

    except ValueError as e:
        # Errores de validación esperados
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        # Errores inesperados, mostrar excepción para debug
        return jsonify({'error': 'Error interno', 'exception': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    if not email or not password:
        return jsonify({'error': 'Email y password requeridos'}), 400
    try:
        token = AuthService.login(email, password)
        return jsonify({'access_token': token}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 401 