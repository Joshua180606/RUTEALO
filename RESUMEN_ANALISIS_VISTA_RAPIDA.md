# 📋 RESUMEN EJECUTIVO ANÁLISIS - Vista Rápida

**Análisis completado:** 2025-12-10  
**Tiempo estimado implementación:** 7-9 horas

---

## 🎯 EL PLAN EN 3 MINUTOS

### ¿Qué queremos?
Cambiar el dashboard para que los usuarios puedan:
1. **Crear nuevas rutas** con nombre, descripción y múltiples archivos
2. **Seleccionar rutas existentes** de una lista
3. Ver el progreso en cada ruta

### ¿Qué hay que cambiar?
| Componente | Estado Actual | Estado Final | Esfuerzo |
|-----------|---------------|-------------|----------|
| **Backend endpoints** | 11 | 15 | +4 endpoints (95 min) |
| **Backend funciones** | 12 | 14 | +2 funciones (35 min) |
| **Schema BD** | 10 campos | 15 campos | +5 campos (15 min) |
| **HTML dashboard** | 452 líneas | 700 líneas | Rediseño (100 min) |
| **JavaScript** | 250 líneas | 425 líneas | +8 funciones (155 min) |
| **CSS** | Existente | +100 líneas | New styles (20 min) |

### ¿Cuánto tiempo?
```
Backend:  160 minutos (2h 40min)
Frontend: 275 minutos (4h 35min)
Testing:  60+ minutos (1h+)
──────────────────────────
TOTAL:    7-9 horas
```

---

## 🏗️ ARQUITECTURA EN DIAGRAMA

```
┌─────────────────────────────────────┐
│     USUARIO (Navegador Web)         │
└────────────┬────────────────────────┘
             │
             ↓
┌─────────────────────────────────────┐
│      FRONTEND (dashboard.html)       │
│  ─────────────────────────────────  │
│  Intro Section                      │
│  ├─ Btn: Crear Nueva Ruta          │
│  └─ Btn: Elegir Ruta Existente     │
│                                     │
│  Modal 1: Crear Ruta               │
│  ├─ Input: nombre_ruta            │
│  ├─ Textarea: descripcion          │
│  ├─ File: múltiples archivos       │
│  └─ Btn: Enviar                    │
│                                     │
│  Modal 2: Listar Rutas             │
│  ├─ Tarjeta 1 (nombre, progreso)  │
│  ├─ Tarjeta 2 (...)               │
│  └─ Btn: Continuar/Detalles       │
│                                     │
│  Sección: Examen/Ruta              │
│  └─ (Mantener lógica existente)    │
└───────────────┬─────────────────────┘
                │ fetch()
                ↓
┌─────────────────────────────────────┐
│      BACKEND FLASK (app.py)         │
│  ─────────────────────────────────  │
│  ✅ GET  /                          │
│  ✅ GET/POST /register              │
│  ✅ GET/POST /login                 │
│  ✅ GET  /dashboard (CAMBIAR)       │
│  ✅ POST /upload (MANTENER)         │
│  ✅ GET  /files                     │
│  ✅ GET  /download/<archivo>        │
│  ✅ GET  /ruta/estado               │
│  ✅ GET  /examen-inicial            │
│  ✅ POST /examen-inicial/responder  │
│  ❌ GET  /rutas/lista      (NUEVA)  │
│  ❌ POST /crear-ruta       (NUEVA)  │
│  ❌ PUT  /ruta/<id>/actua. (NUEVA)  │
│  ❌ DEL  /ruta/<id>        (NUEVA)  │
└───────────────┬─────────────────────┘
                │
                ↓
┌─────────────────────────────────────┐
│    FUNCIONES DE LÓGICA (web_utils)  │
│  ─────────────────────────────────  │
│  ✅ procesar_archivo_web()          │
│  ✅ auto_etiquetar_bloom()          │
│  ✅ generar_ruta_aprendizaje()      │
│  ✅ procesar_respuesta_examen_web() │
│  ❌ procesar_multiples_archivos()   │ (NUEVA)
│  ❌ obtener_rutas_usuario()         │ (NUEVA)
└───────────────┬─────────────────────┘
                │
                ↓
┌─────────────────────────────────────┐
│    DATABASE (MongoDB)               │
│  ─────────────────────────────────  │
│  Collection: usuario_perfil         │
│  Collection: materiales_crudos      │
│  Collection: examen_inicial         │
│  Collection: rutas_aprendizaje      │
│  ├─ usuario (existente)            │
│  ├─ nombre_ruta (NUEVO)            │
│  ├─ descripcion (NUEVO)            │
│  ├─ estado (NUEVO)                 │
│  ├─ archivos_fuente (NUEVO)        │
│  ├─ fecha_creacion (NUEVO)         │
│  ├─ fecha_actualizacion (exist.)   │
│  └─ ... (otros campos existentes)  │
└─────────────────────────────────────┘
```

