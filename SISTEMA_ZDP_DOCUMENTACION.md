# 📊 Sistema de Evaluación y Scoring basado en ZDP (Zona de Desarrollo Próximo)

## 🎯 Descripción General

Este sistema implementa la **Teoría de Vygotsky sobre la Zona de Desarrollo Próximo (ZDP)** para:

1. **Evaluar exámenes** respondidos por estudiantes
2. **Calcular puntajes** por nivel de la Taxonomía de Bloom
3. **Identificar brechas** de conocimiento
4. **Generar rutas personalizadas** omitiendo temas ya dominados
5. **Actualizar el perfil** del estudiante automáticamente

---

## 📚 Concepto ZDP

La ZDP (Zona de Desarrollo Próximo) define que el aprendizaje óptimo ocurre en la brecha entre:

- **Nivel Actual**: Lo que el estudiante puede hacer SOLO
- **Zona Próxima**: Lo que puede hacer CON AYUDA (tutorización, apoyo estructurado)

```
┌─────────────────────────────────────────────────────────────┐
│ ZONAS DE APRENDIZAJE                                        │
├─────────────────────────────────────────────────────────────┤
│ 🔴 NO ALCANZABLE: Muy difícil, requiere años de estudio    │
│ 🟡 ZONA PRÓXIMA: Aquí va el apoyo estructurado              │
│ 🟢 NIVEL ACTUAL: El estudiante puede hacer solo             │
│ ⬜ DOMINADO: Ya competente, omitir en la ruta              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 Componentes Principales

### 1. **Clase `EvaluadorZDP`** (`src/models/evaluacion_zdp.py`)

#### Métodos principales:

#### `evaluar_examen(usuario, respuestas_estudiante, examen_original)`

Evalúa un examen respondido por el estudiante.

**Parámetros:**
```python
usuario = "juan_2024"
respuestas_estudiante = [
    {"pregunta_id": 1, "respuesta": "a", "tiempo_seg": 45},
    {"pregunta_id": 2, "respuesta": "c", "tiempo_seg": 32},
    {"pregunta_id": 3, "respuesta": "b", "tiempo_seg": 28},
]
examen_original = {
    "EXAMENES": {
        "EXAMEN_INICIAL": [
            {
                "id": 1,
                "pregunta": "¿Qué es...?",
                "opciones": ["a", "b", "c", "d"],
                "respuesta_correcta": "a",
                "nivel_bloom_evaluado": "Recordar"
            },
            # ... más preguntas
        ]
    }
}
```

**Retorno:**
```python
{
    "usuario": "juan_2024",
    "puntaje_total": 75.5,  # Puntaje ponderado 0-100
    "nivel_actual": "Comprender",  # Nivel de Bloom alcanzado
    "zona_proxima": ["Aplicar", "Analizar"],  # Próximos objetivos
    
    "resumen_por_nivel": {
        "Recordar": {
            "aciertos": 5,
            "total": 5,
            "porcentaje": 100.0,
            "competente": true
        },
        "Comprender": {
            "aciertos": 3,
            "total": 4,
            "porcentaje": 75.0,
            "competente": true
        },
        "Aplicar": {
            "aciertos": 1,
            "total": 4,
            "porcentaje": 25.0,
            "competente": false
        }
    },
    
    "respuestas_procesadas": [
        {
            "pregunta_id": 1,
            "pregunta": "¿Qué es...?",
            "nivel_bloom": "Recordar",
            "respuesta_estudiante": "a",
            "respuesta_correcta": "a",
            "es_correcto": true,
            "tiempo_segundos": 45
        },
        # ... más respuestas
    ],
    
    "recomendaciones": [
        {
            "tipo": "fortalezas",
            "mensaje": "El estudiante domina: Recordar, Comprender",
            "accion": "Omitir o acelerar estos temas"
        },
        {
            "tipo": "zona_proxima",
            "mensaje": "Próximos objetivos: Aplicar, Analizar",
            "accion": "Trabajar con apoyo estructurado"
        }
    ]
}
```

### 2. **Scoring y Cálculo de Puntaje**

El puntaje se calcula como:

```
PUNTAJE_TOTAL = Σ (porcentaje_por_nivel × peso)

donde:
- porcentaje_por_nivel = (aciertos / total) × 100
- peso = (índice_nivel + 1) / cantidad_niveles
```

**Ejemplo:**
```
Recordar:   100% × (1/6) = 16.67
Comprender:  75% × (2/6) = 25.00
Aplicar:     25% × (3/6) = 12.50
Analizar:     0% × (4/6) =  0.00
----
TOTAL: 54.17 puntos
```

### 3. **Umbral de Competencia**

- **70% de aciertos** = Competente en ese nivel
- **< 70%** = Brecha identificada, necesita refuerzo

---

## 📝 Ejemplo de Uso

### En la Web (`src/web_utils.py`)

```python
from src.web_utils import procesar_respuesta_examen_web, obtener_perfil_estudiante_zdp

