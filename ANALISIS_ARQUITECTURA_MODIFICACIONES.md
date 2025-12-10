# 🔍 ANÁLISIS DE ARQUITECTURA - Modificaciones Necesarias

**Fecha:** 2025-12-10  
**Objetivo:** Identificar todas las modificaciones necesarias para implementar el rediseño del dashboard

---

## 📊 ESTADO ACTUAL DEL CÓDIGO

### 1. **BACKEND - src/app.py**

#### ✅ Rutas Existentes:
- `GET /` - Landing page
- `GET/POST /register` - Registro de usuarios
- `GET/POST /login` - Login
- `GET /logout` - Logout
- `GET /dashboard` - Dashboard principal
- `POST /upload` - Subir un archivo
- `GET /files` - Listar archivos del usuario
- `GET /download/<archivo>` - Descargar archivo
- `GET /ruta/estado` - Estado de ruta y examen
- `GET /examen-inicial` - Obtener examen
- `POST /examen-inicial/responder` - Responder examen

#### ❌ Rutas FALTANTES (para Plan Rediseño):
1. `GET /rutas/lista` - Listar rutas existentes del usuario
2. `POST /crear-ruta` - Crear ruta con múltiples archivos + nombre + descripción
3. `PUT /ruta/<ruta_id>/actualizar` - Actualizar nombre/descripción (OPCIONAL)
4. `DELETE /ruta/<ruta_id>` - Eliminar ruta (OPCIONAL)

---

### 2. **BACKEND - src/database.py**

#### ✅ Estado Actual:
- Singleton pattern implementado
- Pooling y conexión lista
- Health checks
- Métodos: `get_database()`, `get_database_connection()`, `get_mongo_client()`

#### ❌ Faltante - Schema BD:
**Problema:** Las rutas NO tienen campos de identificación/metadatos

**Campos a AGREGAR en colección `rutas_aprendizaje`:**
```json
{
  "_id": ObjectId,
  "usuario": "string",
  "nombre_ruta": "string (NUEVO - required)",
  "descripcion": "string (NUEVO - optional, max 500)",
  "estado": "enum: ACTIVA|PAUSADA|COMPLETADA (NUEVO)",
  "archivos_fuente": [
    {
      "nombre_archivo": "string",
      "tamaño": "number (MB)",
      "fecha_subida": "date"
    }
  ],
  "estructura_ruta": {...},
  "metadatos_ruta": {...},
  "progreso_global": "number",
  "fecha_creacion": "date (NUEVO)",
  "fecha_actualizacion": "date (EXISTING - usar para ordenamiento)",
  
  // Índices a crear:
  // db.rutas_aprendizaje.createIndex({ usuario: 1, nombre_ruta: 1 }, { unique: true })
  // db.rutas_aprendizaje.createIndex({ usuario: 1, fecha_actualizacion: -1 })
}
```

---

### 3. **BACKEND - src/web_utils.py**

#### ✅ Funciones Existentes:
- `procesar_archivo_web()` - Ingesta de un archivo
- `auto_etiquetar_bloom()` - Etiquetado Bloom
- `generar_ruta_aprendizaje()` - Generación de ruta
- `generar_examen_inicial()` - Examen diagnóstico
- `generar_bloque_ruta()` - Bloques por nivel
- `_crear_examen_minimo()` - Fallback
- `_crear_ruta_minima()` - Fallback
- `procesar_respuesta_examen_web()` - Evaluación examen
- `obtener_perfil_estudiante_zdp()` - Perfil ZDP

#### ❌ Modificaciones Necesarias:

**PROBLEMA 1: `procesar_archivo_web()` procesa un solo archivo**
- Actualmente: Recibe `(ruta_archivo, usuario, db)`
- CAMBIO: Mantener igual para compatibilidad, pero necesitamos versión para múltiples

