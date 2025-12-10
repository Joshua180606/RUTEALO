"""
Configuración centralizada del proyecto RUTEALO.
Carga variables de entorno desde claves.env usando python-dotenv.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno desde claves.env
load_dotenv("claves.env")

# --- RUTAS BASE ---
BASE_DIR = Path(__file__).parent.parent  # c:\...\RUTEALO
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

# Crear directorios si no existen
RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# --- MONGODB ATLAS ---
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://default:default@cluster0.mongodb.net/?appName=default")
DB_NAME = os.getenv("DB_NAME", "RUTEALO_DB")

# MongoDB Connection Pool Settings
MONGODB_MIN_POOL_SIZE = int(os.getenv("MONGODB_MIN_POOL_SIZE", "1"))
MONGODB_MAX_POOL_SIZE = int(os.getenv("MONGODB_MAX_POOL_SIZE", "10"))
MONGODB_POOL_SIZE = int(os.getenv("MONGODB_POOL_SIZE", "30000"))  # maxIdleTimeMS
MONGODB_CONNECT_TIMEOUT = int(os.getenv("MONGODB_CONNECT_TIMEOUT", "10000"))  # 10 seconds
MONGODB_SOCKET_TIMEOUT = int(os.getenv("MONGODB_SOCKET_TIMEOUT", "30000"))  # 30 seconds

# Colecciones MongoDB
COLS = {
    "RAW": "materiales_crudos",
    "PERFIL": "usuario_perfil",
    "EXAM_INI": "examen_inicial",
    "RUTAS": "rutas_aprendizaje",
}

# --- GOOGLE GENERATIVE AI ---
# Claves especializadas por función para evitar límites de rate limit
GOOGLE_API_KEY_IDENTIFICADOR = os.getenv("GOOGLE_API_KEY_IDENTIFICADOR", "")
GOOGLE_API_KEY_EXAMEN_INICIAL = os.getenv("GOOGLE_API_KEY_EXAMEN_INICIAL", "")
GOOGLE_API_KEY_RUTEADOR = os.getenv("GOOGLE_API_KEY_RUTEADOR", "")
GOOGLE_API_KEY_CHATBOT = os.getenv("GOOGLE_API_KEY_CHATBOT", "")

# Clave por defecto (para compatibilidad)
GOOGLE_API_KEY = GOOGLE_API_KEY_RUTEADOR or GOOGLE_API_KEY_IDENTIFICADOR

# --- FLASK ---
SECRET_KEY = os.getenv("SECRET_KEY", "RUTEALO_SECRET_KEY_SUPER_SECRETA")
DEBUG = os.getenv("DEBUG", "True").lower() == "true"

# --- UPLOAD CONFIG ---
MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50 MB
ALLOWED_EXTENSIONS = {"pdf", "docx", "pptx"}

# --- GOOGLE GENERATIVE AI CONFIGURATION (Centralizado) ---
from google.generativeai.types import HarmCategory, HarmBlockThreshold

GENAI_MODEL_NAME = "gemini-2.5-flash"
GENAI_TEMPERATURE = 0.2  # Balance: determinístico pero creativo
GENAI_TOP_P = 0.95

# Safety settings estandarizados
GENAI_SAFETY_SETTINGS = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
}

GENAI_GENERATION_CONFIG = {
    "response_mime_type": "application/json",
    "temperature": GENAI_TEMPERATURE,
    "top_p": GENAI_TOP_P,
}


def get_genai_model(api_key_type='default'):
    """
    Retorna la instancia del modelo Gemini configurada con la clave apropiada.
    
    Args:
        api_key_type (str): Tipo de clave a usar:
            - 'default': Clave por defecto (RUTEADOR)
            - 'identificador': Para etiquetado Bloom
            - 'examen': Para generación de exámenes
            - 'ruteador': Para generación de rutas
            - 'chatbot': Para chatbot tutor
    
    Returns:
        GenerativeModel: Modelo configurado
    """
    import google.generativeai as genai

    # Seleccionar la clave apropiada
    api_key_map = {
        'identificador': GOOGLE_API_KEY_IDENTIFICADOR,
        'examen': GOOGLE_API_KEY_EXAMEN_INICIAL,
        'ruteador': GOOGLE_API_KEY_RUTEADOR,
        'chatbot': GOOGLE_API_KEY_CHATBOT,
        'default': GOOGLE_API_KEY
    }
    
    api_key = api_key_map.get(api_key_type, GOOGLE_API_KEY)
    
    if api_key:
        genai.configure(api_key=api_key)
    else:
        raise ValueError(f"No se encontró clave API para tipo: {api_key_type}")
    
    return genai.GenerativeModel(
        model_name=GENAI_MODEL_NAME, 
        generation_config=GENAI_GENERATION_CONFIG, 
        safety_settings=GENAI_SAFETY_SETTINGS
    )
