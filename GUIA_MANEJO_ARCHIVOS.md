# 📁 Guía de Manejo de Archivos - Dashboard Mejorado

**Agregado:** 9 Diciembre 2025  
**Implementación:** Sistema de carpetas por usuario + Preview en Dashboard

---

## 🎯 Características Principales

### 1. **Carpetas Independientes por Usuario**
- Cada usuario tiene su propia carpeta en `data/raw/uploads/{usuario_name}`
- Se crea automáticamente al primer upload
- Archivos aislados y protegidos por validación de acceso

### 2. **Dashboard Mejorado**
- Botón **"📋 Ver Archivos"** en la tarjeta de materiales
- Modal popup con lista de archivos subidos
- Vista en tiempo real (AJAX)
- Información: nombre, fecha, tamaño en MB

### 3. **Descarga Segura**
- Endpoint `/download/<archivo>` con validación de acceso
- Solo el propietario puede descargar sus archivos
- Validación de ruta (previene path traversal)

---

## 🔧 Nuevos Endpoints API

### `GET /files`
Obtiene lista JSON de archivos del usuario autenticado.

**Requiere:** Sesión activa (usuario en sesión)  
**Retorna:** JSON

```json
{
  "usuario": "JOSHUA",
  "archivos": [
    {
      "nombre": "material.pdf",
      "size": 524288,
      "size_mb": 0.5,
      "fecha": "2025-12-09 15:30:45",
      "ruta": "C:\\...\\data\\raw\\uploads\\JOSHUA\\material.pdf"
    },
    {
      "nombre": "presentacion.pptx",
      "size": 2097152,
      "size_mb": 2.0,
      "fecha": "2025-12-09 14:20:10",
      "ruta": "C:\\...\\data\\raw\\uploads\\JOSHUA\\presentacion.pptx"
    }
  ],
  "total": 2
}
```

**Ejemplo JavaScript:**
```javascript
fetch('/files')
  .then(r => r.json())
  .then(data => {
    console.log(`Usuario: ${data.usuario}`);
    console.log(`Total archivos: ${data.total}`);
    data.archivos.forEach(archivo => {
      console.log(`${archivo.nombre} (${archivo.size_mb} MB)`);
    });
  });
```

---

### `GET /download/<archivo>`
Descarga un archivo del usuario.

**Parámetros:**
- `archivo` (path): Nombre del archivo a descargar

**Validaciones:**
- Usuario debe estar autenticado
- Archivo debe existir en la carpeta del usuario
- Se valida que la ruta está dentro de la carpeta del usuario

**Respuestas:**
- `200`: Archivo encontrado, descarga iniciada
- `302`: Redirige a login si no hay sesión
- `302`: Redirige a dashboard si no tiene acceso al archivo

**Ejemplo:**
```html
<!-- Descarga directa -->
<a href="/download/material.pdf">Descargar</a>

<!-- Con JavaScript -->
<script>
  function descargarArchivo(nombre) {
    window.location.href = `/download/${nombre}`;
  }
</script>
```

---

## 📁 Funciones de Utilidad (utils.py)

### `obtener_carpeta_usuario(usuario, base_uploads_path=None) -> str`
Obtiene la ruta de la carpeta del usuario.

```python
from src.utils import obtener_carpeta_usuario

carpeta = obtener_carpeta_usuario("JOSHUA")
# Retorna: C:\...\data\raw\uploads\JOSHUA
```

---

### `crear_carpeta_usuario(usuario, base_uploads_path=None) -> bool`
Crea la carpeta del usuario si no existe.

```python
from src.utils import crear_carpeta_usuario

exito = crear_carpeta_usuario("JOSHUA")
# Retorna: True si se creó o ya existe, False en error
```

---

### `listar_archivos_usuario(usuario, base_uploads_path=None) -> list`
Lista todos los archivos del usuario.

```python
from src.utils import listar_archivos_usuario

archivos = listar_archivos_usuario("JOSHUA")
# Retorna: [
#   {
#     'nombre': 'archivo.pdf',
#     'size': 1024,
#     'size_mb': 0.001,
#     'fecha': '2025-12-09 10:30:45',
#     'ruta': '/ruta/completa'
#   },
#   ...
# ]

# Los archivos están ordenados por fecha (más reciente primero)
for archivo in archivos:
    print(f"{archivo['nombre']} - {archivo['size_mb']} MB")
```

---

### `validar_acceso_archivo(usuario, nombre_archivo, base_uploads_path=None) -> bool`
Valida que el usuario tiene acceso a un archivo.

```python
from src.utils import validar_acceso_archivo

puede_acceder = validar_acceso_archivo("JOSHUA", "material.pdf")
# Retorna: True si puede acceder, False si no

# Esto previene path traversal:
validar_acceso_archivo("JOSHUA", "../../../etc/passwd")  # False
validar_acceso_archivo("JOSHUA", "../../otro_usuario/archivo.pdf")  # False
```

---

### `obtener_ruta_archivo(usuario, nombre_archivo, base_uploads_path=None) -> Optional[str]`
Obtiene la ruta segura de un archivo si el usuario tiene acceso.

```python
from src.utils import obtener_ruta_archivo

ruta = obtener_ruta_archivo("JOSHUA", "material.pdf")
if ruta:
    # Ruta segura validada
    print(f"Acceso permitido: {ruta}")
else:
    # No tiene acceso
    print("Acceso denegado")
```

---

## 🎨 Interfaz del Dashboard

### Estructura HTML
```html
<!-- Botón en header de tarjeta -->
<button class="btn btn-sm btn-success" id="btnVerArchivos" 
        onclick="cargarArchivosModal()">
  📋 Ver Archivos
</button>

<!-- Modal popup -->
<div class="modal fade" id="modalArchivos">
  <!-- Lista de archivos cargada por AJAX -->
</div>
```

