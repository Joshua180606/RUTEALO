# 🏗️ DIAGRAMA DE ARQUITECTURA - NUEVA FUNCIONALIDAD

## Flujo de Datos - Crear Nueva Ruta

```
┌─────────────────────────────────────────────────────────────────────┐
│                     USUARIO EN NAVEGADOR                             │
│                                                                       │
│  [➕ Crear Ruta] → abrirModalCrearRuta()                            │
│         ↓                                                             │
│    [Modal Abre] → formCrearRuta                                      │
│         ↓                                                             │
│  [Ingresa Datos] → validaciones en tiempo real                       │
│    - Nombre (3-100 chars)                                            │
│    - Descripción (0-500 chars)                                       │
│    - Archivos (1+, <50MB c/u, PDF/DOCX/PPTX)                       │
│         ↓                                                             │
│  [Click 🚀 Crear] → validarNombreRuta()                             │
│         ↓             validarDescripcion()                            │
│  [Validaciones OK?] → validarArchivos()                              │
│         ↓ SÍ                                                         │
│  POST /crear-ruta (FormData)                                         │
│                                                                       │
└──────────────────────────┬──────────────────────────────────────────┘
                          │
        ┌─────────────────▼────────────────┐
        │   SERVIDOR FLASK (src/app.py)   │
        │                                  │
        │ @app.route('/crear-ruta', POST) │
        │   ↓                              │
        │ Validar usuario autenticado     │
        │   ↓                              │
        │ Validar nombre único            │
        │   (índice UNIQUE)               │
        │   ↓                              │
        │ procesar_multiples_archivos_web()
        │   ↓                              │
        │ generar_ruta_aprendizaje()      │
        │   ↓                              │
        │ Guardar en MongoDB              │
        │   ↓                              │
        │ Respuesta 201 {ruta_id}         │
        │                                  │
        └─────────────────┬────────────────┘
                          │
        ┌─────────────────▼────────────────┐
        │   MONGODB (rutas_aprendizaje)   │
        │                                  │
        │ db.insertOne({                  │
        │   usuario: "user@...",          │
        │   nombre_ruta: "...",           │
        │   descripcion: "...",           │
        │   estado: "ACTIVA",             │
        │   archivos_fuente: [...],       │
        │   fecha_creacion: ISODate(),    │
        │   ...                           │
        │ })                              │
        │                                  │
        └─────────────────┬────────────────┘
                          │
        ┌─────────────────▼──────────────────────┐
        │  RESPUESTA AL NAVEGADOR                │
        │                                        │
        │ {                                      │
        │   "ruta_id": "507f...",               │
        │   "estado": "ACTIVA",                 │
        │   "message": "Ruta creada"           │
        │ }                                      │
        │                                        │
        │ [Modal Cierra]                        │
        │ [Modal Rutas Recarga]                 │
        │                                        │
        └────────────────────────────────────────┘
```

---

## Flujo de Datos - Ver Mis Rutas

```
┌───────────────────────────────────────────────────┐
│           USUARIO EN NAVEGADOR                     │
│                                                    │
│  [📚 Ver Mis Rutas] → abrirModalListaRutas()     │
│         ↓                                          │
│    [Modal Abre] → cargarListaRutas()             │
│         ↓                                          │
│  GET /rutas/lista                                │
│                                                    │
└────────────────────┬────────────────────────────┘
                     │
         ┌───────────▼──────────┐
         │ SERVIDOR FLASK       │
         │                      │
         │ GET /rutas/lista     │
         │   ↓                  │
         │ obtener_rutas_user() │
         │   ↓                  │
         │ db.find({usuario})   │
         │                      │
         └───────────┬──────────┘
                     │
         ┌───────────▼─────────┐
         │ MONGODB             │
         │                     │
         │ Busca por usuario   │
         │ Retorna array []    │
         │                     │
         └───────────┬─────────┘
                     │
      ┌──────────────▼──────────────┐
      │ RESPUESTA JSON              │
      │                             │
      │ {                           │
      │   "rutas": [                │
      │     {                       │
      │       "ruta_id": "...",     │
      │       "nombre_ruta": "...", │
      │       "descripcion": "...", │
      │       "estado": "ACTIVA",   │
      │       "archivos_count": 3,  │
      │       "niveles_...": 0,     │
      │       "fecha_act...": "..." │
      │     },                      │
      │     ...                     │
      │   ]                         │
      │ }                           │
      │                             │
      └──────────────┬──────────────┘
                     │
      ┌──────────────▼──────────────────┐
      │ NAVEGADOR                       │
      │                                 │
      │ renderizarListaRutas(rutas)    │
      │   ↓                             │
      │ Itera array                     │
      │ Crea cards HTML:                │
      │                                 │
      │ <div class="ruta-card">         │
      │   📚 Nombre                     │
      │   📄 3 archivos                 │
      │   ✓ 0 niveles                   │
      │   🟢 ACTIVA                     │
      │   [▶️ Continuar][👁️ Detalles] │
      │ </div>                          │
      │                                 │
      └─────────────────────────────────┘
```

