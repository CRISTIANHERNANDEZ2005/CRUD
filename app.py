from dotenv import load_dotenv
load_dotenv()

import firebase_admin
from firebase_admin import credentials
import os
from flask import Flask
app = Flask(__name__)

# Ruta al archivo secreto en Render
cred = credentials.Certificate('firestore.json')
firebase_admin.initialize_app(cred)


print("GOOGLE_APPLICATION_CREDENTIALS:", os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"))
print("GOOGLE_APPLICATION_CREDENTIALS_JSON:", os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_JSON"))
print("JWT_SECRET:", os.environ.get("JWT_SECRET"))

from src import create_app

app = create_app()

"""
git add .
git commit -m "eliminar correctamente"
git push -u origin main --force
"""

# Gunicorn busca la variable 'app' por defecto
# if __name__ == "__main__":
#     app.run(debug=True)