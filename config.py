import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'una_chiave_segreta_casuale'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///crm_dermatologa.db'  # Utilizza SQLite per il database
    SQLALCHEMY_TRACK_MODIFICATIONS = False
