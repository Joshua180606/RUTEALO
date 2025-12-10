"""
Utilitarios generales: decoradores de retry, validadores, funciones de helpers.
Centraliza lógica transversal para mantener código limpio en modelos y rutas.
"""

import time
import logging
from functools import wraps
from typing import Callable, Any, Optional, Type, Tuple

logger = logging.getLogger(__name__)


# ============================================================================
# RETRY DECORATOR
# ============================================================================


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    log_level: str = "warning",
) -> Callable:
    """
    Decorador de reintentos con backoff exponencial.

    Args:
        max_attempts: Número máximo de intentos (default: 3)
        delay: Espera inicial en segundos (default: 1.0)
        backoff: Multiplicador de espera entre intentos (default: 2.0)
        exceptions: Tupla de excepciones a capturar (default: (Exception,))
        log_level: Nivel de logging ("debug", "info", "warning", "error")

    Returns:
        Función decoradora que envuelve la función objetivo con lógica de reintentos

    Example:
        @retry(max_attempts=5, delay=0.5, backoff=2.0, exceptions=(ConnectionError, TimeoutError))
        def fetch_data_from_api():
            # código que puede fallar
            pass
    """
    log_fn = getattr(logger, log_level.lower(), logger.warning)

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            current_delay = delay
            last_exception = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts:
                        log_fn(
                            f"[RETRY] {func.__name__} falló (intento {attempt}/{max_attempts}). "
                            f"Esperando {current_delay:.2f}s antes del reintento. Error: {str(e)}"
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        log_fn(
                            f"[RETRY FAILED] {func.__name__} falló después de {max_attempts} intentos. "
                            f"Última excepción: {str(e)}"
                        )

            # Si llegamos aquí, todos los intentos fallaron
            raise (
                last_exception
                if last_exception
                else Exception(f"Unknown error in {func.__name__} after {max_attempts} attempts")
            )

        return wrapper

    return decorator


# ============================================================================
# TIMEOUT DECORATOR
# ============================================================================


def timeout(seconds: float = 30) -> Callable:
    """
    Decorador que establece un timeout para una función (requiere signal en Unix).
    En Windows, es principalmente informativo (usa threading).

    Args:
        seconds: Segundos de timeout (default: 30)

    Returns:
        Función decoradora
    """
    import signal
    import platform

    def decorator(func: Callable) -> Callable:
        if platform.system() == "Windows":
            # En Windows, signal no funciona bien. Registramos un warning.
            @wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                logger.debug(
                    f"[TIMEOUT] {func.__name__} ejecutándose con timeout indicativo de {seconds}s "
                    "(timeout real requiere Unix/Linux)"
                )
                return func(*args, **kwargs)

        else:
            # Unix/Linux: usar signal
            def handler(signum, frame):
                raise TimeoutError(f"{func.__name__} exceeded timeout of {seconds}s")

            @wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                signal.signal(signal.SIGALRM, handler)
                signal.alarm(int(seconds))
                try:
                    result = func(*args, **kwargs)
                finally:
                    signal.alarm(0)
                return result

        return wrapper

    return decorator


# ============================================================================
# VALIDATION HELPERS
# ============================================================================


def validate_email(email: str) -> bool:
    """Valida que una cadena sea un email plausible."""
    import re

    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None


def validate_username(username: str, min_length: int = 3, max_length: int = 50) -> bool:
    """Valida que un username cumpla con restricciones de longitud."""
    if not isinstance(username, str):
        return False
    return min_length <= len(username) <= max_length


def validate_password_strength(password: str, min_length: int = 8) -> Tuple[bool, Optional[str]]:
    """
    Valida la fortaleza de una contraseña.

    Args:
        password: Contraseña a validar
        min_length: Longitud mínima requerida

    Returns:
        Tupla (is_valid, mensaje_error_o_none)
    """
    import re

    if len(password) < min_length:
        return False, f"Contraseña debe tener al menos {min_length} caracteres"

    if not re.search(r"[a-z]", password):
        return False, "Contraseña debe contener al menos una minúscula"

    if not re.search(r"[A-Z]", password):
        return False, "Contraseña debe contener al menos una mayúscula"

    if not re.search(r"[0-9]", password):
        return False, "Contraseña debe contener al menos un dígito"

    return True, None


# ============================================================================
# ERROR HANDLING HELPERS
# ============================================================================


def safe_get_nested(data: dict, path: str, default: Any = None) -> Any:
    """
    Acceso seguro a datos anidados en diccionarios con notación de puntos.

    Example:
        safe_get_nested({"user": {"profile": {"name": "John"}}}, "user.profile.name")
        → "John"
    """
    keys = path.split(".")
    current = data
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    return current


def ensure_directory(path: Any) -> None:
    """Crea un directorio si no existe."""
    from pathlib import Path

    Path(path).mkdir(parents=True, exist_ok=True)
    logger.debug(f"Directory ensured: {path}")


def log_execution_time(func: Callable) -> Callable:
    """Decorador que registra el tiempo de ejecución de una función."""

    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        import time

        start = time.time()
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start
            logger.debug(f"[PERF] {func.__name__} completó en {duration:.4f}s")
            return result
        except Exception as e:
            duration = time.time() - start
            logger.error(f"[PERF] {func.__name__} falló después de {duration:.4f}s: {str(e)}")
            raise

    return wrapper


# ============================================================================
# EXAM RESPONSE VALIDATORS
# ============================================================================


def validate_exam_response(respuesta: dict) -> Tuple[bool, Optional[str]]:
    """
    Valida una respuesta individual de examen.

    Args:
        respuesta (dict): Diccionario con estructura:
            {"pregunta_id": int, "respuesta": str, "tiempo_seg": int (opcional)}

    Returns:
        Tupla (is_valid, mensaje_error_o_none)
    """
    if not isinstance(respuesta, dict):
        return False, "Respuesta debe ser un diccionario"

    # Validar pregunta_id
    if "pregunta_id" not in respuesta:
        return False, "Falta 'pregunta_id' en la respuesta"

    if not isinstance(respuesta["pregunta_id"], (int, float)):
        return False, "'pregunta_id' debe ser un número"

    if respuesta["pregunta_id"] < 1:
        return False, "'pregunta_id' debe ser mayor que 0"

    # Validar respuesta
    if "respuesta" not in respuesta:
        return False, "Falta 'respuesta' en la pregunta"

    if not isinstance(respuesta["respuesta"], str):
        return False, "'respuesta' debe ser una cadena de texto"

    if len(respuesta["respuesta"].strip()) == 0:
        return False, "'respuesta' no puede estar vacía"

    # Validar tiempo_seg (opcional pero si existe debe ser número)
    if "tiempo_seg" in respuesta:
        if not isinstance(respuesta["tiempo_seg"], (int, float)):
            return False, "'tiempo_seg' debe ser un número"
        if respuesta["tiempo_seg"] < 0:
            return False, "'tiempo_seg' no puede ser negativo"

    return True, None


def validate_exam_responses(respuestas: list) -> Tuple[bool, Optional[str]]:
    """
    Valida una lista completa de respuestas de examen.

    Args:
        respuestas (list): Lista de respuestas de examen

    Returns:
        Tupla (is_valid, mensaje_error_o_none)
    """
    if not isinstance(respuestas, list):
        return False, "Las respuestas deben ser una lista"

    if len(respuestas) == 0:
        return False, "No hay respuestas para validar"

    # Validar que no haya más de 100 respuestas (límite razonable)
    if len(respuestas) > 100:
        return False, "Demasiadas respuestas (máx: 100)"

    pregunta_ids = set()

    for idx, respuesta in enumerate(respuestas):
        is_valid, msg = validate_exam_response(respuesta)
        if not is_valid:
            return False, f"Respuesta {idx + 1}: {msg}"

        pregunta_id = respuesta["pregunta_id"]

        # Validar que no hay pregunta_ids duplicados
        if pregunta_id in pregunta_ids:
            return False, f"Pregunta {pregunta_id} aparece más de una vez"

        pregunta_ids.add(pregunta_id)

    return True, None


def validate_exam_structure(examen: dict) -> Tuple[bool, Optional[str]]:
    """
    Valida la estructura básica de un examen.

    Args:
        examen (dict): Diccionario del examen con EXAMENES

    Returns:
        Tupla (is_valid, mensaje_error_o_none)
    """
    if not isinstance(examen, dict):
        return False, "El examen debe ser un diccionario"

    if "EXAMENES" not in examen:
        return False, "El examen debe contener clave 'EXAMENES'"

    examenes = examen["EXAMENES"]

    if not isinstance(examenes, dict):
        return False, "'EXAMENES' debe ser un diccionario"

    if len(examenes) == 0:
        return False, "El examen no contiene pruebas"

    return True, None


# ============================================================================
# UTILIDADES DE TIEMPO Y CONVERSIÓN
# ============================================================================


def minutos_a_horas(minutos: int) -> float:
    """
    Convierte minutos a horas.

    Args:
        minutos: Cantidad de minutos

    Returns:
        Cantidad de horas como decimal (ej: 120 minutos -> 2.0 horas)
    """
    if isinstance(minutos, str):
        minutos = int(minutos)
    return minutos / 60


def horas_a_minutos(horas: float) -> int:
    """
    Convierte horas a minutos.

    Args:
        horas: Cantidad de horas

    Returns:
        Cantidad de minutos como entero
    """
    if isinstance(horas, str):
        horas = float(horas)
    return int(horas * 60)


def formatear_tiempo_estudio(minutos: int) -> str:
    """
    Formatea tiempo de estudio para presentación.

    Args:
        minutos: Cantidad de minutos

    Returns:
        String formateado (ej: "2 horas" o "30 minutos")
    """
    if isinstance(minutos, str):
        minutos = int(minutos)

    horas = minutos // 60
    mins_restantes = minutos % 60

    if horas == 0:
        return f"{mins_restantes} minutos"
    elif mins_restantes == 0:
        return f"{horas} hora{'s' if horas > 1 else ''}"
    else:
        return f"{horas} hora{'s' if horas > 1 else ''} {mins_restantes} minutos"


# ============================================================================
# FILE MANAGEMENT UTILITIES
# ============================================================================


import os
from pathlib import Path


def obtener_carpeta_usuario(usuario: str, base_uploads_path: str = None) -> str:
    """
    Obtiene la ruta de la carpeta del usuario en data/raw/uploads.
    
    Args:
        usuario (str): Nombre de usuario
        base_uploads_path (str, optional): Ruta base uploads. Si no proporciona, 
                                           usa data/raw/uploads relativo
    
    Returns:
        str: Ruta absoluta de la carpeta del usuario
    
    Example:
        >>> obtener_carpeta_usuario("JOSHUA")
        "C:\\...\\data\\raw\\uploads\\JOSHUA"
    """
    if base_uploads_path is None:
        # Obtener ruta relativa al archivo actual
        base_path = Path(__file__).parent.parent / "data" / "raw" / "uploads"
    else:
        base_path = Path(base_uploads_path)
    
    usuario_folder = base_path / usuario
    return str(usuario_folder)


def crear_carpeta_usuario(usuario: str, base_uploads_path: str = None) -> bool:
    """
    Crea la carpeta del usuario si no existe.
    
    Args:
        usuario (str): Nombre de usuario
        base_uploads_path (str, optional): Ruta base uploads
    
    Returns:
        bool: True si se creó o ya existe, False si hay error
    
    Example:
        >>> crear_carpeta_usuario("JOSHUA")
        True
    """
    try:
        carpeta_usuario = obtener_carpeta_usuario(usuario, base_uploads_path)
        Path(carpeta_usuario).mkdir(parents=True, exist_ok=True)
        logger.info(f"Carpeta de usuario creada/verificada: {carpeta_usuario}")
        return True
    except Exception as e:
        logger.error(f"Error creando carpeta de usuario {usuario}: {str(e)}")
        return False


def listar_archivos_usuario(usuario: str, base_uploads_path: str = None) -> list:
    """
    Lista todos los archivos del usuario en su carpeta.
    
    Args:
        usuario (str): Nombre de usuario
        base_uploads_path (str, optional): Ruta base uploads
    
    Returns:
        list: Lista de dicts con info de archivos
               [{'nombre': 'archivo.pdf', 'size': 1024, 'fecha': '2025-12-09 10:30'}, ...]
    
    Example:
        >>> listar_archivos_usuario("JOSHUA")
        [{'nombre': 'material.pdf', 'size': 524288, 'fecha': '2025-12-09 10:30:45'}]
    """
    carpeta_usuario = obtener_carpeta_usuario(usuario, base_uploads_path)
    archivos = []
    
    try:
        if not os.path.exists(carpeta_usuario):
            logger.info(f"Carpeta del usuario {usuario} no existe aún")
            return archivos
        
        for archivo in os.listdir(carpeta_usuario):
            ruta_archivo = os.path.join(carpeta_usuario, archivo)
            
            # Solo archivos, no directorios
            if os.path.isfile(ruta_archivo):
                size = os.path.getsize(ruta_archivo)
                timestamp = os.path.getmtime(ruta_archivo)
                from datetime import datetime
                fecha = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
                
                archivos.append({
                    'nombre': archivo,
                    'size': size,
                    'size_mb': round(size / (1024 * 1024), 2),
                    'fecha': fecha,
                    'ruta': ruta_archivo
                })
        
        # Ordenar por fecha descendente (más reciente primero)
        archivos.sort(key=lambda x: x['fecha'], reverse=True)
        return archivos
    
    except Exception as e:
        logger.error(f"Error listando archivos de {usuario}: {str(e)}")
        return []


def validar_acceso_archivo(usuario: str, nombre_archivo: str, base_uploads_path: str = None) -> bool:
    """
    Valida que el usuario tiene acceso al archivo (pertenece a su carpeta).
    
    Args:
        usuario (str): Nombre de usuario
        nombre_archivo (str): Nombre del archivo a validar
        base_uploads_path (str, optional): Ruta base uploads
    
    Returns:
        bool: True si el usuario puede acceder al archivo
    
    Example:
        >>> validar_acceso_archivo("JOSHUA", "material.pdf")
        True
    """
    try:
        carpeta_usuario = obtener_carpeta_usuario(usuario, base_uploads_path)
        ruta_archivo = os.path.join(carpeta_usuario, nombre_archivo)
        ruta_real = os.path.realpath(ruta_archivo)
        carpeta_real = os.path.realpath(carpeta_usuario)
        
        # Verificar que la ruta está dentro de la carpeta del usuario
        return ruta_real.startswith(carpeta_real) and os.path.isfile(ruta_real)
    except Exception as e:
        logger.error(f"Error validando acceso de {usuario} a {nombre_archivo}: {str(e)}")
        return False


def obtener_ruta_archivo(usuario: str, nombre_archivo: str, base_uploads_path: str = None) -> Optional[str]:
    """
    Obtiene la ruta absoluta del archivo si el usuario tiene acceso.
    
    Args:
        usuario (str): Nombre de usuario
        nombre_archivo (str): Nombre del archivo
        base_uploads_path (str, optional): Ruta base uploads
    
    Returns:
        str: Ruta absoluta del archivo, o None si no tiene acceso
    
    Example:
        >>> obtener_ruta_archivo("JOSHUA", "material.pdf")
        "C:\\...\\data\\raw\\uploads\\JOSHUA\\material.pdf"
    """
    if validar_acceso_archivo(usuario, nombre_archivo, base_uploads_path):
        carpeta_usuario = obtener_carpeta_usuario(usuario, base_uploads_path)
        return os.path.join(carpeta_usuario, nombre_archivo)
    return None

