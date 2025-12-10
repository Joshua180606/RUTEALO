# 📋 PLAN DE IMPLEMENTACIÓN - Dashboard Rediseñado
**Fecha:** 2025-12-10  
**Estado:** Planificación

---

## 🎯 Objetivo General

Rediseñar el dashboard para separar dos flujos principales:
1. **Crear Nueva Ruta** → Subir archivo(s) → Generar automáticamente
2. **Usar Ruta Existente** → Seleccionar de lista → Ver/Continuar estudiando

---

## 📐 Estructura de Datos

### **Modelo: Rutas de Aprendizaje (MongoDB)**

```javascript
{
  "_id": ObjectId,
  "usuario": "joshua",
  "nombre_ruta": "Matemáticas Avanzadas",        // ← Nombre custom del usuario
  "descripcion": "Ruta para aprender cálculo", // ← Descripción optional
  "archivos_fuente": [
    { "nombre_archivo": "doc1.pdf", "tamaño": 2.5, "fecha_subida": "2025-12-10" }
  ],
  "examen_generado": true,
  "examen_pendiente": true,
  "estado": "ACTIVA",  // ACTIVA, PAUSADA, COMPLETADA
  "perfil_zdp": { ... },
  "estructura_ruta": { ... },
  "metadatos_ruta": { ... },
  "fecha_creacion": "2025-12-10",
  "fecha_actualizacion": "2025-12-10",
  "progreso_global": 0,
  "horas_dedicadas": 0
}
```

**Cambios en BD:**
- Agregar campos: `nombre_ruta`, `descripcion`, `estado`
- Usar `nombre_ruta` como identificador visible (no solo usuario)

---

## 🔄 Flujos de Usuario

### **Flujo 1: Primera Vez (Crear Nueva Ruta)**

```
Usuario entra a /dashboard
    ↓
Ve descripción breve + 2 botones
    ├─ [Crear Nueva Ruta]
    └─ [Elegir Ruta Existente]
    ↓
Click "Crear Nueva Ruta"
    ↓
Modal/Página:
  1. Input: Nombre de la ruta (ej: "Matemáticas 2025")
  2. Textarea: Descripción (opcional)
  3. File Input: Uno o más archivos (PDF, DOCX, PPTX)
  4. Botón: "Generar Ruta"
    ↓
Backend: Procesa archivos
  - Ingesta
  - Etiquetado Bloom
  - Generación automática examen + ruta
    ↓
Frontend: Muestra examen diagnóstico
    ↓
Usuario responde + envía
    ↓
Ruta personalizada con flashcards
```

### **Flujo 2: Retorno (Elegir Ruta Existente)**

```
Usuario entra a /dashboard
    ↓
Click "Elegir Ruta Existente"
    ↓
Modal con lista de rutas:
  ┌─────────────────────────────────────────────────────┐
  │ Tus Rutas de Aprendizaje                            │
  ├─────────────────────────────────────────────────────┤
  │                                                     │
  │ 📚 Matemáticas Avanzadas        [Progreso: 35%]   │
  │    3 archivos | 2 niveles completados               │
  │    [Continuar Ruta]  [Ver Detalles]                │
  │                                                     │
  │ 📚 Historia del Siglo XX         [Progreso: 0%]    │
  │    1 archivo | Examen pendiente                     │
  │    [Completar Examen]  [Ver Detalles]              │
  │                                                     │
  │ 📚 Biología Marina               [Progreso: 100%]  │
  │    2 archivos | Completada                          │
  │    [Revisar]  [Ver Detalles]                       │
  │                                                     │
  └─────────────────────────────────────────────────────┘
    ↓
Usuario selecciona una ruta
    ↓
Mostrar:
  - Si examen pendiente → Examen
  - Si en progreso → Ruta personalizada
  - Si completada → Opción para revisar/reintentar
```

---

## 🛠️ Cambios Técnicos (Detallados)

### **FASE 1: Backend - API Endpoints**

#### **1.1 Crear Nueva Ruta (Existente, adaptar)**
```
POST /crear-ruta
Body:
{
  "nombre_ruta": "Matemáticas 2025",
  "descripcion": "Curso de cálculo integral",
  "archivo": <File>  // Uno o más
}
Response:
{
  "ruta_id": "65a3b2c1d4e5f6g7h8i9j0",
  "nombre_ruta": "Matemáticas 2025",
  "estado": "EXAMEN_PENDIENTE"
}
```

**Cambios:**
- Agregar validación de `nombre_ruta` (no vacío, único por usuario)
- Guardar `nombre_ruta` + `descripcion` en BD
- Retornar `ruta_id` para referencias futuras