**SOLUCIÓN:** Crear nueva función:
```python
def procesar_multiples_archivos_web(archivos_rutas_list, usuario, db):
    """
    Procesa múltiples archivos en una sola operación.
    
    Args:
        archivos_rutas_list: List[str] - Rutas locales de archivos
        usuario: str - Usuario propietario
        db: Database - Conexión MongoDB
    
    Returns:
        Tuple[bool, List[str], str] - (éxito, lista_nombres_procesados, mensaje)
    """
    # Procesar cada uno, acumular resultados
    # Retornar lista de éxitos
```

**PROBLEMA 2: Falta endpoint para listar rutas**
- SOLUCIÓN: Crear función helper en web_utils.py:
```python
def obtener_rutas_usuario(usuario, db):
    """
    Lista todas las rutas del usuario con metadata.
    
    Returns:
        List[dict] - Rutas con: ruta_id, nombre, descripción, progreso, estado, etc.
    """
    col = db[COLS["RUTAS"]]
    rutas = list(col.find(
        {"usuario": usuario},
        {
            "nombre_ruta": 1,
            "descripcion": 1,
            "estado": 1,
            "progreso_global": 1,
            "fecha_actualizacion": 1,
            "metadatos_ruta.niveles_incluidos": 1,
        }
    ).sort("fecha_actualizacion", -1))
    
    return [
        {
            "ruta_id": str(r["_id"]),
            "nombre_ruta": r.get("nombre_ruta", "Sin nombre"),
            "descripcion": r.get("descripcion", ""),
            "estado": r.get("estado", "ACTIVA"),
            "progreso": r.get("progreso_global", 0),
            "niveles_completados": len(r.get("metadatos_ruta", {}).get("niveles_incluidos", [])),
            "archivos_count": len(r.get("archivos_fuente", [])),
            "fecha_actualizacion": r.get("fecha_actualizacion"),
        }
        for r in rutas
    ]
```

---

### 4. **FRONTEND - src/templates/dashboard.html**

#### ✅ Estado Actual:
- Sección de subida (col-md-4)
- Tabla de archivos (col-md-8)
- Sección de ruta de aprendizaje
- Funciones JS: `cargarEstadoRuta()`, `renderExamen()`, `renderRuta()`

#### ❌ Cambios Necesarios:

**CAMBIO 1: Eliminar formulario de subida del top (col-md-4)**
- Actualmente: Panel izquierdo con form POST /upload
- CAMBIO: Eliminar completamente de la vista inicial

**CAMBIO 2: Reemplazar intro**
- Crear sección "dashboard-intro" con descripción
- Crear dos botones principales:
  - "➕ Crear Nueva Ruta" → Abre Modal
  - "📂 Elegir Ruta Existente" → Abre Modal

**CAMBIO 3: Modal "Crear Nueva Ruta"**
```html
<div class="modal fade" id="modalCrearRuta" tabindex="-1">
  <div class="modal-dialog">
    <div class="modal-content">
      <div class="modal-header">
        <h5 class="modal-title">➕ Crear Nueva Ruta de Aprendizaje</h5>
      </div>
      <div class="modal-body">
        <form id="formCrearRuta" enctype="multipart/form-data">
          
          <!-- Input: Nombre Ruta -->
          <div class="mb-3">
            <label for="nombreRuta" class="form-label">Nombre de la Ruta *</label>
            <input type="text" class="form-control" id="nombreRuta" 
                   name="nombre_ruta" required maxlength="100" 
                   placeholder="p.ej. Biología Celular">
            <small class="form-text text-muted">Máximo 100 caracteres</small>
          </div>
          
          <!-- Textarea: Descripción -->
          <div class="mb-3">
            <label for="descripcionRuta" class="form-label">Descripción (opcional)</label>
            <textarea class="form-control" id="descripcionRuta" 
                      name="descripcion" maxlength="500" rows="3"
                      placeholder="Describe brevemente el tema..."></textarea>
            <small class="form-text text-muted">Máximo 500 caracteres</small>
          </div>
          
          <!-- File Input: Archivos -->
          <div class="mb-3">
            <label for="archivosRuta" class="form-label">Archivos (PDF, DOCX, PPTX) *</label>
            <input type="file" class="form-control" id="archivosRuta" 
                   name="archivos" multiple required
                   accept=".pdf,.docx,.pptx">
            <small class="form-text text-muted">Máximo 50MB por archivo</small>
          </div>
          
          <!-- Preview Archivos -->
          <div id="previewArchivos" class="mb-3"></div>
          
          <!-- Botones -->
          <div class="d-grid gap-2">
            <button type="submit" class="btn btn-primary">
              🚀 Generar Ruta
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

**CAMBIO 4: Modal "Listar Rutas"**
```html
<div class="modal fade" id="modalListaRutas" tabindex="-1">
  <div class="modal-dialog modal-lg">
    <div class="modal-content">
      <div class="modal-header">
        <h5 class="modal-title">📂 Tus Rutas de Aprendizaje</h5>
      </div>
      <div class="modal-body">
        <!-- Contenedor de rutas (se llena con JS) -->
        <div id="contenedorRutas"></div>
      </div>
    </div>
  </div>
