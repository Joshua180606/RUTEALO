# ✅ CHECKLIST DE IMPLEMENTACIÓN - Dashboard Rediseño
**Fecha:** 2025-12-10  
**Estado:** Pendiente de implementación

---

## 📋 FASE 1: Backend (BD + API)

### 1.1 Modificar Schema MongoDB
- [ ] Agregar campo `nombre_ruta` (string, required)
- [ ] Agregar campo `descripcion` (string, optional, max 500)
- [ ] Agregar campo `estado` (enum: ACTIVA, PAUSADA, COMPLETADA)
- [ ] Agregar índice en `(usuario, nombre_ruta)` para búsquedas rápidas
- [ ] Migrar rutas existentes (asignar nombre genérico si falta)

**Archivo:** `src/database.py` o schema de MongoDB

---

### 1.2 Endpoint: GET /rutas/lista
- [ ] Validar autenticación del usuario
- [ ] Filtrar rutas por `usuario`
- [ ] Ordenar por `fecha_actualizacion` DESC
- [ ] Retornar: `ruta_id`, `nombre_ruta`, `descripcion`, `progreso_global`, `estado`, `archivos_count`, `niveles_completados`
- [ ] Manejo de errores

**Archivo:** `src/app.py`

```python
@app.route("/rutas/lista")
def listar_rutas():
    if "usuario" not in session:
        return {"error": "Unauthorized"}, 401
    
    usuario = session["usuario"]
    rutas = db["rutas_aprendizaje"].find(
        {"usuario": usuario},
        {"nombre_ruta": 1, "descripcion": 1, "progreso_global": 1, ...}
    ).sort("fecha_actualizacion", -1)
    
    rutas_list = []
    for ruta in rutas:
        rutas_list.append({
            "ruta_id": str(ruta["_id"]),
            "nombre_ruta": ruta.get("nombre_ruta", "Sin nombre"),
            ...
        })
    
    return {"rutas": rutas_list}, 200
```

---

### 1.3 Endpoint: POST /crear-ruta (Adaptar)
- [ ] Validar `nombre_ruta` no vacío
- [ ] Validar `nombre_ruta` único por usuario
- [ ] Validar `descripcion` <= 500 caracteres
- [ ] Validar archivos (tipo, tamaño, cantidad)
- [ ] Procesar múltiples archivos
- [ ] Guardar `nombre_ruta` + `descripcion` en BD
- [ ] Guardar lista de archivos en `archivos_fuente`
- [ ] Ejecutar Bloom etiquetado para todos
- [ ] Generar examen inicial
- [ ] Generar ruta
- [ ] Retornar `ruta_id` + `estado`

**Archivo:** `src/app.py`

```python
@app.route("/crear-ruta", methods=["POST"])
def crear_ruta():
    if "usuario" not in session:
        return {"error": "Unauthorized"}, 401
    
    usuario = session["usuario"]
    nombre_ruta = request.form.get("nombre_ruta", "").strip()
    descripcion = request.form.get("descripcion", "").strip()
    archivos = request.files.getlist("archivos")
    
    # Validaciones
    if not nombre_ruta:
        return {"error": "Nombre requerido"}, 400
    
    if len(nombre_ruta) > 100:
        return {"error": "Nombre muy largo"}, 400
    
    # Verificar duplicado
    if db["rutas_aprendizaje"].find_one({"usuario": usuario, "nombre_ruta": nombre_ruta}):
        return {"error": "Nombre ya existe"}, 409
    
    if len(descripcion) > 500:
        return {"error": "Descripción muy larga"}, 400
    
    if not archivos:
        return {"error": "Al menos un archivo requerido"}, 400
    
    # Procesar archivos
    archivos_procesados = []
    for archivo in archivos:
        # Guardar archivo
        filename = secure_filename(archivo.filename)
        filepath = os.path.join(str(app.config["UPLOAD_FOLDER"]), usuario, filename)
        archivo.save(filepath)
        
        # Procesar (ingesta + Bloom)
        procesar_archivo_web(filepath, usuario, db)
        
        archivos_procesados.append({
            "nombre_archivo": filename,
            "tamaño": os.path.getsize(filepath) / 1024 / 1024,  # MB
            "fecha_subida": datetime.datetime.utcnow()
        })
    
    # Generar ruta
    msg_ruta = generar_ruta_aprendizaje(usuario, db)
    
    # Crear documento de ruta
    ruta_doc = {
        "usuario": usuario,
        "nombre_ruta": nombre_ruta,
        "descripcion": descripcion,
        "archivos_fuente": archivos_procesados,
        "estado": "ACTIVA",
        "progreso_global": 0,
        "fecha_creacion": datetime.datetime.utcnow(),
        "fecha_actualizacion": datetime.datetime.utcnow(),
        ...
    }
    
    resultado = db["rutas_aprendizaje"].insert_one(ruta_doc)
    ruta_id = str(resultado.inserted_id)
    
    return {
        "ruta_id": ruta_id,
        "nombre_ruta": nombre_ruta,
        "estado": "EXAMEN_PENDIENTE" if examen_pendiente else "ACTIVA",
        "mensaje": msg_ruta
    }, 201
```