#### **1.2 Listar Rutas del Usuario (NUEVA)**
```
GET /rutas/lista
Response:
{
  "rutas": [
    {
      "ruta_id": "65a3b2c1...",
      "nombre_ruta": "Matemáticas Avanzadas",
      "descripcion": "Cálculo integral",
      "progreso_global": 35,
      "estado": "ACTIVA",
      "examen_pendiente": false,
      "fecha_creacion": "2025-12-08",
      "archivos_count": 3,
      "niveles_completados": 2
    },
    ...
  ]
}
```

**Cambios:**
- Filtrar por `usuario`
- Ordenar por `fecha_actualizacion` DESC
- Incluir metadata para mostrar en tarjetas

#### **1.3 Obtener Detalles de Ruta (Adaptar)**
```
GET /ruta/<ruta_id>/estado
Response:
{
  "ruta_id": "...",
  "nombre_ruta": "Matemáticas Avanzadas",
  "descripcion": "...",
  "examen_pendiente": true/false,
  "examen_generado": true/false,
  "perfil_zdp": { ... },
  "ruta": { ... },
  "archivos": [ ... ]
}
```

**Cambios:**
- Agregar verificación que el usuario sea propietario
- Incluir `nombre_ruta` en respuesta

#### **1.4 Cambiar Nombre de Ruta (NUEVA)**
```
PUT /ruta/<ruta_id>/actualizar
Body:
{
  "nombre_ruta": "Nuevo Nombre",
  "descripcion": "Nueva descripción"
}
Response:
{
  "exito": true,
  "mensaje": "Ruta actualizada"
}
```

#### **1.5 Eliminar Ruta (NUEVA - Opcional)**
```
DELETE /ruta/<ruta_id>
Response:
{
  "exito": true,
  "mensaje": "Ruta eliminada"
}
```

---

### **FASE 2: Frontend - Diseño de Página**

#### **2.1 Nueva Estructura HTML**

```html
<!-- HEADER: Descripción + Botones -->
<section class="dashboard-intro">
  <div class="card">
    <div class="card-body">
      <h2>📚 Ruta de Aprendizaje Personalizada</h2>
      <p class="lead">Crea rutas personalizadas basadas en tus materiales o continúa con rutas anteriores...</p>
      
      <div class="button-group">
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

<!-- SECCIÓN: Crear Nueva Ruta (Modal/Collapse) -->
<div id="seccionCrearRuta" style="display: none;">
  <!-- Modal o Form -->
</div>

<!-- SECCIÓN: Listar Rutas (Modal) -->
<div id="seccionListaRutas" style="display: none;">
  <!-- Lista de rutas -->
</div>

<!-- SECCIÓN: Ruta Activa (Examen + Contenido) -->
<div id="seccionRutaActiva" style="display: none;">
  <!-- La que existe ahora -->
</div>
```

#### **2.2 Modal: Crear Nueva Ruta**

```html
<div class="modal" id="modalCrearRuta">
  <div class="modal-dialog modal-lg">
    <div class="modal-content">
      <div class="modal-header">
        <h5>Crear Nueva Ruta de Aprendizaje</h5>
        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
      </div>
      
      <div class="modal-body">
        <form id="formCrearRuta">
          <!-- Nombre de Ruta -->
          <div class="mb-3">
            <label for="nombreRuta" class="form-label">
              📛 Nombre de la Ruta <span class="text-danger">*</span>
            </label>
            <input 
              type="text" 
              class="form-control" 
              id="nombreRuta" 
              placeholder="Ej: Matemáticas 2025, Historia Medieval, etc."
              required
              maxlength="100"
            >
            <small class="text-muted">Máximo 100 caracteres</small>
          </div>
          
          <!-- Descripción -->
          <div class="mb-3">
            <label for="descripcionRuta" class="form-label">
              📝 Descripción (Opcional)
            </label>
            <textarea 
              class="form-control" 
              id="descripcionRuta" 
              rows="3"
              placeholder="Describe brevemente qué aprenderás en esta ruta..."
              maxlength="500"
            ></textarea>
            <small class="text-muted">Máximo 500 caracteres</small>
          </div>
          
          <!-- Subida de Archivos -->
          <div class="mb-3">
            <label for="archivosRuta" class="form-label">
              📁 Archivos <span class="text-danger">*</span>
            </label>
            <input 
              type="file" 
              class="form-control" 
              id="archivosRuta"
              multiple
              accept=".pdf,.docx,.pptx"
              required
            >
            <small class="text-muted">PDF, DOCX o PPTX. Máximo 50MB por archivo</small>
          </div>
          
          <!-- Vista previa de archivos -->
          <div id="previewArchivos" class="mb-3"></div>
        </form>
      </div>
      
      <div class="modal-footer">
        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
          Cancelar
        </button>
        <button type="button" class="btn btn-primary" id="btnGenerarRuta">
          🚀 Generar Ruta
        </button>
      </div>
    </div>
  </div>
</div>
```