---

## 📝 FLUJOS DE USUARIO

### Flujo 1: Crear Nueva Ruta
```
1. Usuario ve dashboard intro
2. Hace click en "Crear Nueva Ruta"
3. Abre Modal "Crear Ruta"
4. Llena: nombre, descripción, archivos
5. Preview muestra archivos seleccionados
6. Click "Generar Ruta"
7. Frontend valida
8. POST /crear-ruta (con FormData)
9. Backend procesa:
   - Valida nombre (único por usuario)
   - Procesa múltiples archivos
   - Ejecuta Bloom etiquetado
   - Genera examen + ruta
   - Guarda en BD con metadata
10. Respuesta 201 con ruta_id
11. Cierra modal
12. Recarga lista de rutas
13. Usuario ve su ruta en lista
```

### Flujo 2: Seleccionar Ruta Existente
```
1. Usuario ve dashboard intro
2. Hace click en "Elegir Ruta Existente"
3. Abre Modal "Listar Rutas"
4. GET /rutas/lista
5. Backend retorna lista de rutas
6. Frontend renderiza tarjetas con:
   - Nombre + descripción
   - Progress bar
   - Metadata (archivos, niveles)
   - Botones: Continuar, Detalles
7. Usuario click "Continuar"
8. Cierra modal
9. Carga examen o ruta (según estado)
10. Usuario ve examen/ruta personalizado
```

### Flujo 3: Completar Examen
```
1. Usuario ve examen inicial
2. Responde todas las preguntas
3. Click "Enviar Examen"
4. Frontend valida (todas respondidas)
5. POST /examen-inicial/responder
6. Backend evalúa + actualiza ZDP
7. Respuesta 200 con resultado
8. Frontend recarga estado
9. Usuario ve ruta personalizada
```

---

## 🔧 CAMBIOS RESUMIDOS

### Backend (3 archivos)
```diff
src/app.py
+ Endpoint GET /rutas/lista            (30 min)
+ Endpoint POST /crear-ruta            (45 min)
+ Endpoint PUT /ruta/<id>/actualizar   (15 min, OPCIONAL)
+ Endpoint DELETE /ruta/<id>           (10 min, OPCIONAL)
- (No eliminar nada)

src/web_utils.py
+ Función procesar_multiples_archivos_web()  (20 min)
+ Función obtener_rutas_usuario()            (15 min)
- (No eliminar nada)

src/database.py
= (Sin cambios)
```

### Frontend (1 archivo)
```diff
src/templates/dashboard.html

HTML CAMBIOS:
- Eliminar panel izquierdo (upload)
+ Agregar sección intro (descripción + 2 botones)
+ Agregar Modal "Crear Ruta"
+ Agregar Modal "Listar Rutas"

JavaScript CAMBIOS:
+ Función abrirModalCrearRuta()
+ Función actualizarPreviewArchivos()
+ Función validarFormularioCrearRuta()
+ Función enviarFormularioCrearRuta()
+ Función cargarListaRutas()
+ Función renderizarListaRutas()
+ Función continuarRuta()
+ Función verDetallesRuta()
= Mantener cargarEstadoRuta(), renderExamen(), renderRuta()

CSS CAMBIOS:
+ Estilos para intro section
+ Estilos para modales
+ Estilos para tarjetas de ruta
+ Estilos responsivos
```