---

### 1.4 Endpoint: GET /ruta/<ruta_id>/estado (Adaptar)
- [ ] Validar que usuario sea propietario
- [ ] Retornar `nombre_ruta` + `descripcion`
- [ ] Mantener lógica existente de examen/ruta

**Archivo:** `src/app.py`

---

### 1.5 Endpoint: PUT /ruta/<ruta_id>/actualizar (NUEVA)
- [ ] Validar autenticación
- [ ] Validar que usuario sea propietario
- [ ] Validar nuevos valores
- [ ] Actualizar en BD
- [ ] Retornar confirmación

**Archivo:** `src/app.py`

```python
@app.route("/ruta/<ruta_id>/actualizar", methods=["PUT"])
def actualizar_ruta(ruta_id):
    # Implementación similar a otros endpoints
    pass
```

---

### 1.6 Endpoint: DELETE /ruta/<ruta_id> (OPCIONAL)
- [ ] Validar autenticación
- [ ] Validar que usuario sea propietario
- [ ] Eliminar de BD
- [ ] Retornar confirmación

---

## 📄 FASE 2: Frontend - HTML/CSS

### 2.1 Rediseñar Estructura Principal
- [ ] Eliminar formulario de subida del top
- [ ] Crear sección "intro" con descripción
- [ ] Crear 2 botones principales: "Crear Nueva" + "Elegir Existente"
- [ ] Aplicar estilos Bootstrap card

**Archivo:** `src/templates/dashboard.html`

```html
<!-- NUEVA ESTRUCTURA -->
<section class="dashboard-intro mb-4">
  <div class="card">
    <div class="card-body text-center">
      <h2>📚 Ruta de Aprendizaje Personalizada</h2>
      <p class="lead">Crea rutas basadas en tus materiales o continúa con anteriores...</p>
      
      <div class="d-grid gap-2 d-sm-flex justify-content-sm-center">
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

---

### 2.2 Modal: Crear Nueva Ruta
- [ ] Input: Nombre (required, max 100)
- [ ] Textarea: Descripción (optional, max 500)
- [ ] File Input: Múltiples archivos (required)
- [ ] Preview de archivos seleccionados
- [ ] Botones: Cancelar + Generar
- [ ] Estilos responsivos

**Archivo:** `src/templates/dashboard.html`

---

### 2.3 Modal: Listar Rutas
- [ ] Encabezado: "Tus Rutas de Aprendizaje"
- [ ] Lista de tarjetas para cada ruta
- [ ] Mostrar: nombre, descripción, progreso, archivos
- [ ] Progress bar visual
- [ ] Botones: Continuar + Detalles

**Archivo:** `src/templates/dashboard.html`

---

### 2.4 Estilos CSS
- [ ] Card intro styling
- [ ] Button groups responsive
- [ ] Ruta item card styling
- [ ] Progress bar colors
- [ ] Mobile breakpoints

**Archivo:** `src/templates/dashboard.html` (style section)

---

## 🔧 FASE 3: Frontend - JavaScript

### 3.1 Funciones de Estado
- [ ] `cargarDashboard()` - Mostrar intro
- [ ] `abrirModalCrearRuta()` - Abrir modal crear
- [ ] `cargarListaRutas()` - Fetch + render lista
- [ ] `mostrarRutaActiva()` - Mostrar examen o contenido

**Archivo:** `src/templates/dashboard.html` (script section)

---

### 3.2 Funciones de Formulario
- [ ] `actualizarPreviewArchivos()` - Mostrar archivos seleccionados
- [ ] `validarFormulario()` - Validar inputs antes de enviar
- [ ] `enviarFormulario()` - POST /crear-ruta
- [ ] `limpiarFormulario()` - Reset después de envío exitoso

---

### 3.3 Funciones de Ruta
- [ ] `continuarRuta(rutaId)` - Cargar ruta existente
- [ ] `verDetallesRuta(rutaId)` - Mostrar info completa
- [ ] `renderizarListaRutas(rutas)` - Generar HTML dinámico
- [ ] `actualizarRuta(rutaId, datos)` - PUT /ruta/<ruta_id>/actualizar

---

### 3.4 Manejo de Errores
- [ ] Try-catch en todos los fetch
- [ ] Mensajes de error claros
- [ ] Validación de inputs antes de enviar
- [ ] Manejo de archivos inválidos
- [ ] Spinner/loading durante operaciones

---

### 3.5 Event Listeners
- [ ] `#btnCrearNuevaRuta` → `abrirModalCrearRuta()`
- [ ] `#btnElegirRutaExistente` → `cargarListaRutas()`
- [ ] `#formCrearRuta` submit → `enviarFormulario()`
- [ ] `#archivosRuta` change → `actualizarPreviewArchivos()`
- [ ] Botones continuar/detalles en lista