---

## Estructura de Directorios (Actualizada)

```
RUTEALO/
├── src/
│   ├── app.py ★ (actualizados: +4 endpoints, imports)
│   ├── web_utils.py ★ (nuevos: +2 funciones)
│   ├── database.py
│   ├── config.py
│   ├── models/
│   │   ├── etiquetado_bloom.py
│   │   ├── evaluacion_zdp.py
│   │   └── motor_prompting.py
│   ├── data/
│   │   ├── df_bloom.py
│   │   ├── df_flow.py
│   │   ├── df_zdp.py
│   │   └── ingesta_datos.py
│   └── templates/
│       ├── dashboard.html ★ (REDISEÑADO: +500 líneas)
│       ├── base.html
│       ├── login.html
│       ├── register.html
│       └── landing.html
│
├── tests/
│   ├── test_app.py
│   ├── test_database.py
│   ├── test_utils.py
│   └── conftest.py
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── uploads/
│
├── migration_schema_v2.py ★ (NUEVO: ejecutado)
├── test_e2e_phase4.py ★ (NUEVO: testing)
├── ESTADO_FASE4_COMPLETADA.md ★ (NUEVO)
├── RESUMEN_RAPIDO_IMPLEMENTACION.md ★ (NUEVO)
├── GUIA_TESTING_NUEVA_FEATURE.md ★ (NUEVO)
├── requirements.txt
├── pytest.ini
└── README.md
```

---

## Componentes Principales

```
┌─────────────────────────────────────────────────────┐
│              FRONTEND (HTML/CSS/JS)                 │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Dashboard Page                                     │
│  ├─ Intro Section (gradient, 2 botones)           │
│  ├─ Modal: Crear Ruta                              │
│  │   ├─ Form: nombre, descripción, archivos        │
│  │   ├─ Real-time validation                       │
│  │   └─ Error/Success messages                     │
│  │                                                  │
│  ├─ Modal: Lista Rutas                             │
│  │   ├─ Spinner cargando                           │
│  │   ├─ Cards: nombre, desc, estado, archivos      │
│  │   └─ Botones: Continuar, Detalles              │
│  │                                                  │
│  ├─ Sección: Ruta Actual (legacy)                  │
│  └─ Sección: Archivos Legacy                       │
│                                                     │
└─────────────────────────────────────────────────────┘
                        ↕
                   AJAX/Fetch
                        ↕
┌─────────────────────────────────────────────────────┐
│              BACKEND (Flask/Python)                 │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Routes:                                            │
│  ├─ POST /crear-ruta                              │
│  │   ├─ Validar usuario                            │
│  │   ├─ Validar nombre único (índice)             │
│  │   ├─ procesar_multiples_archivos_web()         │
│  │   ├─ generar_ruta_aprendizaje()                │
│  │   └─ return 201 {ruta_id}                      │
│  │                                                  │
│  ├─ GET /rutas/lista                              │
│  │   ├─ obtener_rutas_usuario()                   │
│  │   └─ return 200 {rutas: [...]}                 │
│  │                                                  │
│  ├─ PUT /actualizar                               │
│  │   ├─ Validar ownership                         │
│  │   └─ return 200 {updated}                      │
│  │                                                  │
│  └─ DELETE /ruta/<id>                             │
│      ├─ Validar ownership                         │
│      └─ return 200 {deleted}                      │
│                                                     │
│  Funciones:                                         │
│  ├─ procesar_multiples_archivos_web(files)        │
│  ├─ obtener_rutas_usuario(usuario)                │
│  └─ (existentes: generar_ruta, examen, etc)      │
│                                                     │
└─────────────────────────────────────────────────────┘
                        ↕
                   PyMongo
                        ↕
┌─────────────────────────────────────────────────────┐
│           DATABASE (MongoDB)                        │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Collection: rutas_aprendizaje                      │
│                                                     │
│  Campos:                                            │
│  ├─ _id                                            │
│  ├─ usuario (indexado)                             │
│  ├─ nombre_ruta (requerido, indexado UNIQUE)      │
│  ├─ descripcion                                    │
│  ├─ estado: ACTIVA|PAUSADA|COMPLETADA             │
│  ├─ archivos_fuente (array)                       │
│  ├─ fecha_creacion (indexado DESC)                │
│  ├─ fecha_ingesta                                  │
│  ├─ fecha_actualizacion (indexado DESC)           │
│  └─ ... (campos legacy)                            │
│                                                     │
│  Índices:                                           │
│  ├─ PRIMARY: _id                                   │
│  ├─ UNIQUE: (usuario, nombre_ruta)    ⚡ NUEVO    │
│  └─ INDEX: (usuario, fecha_act) DESC  ⚡ NUEVO    │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## Flujo de Validación - JavaScript

```
Envío de Formulario
        ↓