### Funciones JavaScript

#### `cargarArchivosModal()`
Abre el modal y carga archivos vía AJAX desde `/files`.

```javascript
cargarArchivosModal();
// - Muestra modal
// - Llama a /files
// - Renderiza lista de archivos
```

#### `mostrarArchivosEnModal(archivos)`
Renderiza la lista de archivos en el modal.

```javascript
const archivos = [
  {nombre: 'file.pdf', size_mb: 1.5, fecha: '2025-12-09 10:30:00'},
  // ...
];
mostrarArchivosEnModal(archivos);
// Muestra cada archivo con botón de descarga
```

#### `abrirArchivo(nombreArchivo)`
Inicia descarga de un archivo.

```javascript
abrirArchivo("material.pdf");
// Equivalente a: window.location.href = '/download/material.pdf'
```

---

## 🔐 Seguridad

### Protecciones Implementadas

1. **Autenticación**
   - Endpoints `/files` y `/download` requieren sesión activa
   - Sin sesión → Error 401 o redirige a login

2. **Validación de Acceso**
   - `validar_acceso_archivo()` previene acceso a otros usuarios
   - Valida que la ruta está dentro de la carpeta del usuario
   - Uso de `os.path.realpath()` para prevenir symlinks maliciosos

3. **Sanitización de Rutas**
   - Se rechaza `../` y otros intentos de path traversal
   - Nombres de archivo validados con `secure_filename()`

4. **Logging**
   - Intentos no autorizados registrados
   - Errores de descarga logeados para auditoría

---

## 📊 Flujo de Procesos

### Subir Archivo
```
Usuario selecciona archivo
         ↓
POST /upload
         ↓
Crear carpeta usuario si no existe
         ↓
Guardar en data/raw/uploads/{usuario}/
         ↓
Procesar con ingesta de datos
         ↓
Procesar con IA (Bloom)
         ↓
Redirigir a dashboard
```

### Ver Archivos
```
Click en "Ver Archivos"
         ↓
cargarArchivosModal()
         ↓
GET /files (AJAX)
         ↓
Retorna JSON con lista
         ↓
Renderizar en modal
         ↓
Usuario ve archivos con links de descarga
```

### Descargar Archivo
```
Click en "Descargar"
         ↓
GET /download/nombre_archivo
         ↓
Validar acceso
         ↓
Retornar archivo como attachment
         ↓
Archivo descargado en máquina local
```

---

## 🧪 Tests Disponibles

### Tests de Utilidades (test_utils.py::TestFileManagement)
- `test_obtener_carpeta_usuario`: Ruta correcta
- `test_crear_carpeta_usuario_success`: Creación exitosa
- `test_crear_carpeta_usuario_ya_existe`: Idempotencia
- `test_listar_archivos_usuario_carpeta_vacia`: Lista vacía
- `test_listar_archivos_usuario_con_archivos`: Listar múltiples
- `test_validar_acceso_archivo_valido`: Acceso permitido
- `test_validar_acceso_archivo_inexistente`: Archivo no existe
- `test_validar_acceso_archivo_fuera_carpeta`: Path traversal rechazado
- `test_obtener_ruta_archivo_valido`: Ruta segura
- `test_obtener_ruta_archivo_invalido`: Ruta None

### Tests de API (test_app.py::TestFileManagement)
- `test_files_endpoint_without_session_returns_401`: Auth requerida
- `test_download_endpoint_without_session_redirects_to_login`: Redirige login
- `test_files_endpoint_returns_json_with_session`: JSON válido
- `test_download_nonexistent_file_redirects_to_dashboard`: Error handling

**Ejecutar tests:**
```bash
pytest tests/test_utils.py::TestFileManagement -v
pytest tests/test_app.py::TestFileManagement -v
pytest tests/ -q  # Todos los tests
```

---

## 🚀 Ejemplo Completo

### 1. Usuario sube archivo en dashboard
```html
<form action="/upload" method="POST" enctype="multipart/form-data">
  <input type="file" name="file" required>
  <button type="submit">Subir y Procesar</button>
</form>
```

### 2. Backend crea carpeta y guarda
```python
# En app.py:upload_file()
usuario = session["usuario"]  # "JOSHUA"
crear_carpeta_usuario(usuario)  # Crea data/raw/uploads/JOSHUA/
# Archivo guardado en: data/raw/uploads/JOSHUA/documento.pdf
```

### 3. Usuario abre modal "Ver Archivos"
```javascript
// Llamada AJAX en dashboard.html
fetch('/files').then(r => r.json()).then(data => {
  // data.archivos contiene lista de archivos
  // Mostrar en modal con botones de descarga
});
```

### 4. Usuario descarga archivo
```javascript
window.location.href = '/download/documento.pdf';
// Endpoint valida acceso → Retorna archivo
```

---

## 📝 Notas Importantes

1. **Estructura de Carpetas**
   ```
   data/raw/uploads/
   ├── JOSHUA/
   │   ├── documento.pdf
   │   ├── presentacion.pptx
   │   └── apuntes.docx
   ├── USUARIO2/
   │   ├── archivo1.pdf
   │   └── archivo2.pdf
   └── USUARIO3/
   ```

2. **Tipos de Archivo Permitidos**
   - `.pdf`, `.docx`, `.pptx`
   - Otros rechazados en upload

3. **Tamaño Máximo**
   - 50 MB por archivo

4. **Conversión de Tamaño**
   - Se almacena en bytes (`size`)
   - Se calcula en MB (`size_mb`) para presentación
   - Fórmula: `size_mb = size / (1024 * 1024)`

---

**Versión:** 1.0  
**Tests:** 14 nuevos, todos pasando ✅  
**Estado:** Producción lista
