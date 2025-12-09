# 🔧 Plan de Implementación de Optimizaciones - RUTEALO

**Versión:** 1.0  
**Creado:** Diciembre 2024  
**Objetivo:** Remediar issues críticos y mejorar code quality en fases progresivas

---

## 📋 ÍNDICE
1. [Fase 1: Security + Config Fix](#fase-1-security--config-fix)
2. [Fase 2: Database & Logging](#fase-2-database--logging)
3. [Fase 3: Resilience & Error Handling](#fase-3-resilience--error-handling)
4. [Fase 4: Testing & Deployment](#fase-4-testing--deployment)

---

## ⚡ FASE 1: Security + Config Fix
**Duración Estimada:** 2-3 horas  
**Prioridad:** 🔴 CRÍTICA

### 1.1 Eliminar `load_dotenv()` Redundantes

**Archivos a Actualizar:**
1. `src/models/motor_prompting.py` (línea 11)
2. `src/models/etiquetado_bloom.py` (línea 9) - ✅ PARCIALMENTE HECHO
3. `src/data/ingesta_datos.py` (línea 9)
4. `src/data/df_bloom.py` (línea 6)
5. `src/data/df_flow.py` (línea 7)
6. `src/data/df_zdp.py` (línea 6)

**Cambio:**

```python
# ❌ ANTES
load_dotenv('claves.env')
import os
MONGO_URI = os.getenv('MONGO_URI')
DB_NAME = os.getenv('DB_NAME')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

# ✅ DESPUÉS
from src.config import MONGO_URI, DB_NAME, GOOGLE_API_KEY
# Ya está cargado en src/config.py
```

**Comando verificación:**
```powershell
# En raíz del proyecto
grep -r "load_dotenv('claves.env')" src/
```

### 1.2 Actualizar `src/config.py` con Configuración Gemini

**Archivo:** `src/config.py`

**Agregar al final:**

```python
# --- GOOGLE GENERATIVE AI CONFIGURATION ---
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

# Función helper para inicializar modelo
def get_genai_model():
    import google.generativeai as genai
    if GOOGLE_API_KEY:
        genai.configure(api_key=GOOGLE_API_KEY)
    return genai.GenerativeModel(
        model_name=GENAI_MODEL_NAME,
        generation_config=GENAI_GENERATION_CONFIG,
        safety_settings=GENAI_SAFETY_SETTINGS
    )
```

### 1.3 Actualizar Importes en Archivos Gemini

**Archivos a cambiar:**
- `src/models/motor_prompting.py`
- `src/models/evaluacion_zdp.py`
- `src/web_utils.py`

**Cambio genérico:**

```python
# ❌ ANTES (en cada archivo)
from google.generativeai.types import HarmCategory, HarmBlockThreshold
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel(...)

# ✅ DESPUÉS
from src.config import get_genai_model
model = get_genai_model()
```

### 1.4 ✅ Confirmación Security Fix

**Checklist:**
- [ ] `etiquetado_bloom.py` sin `MONGO_URI` hardcoded ✅ DONE
- [ ] `etiquetado_bloom.py` sin `GOOGLE_API_KEY` hardcoded ✅ DONE
- [ ] Todos los archivos importan desde `src.config`
- [ ] `.gitignore` contiene `claves.env` ✅ VERIFICADO
- [ ] Ejecutar: `grep -r "AIzaSy\|aLTEC358036" src/` (debe estar vacío)

---

## 🗄️ FASE 2: Database & Logging
**Duración Estimada:** 3-4 horas  
**Prioridad:** 🔴 ALTA

### 2.1 Crear `src/database.py` - Singleton MongoDB

**Archivo nuevo:**

```python
# src/database.py
"""
Gestión centralizada de conexión a MongoDB con patrón Singleton.
Garantiza una única conexión por aplicación.
"""

from pymongo import MongoClient
from pymongo.server_api import ServerApi
import gridfs
from src.config import MONGO_URI, DB_NAME

class DatabaseConnection:
    """Singleton para gestionar conexión MongoDB."""
    
    _instance = None
    _client = None
    _db = None
    _fs = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Inicializa la conexión MongoDB una sola vez."""
        try:
            self._client = MongoClient(MONGO_URI, server_api=ServerApi('1'))
            # Verificar conexión
            self._client.admin.command('ping')
            self._db = self._client[DB_NAME]
            self._fs = gridfs.GridFS(self._db)
            print("✅ Conexión MongoDB establecida")
        except Exception as e:
            print(f"❌ Error conectando a MongoDB: {e}")
            raise
    
    @property
    def client(self):
        """Retorna el cliente MongoDB."""
        return self._client
    
    @property
    def db(self):
        """Retorna la base de datos."""
        return self._db
    
    @property
    def fs(self):
        """Retorna GridFS para manejo de archivos binarios."""
        return self._fs
    
    def get_collection(self, collection_name):
        """Obtiene una colección específica."""
        if not self._db:
            raise RuntimeError("Conexión MongoDB no inicializada")
        return self._db[collection_name]
    
    def close(self):
        """Cierra la conexión (usar en shutdown)."""
        if self._client:
            self._client.close()
            self._client = None
            self._db = None
            self._fs = None

# Función de conveniencia
def get_db():
    """Obtiene la instancia singleton de la BD."""
    return DatabaseConnection().db

def get_fs():
    """Obtiene GridFS para archivos."""
    return DatabaseConnection().fs
```

**Uso en cualquier archivo:**

```python
# ✅ NUEVO PATRÓN (simple y eficiente)
from src.database import get_db, get_fs

db = get_db()
fs = get_fs()
col = db.mi_coleccion

# ✅ Automáticamente: una conexión compartida, pooling, etc.
```

### 2.2 Crear `src/logger.py` - Logging Estructurado

**Archivo nuevo:**

```python
# src/logger.py
"""
Sistema de logging centralizado para RUTEALO.
Escribe a archivo y consola con niveles configurables.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime

# Crear directorio de logs
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Nombre del archivo de log con fecha
log_filename = LOG_DIR / f"rutealo_{datetime.now().strftime('%Y%m%d')}.log"

# Crear logger
logger = logging.getLogger("RUTEALO")
logger.setLevel(logging.DEBUG)

# Limpiar handlers previos (importante para tests)
logger.handlers.clear()

# Handler para archivo (todo)
file_handler = logging.FileHandler(log_filename)
file_handler.setLevel(logging.DEBUG)

# Handler para consola (solo INFO+)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)

# Formato detallado para archivo
file_formatter = logging.Formatter(
    '%(asctime)s | %(name)s | %(levelname)-8s | %(filename)s:%(lineno)d | %(funcName)s() | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Formato simplificado para consola
console_formatter = logging.Formatter(
    '%(levelname)-8s | %(message)s'
)

file_handler.setFormatter(file_formatter)
console_handler.setFormatter(console_formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Exportar
__all__ = ['logger']
```

**Uso en cualquier archivo:**

```python
# ✅ NUEVO PATRÓN
from src.logger import logger

try:
    resultado = procesar_examen(usuario, respuestas)
    logger.info(f"Examen procesado para {usuario}, puntaje: {resultado['puntaje_total']}")
except ValueError as e:
    logger.warning(f"Validación fallida para {usuario}: {e}")
except Exception as e:
    logger.error(f"Error crítico procesando examen: {e}", exc_info=True)
```

**Reemplazar en todos los archivos:**

```python
# ❌ ANTES
print(f"✅ Evaluación guardada para {usuario}")
print(f"❌ Error conectando a BD: {e}")

# ✅ DESPUÉS
logger.info(f"Evaluación guardada para {usuario}")
logger.error(f"Error conectando a BD: {e}", exc_info=True)
```

### 2.3 Actualizar Archivos para Usar Logger

**Archivos a actualizar:**
1. `src/models/etiquetado_bloom.py`
2. `src/models/motor_prompting.py`
3. `src/models/evaluacion_zdp.py`
4. `src/data/ingesta_datos.py`
5. `src/web_utils.py`
6. `src/app.py`

**Ejemplo de actualización completa (motor_prompting.py):**

```python
# En el inicio del archivo
from src.logger import logger
from src.database import get_db, get_fs
from src.config import MONGO_URI, DB_NAME, GOOGLE_API_KEY, COLS, get_genai_model

# Reemplazar funciones conectar_bd()
# def conectar_bd():  # ❌ ELIMINAR
#     ...

# Usar en su lugar:
db = get_db()
fs = get_fs()
model = get_genai_model()

# Reemplazar prints:
# print(f"🚀 Iniciando...")  # ❌
logger.info("Iniciando procesamiento")  # ✅

# Reemplazar prints de error:
# except Exception as e: print(f"Error: {e}")  # ❌
# except Exception as e: logger.error(f"Error", exc_info=True)  # ✅
```

---

## 🛡️ FASE 3: Resilience & Error Handling
**Duración Estimada:** 4-5 horas  
**Prioridad:** 🟡 ALTA

### 3.1 Crear `src/utils.py` - Retry Decorator

**Archivo nuevo:**

```python
# src/utils.py
"""
Utilidades compartidas: retry logic, validators, helpers.
"""

import time
import functools
from src.logger import logger

def retry_on_exception(max_retries=3, backoff_base=2, exceptions=(Exception,)):
    """
    Decorator para reintentar una función con backoff exponencial.
    
    Args:
        max_retries: Número máximo de intentos (default 3)
        backoff_base: Base para cálculo de espera (default 2 = exponencial)
        exceptions: Tuple de excepciones a atrapar (default todas)
    
    Ejemplo:
        @retry_on_exception(max_retries=3, exceptions=(RequestException,))
        def llamar_api():
            ...
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_retries - 1:
                        logger.error(
                            f"Falló {func.__name__}() después de {max_retries} intentos. "
                            f"Último error: {e}",
                            exc_info=True
                        )
                        raise
                    
                    # Espera exponencial con jitter
                    wait_time = backoff_base ** attempt
                    logger.warning(
                        f"Intento {attempt + 1}/{max_retries} de {func.__name__}() falló: {e}. "
                        f"Reintentando en {wait_time}s..."
                    )
                    time.sleep(wait_time)
            
            # Nunca debería llegar aquí, pero por seguridad
            if last_exception:
                raise last_exception
        
        return wrapper
    return decorator


def safe_json_parse(json_text):
    """
    Parsea JSON de forma segura, eliminando markdown o caracteres especiales.
    
    Args:
        json_text: String con contenido JSON (posiblemente con markdown)
    
    Returns:
        dict o None si falla
    """
    import json
    import re
    
    try:
        # Limpiar markdown ```json ... ```
        cleaned = re.sub(r"```json\n?|```\n?", "", json_text.strip())
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        logger.error(f"Error parseando JSON: {e}\nTexto: {json_text[:500]}")
        return None
```

### 3.2 Aplicar Retry a Llamadas Gemini

**Archivos a actualizar:**
- `src/models/evaluacion_zdp.py`
- `src/models/motor_prompting.py`
- `src/web_utils.py`

**Ejemplo (evaluacion_zdp.py):**

```python
# En el inicio
from src.utils import retry_on_exception, safe_json_parse

# En generar_ruta_personalizada()
@retry_on_exception(max_retries=3, exceptions=(Exception,))
def llamar_gemini_ruta(prompt):
    respuesta = model.generate_content(prompt)
    datos = safe_json_parse(respuesta.text)
    if not datos:
        raise ValueError("Respuesta Gemini inválida")
    return datos

# Uso:
try:
    datos = llamar_gemini_ruta(prompt)
    return datos.get("ruta_personalizada", {})
except Exception as e:
    logger.error(f"Error generando ruta personalizada: {e}")
    return {"error": "No se pudo generar ruta"}
```

### 3.3 Crear `src/validators.py` - Pydantic Models

**Archivo nuevo:**

```python
# src/validators.py
"""
Modelos Pydantic para validación de input.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional
from enum import Enum

class RespuestaExamen(BaseModel):
    """Validador para respuesta de examen del estudiante."""
    pregunta_id: int = Field(..., gt=0, description="ID de la pregunta")
    respuesta: str = Field(..., min_length=1, description="Respuesta (a/b/c/d)")
    tiempo_seg: int = Field(default=0, ge=0, description="Tiempo en segundos")
    
    @validator('respuesta')
    def respuesta_valida(cls, v):
        """Validar que la respuesta sea válida."""
        v = v.strip().lower()
        if v not in ['a', 'b', 'c', 'd']:
            raise ValueError('respuesta debe ser a, b, c o d')
        return v

class ListaRespuestas(BaseModel):
    """Validador para lista de respuestas."""
    respuestas: List[RespuestaExamen]
    usuario: str = Field(..., min_length=1)
    
    @validator('usuario')
    def usuario_valido(cls, v):
        """Validar usuario."""
        if not v.strip():
            raise ValueError('usuario no puede estar vacío')
        return v.strip()

class ExamenGenerado(BaseModel):
    """Validador para examen generado."""
    id: int
    pregunta: str = Field(..., min_length=5)
    opciones: List[str] = Field(..., min_items=4, max_items=4)
    respuesta_correcta: str
    nivel_bloom_evaluado: str

# Uso:
try:
    respuestas_validadas = ListaRespuestas(**datos_json)
    # Ahora está validado y type-safe
except ValidationError as e:
    logger.error(f"Datos inválidos: {e}")
    return {"error": f"Validación fallida: {e.json()}"}
```

### 3.4 Integrar Validadores en Rutas

**Ejemplo (app.py):**

```python
@app.route('/evaluar-examen', methods=['POST'])
def evaluar_examen():
    if 'usuario' not in session:
        return {"error": "No autenticado"}, 401
    
    try:
        # Validar input
        datos = ListaRespuestas(**request.json)
        
        # Procesar
        resultado = procesar_respuesta_examen_web(
            usuario=datos.usuario,
            respuestas_estudiante=datos.respuestas,
            examen_original=...
        )
        
        logger.info(f"Examen evaluado para {datos.usuario}")
        return jsonify(resultado)
        
    except ValidationError as e:
        logger.warning(f"Validación fallida: {e}")
        return {"error": f"Datos inválidos: {e.json()}"}, 400
    except Exception as e:
        logger.error(f"Error evaluando examen: {e}", exc_info=True)
        return {"error": "Error interno del servidor"}, 500
```

---

## 🧪 FASE 4: Testing & Deployment
**Duración Estimada:** 5-6 horas  
**Prioridad:** 🟡 MEDIA (futuro)

### 4.1 Crear Tests Unitarios

**Archivo:** `tests/test_evaluacion.py`

```python
# tests/test_evaluacion.py
import pytest
from src.models.evaluacion_zdp import EvaluadorZDP
from src.validators import RespuestaExamen, ListaRespuestas

@pytest.fixture
def evaluador():
    return EvaluadorZDP()

def test_respuesta_valida():
    """Test validador de respuesta."""
    r = RespuestaExamen(pregunta_id=1, respuesta="A", tiempo_seg=30)
    assert r.respuesta == "a"  # Normalizado

def test_respuesta_invalida():
    """Test validador rechaza entrada inválida."""
    with pytest.raises(ValueError):
        RespuestaExamen(pregunta_id=1, respuesta="x", tiempo_seg=30)

def test_evaluar_examen(evaluador):
    """Test evaluación básica."""
    resultado = evaluador.evaluar_examen(
        usuario="test_user",
        respuestas_estudiante=[
            {"pregunta_id": 1, "respuesta": "a", "tiempo_seg": 45}
        ],
        examen_original={...}
    )
    assert "puntaje_total" in resultado
    assert resultado["puntaje_total"] >= 0
```

### 4.2 Crear Requirements para Desarrollo

**Archivo:** `requirements-dev.txt`

```txt
# requirements.txt (existente)
-r requirements.txt

# Testing
pytest==7.4.3
pytest-cov==4.1.0
pytest-asyncio==0.21.1

# Code quality
black==23.12.0
flake8==6.1.0
pylint==3.0.3
mypy==1.7.1

# Documentation
sphinx==7.2.6
mkdocs==1.5.3

# Profiling
memory-profiler==0.61.0
line-profiler==4.1.1
```

### 4.3 Checklist Pre-Deployment

- [ ] Todos los tests pasan: `pytest tests/`
- [ ] Coverage > 80%: `pytest --cov=src tests/`
- [ ] Sin errores de lint: `flake8 src/`
- [ ] Sin errores de type hints: `mypy src/`
- [ ] Credenciales regeneradas en MongoDB + Google Cloud
- [ ] `.env` local configurado correctamente
- [ ] Logs generándose en `logs/`
- [ ] Base de datos accesible

---

## 📊 Resumen de Cambios

### Nuevos Archivos
1. `src/database.py` - Singleton MongoDB
2. `src/logger.py` - Sistema de logging
3. `src/utils.py` - Retry decorator + helpers
4. `src/validators.py` - Pydantic models
5. `tests/test_evaluacion.py` - Tests unitarios
6. `requirements-dev.txt` - Dependencias desarrollo
7. `logs/` - Directorio para logs (git-ignored)

### Archivos Modificados
1. `src/config.py` - Agregar genai config
2. `src/models/etiquetado_bloom.py` - ✅ HECHO
3. `src/models/motor_prompting.py` - Usar config + logger + db
4. `src/models/evaluacion_zdp.py` - Usar config + logger + validators
5. `src/data/ingesta_datos.py` - Usar config + logger + db
6. `src/web_utils.py` - Usar config + logger + validators
7. `src/app.py` - Usar logger + validators
8. `src/data/df_*.py` - Simplificar imports

### Mejoras Esperadas
| Métrica | Antes | Después | Mejora |
|---------|-------|---------|--------|
| Credenciales expuestas | 3 | 0 | 100% |
| Conexiones MongoDB/req | ~5 | 1 | 80% |
| Líneas de `print()` | 45+ | 0 | 100% |
| Error handling | Básico | Robusto | +200% |
| Testing | 0% | 80%+ | ∞ |

---

## ⏱️ Timeline Estimado

| Fase | Tareas | Duración | Inicio |
|------|--------|----------|--------|
| 1 | Config + Security | 2-3h | Hoy |
| 2 | Database + Logging | 3-4h | Mañana |
| 3 | Validators + Retry | 4-5h | Día 3 |
| 4 | Tests + Deploy | 5-6h | Día 4-5 |
| **TOTAL** | 7 tareas mayores | **14-18h** | |

**Recomendación:** 2-3 horas diarias durante 1 semana

---

## 🚀 Próximas Acciones (Inmediatas)

1. **HOY**: Implementar FASE 1 completa (security + config)
2. **MAÑANA**: Crear `src/database.py` y `src/logger.py`
3. **DÍA 3**: Reemplazar todos los prints con logger
4. **DÍA 4**: Agregar retry + validators
5. **DÍA 5**: Tests + documentación final

---

## 📞 Soporte & Referencias

- **MongoDB Docs**: https://pymongo.readthedocs.io/
- **Pydantic**: https://docs.pydantic.dev/
- **Logging Python**: https://docs.python.org/3/library/logging.html
- **Pytest**: https://docs.pytest.org/
- **Google AI SDK**: https://github.com/google/generative-ai-python