# 1. Procesar respuestas del examen
resultado_evaluacion = procesar_respuesta_examen_web(
    usuario="juan_2024",
    respuestas_estudiante=[
        {"pregunta_id": 1, "respuesta": "a", "tiempo_seg": 45},
        {"pregunta_id": 2, "respuesta": "c", "tiempo_seg": 32},
        {"pregunta_id": 3, "respuesta": "b", "tiempo_seg": 28},
    ],
    examen_original=examen  # El examen generado
)

# 2. Ver el puntaje y recomendaciones
print(f"Puntaje: {resultado_evaluacion['puntaje_total']}")
print(f"Nivel Actual: {resultado_evaluacion['nivel_actual']}")
print(f"Zona Próxima: {resultado_evaluacion['zona_proxima']}")
for rec in resultado_evaluacion['recomendaciones']:
    print(f"  - {rec['mensaje']}")

# 3. Obtener perfil ZDP actualizado
perfil = obtener_perfil_estudiante_zdp("juan_2024")
print(f"Competencias: {perfil['competencias']}")
```

### En Flask (Endpoint Ejemplo)

```python
@app.route('/evaluar-examen', methods=['POST'])
def evaluar_examen():
    usuario = session.get('usuario')
    datos = request.json
    
    # datos = {
    #     "respuestas": [
    #         {"pregunta_id": 1, "respuesta": "a", "tiempo_seg": 45},
    #         ...
    #     ]
    # }
    
    resultado = procesar_respuesta_examen_web(
        usuario=usuario,
        respuestas_estudiante=datos['respuestas'],
        examen_original=get_examen_estudiante(usuario)
    )
    
    return jsonify({
        "puntaje": resultado['puntaje_total'],
        "nivel_actual": resultado['nivel_actual'],
        "zona_proxima": resultado['zona_proxima'],
        "recomendaciones": resultado['recomendaciones']
    })
```

---

## 🔄 Flujo Completo de Actualización

```
1. Estudiante Resuelve Examen
        ↓
2. procesar_respuesta_examen_web() 
        ↓
3. EvaluadorZDP.evaluar_examen()
        ├─ Procesa cada respuesta
        ├─ Calcula porcentaje por nivel Bloom
        ├─ Identifica Nivel Actual y Zona Próxima
        └─ Genera recomendaciones
        ↓
4. Actualización Automática en MongoDB
        ├─ Colección "evaluaciones_estudiante"
        └─ Colección "usuario_perfil" (puntaje, competencias, ZDP)
        ↓
5. Ruta Personalizada Regenerada
        ├─ Omite temas donde es competente
        ├─ Enfatiza zona próxima con apoyo
        └─ Se guarda en "rutas_aprendizaje"
```

---

## 📊 Estructura en MongoDB

### Colección: `evaluaciones_estudiante`
```json
{
  "_id": ObjectId(...),
  "usuario": "juan_2024",
  "fecha_evaluacion": ISODate("2025-12-09T..."),
  "puntaje_total": 75.5,
  "nivel_actual": "Comprender",
  "zona_proxima": ["Aplicar", "Analizar"],
  "resumen_por_nivel": {
    "Recordar": { "aciertos": 5, "total": 5, "porcentaje": 100.0, "competente": true },
    "Comprender": { "aciertos": 3, "total": 4, "porcentaje": 75.0, "competente": true },
    "Aplicar": { "aciertos": 1, "total": 4, "porcentaje": 25.0, "competente": false }
  },
  "respuestas_procesadas": [...],
  "recomendaciones": [...]
}
```

### Colección: `usuario_perfil` (Actualizada)
```json
{
  "_id": ObjectId(...),
  "usuario": "juan_2024",
  "nivel_actual": "Comprender",
  "zona_proxima": ["Aplicar", "Analizar"],
  "puntaje_ultimo_examen": 75.5,
  "competencias": {
    "Recordar": { "porcentaje": 100.0, "competente": true },
    "Comprender": { "porcentaje": 75.0, "competente": true },
    "Aplicar": { "porcentaje": 25.0, "competente": false }
  },
  "ultima_evaluacion": ISODate("2025-12-09T...")
}
```

---

## 🎓 Ventajas del Sistema

✅ **Personalización**: Cada estudiante recibe una ruta única según su ZDP  
✅ **Eficiencia**: Omite temas donde ya es competente  
✅ **Apoyo estructurado**: Identifica dónde necesita tutorización  
✅ **Escalabilidad**: Funciona con Bloom multi-nivel  
✅ **Evaluación continua**: Se actualiza con cada examen resuelto  
✅ **Recomendaciones automáticas**: Basadas en teoría pedagógica  

---

## 🔮 Extensiones Futuras

1. **Análisis de tiempo de respuesta**: Identificar temas que tardan más
2. **Predicción de desempeño**: Usar ML para predecir éxito en nivel siguiente
3. **Seguimiento de mejora**: Gráficos de progreso en el tiempo
4. **Alertas adaptativas**: Notificaciones cuando está a punto de dominar un nivel
5. **Comparación de cohortes**: Benchmarking anónimo con otros estudiantes

---

## 📚 Referencias

- Vygotsky, L. (1978). *Mind in Society: The Development of Higher Psychological Processes*
- Bloom, B. S. (1956). *Taxonomy of Educational Objectives*
- Wood, D., Bruner, J. S., & Ross, G. (1976). The role of tutoring in problem solving

