import os

class Config:
    FIREBASE_CREDENTIALS = os.environ.get("GOOGLE_CREDENTIALS_FILE")
    PROJECT_ID = "product-shelf-app"