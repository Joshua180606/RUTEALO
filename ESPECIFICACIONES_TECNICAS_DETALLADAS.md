# 🔧 ESPECIFICACIONES TÉCNICAS DETALLADAS

**Documento de referencia técnica** para la implementación del rediseño  
**Fecha:** 2025-12-10

---

## 📌 ÍNDICE RÁPIDO
1. [Schema MongoDB](#schema)
2. [Funciones Backend](#funciones)
3. [Endpoints API](#endpoints)
4. [HTML/CSS Frontend](#html)
5. [JavaScript Frontend](#javascript)

---

## <a name="schema"></a> 📦 SCHEMA MONGODB

### Cambios a Colección: `rutas_aprendizaje`

#### Campos a AGREGAR (5 nuevos)
```javascript
{
  // Existentes (mantener):
  _id: ObjectId,
  usuario: string,
  estructura_ruta: { ... },
  metadatos_ruta: { ... },
  fecha_actualizacion: date,
  
  // NUEVOS:
  nombre_ruta: {
    type: string,
    required: true,
    minLength: 1,
    maxLength: 100,
    description: "Identificador amigable de la ruta"
  },
  
  descripcion: {
    type: string,
    required: false,
    maxLength: 500,
    default: "",
    description: "Descripción breve del contenido"
  },
  
  estado: {
    type: string,
    enum: ["ACTIVA", "PAUSADA", "COMPLETADA"],
    default: "ACTIVA",
    description: "Estado de la ruta"
  },
  
  archivos_fuente: {
    type: array,
    items: {
      nombre_archivo: string,
      tamaño: number,        // en MB
      fecha_subida: date,
      tipo: string           // pdf|docx|pptx
    },
    default: [],
    description: "Lista de archivos que generaron esta ruta"
  },
  
  fecha_creacion: {
    type: date,
    required: true,
    default: datetime.utcnow(),
    description: "Cuándo se creó la ruta"
  }
}
```

#### Índices a CREAR
```javascript
// Índice 1: Unicidad de nombre por usuario
db.rutas_aprendizaje.createIndex(
  { usuario: 1, nombre_ruta: 1 },
  { unique: true }
)

// Índice 2: Ordenamiento por fecha (para listados)
db.rutas_aprendizaje.createIndex(
  { usuario: 1, fecha_actualizacion: -1 }
)
```

#### Migración de Rutas Existentes
```javascript
// Script para asignar nombres/fechas a rutas antiguas
db.rutas_aprendizaje.updateMany(
  { nombre_ruta: { $exists: false } },
  [
    {
      $set: {
        nombre_ruta: {
          $concat: [
            "Ruta ",
            { $toString: { $toDate: "$_id" } }
          ]
        },
        estado: "ACTIVA",
        archivos_fuente: [],
        fecha_creacion: { $toDate: "$_id" }
      }
    }
  ]
)
```

---

## <a name="funciones"></a> 🔧 FUNCIONES BACKEND (web_utils.py)

### Función 1: `procesar_multiples_archivos_web()`

**Ubicación:** Añadir a `src/web_utils.py` después de `procesar_archivo_web()`

**Firma:**
```python
def procesar_multiples_archivos_web(archivos_rutas: List[str], usuario: str, db) -> Tuple[bool, List[dict], str]:
    """
    Procesa múltiples archivos en una operación.
    
    Args:
        archivos_rutas: Lista de rutas locales de archivos
        usuario: ID del usuario propietario
        db: Instancia de Database
    
    Returns:
        (éxito: bool, archivos_procesados: List[dict], mensaje: str)
        
    Formato de retorno:
        [
            {
                "nombre": "documento.pdf",
                "unidades": 10,
                "estado": "OK",
                "error": null
            },
            {
                "nombre": "invalido.txt",
                "unidades": 0,
                "estado": "ERROR",
                "error": "Formato no soportado"
            }
        ]
    """
    resultados = []
    total_unidades = 0
    
    for ruta_archivo in archivos_rutas:
        try:
            # Validar archivo
            if not os.path.exists(ruta_archivo):
                resultados.append({
                    "nombre": os.path.basename(ruta_archivo),
                    "unidades": 0,
                    "estado": "ERROR",
                    "error": "Archivo no encontrado"
                })
                continue
            
            # Procesar
            ok, msg = procesar_archivo_web(ruta_archivo, usuario, db)
            
            if ok:
                resultados.append({
                    "nombre": os.path.basename(ruta_archivo),
                    "unidades": msg,  # msg contiene cantidad de unidades
                    "estado": "OK",
                    "error": None
                })
                total_unidades += msg
            else:
                resultados.append({
                    "nombre": os.path.basename(ruta_archivo),
                    "unidades": 0,
                    "estado": "ERROR",
                    "error": msg
                })
        
        except Exception as e:
            logger.error(f"Error procesando {ruta_archivo}: {e}")
            resultados.append({
                "nombre": os.path.basename(ruta_archivo),
                "unidades": 0,
                "estado": "ERROR",
                "error": str(e)
            })
    
    # Determinar éxito global
    exitosos = [r for r in resultados if r["estado"] == "OK"]
    éxito = len(exitosos) > 0
    
    # Mensaje resumen
    msg_resumen = f"Procesados {len(exitosos)}/{len(archivos_rutas)} archivos ({total_unidades} unidades)"
    
    return éxito, resultados, msg_resumen
```

---

### Función 2: `obtener_rutas_usuario()`

**Ubicación:** Añadir a `src/web_utils.py` al final de las funciones de ruta

**Firma:**
```python
def obtener_rutas_usuario(usuario: str, db) -> List[dict]:
    """
    Obtiene lista de rutas del usuario con metadata.
    
    Args:
        usuario: ID del usuario
        db: Instancia de Database
    
    Returns:
        Lista de rutas ordenadas por fecha_actualizacion DESC:
        [
            {
                "ruta_id": "60d5ec49c1234567890abcde",
                "nombre_ruta": "Biología Celular",
                "descripcion": "Estudio de estructura y función...",
                "estado": "ACTIVA",
                "progreso": 45,
                "archivos_count": 3,
                "niveles_completados": 2,
                "fecha_actualizacion": datetime.datetime(...)
            },
            ...
        ]
    """
    col = db[COLS["RUTAS"]]
    
    try:
        rutas_cursor = col.find(
            {"usuario": usuario},
            {
                "_id": 1,
                "nombre_ruta": 1,
                "descripcion": 1,
                "estado": 1,
                "progreso_global": 1,
                "fecha_actualizacion": 1,
                "archivos_fuente": 1,
                "metadatos_ruta.niveles_incluidos": 1
            }
        ).sort("fecha_actualizacion", -1)
        
        rutas_list = []
        for ruta in rutas_cursor:
            niveles = ruta.get("metadatos_ruta", {}).get("niveles_incluidos", [])
            archivos = ruta.get("archivos_fuente", [])
            
            rutas_list.append({
                "ruta_id": str(ruta["_id"]),
                "nombre_ruta": ruta.get("nombre_ruta", "Sin nombre"),
                "descripcion": ruta.get("descripcion", ""),
                "estado": ruta.get("estado", "ACTIVA"),
                "progreso": ruta.get("progreso_global", 0),
                "archivos_count": len(archivos),
                "niveles_completados": len(niveles),
                "fecha_actualizacion": ruta.get("fecha_actualizacion")
            })
        
        return rutas_list
    
    except Exception as e:
        logger.error(f"Error obteniendo rutas para {usuario}: {e}")
        return []
```

---

## <a name="endpoints"></a> 🌐 ENDPOINTS API (src/app.py)

### Endpoint 1: `GET /rutas/lista`

**Ubicación:** Añadir a `src/app.py` después de `GET /ruta/estado`

**Código:**
```python
@app.route("/rutas/lista", methods=["GET"])
def listar_rutas():
    """
    Retorna lista de rutas del usuario autenticado.
    
    Response:
        200: { "rutas": [...] }
        401: { "error": "Unauthorized" }
    """
    if "usuario" not in session:
        return {"error": "Unauthorized"}, 401
    
    usuario = session["usuario"]
    
    try:
        from src.web_utils import obtener_rutas_usuario
        
        rutas = obtener_rutas_usuario(usuario, db)
        
        return {
            "rutas": rutas,
            "total": len(rutas)
        }, 200
    
    except Exception as e:
        logger.error(f"Error listando rutas para {usuario}: {e}")
        return {"error": "Error cargando rutas"}, 500
```

---

### Endpoint 2: `POST /crear-ruta`

**Ubicación:** Añadir a `src/app.py` después de `POST /upload`

**Código:**
```python
@app.route("/crear-ruta", methods=["POST"])
def crear_ruta():
    """
    Crea una nueva ruta de aprendizaje con múltiples archivos.
    
    Form Data:
        nombre_ruta: str (required, max 100)
        descripcion: str (optional, max 500)
        archivos: FileStorage[] (required, 1+)
    
    Response:
        201: { "ruta_id": "...", "nombre_ruta": "...", "estado": "...", "mensaje": "..." }
        400: { "error": "..." }
        409: { "error": "Nombre ya existe" }
    """
    if "usuario" not in session:
        return {"error": "Unauthorized"}, 401
    
    usuario = session["usuario"]
    nombre_ruta = request.form.get("nombre_ruta", "").strip()
    descripcion = request.form.get("descripcion", "").strip()
    
    # VALIDACIONES
    # 1. Validar nombre
    if not nombre_ruta:
        return {"error": "Nombre de ruta requerido"}, 400
    
    if len(nombre_ruta) > 100:
        return {"error": "Nombre muy largo (máx 100 caracteres)"}, 400
    
    # 2. Validar descripción
    if len(descripcion) > 500:
        return {"error": "Descripción muy larga (máx 500 caracteres)"}, 400
    
    # 3. Validar archivos
    if "archivos" not in request.files:
        return {"error": "No se seleccionaron archivos"}, 400
    
    archivos = request.files.getlist("archivos")
    if not archivos or all(f.filename == "" for f in archivos):
        return {"error": "Al menos un archivo requerido"}, 400
    
    # 4. Validar nombre único por usuario
    col_rutas = db[COLS["RUTAS"]]
    if col_rutas.find_one({"usuario": usuario, "nombre_ruta": nombre_ruta}):
        return {"error": "Ya existe una ruta con ese nombre"}, 409
    
    # PROCESAR ARCHIVOS
    archivos_procesados = []
    archivos_rutas = []
    ALLOWED_EXTENSIONS = {".pdf", ".docx", ".pptx"}
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    
    try:
        # Crear carpeta usuario si no existe
        crear_carpeta_usuario(usuario, str(app.config["UPLOAD_FOLDER"]))
        usuario_folder = os.path.join(str(app.config["UPLOAD_FOLDER"]), usuario)
        
        # Procesar cada archivo
        for archivo in archivos:
            # Validar nombre
            if archivo.filename == "":
                continue
            
            # Validar extensión
            filename = secure_filename(archivo.filename)
            ext = os.path.splitext(filename)[1].lower()
            
            if ext not in ALLOWED_EXTENSIONS:
                return {
                    "error": f"Tipo de archivo no permitido: {ext}"
                }, 400
            
            # Validar tamaño
            archivo.seek(0, os.SEEK_END)
            file_size = archivo.tell()
            archivo.seek(0)
            
            if file_size > MAX_FILE_SIZE:
                return {
                    "error": f"Archivo {filename} demasiado grande (máx 50MB)"
                }, 400
            
            # Guardar archivo
            filepath = os.path.join(usuario_folder, filename)
            archivo.save(filepath)
            
            # Registrar para procesamiento
            archivos_rutas.append(filepath)
            archivos_procesados.append({
                "nombre_archivo": filename,
                "tamaño": file_size / 1024 / 1024,  # MB
                "fecha_subida": datetime.datetime.utcnow(),
                "tipo": ext.replace(".", "")
            })
        
        if not archivos_rutas:
            return {"error": "No se pudieron procesar los archivos"}, 400
        
        # PROCESAR CONTENIDO
        from src.web_utils import procesar_multiples_archivos_web
        
        ok, resultados, msg_ingesta = procesar_multiples_archivos_web(
            archivos_rutas, usuario, db
        )
        
        if not ok:
            return {
                "error": f"Error procesando archivos: {msg_ingesta}"
            }, 400
        
        # ETIQUETADO BLOOM
        try:
            processed_count = auto_etiquetar_bloom(usuario, db)
            logger.info(f"Bloom tagging: {processed_count} documentos para {usuario}")
        except Exception as e:
            logger.warning(f"Bloom tagging error para {usuario}: {e}")
        
        # GENERAR RUTA Y EXAMEN
        try:
            msg_ruta = generar_ruta_aprendizaje(usuario, db)
            logger.info(f"Ruta generada para {usuario}: {msg_ruta}")
        except Exception as e:
            return {
                "error": f"Error generando ruta: {str(e)}"
            }, 500
        
        # CREAR DOCUMENTO DE RUTA
        col_rutas = db[COLS["RUTAS"]]
        
        ruta_doc = {
            "usuario": usuario,
            "nombre_ruta": nombre_ruta,
            "descripcion": descripcion,
            "estado": "ACTIVA",
            "archivos_fuente": archivos_procesados,
            "fecha_creacion": datetime.datetime.utcnow(),
            "fecha_actualizacion": datetime.datetime.utcnow(),
            # estructura_ruta y metadatos_ruta ya están creados por generar_ruta_aprendizaje()
        }
        
        # Obtener la ruta recién creada para agregar metadata
        ruta_existente = col_rutas.find_one({"usuario": usuario})
        if ruta_existente:
            ruta_doc["estructura_ruta"] = ruta_existente.get("estructura_ruta", {})
            ruta_doc["metadatos_ruta"] = ruta_existente.get("metadatos_ruta", {})
            ruta_doc["progreso_global"] = ruta_existente.get("progreso_global", 0)
        
        resultado = col_rutas.replace_one(
            {"usuario": usuario},
            ruta_doc,
            upsert=True
        )
        
        ruta_id = str(resultado.upserted_id or ruta_existente["_id"])
        
        # Verificar si hay examen pendiente
        exam_doc = db[COLS["EXAM_INI"]].find_one({"usuario": usuario})
        estado_examen = "EXAMEN_PENDIENTE" if not exam_doc or exam_doc.get("estado") != "COMPLETADO" else "ACTIVA"
        
        return {
            "ruta_id": ruta_id,
            "nombre_ruta": nombre_ruta,
            "estado": estado_examen,
            "mensaje": msg_ruta,
            "archivos_procesados": len(archivos_procesados)
        }, 201
    
    except Exception as e:
        logger.error(f"Error creando ruta para {usuario}: {e}")
        return {
            "error": f"Error al crear ruta: {str(e)}"
        }, 500
```

---

### Endpoint 3: `PUT /ruta/<ruta_id>/actualizar` (OPCIONAL)

**Ubicación:** Después de POST /crear-ruta

```python
@app.route("/ruta/<ruta_id>/actualizar", methods=["PUT"])
def actualizar_ruta(ruta_id):
    """
    Actualiza nombre y/o descripción de una ruta.
    
    JSON Body:
        {
            "nombre_ruta": "str (optional)",
            "descripcion": "str (optional)",
            "estado": "enum (optional)"
        }
    
    Response:
        200: { "mensaje": "Actualizado exitosamente" }
        400: { "error": "..." }
        404: { "error": "Ruta no encontrada" }
    """
    if "usuario" not in session:
        return {"error": "Unauthorized"}, 401
    
    usuario = session["usuario"]
    
    try:
        from bson.objectid import ObjectId
        
        ruta_id_obj = ObjectId(ruta_id)
    except:
        return {"error": "ID de ruta inválido"}, 400
    
    # Obtener datos a actualizar
    data = request.get_json(silent=True) or {}
    updates = {}
    
    # Validar y agregar campos
    if "nombre_ruta" in data:
        nombre = data["nombre_ruta"].strip()
        if not nombre:
            return {"error": "Nombre no puede estar vacío"}, 400
        if len(nombre) > 100:
            return {"error": "Nombre muy largo"}, 400
        updates["nombre_ruta"] = nombre
    
    if "descripcion" in data:
        desc = data["descripcion"].strip()
        if len(desc) > 500:
            return {"error": "Descripción muy larga"}, 400
        updates["descripcion"] = desc
    
    if "estado" in data:
        estado = data["estado"]
        if estado not in ["ACTIVA", "PAUSADA", "COMPLETADA"]:
            return {"error": "Estado inválido"}, 400
        updates["estado"] = estado
    
    if not updates:
        return {"error": "No hay campos para actualizar"}, 400
    
    # Validar que sea propietario
    col_rutas = db[COLS["RUTAS"]]
    ruta = col_rutas.find_one({
        "_id": ruta_id_obj,
        "usuario": usuario
    })
    
    if not ruta:
        return {"error": "Ruta no encontrada"}, 404
    
    # Actualizar
    try:
        updates["fecha_actualizacion"] = datetime.datetime.utcnow()
        
        result = col_rutas.update_one(
            {"_id": ruta_id_obj, "usuario": usuario},
            {"$set": updates}
        )
        
        if result.matched_count == 0:
            return {"error": "Ruta no encontrada"}, 404
        
        return {
            "mensaje": "Ruta actualizada exitosamente",
            "campos_actualizados": list(updates.keys())
        }, 200
    
    except Exception as e:
        logger.error(f"Error actualizando ruta {ruta_id}: {e}")
        return {"error": "Error al actualizar"}, 500
```

---

### Endpoint 4: `DELETE /ruta/<ruta_id>` (OPCIONAL)

```python
@app.route("/ruta/<ruta_id>", methods=["DELETE"])
def eliminar_ruta(ruta_id):
    """
    Elimina una ruta de aprendizaje.
    
    Response:
        200: { "mensaje": "Ruta eliminada" }
        404: { "error": "Ruta no encontrada" }
    """
    if "usuario" not in session:
        return {"error": "Unauthorized"}, 401
    
    usuario = session["usuario"]
    
    try:
        from bson.objectid import ObjectId
        ruta_id_obj = ObjectId(ruta_id)
    except:
        return {"error": "ID de ruta inválido"}, 400
    
    try:
        col_rutas = db[COLS["RUTAS"]]
        
        result = col_rutas.delete_one({
            "_id": ruta_id_obj,
            "usuario": usuario
        })
        
        if result.deleted_count == 0:
            return {"error": "Ruta no encontrada"}, 404
        
        return {
            "mensaje": "Ruta eliminada exitosamente"
        }, 200
    
    except Exception as e:
        logger.error(f"Error eliminando ruta {ruta_id}: {e}")
        return {"error": "Error al eliminar"}, 500
```

---

## <a name="html"></a> 🎨 HTML/CSS FRONTEND

### Cambios a `src/templates/dashboard.html`

#### ELIMINAR (Líneas ~4-30)
```html
<!-- Eliminar completamente el panel izquierdo col-md-4 -->
<!-- Esto incluye toda la sección de upload -->
```

#### AGREGAR: Intro Section (REEMPLAZAR inicio)
```html
{% extends "base.html" %}
{% block content %}

<!-- NUEVA INTRO SECTION -->
<section class="dashboard-intro mb-4">
    <div class="card border-0 shadow-sm">
        <div class="card-body text-center py-5">
            <h1 class="display-5 fw-bold mb-3">📚 Tu Ruta de Aprendizaje Personalizada</h1>
            <p class="lead text-muted mb-5">
                Crea una nueva ruta basada en tus materiales o continúa con una ruta anterior
            </p>
            
            <div class="d-grid gap-3 d-sm-flex justify-content-sm-center">
                <button class="btn btn-primary btn-lg px-5" id="btnCrearNuevaRuta">
                    <i class="bi bi-plus-circle"></i> Crear Nueva Ruta
                </button>
                <button class="btn btn-success btn-lg px-5" id="btnElegirRutaExistente">
                    <i class="bi bi-folder"></i> Elegir Ruta Existente
                </button>
            </div>
        </div>
    </div>
</section>

<!-- SECCIÓN DE RUTA (MANTENER EXISTENTE) -->
<div class="row mt-4">
    <div class="col-12">
        <div class="card">
            <div class="card-header d-flex justify-content-between align-items-center">
                <div>
                    🛤️ Ruta de Aprendizaje
                    <div class="small text-muted">Generada automáticamente al subir material</div>
                </div>
                <button class="btn btn-outline-primary" id="btnIniciarRuta">Iniciar ruta de aprendizaje</button>
            </div>
            <div class="card-body" id="rutaAprendizaje">
                <div class="text-muted">Presiona el botón para cargar tu estado de ruta y examen inicial.</div>
            </div>
        </div>
    </div>
</div>
```

#### AGREGAR: Modal "Crear Ruta"
```html
<!-- Modal: Crear Nueva Ruta -->
<div class="modal fade" id="modalCrearRuta" tabindex="-1" aria-labelledby="modalCrearRutaLabel" aria-hidden="true">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header border-bottom">
                <h5 class="modal-title" id="modalCrearRutaLabel">
                    <i class="bi bi-plus-circle"></i> Crear Nueva Ruta de Aprendizaje
                </h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            
            <div class="modal-body">
                <form id="formCrearRuta" enctype="multipart/form-data">
                    <!-- Nombre de la Ruta -->
                    <div class="mb-3">
                        <label for="nombreRuta" class="form-label fw-bold">
                            Nombre de la Ruta <span class="text-danger">*</span>
                        </label>
                        <input 
                            type="text" 
                            class="form-control" 
                            id="nombreRuta" 
                            name="nombre_ruta" 
                            required 
                            maxlength="100"
                            placeholder="p.ej. Biología Celular, Python Avanzado"
                        >
                        <small class="form-text text-muted d-block mt-1">
                            Máximo 100 caracteres. Este nombre identificará tu ruta.
                        </small>
                    </div>
                    
                    <!-- Descripción -->
                    <div class="mb-3">
                        <label for="descripcionRuta" class="form-label fw-bold">
                            Descripción (Opcional)
                        </label>
                        <textarea 
                            class="form-control" 
                            id="descripcionRuta" 
                            name="descripcion" 
                            maxlength="500" 
                            rows="3"
                            placeholder="Describe brevemente qué temas cubre esta ruta..."
                        ></textarea>
                        <small class="form-text text-muted d-block mt-1">
                            Máximo 500 caracteres
                        </small>
                    </div>
                    
                    <!-- Archivos -->
                    <div class="mb-3">
                        <label for="archivosRuta" class="form-label fw-bold">
                            Archivos <span class="text-danger">*</span>
                        </label>
                        <input 
                            type="file" 
                            class="form-control" 
                            id="archivosRuta" 
                            name="archivos" 
                            multiple 
                            required
                            accept=".pdf,.docx,.pptx"
                        >
                        <small class="form-text text-muted d-block mt-1">
                            Soporta PDF, DOCX y PPTX. Máximo 50MB por archivo.
                        </small>
                    </div>
                    
                    <!-- Preview de archivos -->
                    <div id="previewArchivos" class="mb-3"></div>
                    
                    <!-- Botones -->
                    <div class="d-grid gap-2">
                        <button type="submit" class="btn btn-primary btn-lg">
                            <i class="bi bi-rocket"></i> Generar Ruta
                        </button>
                        <button type="button" class="btn btn-outline-secondary" data-bs-dismiss="modal">
                            Cancelar
                        </button>
                    </div>
                </form>
            </div>
        </div>
    </div>
</div>
```

#### AGREGAR: Modal "Listar Rutas"
```html
<!-- Modal: Listar Rutas Existentes -->
<div class="modal fade" id="modalListaRutas" tabindex="-1" aria-labelledby="modalListaRutasLabel" aria-hidden="true">
    <div class="modal-dialog modal-lg">
        <div class="modal-content">
            <div class="modal-header border-bottom">
                <h5 class="modal-title" id="modalListaRutasLabel">
                    <i class="bi bi-folder"></i> Tus Rutas de Aprendizaje
                </h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            
            <div class="modal-body">
                <div id="contenedorRutas">
                    <!-- Llenar dinámicamente con JavaScript -->
                </div>
            </div>
        </div>
    </div>
</div>
```

#### AGREGAR: CSS Nuevos
```css
<style>
    /* Dashboard Intro */
    .dashboard-intro .card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    .dashboard-intro .card-body {
        padding: 3rem 2rem !important;
    }
    
    .dashboard-intro h1 {
        color: white;
        font-weight: 700 !important;
    }
    
    .dashboard-intro .lead {
        color: rgba(255,255,255,0.9);
    }
    
    .dashboard-intro .btn {
        font-weight: 600;
        padding: 0.75rem 1.5rem;
        border-radius: 0.5rem;
        transition: all 0.3s ease;
    }
    
    .dashboard-intro .btn-primary {
        background-color: #fff;
        color: #667eea;
    }
    
    .dashboard-intro .btn-primary:hover {
        background-color: #f0f0f0;
        transform: translateY(-2px);
        box-shadow: 0 8px 16px rgba(0,0,0,0.2);
    }
    
    .dashboard-intro .btn-success {
        background-color: #28a745;
        border-color: #28a745;
        color: white;
    }
    
    .dashboard-intro .btn-success:hover {
        background-color: #218838;
        transform: translateY(-2px);
        box-shadow: 0 8px 16px rgba(0,0,0,0.2);
    }
    
    /* Ruta Card */
    .ruta-card {
        border: 1px solid #e0e0e0;
        border-radius: 0.75rem;
        padding: 1.5rem;
        margin-bottom: 1rem;
        transition: all 0.3s ease;
        background-color: #f8f9fa;
    }
    
    .ruta-card:hover {
        border-color: #667eea;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);
        transform: translateY(-2px);
    }
    
    .ruta-card-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 1rem;
    }
    
    .ruta-card-title {
        font-weight: 600;
        font-size: 1.1rem;
        margin-bottom: 0.25rem;
    }
    
    .ruta-card-description {
        font-size: 0.9rem;
        color: #6c757d;
        margin-bottom: 0.5rem;
    }
    
    .ruta-card-meta {
        font-size: 0.85rem;
        color: #6c757d;
        display: flex;
        gap: 1rem;
        margin-bottom: 1rem;
        flex-wrap: wrap;
    }
    
    .progress-ruta {
        height: 24px;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    
    .progress-ruta .progress-bar {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: 600;
        font-size: 0.8rem;
    }
    
    .ruta-card-buttons {
        display: flex;
        gap: 0.5rem;
    }
    
    .ruta-card-buttons .btn {
        flex: 1;
    }
    
    /* Preview de archivos -->
    .file-preview-alert {
        background-color: #e7f3ff;
        border: 1px solid #b3d9ff;
        border-radius: 0.5rem;
        padding: 1rem;
    }
    
    .file-preview-list {
        list-style: none;
        padding: 0;
        margin: 0.5rem 0 0 0;
    }
    
    .file-preview-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.5rem 0;
        border-bottom: 1px solid #ccc;
    }
    
    .file-preview-item:last-child {
        border-bottom: none;
    }
    
    .file-preview-name {
        flex: 1;
        word-break: break-word;
    }
    
    .file-preview-size {
        color: #6c757d;
        font-size: 0.85rem;
        margin-left: 1rem;
        white-space: nowrap;
    }
    
    /* Modal styling */
    .modal-content {
        border-radius: 0.75rem;
        border: none;
        box-shadow: 0 10px 40px rgba(0,0,0,0.1);
    }
    
    .modal-header {
        background-color: #f8f9fa;
        border-bottom: 1px solid #dee2e6;
    }
    
    /* Responsive */
    @media (max-width: 768px) {
        .dashboard-intro .card-body {
            padding: 2rem 1rem !important;
        }
        
        .dashboard-intro h1 {
            font-size: 1.75rem;
        }
        
        .d-sm-flex {
            flex-direction: column !important;
        }
        
        .dashboard-intro .btn {
            width: 100%;
        }
        
        .ruta-card-buttons {
            flex-direction: column;
        }
        
        .ruta-card-buttons .btn {
            width: 100%;
        }
    }
</style>
```

---

## <a name="javascript"></a> 📜 JAVASCRIPT FRONTEND

Ver documento separado: `ESPECIFICACIONES_JAVASCRIPT_FRONTEND.md`

---

**Fin del documento técnico**

