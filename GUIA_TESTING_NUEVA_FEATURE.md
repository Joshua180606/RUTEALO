# 🚀 GUÍA RÁPIDA DE TESTING - NUEVA FUNCIONALIDAD

## Inicio Rápido

### 1. Activar Entorno Virtual
```powershell
cd C:\Users\joshu\Documents\Joshua\Tesis\RUTEALO
. .\.venv\Scripts\Activate.ps1
```

### 2. Iniciar Servidor Flask
```powershell
python -m flask --app src.app run --host=127.0.0.1 --port=5000
```

### 3. Abrir en Navegador
```
http://127.0.0.1:5000/dashboard
```

---

## Pruebas Manuales

### Test 1: Crear Nueva Ruta ✅

**Pasos**:
1. Click en botón "➕ Crear Nueva Ruta"
2. Llenar formulario:
   - **Nombre**: "Python Avanzado 2025"
   - **Descripción**: "Curso completo de Python con proyectos reales"
   - **Archivos**: Selecciona 1-3 PDFs/DOCX/PPTX del proyecto
3. Click en "🚀 Crear Ruta"

**Resultado Esperado**:
- ✅ Validaciones en tiempo real
- ✅ Mensaje de éxito con ruta_id
- ✅ Modal se cierra automáticamente
- ✅ Notificación visual

**Errores a Probar**:
- Nombre vacío → "El nombre es requerido"
- Nombre < 3 chars → "Debe tener al menos 3 caracteres"
- Nombre > 100 chars → "No puede exceder 100 caracteres"
- Sin archivos → "Debes seleccionar al menos 1 archivo"
- Archivo .txt → "extensión no válida"
- Archivo > 50MB → "excede el límite de 50MB"

---

### Test 2: Ver Mis Rutas ✅

**Pasos**:
1. Click en botón "📚 Ver Mis Rutas"
2. Esperar a que carguen las rutas

**Resultado Esperado**:
- ✅ Modal abre con lista de rutas
- ✅ Cada ruta muestra:
  - 📚 Nombre
  - 📄 Cantidad de archivos
  - ✓ Niveles completados
  - 📅 Fecha de actualización
  - 🟢 Estado (ACTIVA/PAUSADA/COMPLETADA)
- ✅ Botones funcionales: "▶️ Continuar" y "👁️ Detalles"

**Flujo**:
```
Si es primera vez:
  → Modal muestra "No tienes rutas aún"
  → Link para crear ruta

Si hay rutas:
  → Lista de cards
  → Cada card con metadatos
  → Acciones disponibles
```

---

### Test 3: Ruta Legacy (Automática) ✅

**Pasos**:
1. Click en "Cargar Estado"
2. Sistema intenta cargar ruta automática

**Resultado Esperado**:
- ✅ Si no hay ruta: "Sube material para generar..."
- ✅ Si hay ruta sin examen: muestra contenido
- ✅ Si hay examen pendiente: muestra preguntas
- ✅ Examen con niveles Bloom coloreados

---

## Pruebas via API (curl/Postman)

### 1. Obtener Lista de Rutas
```bash
curl -X GET http://127.0.0.1:5000/rutas/lista \
  -H "Content-Type: application/json" \
  --cookie "session=YOUR_SESSION_ID"
```

**Respuesta 200**:
```json
{
  "rutas": [
    {
      "ruta_id": "507f1f77bcf86cd799439011",
      "nombre_ruta": "Python Avanzado",
      "descripcion": "Curso completo",
      "estado": "ACTIVA",
      "archivos_count": 3,
      "niveles_completados": 0,
      "fecha_actualizacion": "2025-12-10T01:40:00"
    }
  ]
}
```

---

### 2. Crear Nueva Ruta
```bash
curl -X POST http://127.0.0.1:5000/crear-ruta \
  -F "nombre_ruta=Mi Nueva Ruta" \
  -F "descripcion=Descripción de la ruta" \
  -F "archivos=@archivo1.pdf" \
  -F "archivos=@archivo2.docx" \
  --cookie "session=YOUR_SESSION_ID"
```

**Respuesta 201**:
```json
{
  "ruta_id": "507f1f77bcf86cd799439012",
  "nombre_ruta": "Mi Nueva Ruta",
  "estado": "ACTIVA",
  "archivos_procesados": 2
}
```

