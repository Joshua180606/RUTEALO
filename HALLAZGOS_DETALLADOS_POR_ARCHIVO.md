# 🔍 HALLAZGOS DETALLADOS POR ARCHIVO

**Fecha:** 2025-12-10

---

## 📄 src/app.py (544 líneas)

### Estado General
✅ **Bien estructurado** con separación clara de rutas  
✅ **Manejo de errores** robusto  
✅ **Logging** completo  
❌ **Falta:** 4 endpoints para rediseño

### Rutas Existentes (11)
```python
✅ @app.route("/")                                    # Landing page
✅ @app.route("/register", ["GET", "POST"])         # Registro
✅ @app.route("/login", ["GET", "POST"])            # Login
✅ @app.route("/logout")                             # Logout
✅ @app.route("/dashboard")                          # Dashboard (MODIFICAR)
✅ @app.route("/upload", ["POST"])                   # Upload 1 archivo (MANTENER)
✅ @app.route("/files")                              # Listar archivos usuario
✅ @app.route("/download/<archivo>")                 # Descargar archivo
✅ @app.route("/ruta/estado")                        # Estado ruta
✅ @app.route("/examen-inicial")                     # Get examen
✅ @app.route("/examen-inicial/responder", ["POST"]) # Responder examen
```

### Rutas Faltantes (4)
```python
❌ @app.route("/rutas/lista", ["GET"])              # NUEVA
❌ @app.route("/crear-ruta", ["POST"])              # NUEVA (reemplaza /upload)
❌ @app.route("/ruta/<ruta_id>/actualizar", ["PUT"])# NUEVA (OPCIONAL)
❌ @app.route("/ruta/<ruta_id>", ["DELETE"])        # NUEVA (OPCIONAL)
```

### Importaciones Necesarias
```python
# Agregar:
from bson.objectid import ObjectId  # Para manejar _id
import json                          # Para respuestas
```

### Validaciones a Agregar
```python
# En POST /crear-ruta:
✅ Validar nombre_ruta no vacío + max 100 chars
✅ Validar descripcion max 500 chars
✅ Validar nombre_ruta único por usuario
✅ Validar al menos 1 archivo
✅ Validar tipo de archivo (.pdf, .docx, .pptx)
✅ Validar tamaño máximo 50MB por archivo
✅ Validar usuario autenticado
```

### Estructura esperada de respuestas
```python
GET /rutas/lista
  200: {
    "rutas": [
      {
        "ruta_id": "str",
        "nombre_ruta": "str",
        "descripcion": "str",
        "estado": "ACTIVA|PAUSADA|COMPLETADA",
        "progreso": number,
        "archivos_count": number,
        "niveles_completados": number,
        "fecha_actualizacion": "date"
      }
    ]
  }

POST /crear-ruta
  201: {
    "ruta_id": "str",
    "nombre_ruta": "str",
    "estado": "EXAMEN_PENDIENTE|ACTIVA",
    "mensaje": "str"
  }
  400: { "error": "str" }
  409: { "error": "Nombre ya existe" }
```

---

## 📄 src/web_utils.py (596 líneas)

### Estado General
✅ **Muy bien implementado**  
✅ **Funciones de IA integradas**  
✅ **Manejo robusto de errores**  
❌ **Falta:** 2 funciones nuevas

### Funciones Existentes (12)
```python
✅ procesar_archivo_web()              # Ingesta 1 archivo
✅ guardar_imagen_gridfs()             # Almacenamiento imágenes
✅ auto_etiquetar_bloom()              # IA Bloom
✅ obtener_contexto_usuario()          # Contexto para IA
✅ generar_examen_inicial()            # Examen diagnóstico
✅ generar_bloque_ruta()               # Bloques por nivel
✅ generar_ruta_aprendizaje()          # Orquestador principal
✅ _crear_examen_minimo()              # Fallback examen
✅ _crear_ruta_minima()                # Fallback ruta
✅ procesar_respuesta_examen_web()     # Evaluación
✅ obtener_ruta_personalizada_web()    # Ruta personalizada
✅ obtener_perfil_estudiante_zdp()     # Perfil estudiante
```

### Funciones Faltantes (2)
```python
❌ procesar_multiples_archivos_web(archivos_list, usuario, db)
   - Itera lista de archivos
   - Llama procesar_archivo_web() para cada uno
   - Acumula resultados
   - Retorna: (bool, List[str], str)

❌ obtener_rutas_usuario(usuario, db)
   - Query a colección "rutas_aprendizaje"
   - Filtra por usuario
   - Ordena por fecha_actualizacion DESC
   - Retorna: List[dict] con metadata
```