</div>
```

**Estructura de cada tarjeta de ruta:**
```html
<div class="card mb-3">
  <div class="card-body">
    <div class="d-flex justify-content-between align-items-start mb-2">
      <div>
        <h6 class="card-title mb-1">{{ nombre_ruta }}</h6>
        <p class="card-text text-muted small">{{ descripcion }}</p>
      </div>
      <span class="badge bg-{{ estado_color }}">{{ estado }}</span>
    </div>
    
    <!-- Progress Bar -->
    <div class="progress mb-3" style="height: 20px;">
      <div class="progress-bar bg-success" style="width: {{ progreso }}%">
        {{ progreso }}%
      </div>
    </div>
    
    <!-- Metadata -->
    <div class="small text-muted mb-3">
      📁 {{ archivos_count }} archivos | 
      📚 {{ niveles_completados }} niveles |
      ⏰ {{ fecha_actualizacion }}
    </div>
    
    <!-- Botones -->
    <div class="d-flex gap-2">
      <button class="btn btn-sm btn-primary" onclick="continuarRuta('{{ ruta_id }}')">
        ▶️ Continuar
      </button>
      <button class="btn btn-sm btn-outline-secondary" onclick="verDetallesRuta('{{ ruta_id }}')">
        ℹ️ Detalles
      </button>
    </div>
  </div>
