import bcrypt
import jwt
from datetime import datetime, timedelta
from google.cloud import firestore
from .firestore_db import get_firestore_client
import os
from flask import request
from functools import wraps
from .schemas import is_valid_email, is_strong_password

JWT_SECRET = os.environ.get('JWT_SECRET', 'supersecretkey')
JWT_ALGORITHM = 'HS256'
JWT_EXP_DELTA_SECONDS = 3600

class AuthService:
    _db = None

    @classmethod
    def _get_db(cls):
        if cls._db is None:
            cls._db = get_firestore_client()
        return cls._db

    @classmethod
    def register(cls, email: str, password: str) -> dict:
        if not is_valid_email(email):
            raise ValueError('El email no tiene un formato válido')
        if not is_strong_password(password):
            raise ValueError('La contraseña debe tener al menos 6 caracteres, una letra y un número')
        users_ref = cls._get_db().collection('users')
        if users_ref.where('email', '==', email).get():
            raise ValueError('El usuario ya existe')
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        user_data = {
            'email': email,
            'password': hashed.decode('utf-8'),
            'created_at': datetime.utcnow().isoformat()
        }
        user_ref = users_ref.document()
        user_ref.set(user_data)
        return {'id': user_ref.id, 'email': email}

    @classmethod
    def login(cls, email: str, password: str) -> str:
        if not is_valid_email(email):
            raise ValueError('El email no tiene un formato válido')
        users_ref = cls._get_db().collection('users')
        user_docs = users_ref.where('email', '==', email).get()
        if not user_docs:
            raise ValueError('Usuario o contraseña incorrectos')
        user = user_docs[0].to_dict()
        if not bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
            raise ValueError('Usuario o contraseña incorrectos')
        payload = {
            'email': email,
            'exp': datetime.utcnow() + timedelta(seconds=JWT_EXP_DELTA_SECONDS)
        }
        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        return token

    @staticmethod
    def verify_token(token: str) -> dict:
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise ValueError('Token expirado')
        except jwt.InvalidTokenError:
            raise ValueError('Token inválido')

def require_jwt(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', None)
        if not auth_header or not auth_header.startswith('Bearer '):
            return {'error': 'Token requerido'}, 401
        token = auth_header.split(' ')[1]
        try:
            payload = AuthService.verify_token(token)
            request.user = payload
        except Exception as e:
            return {'error': str(e)}, 401
        return f(*args, **kwargs)
    return decorated 