#### **2.3 Modal: Listar Rutas Existentes**

```html
<div class="modal" id="modalListaRutas">
  <div class="modal-dialog modal-lg">
    <div class="modal-content">
      <div class="modal-header">
        <h5>📚 Tus Rutas de Aprendizaje</h5>
        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
      </div>
      
      <div class="modal-body">
        <div id="listaRutasContainer">
          <!-- Spinner mientras carga -->
          <div class="text-center">
            <div class="spinner-border text-primary"></div>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>
```

**Contenido dinámico (generado por JS):**
```html
<div class="ruta-item card mb-3 cursor-pointer">
  <div class="card-body d-flex justify-content-between align-items-center">
    <div class="flex-grow-1">
      <h6 class="card-title mb-1">📚 Matemáticas Avanzadas</h6>
      <small class="text-muted d-block">Cálculo integral y ecuaciones diferenciales</small>
      <small class="text-muted d-block">3 archivos | 2 niveles completados</small>
      
      <!-- Progress Bar -->
      <div class="progress mt-2" style="height: 10px;">
        <div class="progress-bar bg-success" style="width: 35%"></div>
      </div>
      <small class="text-muted">Progreso: 35%</small>
    </div>
    
    <div class="button-group ms-3">
      <button class="btn btn-sm btn-primary" onclick="continuarRuta('ruta_id')">
        ▶ Continuar
      </button>
      <button class="btn btn-sm btn-outline-secondary" onclick="verDetalles('ruta_id')">
        👁 Detalles
      </button>
    </div>
  </div>
</div>
```

---

### **FASE 3: Lógica JavaScript**

#### **3.1 Funciones Principales**

```javascript
// --- Cargar estado inicial ---
async function cargarDashboard() {
  // Mostrar intro con 2 botones
  mostrarIntro();
}

// --- Botón: Crear Nueva Ruta ---
async function abrirModalCrearRuta() {
  const modal = new bootstrap.Modal(document.getElementById('modalCrearRuta'));
  modal.show();
}

// --- Botón: Elegir Ruta Existente ---
async function cargarListaRutas() {
  try {
    const res = await fetch('/rutas/lista');
    const data = await res.json();
    renderizarListaRutas(data.rutas);
    const modal = new bootstrap.Modal(document.getElementById('modalListaRutas'));
    modal.show();
  } catch (error) {
    alert('Error cargando rutas: ' + error.message);
  }
}

// --- Generar Nueva Ruta (Form Submit) ---
document.getElementById('formCrearRuta').addEventListener('submit', async (e) => {
  e.preventDefault();
  
  const nombreRuta = document.getElementById('nombreRuta').value;
  const descripcionRuta = document.getElementById('descripcionRuta').value;
  const archivos = document.getElementById('archivosRuta').files;
  
  // Validaciones
  if (!nombreRuta.trim()) {
    alert('El nombre de la ruta es requerido');
    return;
  }
  
  if (archivos.length === 0) {
    alert('Debes subir al menos un archivo');
    return;
  }
  
  // Crear FormData para enviar files
  const formData = new FormData();
  formData.append('nombre_ruta', nombreRuta);
  formData.append('descripcion', descripcionRuta);
  Array.from(archivos).forEach(archivo => {
    formData.append('archivos', archivo);
  });
  
  // Enviar al backend
  try {
    const res = await fetch('/crear-ruta', {
      method: 'POST',
      body: formData  // No incluir Content-Type; el navegador lo hace
    });
    
    if (!res.ok) throw new Error('Error creando ruta');
    
    const data = await res.json();
    // Guardar ruta_id
    rutaActualId = data.ruta_id;
    
    // Cerrar modal
    bootstrap.Modal.getInstance(document.getElementById('modalCrearRuta')).hide();
    
    // Mostrar examen o ruta
    mostrarRutaActiva(data.ruta_id);
  } catch (error) {
    alert('Error: ' + error.message);
  }
});

// --- Continuar Ruta Existente ---
async function continuarRuta(rutaId) {
  try {
    const res = await fetch(`/ruta/${rutaId}/estado`);
    const data = await res.json();
    
    rutaActualId = rutaId;
    
    // Cerrar modal
    bootstrap.Modal.getInstance(document.getElementById('modalListaRutas')).hide();
    
    // Mostrar ruta/examen
    mostrarRutaActiva(rutaId);
  } catch (error) {
    alert('Error: ' + error.message);
  }
}

// --- Renderizar Lista de Rutas ---
function renderizarListaRutas(rutas) {
  const container = document.getElementById('listaRutasContainer');
  
  if (rutas.length === 0) {
    container.innerHTML = '<div class="alert alert-info">No tienes rutas creadas aún.</div>';
    return;
  }
  
  let html = '';
  rutas.forEach(ruta => {
    html += `
    <div class="ruta-item card mb-3">
      <div class="card-body d-flex justify-content-between align-items-start">
        <div class="flex-grow-1">
          <h6 class="card-title mb-1">📚 ${ruta.nombre_ruta}</h6>
          <small class="text-muted d-block">${ruta.descripcion || 'Sin descripción'}</small>
          <small class="text-muted d-block">${ruta.archivos_count} archivo(s) | ${ruta.niveles_completados} niveles completados</small>
          
          <div class="progress mt-2" style="height: 10px;">
            <div class="progress-bar bg-success" style="width: ${ruta.progreso_global}%"></div>
          </div>
          <small class="text-muted">Progreso: ${ruta.progreso_global}%</small>
        </div>
        
        <div class="button-group ms-3" style="white-space: nowrap;">
          <button class="btn btn-sm btn-primary" onclick="continuarRuta('${ruta.ruta_id}')">
            ▶ Continuar
          </button>
          <button class="btn btn-sm btn-outline-secondary" onclick="verDetallesRuta('${ruta.ruta_id}')">
            👁 Detalles
          </button>
        </div>
      </div>
    </div>
    `;
  });
  
  container.innerHTML = html;
}

// --- Mostrar Ruta Activa (Examen + Contenido) ---
async function mostrarRutaActiva(rutaId) {
  try {
    const res = await fetch(`/ruta/${rutaId}/estado`);
    const data = await res.json();
    
    const cont = document.getElementById('rutaAprendizaje');
    
    if (data.examen_pendiente && data.examen_generado) {
      // Mostrar examen
      await cargarExamenInicial(rutaId);
    } else if (data.examen_generado) {
      // Mostrar ruta
      renderRuta(data);
    }
  } catch (error) {
    console.error('Error:', error);
  }
}
```