</div>
```

---

### 5. **FRONTEND - JavaScript en dashboard.html**

#### ❌ Funciones a CREAR:

**1. `abrirModalCrearRuta()`**
```javascript
function abrirModalCrearRuta() {
    document.getElementById('formCrearRuta').reset();
    document.getElementById('previewArchivos').innerHTML = '';
    const modal = new bootstrap.Modal(document.getElementById('modalCrearRuta'));
    modal.show();
}
```

**2. `actualizarPreviewArchivos()`**
```javascript
document.getElementById('archivosRuta').addEventListener('change', function(e) {
    const preview = document.getElementById('previewArchivos');
    const archivos = e.target.files;
    
    if (archivos.length === 0) {
        preview.innerHTML = '';
        return;
    }
    
    let html = '<div class="alert alert-info"><strong>Archivos seleccionados:</strong><ul>';
    for (let f of archivos) {
        const sizeMB = (f.size / 1024 / 1024).toFixed(2);
        html += `<li>${f.name} (${sizeMB} MB)</li>`;
    }
    html += '</ul></div>';
    preview.innerHTML = html;
});
```

**3. `validarFormularioCrearRuta()`**
```javascript
function validarFormularioCrearRuta(form) {
    const nombre = form.get('nombre_ruta').trim();
    const archivos = document.getElementById('archivosRuta').files;
    
    if (!nombre) {
        alert('⚠️ El nombre de la ruta es requerido');
        return false;
    }
    
    if (nombre.length > 100) {
        alert('⚠️ Nombre muy largo (máx 100 caracteres)');
        return false;
    }
    
    if (archivos.length === 0) {
        alert('⚠️ Debes seleccionar al menos un archivo');
        return false;
    }
    
    // Validar tamaño total
    let totalSize = 0;
    for (let f of archivos) {
        totalSize += f.size;
        if (f.size > 50 * 1024 * 1024) {
            alert(`⚠️ ${f.name} es demasiado grande (máx 50MB)`);
            return false;
        }
    }
    
    return true;
}
```

**4. `enviarFormularioCrearRuta()`**
```javascript
document.getElementById('formCrearRuta').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const form = new FormData(e.target);
    
    if (!validarFormularioCrearRuta(form)) {
        return;
    }
    
    const btn = e.target.querySelector('button[type="submit"]');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Generando...';
    
    try {
        const resp = await fetch('/crear-ruta', {
            method: 'POST',
            body: form
        });
        
        if (!resp.ok) {
            const err = await resp.json().catch(() => ({}));
            alert('❌ ' + (err.error || 'Error creando ruta'));
            return;
        }
        
        const data = await resp.json();
        alert('✅ Ruta creada exitosamente');
        
        // Cerrar modal
        bootstrap.Modal.getInstance(document.getElementById('modalCrearRuta')).hide();
        
        // Recargar lista de rutas
        cargarListaRutas();
        
    } catch (error) {
        alert('❌ Error: ' + error.message);
    } finally {
        btn.disabled = false;
        btn.innerHTML = '🚀 Generar Ruta';
    }
});
```

**5. `cargarListaRutas()`**
```javascript
async function cargarListaRutas() {
    const cont = document.getElementById('contenedorRutas');
    cont.innerHTML = '<div class="text-center"><div class="spinner-border"></div></div>';
    
    const modal = new bootstrap.Modal(document.getElementById('modalListaRutas'));
    modal.show();
    
    try {
        const resp = await fetch('/rutas/lista');
        if (!resp.ok) throw new Error('Error cargando rutas');
        
        const data = await resp.json();
        renderizarListaRutas(data.rutas);
        
    } catch (error) {
        cont.innerHTML = `<div class="alert alert-danger">${error.message}</div>`;
    }
}
```

**6. `renderizarListaRutas(rutas)`**
```javascript
function renderizarListaRutas(rutas) {
    const cont = document.getElementById('contenedorRutas');
    
    if (!rutas || rutas.length === 0) {
        cont.innerHTML = '<div class="alert alert-info">No hay rutas aún. ¡Crea una!</div>';
        return;
    }
    
    let html = '';
    rutas.forEach(ruta => {
        const colorEstado = {
            'ACTIVA': 'primary',
            'PAUSADA': 'warning',
            'COMPLETADA': 'success'
        }[ruta.estado] || 'secondary';
        
        html += `
        <div class="card mb-3">
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-start mb-2">
                    <div>
                        <h6 class="card-title mb-1">${escapeHtml(ruta.nombre_ruta)}</h6>
                        <p class="card-text text-muted small">${escapeHtml(ruta.descripcion || '')}</p>
                    </div>
                    <span class="badge bg-${colorEstado}">${ruta.estado}</span>
                </div>
                
                <div class="progress mb-3" style="height: 20px;">
                    <div class="progress-bar bg-success" style="width: ${ruta.progreso}%">
                        ${ruta.progreso}%
                    </div>
                </div>
                
                <div class="small text-muted mb-3">
                    📁 ${ruta.archivos_count} archivos | 
                    📚 ${ruta.niveles_completados} niveles |
                    ⏰ ${new Date(ruta.fecha_actualizacion).toLocaleDateString()}
                </div>
                
                <div class="d-flex gap-2">
                    <button class="btn btn-sm btn-primary" onclick="continuarRuta('${ruta.ruta_id}')">
                        ▶️ Continuar
                    </button>
                    <button class="btn btn-sm btn-outline-secondary" onclick="verDetallesRuta('${ruta.ruta_id}')">
                        ℹ️ Detalles
                    </button>
                </div>
            </div>
        </div>
        `;
    });
    
    cont.innerHTML = html;
}
```

**7. `continuarRuta(rutaId)`**
```javascript
async function continuarRuta(rutaId) {
    // Cerrar modal de lista
    const modal = bootstrap.Modal.getInstance(document.getElementById('modalListaRutas'));
    if (modal) modal.hide();
    
    // Cargar la ruta (simular click en "Iniciar ruta")
    // O ir directamente a cargar examen/contenido
    window.location.href = `/dashboard?ruta=${rutaId}`;
}
```

**8. `verDetallesRuta(rutaId)`**
```javascript
function verDetallesRuta(rutaId) {
    // Mostrar modal con detalles
    // Por ahora, solo log
    console.log('Detalles de ruta:', rutaId);
    alert('Función en desarrollo: Ver detalles de ' + rutaId);
}
```

---

## 📋 RESUMEN DE CAMBIOS

### Backend (src/app.py)
| Tarea | Prioridad | Estimado |
|-------|-----------|----------|
| Agregar `GET /rutas/lista` | 🔴 Alta | 30 min |
| Agregar `POST /crear-ruta` | 🔴 Alta | 45 min |
| Validar estructura de datos | 🟡 Media | 20 min |
| **SUBTOTAL** | | **95 min** |

### Backend (src/web_utils.py)
| Tarea | Prioridad | Estimado |
|-------|-----------|----------|
| Crear `procesar_multiples_archivos_web()` | 🔴 Alta | 20 min |
| Crear `obtener_rutas_usuario()` | 🔴 Alta | 15 min |
| **SUBTOTAL** | | **35 min** |

### Backend (Database)
| Tarea | Prioridad | Estimado |
|-------|-----------|----------|
| Agregar campos a schema | 🔴 Alta | 10 min |
| Crear índices | 🔴 Alta | 5 min |
| Migrar rutas existentes | 🟡 Media | 15 min |
| **SUBTOTAL** | | **30 min** |

### Frontend (HTML)
| Tarea | Prioridad | Estimado |
|-------|-----------|----------|
| Rediseñar estructura intro | 🔴 Alta | 20 min |
| Crear Modal "Crear Ruta" | 🔴 Alta | 30 min |
| Crear Modal "Listar Rutas" | 🔴 Alta | 30 min |
| Estilos CSS | 🟡 Media | 20 min |
| **SUBTOTAL** | | **100 min** |

### Frontend (JavaScript)
| Tarea | Prioridad | Estimado |
|-------|-----------|----------|
| Funciones de state (`abrirModalCrearRuta`, etc.) | 🔴 Alta | 40 min |
| Funciones de formulario (validar, enviar) | 🔴 Alta | 50 min |
| Funciones de ruta (cargar, renderizar) | 🔴 Alta | 50 min |
| Event listeners | 🟡 Media | 15 min |
| Error handling mejorado | 🟡 Media | 20 min |
| **SUBTOTAL** | | **175 min** |

---

## 🎯 ORDEN DE IMPLEMENTACIÓN RECOMENDADO

1. **BACKEND PRIMERO** (160 min total)
   - Agregar campos + índices BD
   - Crear funciones en web_utils.py
   - Crear endpoints en app.py

2. **FRONTEND DESPUÉS** (275 min total)
   - Rediseñar HTML
   - Agregar modales
   - Implementar JavaScript

3. **TESTING E INTEGRACIÓN** (60+ min)

**TOTAL ESTIMADO: 7-9 horas**

---

## ✅ CRITERIOS DE ÉXITO

- [x] Usuarios pueden crear rutas con nombre, descripción y múltiples archivos
- [x] Usuarios pueden listar sus rutas existentes
- [x] Validación de inputs (nombre, descripción, archivos)
- [x] Progreso visual en tarjetas de ruta
- [x] Examen auto-trigger funciona con rutas nuevas y existentes
- [x] Manejo de errores y mensajes claros
- [x] Responsive en móvil
- [x] Sin regresiones en funcionalidad existente

---

**Próximo paso:** Iniciar con FASE 1 (Backend) siguiendo este análisis

