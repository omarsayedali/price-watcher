import os

class Config:
    # This secret key is for security (cookies/sessions)
    SECRET_KEY = 'dev-secret-key'
    
    # DATABASE CONFIGURATION
    # If we are on Railway, use their DB.
    # If we are on your laptop, use a local file named 'site.db'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///site.db'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False