---

## 📋 Checklist de Implementación

### **FASE 1: Backend**

- [ ] **1.1** Modificar BD schema
  - [ ] Agregar campos `nombre_ruta`, `descripcion`, `estado` a colección `rutas_aprendizaje`
  - [ ] Crear índice en `usuario` + `nombre_ruta` para búsquedas rápidas
  
- [ ] **1.2** Crear/Modificar Endpoints
  - [ ] `GET /rutas/lista` → Listar rutas del usuario
  - [ ] `POST /crear-ruta` → Crear nueva ruta con múltiples archivos
  - [ ] `GET /ruta/<ruta_id>/estado` → Obtener detalles (adaptar existente)
  - [ ] `PUT /ruta/<ruta_id>/actualizar` → Actualizar nombre/descripción
  - [ ] `DELETE /ruta/<ruta_id>` → Eliminar ruta (opcional)

- [ ] **1.3** Validaciones Backend
  - [ ] Validar `nombre_ruta` no vacío, no duplicado por usuario
  - [ ] Validar que usuario sea propietario de la ruta
  - [ ] Validar archivos (tipo, tamaño)
  - [ ] Validar `descripcion` <= 500 caracteres

- [ ] **1.4** Manejo de Múltiples Archivos
  - [ ] Procesar múltiples files en una sola request
  - [ ] Guardar lista de archivos en `archivos_fuente`
  - [ ] Procesar Bloom para todos simultáneamente

---

### **FASE 2: Frontend - HTML/CSS**

- [ ] **2.1** Rediseñar Estructura
  - [ ] Eliminar formulario de subida del dashboard principal
  - [ ] Agregar sección "intro" con descripción + 2 botones
  - [ ] Crear modal "Crear Nueva Ruta"
  - [ ] Crear modal "Elegir Ruta Existente"
  - [ ] Mantener sección "Ruta Activa" (oculta inicialmente)

- [ ] **2.2** Estilos CSS
  - [ ] Estilos para intro card
  - [ ] Estilos para tarjetas de ruta (nombre, descripción, progreso)
  - [ ] Progress bar styling
  - [ ] Responsive en móvil

- [ ] **2.3** Validación HTML
  - [ ] Campos requeridos marcados
  - [ ] Máximos de caracteres en inputs
  - [ ] Accept types en file input

---

### **FASE 3: Frontend - JavaScript**