### Constantes a Usar
```python
# Existentes y listos:
✅ JERARQUIA_BLOOM = ["Recordar", "Comprender", "Aplicar", "Analizar", "Evaluar", "Crear"]
✅ COL_EXAM_INI = "examen_inicial"
✅ COL_RUTAS = "rutas_aprendizaje"
✅ COL_RAW = "materiales_crudos"
```

### Detalles de Implementación

#### Función: `procesar_multiples_archivos_web()`
```python
Entrada:
  - archivos_rutas_list: List[str] - Rutas locales de 1+ archivo
  - usuario: str
  - db: Database

Salida:
  - (bool, List[dict], str) 
  - List[dict] contiene: {"nombre": str, "unidades": int, "estado": "OK"|"ERROR"}

Lógica:
  1. Itera cada archivo
  2. Valida tipo y tamaño
  3. Llama procesar_archivo_web()
  4. Si OK: agrega a lista
  5. Si ERROR: registra pero continúa
  6. Retorna resumen
```

#### Función: `obtener_rutas_usuario()`
```python
Entrada:
  - usuario: str
  - db: Database

Salida:
  - List[dict] con estructura:
    {
      "ruta_id": str(ObjectId),
      "nombre_ruta": str,
      "descripcion": str,
      "estado": str,
      "progreso": number,
      "niveles_completados": int,
      "archivos_count": int,
      "fecha_actualizacion": datetime
    }

Query MongoDB:
  db["rutas_aprendizaje"].find(
    {"usuario": usuario},
    {projection: fields necesarios}
  ).sort("fecha_actualizacion", -1)
```

### Notas de Implementación
- ✅ Todas las funciones usan `datetime.datetime.utcnow()` - mantener consistencia
- ✅ Logging con logger.info/warning/error - mantener
- ✅ Manejo de excepciones con try-except - required
- ✅ JSON serialization para MongoDB - importante
- ✅ Validación de inputs - critical

---

## 📄 src/database.py (191 líneas)

### Estado General
✅ **Excelente implementación**  
✅ **Singleton pattern correcto**  
✅ **Health checks incluidos**  
✅ **No requiere cambios**

### Funciones Disponibles
```python
✅ DatabaseConnection.__init__()    # Singleton
✅ DatabaseConnection._connect()    # Conexión
✅ DatabaseConnection._health_check()
✅ DatabaseConnection.get_client()
✅ DatabaseConnection.get_database()
✅ DatabaseConnection.close()
✅ DatabaseConnection.reconnect()
✅ DatabaseConnection.is_connected()
✅ get_database_connection()        # Factory
✅ get_database()                   # Convenience
✅ get_mongo_client()               # Convenience
```

### Configuración MongoDB
```python
# Desde src/config:
✅ MONGO_URI = "mongodb://..."
✅ MONGODB_POOL_SIZE = 50
✅ MONGODB_CONNECT_TIMEOUT = 5000
✅ MONGODB_SOCKET_TIMEOUT = 5000
✅ MONGODB_MAX_POOL_SIZE = 50
✅ MONGODB_MIN_POOL_SIZE = 10
✅ DB_NAME = "RUTEALO"
```

### Validación de Conexión
```
✅ Pooling configurado correctamente
✅ Retry logic implementado
✅ Error handling robust
✅ No cambios necesarios
```

---

## 📄 src/templates/dashboard.html (452 líneas)

### Estado General
⚠️ **Necesita rediseño completo para flujo**  
✅ **Examen y ruta rendering funcionan**  
❌ **UI confusa para crear/seleccionar ruta**

### Secciones Existentes
```html
✅ Panel subida (col-md-4)              # ELIMINAR COMPLETAMENTE
✅ Panel archivos (col-md-8)            # MODIFICAR O ELIMINAR
✅ Sección ruta aprendizaje             # MANTENER LÓGICA, MOVER
✅ Modal ver archivos                   # MANTENER (pero opcional)
✅ Estilos CSS                          # MANTENER + AGREGAR
✅ JavaScript existente                 # MANTENER, AGREGAR MÁS
```

### HTML a ELIMINAR
```html
<!-- Líneas ~4-30: Panel izquierdo col-md-4 con form /upload -->
<div class="col-md-4 mb-4" style="overflow: hidden;">
  <div class="card h-100" style="display: flex; flex-direction: column;">
    <!-- TODO esto se elimina -->
  </div>
</div>
```

### HTML a AGREGAR

#### 1. Intro Section (TOP)
```html
<section class="dashboard-intro mb-4">
  <div class="card">
    <div class="card-body text-center">
      <h1 class="mb-3">📚 Ruta de Aprendizaje Personalizada</h1>
      <p class="lead mb-4">Crea una nueva ruta basada en tus materiales o continúa con una anterior</p>
      
      <div class="d-grid gap-3 d-sm-flex justify-content-sm-center">
        <button class="btn btn-primary btn-lg" id="btnCrearNuevaRuta">
          ➕ Crear Nueva Ruta
        </button>
        <button class="btn btn-success btn-lg" id="btnElegirRutaExistente">
          📂 Elegir Ruta Existente
        </button>
      </div>
    </div>
  </div>
</section>
```

