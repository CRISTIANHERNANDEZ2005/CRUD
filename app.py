from dotenv import load_dotenv
load_dotenv()

import os
print("GOOGLE_APPLICATION_CREDENTIALS:", os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"))
print("GOOGLE_APPLICATION_CREDENTIALS_JSON:", os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_JSON"))
print("JWT_SECRET:", os.environ.get("JWT_SECRET"))

from src import create_app

app = create_app()

# Gunicorn busca la variable 'app' por defecto
# if __name__ == "__main__":
#     app.run(debug=True)