- [ ] **3.1** Funciones de Estado
  - [ ] `cargarDashboard()` → Mostrar intro
  - [ ] `abrirModalCrearRuta()` → Abrir modal crear
  - [ ] `cargarListaRutas()` → Fetch + render lista

- [ ] **3.2** Funciones de Formulario
  - [ ] Preview de archivos seleccionados
  - [ ] Validación antes de enviar
  - [ ] Manejo de FormData con múltiples files

- [ ] **3.3** Funciones de Ruta
  - [ ] `continuarRuta(rutaId)` → Cargar ruta existente
  - [ ] `verDetallesRuta(rutaId)` → Mostrar info completa
  - [ ] `renderizarListaRutas(rutas)` → HTML dinámico
  - [ ] `mostrarRutaActiva(rutaId)` → Mostrar examen o contenido

- [ ] **3.4** Error Handling
  - [ ] Try-catch en todos los fetch
  - [ ] Mensajes claros al usuario
  - [ ] Manejo de archivos no válidos
  - [ ] Validación de inputs

---

### **FASE 4: Integración**

- [ ] **4.1** Conectar Backend ↔ Frontend
  - [ ] Probar endpoint `/rutas/lista`
  - [ ] Probar endpoint `/crear-ruta` con múltiples archivos
  - [ ] Probar flujo crear → examen → ruta
  - [ ] Probar flujo elegir → examen/ruta

- [ ] **4.2** Testing Manual
  - [ ] Crear nueva ruta con 1 archivo
  - [ ] Crear nueva ruta con múltiples archivos
  - [ ] Ver lista de rutas
  - [ ] Continuar ruta existente
  - [ ] Completar examen
  - [ ] Ver ruta personalizada
  - [ ] En móvil (responsive)

- [ ] **4.3** Edge Cases
  - [ ] Nombre de ruta muy largo
  - [ ] Archivo muy grande
  - [ ] Sin archivos seleccionados
  - [ ] Usuario sin rutas creadas
  - [ ] Ruta en diferente estado (examen pendiente, completada, etc.)

---

### **FASE 5: Documentación**

- [ ] **5.1** Documentar cambios
  - [ ] API endpoints nuevos/modificados
  - [ ] Schema BD
  - [ ] Flujos de usuario
  - [ ] Cambios en dashboard.html

- [ ] **5.2** Actualizar README
  - [ ] Describir nuevos flujos
  - [ ] Ejemplos de uso

---

## 📊 Estimación de Tiempo

| Fase | Tareas | Tiempo |
|------|--------|--------|
| **1: Backend** | 5 tareas | 2-3 horas |
| **2: Frontend HTML/CSS** | 3 tareas | 1-2 horas |
| **3: Frontend JS** | 4 tareas | 2-3 horas |
| **4: Integración** | 3 tareas | 1-2 horas |
| **5: Documentación** | 2 tareas | 30 min |
| **TOTAL** | 17 tareas | **7-11 horas** |

---

## 🔄 Orden de Ejecución Recomendado

1. **PRIMERO:** Fases 1 (Backend)
2. **SEGUNDO:** Fases 2-3 (Frontend)
3. **TERCERO:** Fase 4 (Integración)
4. **CUARTO:** Fase 5 (Documentación)

---

## 📝 Notas Importantes

### **Bases de Datos**
- La colección `rutas_aprendizaje` necesita campos nuevos
- Importante: `nombre_ruta` debe ser visible al usuario, no `_id`
- Considerar migración de rutas existentes (agregar `nombre_ruta = "Ruta por defecto"`)

### **Múltiples Archivos**
- FormData permite enviar múltiples files con `formData.append('archivos', file)`
- Backend debe procesarlos en un loop
- Guardar lista de archivos procesados en `archivos_fuente`

### **Seguridad**
- Validar que usuario sea propietario de la ruta en CADA endpoint
- No devolver datos de otros usuarios
- Validar tipos de archivo en frontend Y backend

### **Performance**
- Procesar múltiples archivos puede tomar tiempo
- Mostrar spinner/progress durante generación
- Considerar queue en backend si muchos archivos

---

## ✅ Criterios de Éxito

- [ ] Dashboard muestra intro con 2 botones (sin formulario de subida)
- [ ] "Crear Nueva Ruta" abre modal con inputs y file upload
- [ ] "Elegir Ruta Existente" abre modal con lista de rutas
- [ ] Cada ruta tiene nombre, descripción, progreso visible
- [ ] Continuar ruta carga examen o contenido correctamente
- [ ] Múltiples archivos se procesan en una sola operación
- [ ] Todo funciona en móvil

---

