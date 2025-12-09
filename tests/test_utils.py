"""
Tests para src/utils.py: decoradores de retry, validadores, helpers.
"""

import time
import pytest
from src.utils import (
    retry,
    validate_email,
    validate_username,
    validate_password_strength,
    safe_get_nested,
    log_execution_time
)


class TestRetryDecorator:
    """Tests para el decorador de retry."""
    
    def test_retry_success_first_attempt(self):
        """Una función que funciona a la primera no debería reintentar."""
        call_count = 0
        
        @retry(max_attempts=3, delay=0.1)
        def func():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = func()
        assert result == "success"
        assert call_count == 1
    
    def test_retry_success_after_failures(self):
        """Debe reintentar y eventualmente funcionar."""
        call_count = 0
        
        @retry(max_attempts=3, delay=0.1)
        def func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Fallo temporal")
            return "success"
        
        result = func()
        assert result == "success"
        assert call_count == 3
    
    def test_retry_exhausted(self):
        """Debe lanzar excepción después de agotar intentos."""
        @retry(max_attempts=2, delay=0.05)
        def func():
            raise ValueError("Fallo permanente")
        
        with pytest.raises(ValueError, match="Fallo permanente"):
            func()
    
    def test_retry_specific_exception(self):
        """Solo debe reintentar excepciones especificadas."""
        @retry(max_attempts=3, exceptions=(ValueError,))
        def func():
            raise TypeError("No debería reintentar")
        
        with pytest.raises(TypeError):
            func()


class TestValidators:
    """Tests para funciones de validación."""
    
    def test_validate_email_valid(self):
        """Validar emails válidos."""
        assert validate_email("user@example.com") is True
        assert validate_email("test.user+tag@domain.co.uk") is True
    
    def test_validate_email_invalid(self):
        """Validar emails inválidos."""
        assert validate_email("notanemail") is False
        assert validate_email("@example.com") is False
        assert validate_email("user@") is False
    
    def test_validate_username_valid(self):
        """Validar usernames válidos."""
        assert validate_username("john123") is True
        assert validate_username("user", min_length=3, max_length=50) is True
    
    def test_validate_username_invalid_length(self):
        """Validar usernames fuera de rango."""
        assert validate_username("ab", min_length=3) is False
        assert validate_username("a" * 51, max_length=50) is False
    
    def test_validate_password_strength_valid(self):
        """Validar contraseñas fuertes."""
        is_valid, msg = validate_password_strength("SecurePass123")
        assert is_valid is True
        assert msg is None
    
    def test_validate_password_strength_too_short(self):
        """Validar contraseña muy corta."""
        is_valid, msg = validate_password_strength("Short1A", min_length=8)
        assert is_valid is False
        assert "al menos 8" in msg
    
    def test_validate_password_strength_missing_uppercase(self):
        """Validar contraseña sin mayúscula."""
        is_valid, msg = validate_password_strength("lowercase123")
        assert is_valid is False
        assert "mayúscula" in msg


class TestSafeGetNested:
    """Tests para acceso seguro a datos anidados."""
    
    def test_safe_get_nested_found(self):
        """Debe obtener valor anidado correctamente."""
        data = {"user": {"profile": {"name": "John", "age": 30}}}
        assert safe_get_nested(data, "user.profile.name") == "John"
        assert safe_get_nested(data, "user.profile.age") == 30
    
    def test_safe_get_nested_not_found(self):
        """Debe retornar default si la ruta no existe."""
        data = {"user": {"profile": {"name": "John"}}}
        assert safe_get_nested(data, "user.settings.theme", "dark") == "dark"
        assert safe_get_nested(data, "nonexistent") is None
    
    def test_safe_get_nested_non_dict(self):
        """Debe manejar datos no-dict en la ruta."""
        data = {"user": None}
        assert safe_get_nested(data, "user.profile.name", "default") == "default"


class TestLogExecutionTime:
    """Tests para el decorador de medición de tiempo."""
    
    def test_log_execution_time_success(self):
        """Debe medir tiempo de ejecución exitosa."""
        @log_execution_time
        def fast_func():
            time.sleep(0.1)
            return "done"
        
        result = fast_func()
        assert result == "done"
    
    def test_log_execution_time_failure(self):
        """Debe registrar tiempo incluso si falla."""
        @log_execution_time
        def failing_func():
            time.sleep(0.05)
            raise ValueError("Test error")
        
        with pytest.raises(ValueError, match="Test error"):
            failing_func()