#### 2. Modal "Crear Ruta"
```html
<div class="modal fade" id="modalCrearRuta" tabindex="-1" aria-labelledby="modalCrearRutaLabel" aria-hidden="true">
  <div class="modal-dialog">
    <div class="modal-content">
      <!-- Header, Body, Footer -->
      <!-- Con: nombre input, descripcion textarea, file input, preview, buttons -->
    </div>
  </div>
</div>
```

#### 3. Modal "Listar Rutas"
```html
<div class="modal fade" id="modalListaRutas" tabindex="-1" aria-labelledby="modalListaRutasLabel" aria-hidden="true">
  <div class="modal-dialog modal-lg">
    <div class="modal-content">
      <!-- Header, Body (contenedorRutas), Footer -->
    </div>
  </div>
</div>
```

### JavaScript Existente a MANTENER
```javascript
✅ let estadoRuta = null;
✅ let examenActual = null;
✅ let isLoading = false;

✅ function cargarEstadoRuta() { ... }
✅ function cargarExamenInicial() { ... }
✅ function renderExamen(contenido) { ... }
✅ function renderRuta() { ... }

✅ document.addEventListener('DOMContentLoaded', () => { ... })
```

### JavaScript a AGREGAR (8 funciones)
```javascript
❌ function abrirModalCrearRuta() { }
❌ function actualizarPreviewArchivos() { }
❌ function validarFormularioCrearRuta(form) { }
❌ function enviarFormularioCrearRuta(e) { }
❌ function cargarListaRutas() { }
❌ function renderizarListaRutas(rutas) { }
❌ function continuarRuta(rutaId) { }
❌ function verDetallesRuta(rutaId) { }
```

### CSS a AGREGAR
```css
❌ .dashboard-intro { /* styling */ }
❌ .ruta-card { /* card styling */ }
❌ .progress-bar { /* colors */ }
❌ .badge { /* estado colors */ }
❌ @media (max-width: 768px) { /* mobile */ }
```

---

## 📄 src/config.py

### Estado General
✅ **No requiere cambios**

### Variables Críticas Disponibles
```python
✅ COLS = {
    "RAW": "materiales_crudos",
    "EXAM_INI": "examen_inicial",
    "RUTAS": "rutas_aprendizaje",
    "PERFIL": "usuario_perfil",
    ...
}

✅ RAW_DIR = Path to data/raw/
✅ DB_NAME = "RUTEALO"
✅ SECRET_KEY = "..."
✅ DEBUG = True|False
✅ UPLOAD_FOLDER configurado
```

---

## 📄 src/models/evaluacion_zdp.py

### Estado General
✅ **No requiere cambios para esta fase**

### Funciones Disponibles (por referencia)
```python
✅ EvaluadorZDP.evaluar_examen()
✅ EvaluadorZDP.generar_ruta_personalizada()
✅ obtener_perfil_zdp()
```

---

## 📊 RESUMEN DE CAMBIOS

| Archivo | Líneas | +Código | +Funciones | +Endpoints | Riesgo |
|---------|--------|---------|-----------|-----------|--------|
| `app.py` | 544 | +200 | 0 | +4 | 🟡 Med |
| `web_utils.py` | 596 | +60 | +2 | 0 | 🟢 Bajo |
| `dashboard.html` | 452 | +300 | +8 | 0 | 🟡 Med |
| `database.py` | 191 | 0 | 0 | 0 | 🟢 Bajo |
| `config.py` | N/A | 0 | 0 | 0 | 🟢 Bajo |
| Schema MongoDB | N/A | +5 campos | 0 | 0 | 🟢 Bajo |

---

## 🎯 LISTA DE VERIFICACIÓN TÉCNICA

### Pre-implementación
- [ ] Tener backup de código actual (git)
- [ ] Ambiente de desarrollo limpio
- [ ] Venv activado
- [ ] Dependencies instaladas
- [ ] Database accesible

### Durante implementación
- [ ] Seguir orden: Backend → Frontend
- [ ] Test cada función después de crear
- [ ] Commits frecuentes
- [ ] Documentar cambios
- [ ] No eliminar código viejo aún

### Post-implementación
- [ ] Todos los endpoints responden
- [ ] No hay regresiones
- [ ] UI funciona como esperado
- [ ] Errores manejados correctamente
- [ ] Documentación actualizada

---

**Análisis completado:** 2025-12-10  
**Siguiente:** Iniciar FASE 1 (Backend)

