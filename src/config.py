"""
Configuración centralizada del proyecto RUTEALO.
Carga variables de entorno desde claves.env usando python-dotenv.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno desde claves.env
load_dotenv('claves.env')

# --- RUTAS BASE ---
BASE_DIR = Path(__file__).parent.parent  # c:\...\RUTEALO
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

# Crear directorios si no existen
RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# --- MONGODB ATLAS ---
MONGO_URI = os.getenv('MONGO_URI', 'mongodb+srv://default:default@cluster0.mongodb.net/?appName=default')
DB_NAME = os.getenv('DB_NAME', 'RUTEALO_DB')

# Colecciones MongoDB
COLS = {
    "RAW": "materiales_crudos",
    "PERFIL": "usuario_perfil",
    "EXAM_INI": "examen_inicial",
    "RUTAS": "rutas_aprendizaje"
}

# --- GOOGLE GENERATIVE AI ---
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY', '')

# --- FLASK ---
SECRET_KEY = os.getenv('SECRET_KEY', 'RUTEALO_SECRET_KEY_SUPER_SECRETA')
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# --- UPLOAD CONFIG ---
MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50 MB
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'pptx'}