### Database Schema
```diff
rutas_aprendizaje

+ nombre_ruta: string (required, max 100)
+ descripcion: string (optional, max 500)
+ estado: enum (ACTIVA|PAUSADA|COMPLETADA)
+ archivos_fuente: array de objects
+ fecha_creacion: date

+ Index: (usuario, nombre_ruta) UNIQUE
+ Index: (usuario, fecha_actualizacion) DESC
```

---

## ⚠️ RIESGOS Y MITIGACIÓN

| Riesgo | Prob. | Impacto | Mitigación |
|--------|-------|--------|-----------|
| Rutas existentes sin nombre | Media | Alto | Migración asigna nombres genéricos |
| Validación insuficiente | Alta | Medio | Validar en backend + frontend |
| Confusión UI usuarios | Media | Bajo | Instrucciones claras + testing |
| Rendimiento con muchas rutas | Baja | Medio | Índices BD + paginación futura |
| Regresiones en funcionalidad | Media | Alto | Testing E2E completo |

---

## ✅ CRITERIOS DE ÉXITO

**Backend:**
- [ ] GET /rutas/lista retorna lista correcta
- [ ] POST /crear-ruta crea ruta con metadata
- [ ] Validaciones funcionan (nombre único, tamaño, etc.)
- [ ] Múltiples archivos procesan correctamente
- [ ] Examen + ruta generan en nueva ruta

**Frontend:**
- [ ] Dashboard intro muestra correctamente
- [ ] Modales abren/cierran sin errores
- [ ] Preview de archivos funciona
- [ ] Validación previene submit incompleto
- [ ] Lista de rutas renderiza tarjetas
- [ ] Continuar ruta carga examen/contenido

**Integración:**
- [ ] Flujo completo: crear → examen → ruta funciona
- [ ] Flujo completo: seleccionar existente funciona
- [ ] Sin regresiones en flujos antiguos
- [ ] Manejo de errores claro para usuario
- [ ] Responsive en móvil

---

## 📅 CRONOGRAMA ESTIMADO

```
FASE 1: Backend (160 min)
├─ Schema BD (15 min)
├─ Funciones web_utils (35 min)
└─ Endpoints app.py (95 min)
   ├─ GET /rutas/lista (30 min)
   ├─ POST /crear-ruta (45 min)  ← MÁS COMPLEJO
   └─ PUT/DELETE (20 min, opcional)

FASE 2: Frontend (275 min)
├─ HTML (100 min)
│  ├─ Intro section (50 min)
│  └─ 2 Modales (50 min)
├─ CSS (20 min)
└─ JavaScript (155 min)
   ├─ Funciones form (90 min)
   ├─ Funciones ruta (50 min)
   └─ Event listeners (15 min)

FASE 3: Integración (60+ min)
├─ Testing E2E (30 min)
├─ Debugging (20 min)
└─ Optimizaciones (10+ min)

TOTAL: 7-9 horas
```

---

## 🎓 PUNTOS CLAVE RECORDAR

1. **Backend PRIMERO:** Frontend no funcionará sin endpoints
2. **Test cada función:** No esperar al final
3. **Mantener compatibilidad:** /upload original sigue funcionando
4. **Orden crítico:** BD → Funciones → Endpoints → Frontend
5. **Documentar cambios:** Actualizar comentarios en código
6. **Git commits frecuentes:** Cada sección completada
7. **No eliminar código:** Solo agregar nuevas features

---

## 📊 ESTADO ACTUAL

| Ítem | Estado | Progreso |
|------|--------|----------|
| **Análisis completado** | ✅ | 100% |
| **Arquitectura definida** | ✅ | 100% |
| **Plan detallado** | ✅ | 100% |
| **Documentación** | ✅ | 100% |
| **Implementación** | ⏳ | 0% |
| **Testing** | ⏳ | 0% |
| **Deployment** | ⏳ | 0% |

---

## 🚀 PRÓXIMO PASO

**Iniciar FASE 1: Backend - Schema MongoDB**
- Crear script de migración
- Agregar 5 nuevos campos
- Crear 2 índices
- Validar conexión

**Tiempo:** 15 minutos

---

**Análisis por:** AI Assistant  
**Fecha:** 2025-12-10  
**Validación:** Pendiente