**Respuesta 400 (Error)**:
```json
{
  "error": "El nombre de la ruta ya existe para este usuario"
}
```

---

### 3. Validaciones de Archivo
```bash
# Archivo con extensión inválida
curl -X POST http://127.0.0.1:5000/crear-ruta \
  -F "nombre_ruta=Test" \
  -F "archivos=@archivo.txt"

# Respuesta 400
{
  "error": "Extensión .txt no soportada. Solo: PDF, DOCX, PPTX"
}
```

---

## Verificación de Base de Datos

### Ver Documentos Migrados
```bash
# En MongoDB shell
db.rutas_aprendizaje.find().pretty()

# Resultado esperado:
{
  "_id": ObjectId("..."),
  "usuario": "user@example.com",
  "nombre_ruta": "Ruta 1",
  "descripcion": "Importada automáticamente",
  "estado": "ACTIVA",
  "archivos_fuente": [...],
  "fecha_creacion": ISODate("..."),
  "fecha_ingesta": ISODate("..."),
  "fecha_actualizacion": ISODate("..."),
  ...
}
```

### Ver Índices
```bash
db.rutas_aprendizaje.getIndexes()

# Resultado esperado:
[
  { "v": 2, "key": { "_id": 1 } },
  { "v": 2, "key": { "usuario": 1, "nombre_ruta": 1 }, "unique": true },
  { "v": 2, "key": { "usuario": 1, "fecha_actualizacion": -1 } }
]
```

---

## Checklist de Testing

```
Frontend UI
☐ Botón "Crear Nueva Ruta" visible y funcional
☐ Modal abre con formulario
☐ Validaciones en tiempo real (nombre, archivo)
☐ Error messages formatados
☐ Botón "Ver Mis Rutas" visible
☐ Modal lista con cards renderizadas
☐ Botones "Continuar" y "Detalles" funcionales
☐ Sección legacy "Cargar Estado" funciona

Backend API
☐ GET /rutas/lista retorna 200
☐ POST /crear-ruta retorna 201
☐ Validación de nombre único por usuario
☐ Validación de extensiones
☐ Validación de tamaño archivo
☐ FormData procesado correctamente

Database
☐ Campo nombre_ruta existe
☐ Índice UNIQUE (usuario, nombre_ruta) funciona
☐ Índice (usuario, fecha_actualizacion) DESC funciona
☐ Documentos viejos migraron correctamente

Security
☐ XSS protection activo (escape_html)
☐ Validación servidor + cliente
☐ Límites de tamaño aplicados
☐ Sesión requerida para acceso
```

---

## Troubleshooting

### "Redirigido a login"
→ Necesitas estar logueado. Accede a http://127.0.0.1:5000/login primero

### "Error 404 /crear-ruta"
→ Verifica que app.py esté actualizado con los 4 nuevos endpoints

### "Extensión PDF no soportada"
→ Revisa la validación en `validarArchivos()` - incluye 'pdf'

### "Índice UNIQUE ya existe"
→ Normal si ejecutaste migration dos veces, no hay problema

### Modal no carga rutas
→ Abre la consola (F12) y revisa Network tab en /rutas/lista

---

## Comandos Útiles

```powershell
# Ejecutar migration manualmente
python migration_schema_v2.py

# Ejecutar testing E2E
python test_e2e_phase4.py

# Ver logs del servidor Flask
# (Flask logging activo por defecto)

# Resetear base de datos (ADVERTENCIA: borra datos)
# db.rutas_aprendizaje.deleteMany({})
```

---

## Notas Importantes

⚠️ **Importante**: La feature de "Crear Ruta" requiere:
- Usuario autenticado (sesión activa)
- Archivos en formato PDF/DOCX/PPTX
- Nombre único por usuario (índice UNIQUE)
- Conexión a MongoDB funcional

✅ **Backward Compatible**: Las rutas antiguas siguen funcionando sin cambios

🔄 **Documentos Migrados**: 1 documento actualizado automáticamente con nombre "Ruta 1"

---

## Contacto / Preguntas

Si encuentras problemas:
1. Revisa la consola del navegador (F12 → Console)
2. Revisa los logs del servidor Flask
3. Verifica que MongoDB esté en línea
4. Confirma que estés autenticado

