# 📚 Guía de Conversión de Tiempo - RUTEALO

**Agregado:** 9 Diciembre 2025  
**Ubicación:** `src/utils.py`

---

## 🎯 Funciones Disponibles

### 1. `minutos_a_horas(minutos: int) -> float`

Convierte minutos a horas.

**Parámetros:**
- `minutos` (int o str): Cantidad de minutos a convertir

**Retorna:**
- `float`: Cantidad de horas como decimal

**Ejemplos:**
```python
from src.utils import minutos_a_horas

minutos_a_horas(120)   # Retorna: 2.0
minutos_a_horas(90)    # Retorna: 1.5
minutos_a_horas(60)    # Retorna: 1.0
minutos_a_horas("120") # Retorna: 2.0 (también acepta strings)
```

---

### 2. `horas_a_minutos(horas: float) -> int`

Convierte horas a minutos.

**Parámetros:**
- `horas` (float o str): Cantidad de horas a convertir

**Retorna:**
- `int`: Cantidad de minutos como entero

**Ejemplos:**
```python
from src.utils import horas_a_minutos

horas_a_minutos(2.0)   # Retorna: 120
horas_a_minutos(1.5)   # Retorna: 90
horas_a_minutos(0.5)   # Retorna: 30
horas_a_minutos("2.0") # Retorna: 120 (también acepta strings)
```

---

### 3. `formatear_tiempo_estudio(minutos: int) -> str`

Formatea tiempo de estudio para presentación legible.

**Parámetros:**
- `minutos` (int o str): Cantidad de minutos a formatear

**Retorna:**
- `str`: String formateado

**Ejemplos:**
```python
from src.utils import formatear_tiempo_estudio

formatear_tiempo_estudio(30)   # Retorna: "30 minutos"
formatear_tiempo_estudio(60)   # Retorna: "1 hora"
formatear_tiempo_estudio(120)  # Retorna: "2 horas"
formatear_tiempo_estudio(90)   # Retorna: "1 hora 30 minutos"
formatear_tiempo_estudio(150)  # Retorna: "2 horas 30 minutos"
formatear_tiempo_estudio("120")# Retorna: "2 horas" (también acepta strings)
```

---

## 📋 Casos de Uso

### Caso 1: Mostrar tiempo de estudio diario

```python
from src.utils import formatear_tiempo_estudio

tiempo_minutos = usuario['preferencias']['tiempo_diario']  # "120"
tiempo_formateado = formatear_tiempo_estudio(tiempo_minutos)
print(f"Estudias {tiempo_formateado} por día")  # Output: "Estudias 2 horas por día"
```

### Caso 2: Calcular horas de estudio en una semana

```python
from src.utils import minutos_a_horas

tiempo_diario = 120  # minutos
dias_semana = 6  # 6 días (excluyendo día de descanso)
tiempo_semanal_horas = minutos_a_horas(tiempo_diario) * dias_semana
print(f"Estudias {tiempo_semanal_horas} horas por semana")  # Output: "Estudias 12.0 horas por semana"
```

### Caso 3: Convertir preferencias de usuario

```python
from src.utils import minutos_a_horas, formatear_tiempo_estudio

usuario = {
    'preferencias': {
        'tiempo_diario': '120'  # Guardado como string en BD
    }
}

tiempo_minutos = int(usuario['preferencias']['tiempo_diario'])
tiempo_horas = minutos_a_horas(tiempo_minutos)
tiempo_legible = formatear_tiempo_estudio(tiempo_minutos)

print(f"Horas: {tiempo_horas}")      # Output: "Horas: 2.0"
print(f"Formato: {tiempo_legible}")  # Output: "Formato: 2 horas"
```

---

## 🧪 Tests Disponibles

Todas las funciones tienen tests unitarios en `tests/test_utils.py`:

```bash
# Ejecutar tests de conversión de tiempo
pytest tests/test_utils.py::TestTimeConversions -v

# Resultado esperado
tests/test_utils.py::TestTimeConversions::test_minutos_a_horas_120 PASSED
tests/test_utils.py::TestTimeConversions::test_minutos_a_horas_90 PASSED
tests/test_utils.py::TestTimeConversions::test_minutos_a_horas_string PASSED
tests/test_utils.py::TestTimeConversions::test_minutos_a_horas_60 PASSED
tests/test_utils.py::TestTimeConversions::test_horas_a_minutos_2 PASSED
tests/test_utils.py::TestTimeConversions::test_horas_a_minutos_1_5 PASSED
tests/test_utils.py::TestTimeConversions::test_horas_a_minutos_string PASSED
tests/test_utils.py::TestTimeConversions::test_formatear_tiempo_solo_minutos PASSED
tests/test_utils.py::TestTimeConversions::test_formatear_tiempo_solo_horas PASSED
tests/test_utils.py::TestTimeConversions::test_formatear_tiempo_horas_y_minutos PASSED
tests/test_utils.py::TestTimeConversions::test_formatear_tiempo_string PASSED
```

---

## 💡 Notas Importantes

1. **Flexibilidad de entrada:** Todas las funciones aceptan tanto `int`/`float` como `str`
2. **Almacenamiento en BD:** El tiempo se guarda como string (`"120"`) en `preferencias.tiempo_diario`
3. **Rangos válidos:** El formulario de registro valida 15-480 minutos (0.25-8 horas)
4. **Plural automático:** `formatear_tiempo_estudio()` maneja plurales correctamente
   - "1 hora" vs "2 horas"
   - "1 minuto" vs "30 minutos"

---

## 🔧 Integración en el Proyecto

Estas funciones se utilizan en:

1. **Formulario de registro** (`templates/register.html`)
   - Entrada: minutos (15-480)
   - Almacenamiento: string en BD

2. **Dashboard** (futuro)
   - Mostrar tiempo diario formateado
   - Calcular tiempo semanal/mensual

3. **API endpoints** (futuro)
   - Retornar tiempos en formato JSON
   - Convertir entre formatos según necesidad

---

**Versión:** 1.0  
**Tests:** 11 unitarios, todos pasando ✅  
**Documentación:** Completa