validarNombreRuta(nombre)
  ├─ ¿Está vacío? → Error "requerido"
  ├─ ¿< 3 chars? → Error "mínimo 3"
  ├─ ¿> 100 chars? → Error "máximo 100"
  └─ ✅ Válido
        ↓
validarDescripcion(desc)
  ├─ ¿> 500 chars? → Error "máximo 500"
  └─ ✅ Válido
        ↓
validarArchivos(files)
  ├─ ¿Sin archivos? → Error "mínimo 1"
  ├─ Para cada archivo:
  │   ├─ ¿Ext inválida? → Error "(docx no soportado)"
  │   ├─ ¿> 50MB? → Error "excede límite"
  │   └─ ✅ Válido
  └─ ✅ Todos válidos
        ↓
FormData + POST /crear-ruta
        ↓
Respuesta del servidor
  ├─ 201 → Éxito, ruta_id
  ├─ 400 → Error validación servidor
  ├─ 409 → Conflicto (nombre duplicado)
  └─ 401 → No autenticado
```

---

## Timeline de Desarrollo

```
Hora 1:00 - 1:30  →  FASE 1.1: Schema migration MongoDB ✅
Hora 1:30 - 2:00  →  FASE 1.2: Funciones web_utils.py ✅
Hora 2:00 - 2:30  →  FASE 1.3: Endpoints Flask ✅
Hora 2:30 - 3:00  →  FASE 2: Frontend HTML/CSS ✅
Hora 3:00 - 3:30  →  FASE 3: JavaScript + Validaciones ✅
Hora 3:30 - 4:00  →  FASE 4: Testing E2E ✅
Hora 4:00 - 4:30  →  FASE 5: Documentación ✅

Total: ~4.5 horas
Código: ~1,200+ líneas
Tests: 5 pruebas E2E
```

---

## Métricas Finales

| Métrica | Valor |
|---------|-------|
| **Endpoints Nuevos** | 4 |
| **Funciones Nuevas** | 2 |
| **Funciones JavaScript** | 12+ |
| **Líneas de Código** | ~1,200 |
| **Líneas Frontend** | +500 (dashboard.html) |
| **Líneas Backend** | +400 (app.py + web_utils.py) |
| **Líneas Database** | +5 campos, +2 índices |
| **Tests E2E** | 5 |
| **Documentación** | 4 archivos |
| **Cobertura** | CRUD completo |
| **Seguridad** | XSS, validación, UNIQUE |

---

**Estado Final**: ✅ 100% Completado y Documentado

