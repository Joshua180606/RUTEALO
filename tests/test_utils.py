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
    validate_exam_response,
    validate_exam_responses,
    validate_exam_structure,
    safe_get_nested,
    log_execution_time,
    minutos_a_horas,
    horas_a_minutos,
    formatear_tiempo_estudio
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


class TestExamValidators:
    """Tests para validadores de respuestas de examen."""
    
    def test_validate_exam_response_valid(self):
        """Validar respuesta de examen válida."""
        respuesta = {"pregunta_id": 1, "respuesta": "a"}
        is_valid, msg = validate_exam_response(respuesta)
        assert is_valid is True
        assert msg is None
    
    def test_validate_exam_response_with_tiempo(self):
        """Validar respuesta con tiempo_seg."""
        respuesta = {"pregunta_id": 1, "respuesta": "b", "tiempo_seg": 45}
        is_valid, msg = validate_exam_response(respuesta)
        assert is_valid is True
        assert msg is None
    
    def test_validate_exam_response_missing_pregunta_id(self):
        """Validar que rechaza si falta pregunta_id."""
        respuesta = {"respuesta": "a"}
        is_valid, msg = validate_exam_response(respuesta)
        assert is_valid is False
        assert "pregunta_id" in msg
    
    def test_validate_exam_response_missing_respuesta(self):
        """Validar que rechaza si falta respuesta."""
        respuesta = {"pregunta_id": 1}
        is_valid, msg = validate_exam_response(respuesta)
        assert is_valid is False
        assert "respuesta" in msg
    
    def test_validate_exam_response_empty_respuesta(self):
        """Validar que rechaza respuestas vacías."""
        respuesta = {"pregunta_id": 1, "respuesta": "   "}
        is_valid, msg = validate_exam_response(respuesta)
        assert is_valid is False
    
    def test_validate_exam_response_invalid_tiempo(self):
        """Validar que rechaza tiempo_seg negativo."""
        respuesta = {"pregunta_id": 1, "respuesta": "a", "tiempo_seg": -5}
        is_valid, msg = validate_exam_response(respuesta)
        assert is_valid is False
    
    def test_validate_exam_responses_valid_list(self):
        """Validar lista válida de respuestas."""
        respuestas = [
            {"pregunta_id": 1, "respuesta": "a"},
            {"pregunta_id": 2, "respuesta": "b", "tiempo_seg": 30},
            {"pregunta_id": 3, "respuesta": "c"}
        ]
        is_valid, msg = validate_exam_responses(respuestas)
        assert is_valid is True
        assert msg is None
    
    def test_validate_exam_responses_empty_list(self):
        """Validar que rechaza lista vacía."""
        is_valid, msg = validate_exam_responses([])
        assert is_valid is False
        assert "No hay respuestas" in msg
    
    def test_validate_exam_responses_duplicate_pregunta_id(self):
        """Validar que rechaza pregunta_ids duplicados."""
        respuestas = [
            {"pregunta_id": 1, "respuesta": "a"},
            {"pregunta_id": 1, "respuesta": "b"}
        ]
        is_valid, msg = validate_exam_responses(respuestas)
        assert is_valid is False
        assert "más de una vez" in msg
    
    def test_validate_exam_responses_too_many(self):
        """Validar que rechaza más de 100 respuestas."""
        respuestas = [{"pregunta_id": i, "respuesta": "a"} for i in range(101)]
        is_valid, msg = validate_exam_responses(respuestas)
        assert is_valid is False
        assert "demasiadas" in msg.lower()
    
    def test_validate_exam_structure_valid(self):
        """Validar estructura de examen válida."""
        examen = {"EXAMENES": {"EXAMEN_INICIAL": [{"id": 1, "pregunta": "?"}]}}
        is_valid, msg = validate_exam_structure(examen)
        assert is_valid is True
        assert msg is None
    
    def test_validate_exam_structure_missing_examenes(self):
        """Validar que rechaza si falta EXAMENES."""
        examen = {"preguntas": []}
        is_valid, msg = validate_exam_structure(examen)
        assert is_valid is False
        assert "EXAMENES" in msg
    
    def test_validate_exam_structure_empty_examenes(self):
        """Validar que rechaza EXAMENES vacío."""
        examen = {"EXAMENES": {}}
        is_valid, msg = validate_exam_structure(examen)
        assert is_valid is False
        assert "no contiene" in msg.lower()


class TestTimeConversions:
    """Tests para funciones de conversión de tiempo."""
    
    def test_minutos_a_horas_120(self):
        """120 minutos debe ser 2 horas."""
        assert minutos_a_horas(120) == 2.0
    
    def test_minutos_a_horas_90(self):
        """90 minutos debe ser 1.5 horas."""
        assert minutos_a_horas(90) == 1.5
    
    def test_minutos_a_horas_string(self):
        """Debe convertir strings a horas."""
        assert minutos_a_horas("120") == 2.0
    
    def test_minutos_a_horas_60(self):
        """60 minutos debe ser 1 hora."""
        assert minutos_a_horas(60) == 1.0
    
    def test_horas_a_minutos_2(self):
        """2 horas debe ser 120 minutos."""
        assert horas_a_minutos(2.0) == 120
    
    def test_horas_a_minutos_1_5(self):
        """1.5 horas debe ser 90 minutos."""
        assert horas_a_minutos(1.5) == 90
    
    def test_horas_a_minutos_string(self):
        """Debe convertir strings a minutos."""
        assert horas_a_minutos("2.0") == 120
    
    def test_formatear_tiempo_solo_minutos(self):
        """Debe formatear correctamente solo minutos."""
        assert formatear_tiempo_estudio(30) == "30 minutos"
        assert formatear_tiempo_estudio(45) == "45 minutos"
    
    def test_formatear_tiempo_solo_horas(self):
        """Debe formatear correctamente solo horas."""
        assert formatear_tiempo_estudio(60) == "1 hora"
        assert formatear_tiempo_estudio(120) == "2 horas"
    
    def test_formatear_tiempo_horas_y_minutos(self):
        """Debe formatear correctamente horas y minutos."""
        assert formatear_tiempo_estudio(90) == "1 hora 30 minutos"
        assert formatear_tiempo_estudio(150) == "2 horas 30 minutos"
    
    def test_formatear_tiempo_string(self):
        """Debe funcionar con strings."""
        assert formatear_tiempo_estudio("120") == "2 horas"
        assert formatear_tiempo_estudio("90") == "1 hora 30 minutos"

