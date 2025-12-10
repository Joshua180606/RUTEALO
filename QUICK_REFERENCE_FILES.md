# 🚀 Quick Reference - File Management System

**Última Actualización:** 9 Diciembre 2025

---

## 📁 Carpetas por Usuario

```
data/raw/uploads/
├── {usuario}/
│   ├── archivo1.pdf
│   ├── archivo2.docx
│   └── archivo3.pptx
```

Cada usuario tiene su propia carpeta. Se crea automáticamente en el primer upload.

---

## 🔌 Endpoints API

### GET /files
```javascript
// Obtener lista de archivos del usuario
fetch('/files')
  .then(r => r.json())
  .then(data => {
    console.log(data.usuario);      // "JOSHUA"
    console.log(data.total);        // 3
    console.log(data.archivos);     // Array de archivos
  });
```

**Respuesta:**
```json
{
  "usuario": "JOSHUA",
  "total": 2,
  "archivos": [
    {
      "nombre": "archivo.pdf",
      "size": 524288,
      "size_mb": 0.5,
      "fecha": "2025-12-09 10:30:45"
    }
  ]
}
```

### GET /download/{archivo}
```html
<!-- Descargar archivo -->
<a href="/download/archivo.pdf">Descargar</a>
```

Requiere autenticación. Valida que el usuario es propietario.

---

## 🛠️ Funciones Utilidad

### Obtener carpeta del usuario
```python
from src.utils import obtener_carpeta_usuario

carpeta = obtener_carpeta_usuario("JOSHUA")
# C:\...\data\raw\uploads\JOSHUA
```

### Crear carpeta del usuario
```python
from src.utils import crear_carpeta_usuario

crear_carpeta_usuario("JOSHUA")  # Retorna True
```

### Listar archivos del usuario
```python
from src.utils import listar_archivos_usuario

archivos = listar_archivos_usuario("JOSHUA")
# [{nombre, size, size_mb, fecha, ruta}, ...]
```

### Validar acceso a archivo
```python
from src.utils import validar_acceso_archivo

tiene_acceso = validar_acceso_archivo("JOSHUA", "archivo.pdf")
# True o False
```

### Obtener ruta segura de archivo
```python
from src.utils import obtener_ruta_archivo

ruta = obtener_ruta_archivo("JOSHUA", "archivo.pdf")
# C:\...\data\raw\uploads\JOSHUA\archivo.pdf (o None si no tiene acceso)
```

---

## 📊 Dashboard

### Botón Ver Archivos
```html
<button onclick="cargarArchivosModal()">📋 Ver Archivos</button>
```

Abre modal con lista actualizada de archivos.

### Funciones JavaScript
```javascript
// Cargar lista de archivos en modal
cargarArchivosModal()

// Renderizar archivos en modal
mostrarArchivosEnModal(archivos)

// Descargar archivo
abrirArchivo("nombre_archivo.pdf")
```

---

## 🔐 Seguridad

| Aspecto | Protección |
|---------|-----------|
| **Auth** | Sesión requerida en /files y /download |
| **Authz** | validar_acceso_archivo() verifica propiedad |
| **Path** | os.path.realpath() + validación |
| **Names** | secure_filename() sanitiza nombres |
| **Log** | Intentos no autorizados registrados |

---

## 🧪 Tests

```bash
# Todos los tests
pytest tests/ -q

# Solo file management
pytest tests/test_utils.py::TestFileManagement -v
pytest tests/test_app.py::TestFileManagement -v
```

---

## 💾 Modelos de Datos

### Estructura de Archivo (en lista)
```python
{
    "nombre": "documento.pdf",           # str
    "size": 524288,                      # int (bytes)
    "size_mb": 0.5,                      # float
    "fecha": "2025-12-09 10:30:45",     # str
    "ruta": "C:\\...\\uploads\\user\\..."  # str (solo en BD)
}
```

---

## 📝 Flujo Típico

### 1. Usuario sube archivo
```python
# En app.py:upload_file()
usuario = session["usuario"]
crear_carpeta_usuario(usuario)
# Guardar en: data/raw/uploads/{usuario}/nombre
```

### 2. Usuario abre modal "Ver Archivos"
```javascript
// En dashboard.html
cargarArchivosModal() // Llama GET /files
```

### 3. Usuario descarga archivo
```html
<!-- En modal -->
<a href="/download/archivo.pdf">⬇️ Descargar</a>
```

---

## ⚙️ Configuración

### Variables Importantes
- `UPLOAD_FOLDER`: `data/raw/uploads`
- `MAX_FILE_SIZE`: 50 MB
- `ALLOWED_EXTENSIONS`: `.pdf`, `.docx`, `.pptx`

### Crear carpeta manualmente
```python
from src.utils import crear_carpeta_usuario
crear_carpeta_usuario("NUEVO_USUARIO")
```

---

## 🐛 Troubleshooting

### Archivo no aparece después de upload
- Verificar que la carpeta del usuario existe
- Verificar permisos de carpeta
- Revisar logs de aplicación

### No puedo descargar archivo
- Verificar sesión activa
- Verificar que el archivo pertenece al usuario
- Revisar logs de intentos no autorizados

### Path traversal attempt rechazado
- Esto es correcto - sistema de seguridad funcionando
- Usuario solo puede acceder a sus archivos

---

## 📚 Documentación Completa

- **GUIA_MANEJO_ARCHIVOS.md**: Documentación técnica completa
- **RESUMEN_MANEJO_ARCHIVOS.md**: Executive summary
- **GUIA_CONVERSIONES_TIEMPO.md**: Conversión tiempo minutos/horas

---

## 🚀 Ejemplos Prácticos

### Listar todos los archivos de un usuario
```python
from src.utils import listar_archivos_usuario

archivos = listar_archivos_usuario("JOSHUA")
for archivo in archivos:
    print(f"{archivo['nombre']} - {archivo['size_mb']} MB")
```

### Validar y obtener ruta segura
```python
from src.utils import obtener_ruta_archivo

ruta = obtener_ruta_archivo("JOSHUA", "documento.pdf")
if ruta:
    with open(ruta, 'rb') as f:
        contenido = f.read()
else:
    print("Acceso denegado")
```

### Crear carpeta si no existe
```python
from src.utils import crear_carpeta_usuario

if crear_carpeta_usuario("NUEVO_USUARIO"):
    print("Carpeta lista")
else:
    print("Error creando carpeta")
```

---

## ✅ Checklist de Implementación

- [x] Carpetas por usuario en data/raw/uploads
- [x] Aislamiento de archivos (solo propietario accede)
- [x] Endpoint GET /files para listar
- [x] Endpoint GET /download para descargar
- [x] 5 funciones utilidad reutilizables
- [x] Dashboard con botón "Ver Archivos"
- [x] Modal con lista actualizada en tiempo real
- [x] Validación de seguridad (path traversal, auth)
- [x] 14 tests (10 utils + 4 api)
- [x] Documentación completa
- [x] 2 commits con historiales detallados

---

**Versión:** 1.0  
**Estado:** ✅ Producción  
**Tests:** 66/66 PASANDO
