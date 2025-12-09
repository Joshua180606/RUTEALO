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
    log_level: str = "warning"
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
            raise last_exception if last_exception else Exception(
                f"Unknown error in {func.__name__} after {max_attempts} attempts"
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
