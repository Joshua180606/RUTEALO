# Cambios Pendientes en dashboard.html

## Resumen
Los cambios en el backend están completados. Falta actualizar el JavaScript en `dashboard.html`.

## Backend Completado ✅
1. Uploads ahora crean carpeta por ruta: `uploads/USUARIO/NOMBRE_RUTA/`
2. Endpoint `/ruta/<ruta_id>/fuentes` creado
3. Renombrado `examen_inicial` → `test_inicial`
4. Modal Fuentes agregado al HTML

## Frontend Pendiente 🔄

### 1. Reemplazar función `renderRutaEspecifica` (línea ~713)
- Agregar variable global: `let rutaActualCargada = null;`
- Renombrar `examenInicial` → `testInicial`
- Implementar lógica progresiva:
  - Si test pendiente: mostrar solo card del test
  - Si test completado: mostrar solo nivel Bloom actual (primer nivel disponible)
  - Ocultar niveles bloqueados

### 2. Agregar función `cargarTestInicial()`
Cargar test diagnóstico y renderizarlo

### 3. Agregar función `renderTestInicial(contenido)`
Renderizar formulario del test

### 4. Agregar función `abrirModalFuentes()`
Mostrar archivos fuente de la ruta actual

### 5. Renombrar en toda la UI
- "Examen" → "Test"
- "Examen inicial" → "Test diagnóstico"
- "Examen Diagnóstico" → "Test Diagnóstico"

## Instrucción para el usuario
Por favor, reinicia el servidor Flask y prueba:
1. Crear nueva ruta
2. Ver que archivos se guardan en `uploads/USUARIO/NOMBRE_RUTA/`
3. Hacer clic en "Fuentes" (debería abrir modal con archivos)
4. Ver que solo se muestra el paso actual (test o nivel Bloom)
