import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a_default_secret_key'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or 'app/static/uploads/documents'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # Limit upload size to 16 MB
    DEBUG = os.environ.get('DEBUG', 'False').lower() in ('true', '1', 't')