---

## 🔗 FASE 4: Integración

### 4.1 Testing Backend
- [ ] Probar POST /crear-ruta con 1 archivo
- [ ] Probar POST /crear-ruta con múltiples archivos
- [ ] Probar GET /rutas/lista
- [ ] Probar GET /ruta/<ruta_id>/estado
- [ ] Probar PUT /ruta/<ruta_id>/actualizar
- [ ] Verificar BD (campos nuevos guardados)

---

### 4.2 Testing Frontend
- [ ] Dashboard muestra intro
- [ ] Modal crear abre correctamente
- [ ] Modal lista abre correctamente
- [ ] Validación funciona (nombre vacío, sin archivos)
- [ ] Preview de archivos funciona
- [ ] Crear ruta exitosa
- [ ] Listar rutas exitosa
- [ ] Continuar ruta carga examen/contenido

---

### 4.3 Testing E2E
- [ ] Flujo completo: crear → examen → ruta
- [ ] Flujo completo: elegir → examen/ruta
- [ ] Pruebas en móvil
- [ ] Pruebas en diferentes navegadores
- [ ] Edge cases (nombre muy largo, sin permisos, etc.)

---

## 📚 FASE 5: Documentación

### 5.1 Documentar Cambios
- [ ] API endpoints nuevos/modificados
- [ ] Schema BD actualizado
- [ ] Flujos de usuario
- [ ] Cambios en dashboard.html

**Archivo a crear:** `RESUMEN_CAMBIOS_DASHBOARD_REDISEÑO.md`

---

### 5.2 Actualizar README
- [ ] Describir nuevos flujos
- [ ] Agregar ejemplos de uso
- [ ] Links a documentación

**Archivo:** `README.md`

---

## 🎯 Estado General

| Fase | Descripción | Estado | % Completado |
|------|-------------|--------|--------------|
| **1** | Backend (BD + API) | ⏳ No iniciada | 0% |
| **2** | Frontend HTML/CSS | ⏳ No iniciada | 0% |
| **3** | Frontend JS | ⏳ No iniciada | 0% |
| **4** | Integración | ⏳ No iniciada | 0% |
| **5** | Documentación | ⏳ No iniciada | 0% |
| **TOTAL** | | ⏳ **No iniciada** | **0%** |

---

## 📝 Notas de Implementación

### **Prioridad Alta**
1. Backend endpoints (FASE 1)
2. Formulario crear ruta (FASE 2-3)
3. Lista de rutas (FASE 2-3)
4. Integración básica (FASE 4)

### **Prioridad Media**
5. Validaciones robustas (FASE 1-3)
6. Error handling mejorado (FASE 3)
7. Testing exhaustivo (FASE 4)

### **Prioridad Baja**
8. Detalles de ruta (FASE 3)
9. Editar nombre/descripción (FASE 1-3)
10. Eliminar ruta (FASE 1-3)

---

## 🚀 Próximos Pasos

1. **Confirmar plan con usuario** ← Estamos aquí
2. Implementar FASE 1 (Backend)
3. Implementar FASE 2-3 (Frontend)
4. Hacer testing (FASE 4)
5. Documentar (FASE 5)

---

**Creado:** 2025-12-10  
**Actualización:** [Pendiente]

