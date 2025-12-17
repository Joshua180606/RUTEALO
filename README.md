# RUTEALO

**Sistema Inteligente de Rutas de Aprendizaje Personalizado**

Plataforma web educativa que utiliza IA para generar rutas de aprendizaje adaptadas a cada estudiante, basándose en la **Zona de Desarrollo Próximo (ZDP)** de Vygotsky y la **Taxonomía de Bloom**. Incluye procesamiento de documentos académicos, evaluación automática, generación de material pedagógico y un chatbot tutor multilingüe.

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-Web_Framework-green.svg)](https://flask.palletsprojects.com/)
[![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-green.svg)](https://www.mongodb.com/cloud/atlas)
[![Gemini AI](https://img.shields.io/badge/Gemini-AI_1.5_Pro-orange.svg)](https://ai.google.dev/)

---

## ✨ Características Principales

### 🎯 Evaluación Inteligente con ZDP
- **Evaluación diagnóstica inicial** con 30 preguntas multinivel
- **Scoring automático** por niveles de Bloom (umbral de competencia: 70%)
- **Identificación de zona próxima** de desarrollo del estudiante
- **Adaptación dinámica** del contenido según el perfil del usuario

### 📚 Clasificación Automática de Contenido
- **Etiquetado Bloom automático** utilizando Gemini AI
- **6 niveles cognitivos**: Recordar, Comprender, Aplicar, Analizar, Evaluar, Crear
- **Procesamiento de documentos**: PDF, DOCX, PPTX con extracción de texto e imágenes
- **Almacenamiento con GridFS** para archivos grandes en MongoDB

### 🎓 Generadores Pedagógicos Especializados
- **Flashcards enriquecidas** con teoría pedagógica (150+ palabras por tarjeta)
- **Exámenes multinivel** con feedback diferenciado según estrategia ZDP
- **3 estrategias de generación**:
  - `scaffolding`: Para niveles inferiores (5-7 flashcards, soporte adicional)
  - `refuerzo`: Para consolidación (7+ flashcards, ejercicios variados)
  - `estándar`: Para niveles competentes (3-5 flashcards equilibradas)

### 🤖 Chatbot Tutor Multilingüe
- **Transcripción de audio** con OpenAI Whisper API
- **Soporte de 3 idiomas**: Español, Inglés, Quechua
- **Contexto de ruta inteligente**: Accede a flashcards, exámenes y material del estudiante
- **Respuestas pedagógicas adaptadas** al nivel Bloom actual del usuario
- **Prompts especializados** por idioma con estrategias de enseñanza diferenciadas

### 🔧 Optimizaciones Implementadas
- **Reducción de tokens del 40%** mediante omisión inteligente de contenido ya dominado
- **Connection pooling** de MongoDB con configuración optimizada
- **4 claves API especializadas** de Google Gemini para evitar límites de rate limit:
  - `IDENTIFICADOR`: Etiquetado Bloom
  - `EXAMEN_INICIAL`: Generación de exámenes diagnósticos
  - `RUTEADOR`: Creación de rutas de aprendizaje
  - `CHATBOT`: Tutor virtual multilingüe

### 🌐 Dashboard Web Interactivo
- **Sistema de autenticación** con validación de credenciales
- **Gestión de archivos** por usuario con carpetas aisladas
- **Visualización de rutas** con progreso en tiempo real
- **Modales enriquecidos** con Bootstrap para flashcards y exámenes
- **API REST** para operaciones CRUD de rutas

### ✅ Testing Automatizado
- **50+ tests unitarios** implementados con pytest
- **Cobertura de módulos**: utils, database, app
- **Tests de validación**: credenciales, exámenes, respuestas, manejo de archivos
- **Configuración UTF-8** para compatibilidad internacional

## 🛠️ Tecnologías Utilizadas

### Backend
- **Flask** - Framework web Python para API REST y renderizado de templates
- **Python 3.8+** - Lenguaje principal del proyecto
- **python-dotenv** - Gestión de variables de entorno desde `claves.env`

### Base de Datos
- **MongoDB Atlas** - Base de datos NoSQL en la nube
- **PyMongo 4.0+** - Driver oficial de MongoDB para Python
- **GridFS** - Sistema de archivos distribuido para almacenar documentos grandes

### Inteligencia Artificial
- **Google Gemini 1.5 Pro** (gemini-2.5-flash) - Modelo generativo para:
  - Clasificación automática según Taxonomía de Bloom
  - Generación de exámenes diagnósticos personalizados
  - Creación de flashcards pedagógicas enriquecidas
  - Chatbot tutor con contexto de ruta
- **OpenAI Whisper API** - Transcripción de audio multilingüe (chatbot)

### Procesamiento de Documentos
- **PyPDF** - Extracción de texto e imágenes de archivos PDF
- **python-docx** - Lectura de documentos Word (.docx)
- **python-pptx** - Procesamiento de presentaciones PowerPoint (.pptx)
- **Pillow** - Manipulación de imágenes extraídas

### Testing y Calidad
- **pytest** - Framework de testing con 50+ tests unitarios
- **pytest.ini** - Configuración UTF-8 y estructura de tests

### Frontend
- **HTML5/CSS3/JavaScript** - Interfaz web responsive
- **Bootstrap** - Framework CSS para modales y componentes UI
- **Werkzeug** - Utilidades WSGI para manejo seguro de archivos

### Logging y Monitoreo
- **logging** (Python estándar) - Sistema de logs estructurado con:
  - Formato JSON para logs de producción
  - Rotación automática de archivos de log
  - Niveles configurables (DEBUG/INFO según entorno)
  - Logs coloreados para desarrollo

---

## 📋 Requisitos Previos

Antes de instalar RUTEALO, asegúrate de tener:

1. **Python 3.8 o superior** instalado
   ```powershell
   python --version  # Debe mostrar Python 3.8+
   ```

2. **Cuenta de MongoDB Atlas** (gratuita)
   - Crear cluster en: https://www.mongodb.com/cloud/atlas/register
   - Obtener URI de conexión con formato: `mongodb+srv://usuario:password@cluster.mongodb.net/`

3. **Claves API de Google AI Studio** (4 claves recomendadas)
   - Obtener en: https://ai.google.dev/
   - Se recomiendan 4 claves para evitar límites de rate limit

4. **Clave API de OpenAI** (para chatbot)
   - Obtener en: https://platform.openai.com/api-keys
   - Solo necesaria si usarás la funcionalidad de transcripción de audio

5. **Windows PowerShell** (recomendado para instalación)
   - Incluido en Windows 10/11 por defecto

---

## 📦 Instalación

### Opción 1: Instalación Automatizada (Recomendada)

Ejecuta el script de PowerShell que crea automáticamente el entorno virtual e instala dependencias:

```powershell
.\install_requirements.ps1
```

Este script:
1. Crea una carpeta `.venv` con el entorno virtual
2. Instala todas las dependencias de `requirements.txt`
3. Activa automáticamente el entorno virtual

### Opción 2: Instalación Manual

```powershell
# Crear entorno virtual
python -m venv .venv

# Activar entorno virtual
.\.venv\Scripts\Activate.ps1

# Instalar dependencias
pip install -r requirements.txt
```

### Dependencias Instaladas

```txt
pandas                    # Procesamiento de datos CSV (marcos pedagógicos)
pypdf                     # Extracción de PDFs
pymongo>=4.0              # Driver MongoDB con connection pooling
python-docx               # Lectura de archivos Word
python-pptx               # Procesamiento de PowerPoint
google-generativeai       # SDK de Google Gemini
python-dotenv             # Variables de entorno
flask                     # Framework web
werkzeug                  # Utilidades WSGI
pillow                    # Procesamiento de imágenes
openai>=1.0.0             # API de OpenAI (Whisper)
```

---

## ⚙️ Configuración

### 1. Crear Archivo de Variables de Entorno

Crea un archivo `claves.env` en la raíz del proyecto con el siguiente contenido:

```env
# ============================================
# CONFIGURACIÓN DE MONGODB ATLAS
# ============================================
MONGO_URI="mongodb+srv://usuario:password@cluster.mongodb.net/?retryWrites=true&w=majority"
DB_NAME="RUTEALO_DB"

# Configuración de connection pooling (opcional)
MONGODB_MIN_POOL_SIZE=1
MONGODB_MAX_POOL_SIZE=10
MONGODB_POOL_SIZE=30000
MONGODB_CONNECT_TIMEOUT=10000
MONGODB_SOCKET_TIMEOUT=30000

# ============================================
# CLAVES API DE GOOGLE GEMINI (4 especializadas)
# ============================================
# Clave 1: Para etiquetado automático de Bloom
GOOGLE_API_KEY_IDENTIFICADOR="AIza..."

# Clave 2: Para generación de exámenes diagnósticos
GOOGLE_API_KEY_EXAMEN_INICIAL="AIza..."

# Clave 3: Para creación de rutas de aprendizaje
GOOGLE_API_KEY_RUTEADOR="AIza..."

# Clave 4: Para chatbot tutor multilingüe
GOOGLE_API_KEY_CHATBOT="AIza..."

# ============================================
# CLAVE API DE OPENAI (Chatbot)
# ============================================
# Solo necesaria si usarás transcripción de audio
OPENAI_API_KEY="sk-..."

# ============================================
# CONFIGURACIÓN DE FLASK
# ============================================
SECRET_KEY="CAMBIA_ESTA_CLAVE_POR_UNA_SEGURA_Y_ALEATORIA"
DEBUG=True

# ============================================
# CONFIGURACIÓN DE UPLOADS (opcional)
# ============================================
# MAX_UPLOAD_SIZE=52428800  # 50 MB por defecto
# ALLOWED_EXTENSIONS=pdf,docx,pptx
```

### 2. Notas de Seguridad sobre Claves API

- **Google Gemini**: Puedes usar la misma clave para las 4 variables si solo tienes una, pero se recomienda usar 4 diferentes para evitar límites de rate limit
- **MongoDB URI**: Incluye usuario y contraseña. NUNCA la subas a control de versiones
- **SECRET_KEY**: Genera una clave segura con:
  ```python
  python -c "import secrets; print(secrets.token_hex(32))"
  ```

### 3. Configurar Colecciones de MongoDB

El sistema creará automáticamente 4 colecciones en MongoDB:

| Colección | Propósito |
|-----------|-----------|
| `materiales_crudos` | Archivos procesados (PDF/DOCX/PPTX) con GridFS para imágenes |
| `usuario_perfil` | Perfiles de estudiantes con preferencias de tiempo y descanso |
| `examen_inicial` | Resultados de evaluaciones diagnósticas y scoring ZDP |
| `rutas_aprendizaje` | Rutas personalizadas con flashcards, exámenes y progreso |

### 4. Marcos Pedagógicos (CSV)

El sistema utiliza 3 archivos CSV ubicados en `data/processed/`:

- **df_bloom.csv**: Taxonomía de Bloom con 6 niveles cognitivos y subtipos
- **df_zdp.csv**: Estrategias de Zona de Desarrollo Próximo
- **df_flow.csv**: Teoría de Flow para equilibrio desafío-habilidad

Estos archivos se generan automáticamente al ejecutar:
```powershell
python src/data/df_bloom.py
python src/data/df_zdp.py
python src/data/df_flow.py
```

---

## 🚀 Uso del Sistema

### Iniciar la Aplicación Web

Para ejecutar la aplicación web localmente, usa el modo de módulo desde la raíz del proyecto:

**PowerShell (Recomendado):**
```powershell
# Activar el virtualenv
.\.venv\Scripts\Activate.ps1

# Ejecutar como módulo (mantiene la importación de paquetes)
python -m src.app
```

**Alternativa con Flask CLI:**
```powershell
.\.venv\Scripts\Activate.ps1
flask run --port 5000
```

**Windows CMD:**
```bat
.\.venv\Scripts\activate.bat
python -m src.app
```

La aplicación estará disponible en: **http://localhost:5000**

> ⚠️ **Importante**: Evita ejecutar `python src/app.py` directamente desde la carpeta `src/`, ya que Python no añade automáticamente la raíz del proyecto a `sys.path` y provocará errores de importación.

### Flujo de Uso Completo

#### 1. Registro e Inicio de Sesión
1. Accede a **http://localhost:5000**
2. Haz clic en **"Registrarse"**
3. Completa el formulario con:
   - Datos personales (nombre, apellidos, email, teléfono)
   - Credenciales (usuario y contraseña)
   - Preferencias de estudio (tiempo diario en minutos, día de descanso)
4. Acepta los términos y condiciones
5. Inicia sesión con tus credenciales

#### 2. Subir Material de Estudio
1. En el dashboard, usa el botón **"Subir Archivos"**
2. Selecciona archivos soportados: **PDF**, **DOCX** o **PPTX**
3. El sistema procesará automáticamente:
   - Extracción de texto de cada página/diapositiva
   - Extracción de imágenes (guardadas en GridFS)
   - Almacenamiento en la colección `materiales_crudos`

#### 3. Clasificación Automática (Bloom)
1. Haz clic en **"Etiquetar con Bloom"**
2. El sistema utiliza Gemini AI para clasificar cada unidad de contenido en uno de los 6 niveles:
   - **Recordar**: Definiciones, hechos, conceptos básicos
   - **Comprender**: Explicaciones, resúmenes, interpretaciones
   - **Aplicar**: Procedimientos, ejercicios, casos prácticos
   - **Analizar**: Comparaciones, relaciones, estructuras
   - **Evaluar**: Críticas, juicios, valoraciones
   - **Crear**: Diseños, propuestas, soluciones originales

#### 4. Examen Diagnóstico Inicial
1. Accede a **"Tomar Examen Inicial"**
2. Responde 30 preguntas distribuidas en los 6 niveles de Bloom (5 por nivel)
3. El sistema evaluará automáticamente:
   - **Puntaje por nivel** (porcentaje de aciertos)
   - **Nivel actual** (último nivel con ≥70% de aciertos)
   - **Zona próxima** (niveles inmediatamente superiores al actual)
4. Resultados guardados en `examen_inicial` y `usuario_perfil`

#### 5. Generación de Ruta Personalizada
1. Haz clic en **"Crear Ruta de Aprendizaje"**
2. Proporciona:
   - **Nombre de la ruta** (ej: "Introducción a Física")
   - **Descripción** (opcional)
   - **Duración estimada en horas**
3. El sistema genera automáticamente:
   - **Flashcards pedagógicas** por nivel Bloom con teoría enriquecida (150+ palabras)
   - **Exámenes formativos** adaptados a tu zona próxima
   - **Calendario de estudio** basado en tus preferencias de tiempo
4. La ruta se guarda en `rutas_aprendizaje` con estructura:
   ```json
   {
     "usuario": "nombre_usuario",
     "nombre": "Nombre de la Ruta",
     "descripcion": "Descripción breve",
     "estructura_ruta": {
       "flashcards": {
         "Recordar": [...],
         "Comprender": [...],
         ...
       },
       "examenes": {
         "Recordar": [...],
         "Comprender": [...],
         ...
       }
     },
     "metadatos_ruta": {
       "nivel_actual_estudiante": "Comprender",
       "zona_proxima": ["Aplicar", "Analizar"],
       "duracion_horas": 20,
       "fecha_creacion": "2025-12-17T..."
     },
     "progreso": {
       "flashcards_vistas": 0,
       "examenes_completados": 0,
       "porcentaje_completado": 0
     }
   }
   ```

#### 6. Estudiar con Flashcards
1. Abre una ruta desde el dashboard
2. Navega por las flashcards organizadas por nivel
3. Cada flashcard incluye:
   - **Frente**: Pregunta o concepto clave
   - **Reverso**: Explicación enriquecida con contexto pedagógico
   - Estado **"visto"** que se actualiza automáticamente

#### 7. Practicar con Exámenes
1. Selecciona un examen de la ruta
2. Responde las preguntas en el tiempo estimado
3. Obtén feedback inmediato con:
   - **Calificación automática**
   - **Explicaciones detalladas** de respuestas correctas
   - **Recomendaciones** según tu estrategia ZDP

#### 8. Usar el Chatbot Tutor Multilingüe
1. En cualquier ruta, abre el **chatbot tutor**
2. Selecciona tu idioma preferido: **Español**, **English** o **Quechua**
3. Opciones de interacción:
   - **Texto**: Escribe tu pregunta directamente
   - **Audio**: Graba tu pregunta (transcripción automática con Whisper)
4. El chatbot responderá con:
   - Contexto de tu ruta de aprendizaje
   - Referencias a tus flashcards y material
   - Tono pedagógico adaptado a tu nivel Bloom
   - Ejemplos concretos del material cargado

**Endpoints del Chatbot:**
- `POST /api/transcribir-audio`: Transcribe audio a texto
- `POST /api/chatbot`: Genera respuesta pedagógica

### Procesador de Archivos Standalone

Para procesar archivos sin usar la interfaz web:

```powershell
# Activar virtualenv
.\.venv\Scripts\Activate.ps1

# Ejecutar procesador (abre ventana GUI para seleccionar archivos)
python src/data/ingesta_datos.py
```

Este script:
1. Abre un diálogo de selección de archivos
2. Solicita nombre de usuario
3. Procesa los archivos seleccionados (PDF, DOCX, PPTX)
4. Guarda en MongoDB con estado `PENDIENTE`
5. Muestra resultados en consola

### Gestión de Archivos por Usuario

Cada usuario tiene una carpeta aislada en:
```
data/raw/uploads/<NOMBRE_USUARIO>/
```

Rutas disponibles en la API:
- `GET /files` - Lista archivos del usuario actual
- `GET /download/<archivo>` - Descarga archivo específico
- `POST /upload` - Sube nuevos archivos (límite: 50 MB)

---

## 🏗️ Arquitectura del Sistema

### Estructura de Módulos

```
RUTEALO/
├── src/
│   ├── __init__.py
│   ├── app.py                    # Aplicación Flask principal (21 rutas)
│   ├── config.py                 # Configuración centralizada
│   ├── database.py               # Conexión MongoDB con pooling
│   ├── logging_config.py         # Sistema de logs estructurado
│   ├── utils.py                  # Validaciones y helpers
│   ├── web_utils.py              # Lógica de negocio web
│   ├── generadores_pedagogicos.py # Generadores de flashcards/exámenes
│   │
│   ├── data/                     # Procesamiento de datos
│   │   ├── __init__.py
│   │   ├── ingesta_datos.py      # Procesador de archivos
│   │   ├── df_bloom.py           # Generador CSV Taxonomía Bloom
│   │   ├── df_zdp.py             # Generador CSV ZDP
│   │   └── df_flow.py            # Generador CSV Teoría Flow
│   │
│   ├── models/                   # Lógica IA y modelos
│   │   ├── __init__.py
│   │   ├── chatbot_tutor.py      # Chatbot multilingüe (TutorVirtual)
│   │   ├── etiquetado_bloom.py   # Clasificación automática Bloom
│   │   ├── evaluacion_zdp.py     # Evaluación y scoring (EvaluadorZDP)
│   │   └── motor_prompting.py    # Motor de generación de rutas
│   │
│   ├── templates/                # Vistas HTML
│   │   ├── base.html             # Template base con Bootstrap
│   │   ├── landing.html          # Página de inicio
│   │   ├── login.html            # Formulario login
│   │   ├── register.html         # Formulario registro
│   │   └── dashboard.html        # Dashboard principal (modales ZDP)
│   │
│   └── utils/                    # Utilidades adicionales
│       └── procesar_flashcards.py
│
├── tests/                        # Suite de pruebas (50+ tests)
│   ├── conftest.py               # Fixtures compartidas
│   ├── test_app.py               # Tests de rutas Flask
│   ├── test_database.py          # Tests de conexión MongoDB
│   └── test_utils.py             # Tests de validaciones y helpers
│
├── data/                         # Datos del proyecto
│   ├── processed/                # CSVs pedagógicos generados
│   │   ├── df_bloom.csv
│   │   ├── df_zdp.csv
│   │   └── df_flow.csv
│   └── raw/
│       └── uploads/              # Archivos por usuario
│           └── <USUARIO>/
│
├── logs/                         # Archivos de log (auto-rotación)
├── claves.env                    # Variables de entorno (NO subir a Git)
├── requirements.txt              # Dependencias Python
├── pytest.ini                    # Configuración de tests
├── install_requirements.ps1      # Script instalación Windows
└── README.md                     # Este archivo
```

### Rutas de la Aplicación Flask

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/` | Landing page (redirige a dashboard si está logueado) |
| GET/POST | `/register` | Formulario de registro con validaciones |
| GET/POST | `/login` | Autenticación de usuarios |
| GET | `/logout` | Cierre de sesión |
| GET | `/dashboard` | Panel principal del estudiante |
| POST | `/upload` | Subida de archivos (PDF/DOCX/PPTX) |
| GET | `/files` | Lista de archivos del usuario |
| GET | `/download/<archivo>` | Descarga de archivo específico |
| GET | `/examen-inicial` | Genera examen diagnóstico |
| POST | `/examen-inicial/responder` | Evalúa respuestas del examen |
| GET | `/api/perfil-zdp` | Obtiene perfil ZDP del usuario |
| GET | `/rutas/lista` | Lista rutas del usuario |
| POST | `/crear-ruta` | Crea nueva ruta personalizada |
| GET | `/ruta/estado` | Estado de generación de ruta |
| GET | `/ruta/<id>/contenido` | Flashcards y exámenes de ruta |
| PUT | `/ruta/<id>/actualizar` | Actualiza progreso de ruta |
| DELETE | `/ruta/<id>` | Elimina ruta |
| POST | `/ruta/<id>/regenerar-test` | Regenera examen de nivel |
| GET | `/ruta/<id>/fuentes` | Fuentes de material de ruta |
| POST | `/api/transcribir-audio` | Transcribe audio (Whisper) |
| POST | `/api/chatbot` | Chatbot tutor multilingüe |

### Colecciones de MongoDB

#### `materiales_crudos`
Almacena documentos procesados con su contenido extraído:
```json
{
  "_id": ObjectId("..."),
  "usuario_propietario": "nombre_usuario",
  "nombre_archivo": "documento.pdf",
  "tipo_archivo": "pdf",
  "fecha_ingesta": ISODate("2025-12-17T..."),
  "unidades_contenido": [
    {
      "indice": 1,
      "tipo_unidad": "pagina",
      "contenido_texto": "Texto extraído...",
      "imagenes": [
        {
          "gridfs_id": ObjectId("..."),
          "nombre_archivo": "usuario_documento_P1_IMG0.png"
        }
      ],
      "metadata_bloom": {
        "Categoria_Bloom": "Comprender",
        "Pedagogia_Detalle": {
          "justificacion": "Explica conceptos..."
        }
      }
    }
  ],
  "estado_procesamiento": "COMPLETADO" // o "PENDIENTE"
}
```

#### `usuario_perfil`
Perfil del estudiante con preferencias y scoring ZDP:
```json
{
  "_id": ObjectId("..."),
  "usuario": "nombre_usuario",
  "password_hash": "pbkdf2:sha256:...",
  "datos_personales": {
    "nombres": "Juan",
    "apellidos": "Pérez",
    "email": "juan@example.com",
    "telefono": "987654321"
  },
  "preferencias_estudio": {
    "tiempo_diario_min": 120,
    "dia_descanso": "Domingo"
  },
  "scoring_bloom": {
    "Recordar": 85.0,
    "Comprender": 75.0,
    "Aplicar": 60.0,
    "Analizar": 45.0,
    "Evaluar": 30.0,
    "Crear": 20.0
  },
  "nivel_actual": "Comprender",
  "zona_proxima": ["Aplicar", "Analizar"],
  "fecha_registro": ISODate("2025-12-17T...")
}
```

#### `examen_inicial`
Resultados de evaluaciones diagnósticas:
```json
{
  "_id": ObjectId("..."),
  "usuario": "nombre_usuario",
  "fecha_evaluacion": ISODate("2025-12-17T..."),
  "respuestas_procesadas": [
    {
      "pregunta_id": 1,
      "respuesta_estudiante": "a",
      "respuesta_correcta": "a",
      "es_correcta": true,
      "tiempo_seg": 45,
      "nivel_bloom": "Recordar"
    }
  ],
  "resumen_por_nivel": {
    "Recordar": {
      "total": 5,
      "correctas": 4,
      "porcentaje": 80.0
    }
  },
  "puntaje_total": 70.0,
  "nivel_actual": "Comprender",
  "zona_proxima": ["Aplicar", "Analizar"],
  "recomendaciones": [
    "Reforzar nivel Aplicar con ejercicios prácticos"
  ]
}
```

#### `rutas_aprendizaje`
Rutas personalizadas con material pedagógico:
```json
{
  "_id": ObjectId("..."),
  "usuario": "nombre_usuario",
  "nombre": "Introducción a Física",
  "descripcion": "Conceptos básicos de mecánica",
  "estructura_ruta": {
    "flashcards": {
      "Recordar": [
        {
          "id": 1,
          "frente": "¿Qué es la velocidad?",
          "reverso": "La velocidad es una magnitud vectorial que relaciona el desplazamiento con el tiempo. Se expresa como v = Δx/Δt...",
          "visto": false
        }
      ],
      "Comprender": [...],
      "Aplicar": [...]
    },
    "examenes": {
      "Recordar": [
        {
          "pregunta": "¿Cuál es la fórmula de velocidad?",
          "opciones": ["a) v = d/t", "b) v = m*a", "c) v = F/m", "d) v = a*t"],
          "respuesta_correcta": "a",
          "explicacion": "La velocidad se define como...",
          "tiempo_estimado_seg": 60
        }
      ]
    }
  },
  "metadatos_ruta": {
    "nivel_actual_estudiante": "Comprender",
    "zona_proxima": ["Aplicar", "Analizar"],
    "duracion_horas": 20,
    "fecha_creacion": ISODate("2025-12-17T..."),
    "ultima_modificacion": ISODate("2025-12-17T...")
  },
  "progreso": {
    "flashcards_vistas": 5,
    "examenes_completados": 2,
    "porcentaje_completado": 15.5,
    "ultima_actividad": ISODate("2025-12-17T...")
  },
  "fuentes_material": [
    ObjectId("...")  // Referencias a materiales_crudos
  ]
}
```

---

## ✅ Testing

### Ejecutar Tests

```powershell
# Activar virtualenv
.\.venv\Scripts\Activate.ps1

# Ejecutar todos los tests
pytest

# Modo verboso
pytest -v

# Modo quieto (solo resumen)
pytest -q

# Test específico
pytest tests/test_utils.py

# Con cobertura
pytest --cov=src
```

### Suite de Tests (50+ tests)

#### `tests/test_utils.py` (40+ tests)
- **Decorador @retry**: Tests de reintentos con fallos y éxitos
- **Validaciones**: Email, username, password strength
- **Manejo de datos**: Nested dictionaries, exam responses, exam structure
- **Conversiones de tiempo**: Minutos a horas, formateo
- **Gestión de archivos**: Creación carpetas, listado, validación de acceso
- **Seguridad**: Path traversal, validación de permisos

#### `tests/test_database.py`
- **Connection singleton**: Verificación de patrón singleton
- **Configuración**: Validación de parámetros de pooling

#### `tests/test_app.py`
- **Rutas Flask**: Tests de endpoints principales
- **Autenticación**: Login, logout, registro
- **Autorización**: Validación de acceso a recursos protegidos

### Configuración de pytest

Archivo `pytest.ini`:
```ini
[pytest]
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
testpaths = tests
junit_family = xunit2
```

---

## 🎯 Conceptos Pedagógicos Clave

### Zona de Desarrollo Próximo (ZDP)

Teoría de Vygotsky que define 3 zonas de aprendizaje:

1. **Zona de Confort** (Nivel Actual)
   - Lo que el estudiante puede hacer solo
   - Umbral: ≥70% de aciertos en examen
   - Estrategia: Contenido de refuerzo opcional

2. **Zona de Desarrollo Próximo** (ZDP)
   - Lo que puede hacer con ayuda (andamiaje)
   - Niveles inmediatamente superiores al actual
   - Estrategia: Scaffolding (soporte estructurado)

3. **Zona de Frustración**
   - Demasiado difícil, incluso con ayuda
   - Niveles muy alejados del actual
   - Estrategia: Omitir temporalmente (optimización de tokens)

**Implementación en RUTEALO:**
- Evaluación diagnóstica identifica zona actual
- Generadores pedagógicos aplican estrategias diferenciadas:
  - `scaffolding`: 5-7 flashcards con soporte adicional
  - `refuerzo`: 7+ flashcards de consolidación
  - `estándar`: 3-5 flashcards equilibradas
- Omisión inteligente de niveles dominados (40% ahorro tokens)

### Taxonomía de Bloom

Jerarquía de 6 niveles cognitivos (del más simple al más complejo):

| Nivel | Descripción | Verbos Clave | Ejemplo |
|-------|-------------|--------------|---------|
| **Recordar** | Recuperar conocimiento de la memoria | Definir, listar, identificar | "¿Qué es la fotosíntesis?" |
| **Comprender** | Construir significado, interpretar | Explicar, resumir, clasificar | "Explica cómo funciona la fotosíntesis" |
| **Aplicar** | Usar conocimiento en situaciones nuevas | Resolver, calcular, implementar | "Calcula la tasa de fotosíntesis en..." |
| **Analizar** | Dividir en partes, encontrar relaciones | Comparar, contrastar, diferenciar | "Compara fotosíntesis con respiración" |
| **Evaluar** | Hacer juicios basados en criterios | Criticar, justificar, valorar | "Evalúa la eficiencia de diferentes plantas" |
| **Crear** | Combinar elementos para crear algo nuevo | Diseñar, planear, construir | "Diseña un experimento para medir..." |

**Implementación en RUTEALO:**
- Clasificación automática con Gemini AI usando prompts especializados
- Archivo CSV `df_bloom.csv` con descripciones y subtipos
- Generación de contenido pedagógico por nivel con verbos apropiados
- Rutas de aprendizaje organizadas secuencialmente por jerarquía

### Teoría del Flow

Balance entre desafío y habilidad para lograr estado de flujo óptimo:

- **Desafío > Habilidad**: Ansiedad (frustración)
- **Desafío < Habilidad**: Aburrimiento
- **Desafío ≈ Habilidad**: Flow (aprendizaje óptimo)

**Implementación en RUTEALO:**
- Archivo CSV `df_flow.csv` con estrategias de balance
- Ajuste de dificultad según perfil ZDP del estudiante
- Progresión gradual por niveles de Bloom

---

## ⚠️ Notas Importantes

### Seguridad

- ✅ **Credenciales migradas a variables de entorno** (`claves.env`)
- ✅ **Hashing de contraseñas** con `pbkdf2:sha256` (Werkzeug)
- ✅ **Validación robusta** de inputs (username, password, email)
- ✅ **Carpetas aisladas** por usuario en sistema de archivos
- ✅ **Path traversal protection** en rutas de descarga
- ⚠️ **Regenerar claves API** si fueron expuestas previamente
- ⚠️ **Cambiar SECRET_KEY** en producción (usar secrets.token_hex(32))
- ⚠️ **HTTPS requerido** en producción (SSL/TLS)
- ⚠️ **Revisar configuración CORS** si se implementa API pública

### Rendimiento

- ✅ **Connection pooling** de MongoDB implementado
  - Min pool size: 1
  - Max pool size: 10
  - Max idle time: 30 segundos
- ✅ **4 claves API especializadas** de Gemini para evitar rate limits
- ✅ **Optimización de tokens** (40% reducción con omisión inteligente)
- ✅ **GridFS** para archivos grandes (imágenes >16MB)
- ⏳ **Pendiente**: Implementar caché de respuestas de Gemini
- ⏳ **Pendiente**: Lazy loading de flashcards en frontend
- ⏳ **Pendiente**: Paginación de resultados de rutas

### Limitaciones Conocidas

1. **Límite de uploads**: 50 MB por archivo
2. **Formatos soportados**: Solo PDF, DOCX, PPTX
3. **Idiomas del chatbot**: Quechua depende de capacidad del modelo Gemini
4. **Transcripción de audio**: Requiere API de OpenAI (costo adicional)
5. **Compatibilidad**: Optimizado para Windows PowerShell

---

## 🚀 Roadmap

- [x] Sistema de evaluación ZDP con scoring por nivel Bloom
- [x] Integración con Gemini AI (4 claves especializadas)
- [x] Clasificación automática de contenido según Bloom
- [x] Generadores pedagógicos con teoría enriquecida
- [x] Chatbot tutor multilingüe (ES/EN/QU)
- [x] Transcripción de audio con Whisper
- [x] Dashboard web con modales enriquecidos
- [x] Logging estructurado con rotación
- [x] Tests automatizados (50+ tests unitarios)
- [x] Connection pooling de MongoDB
- [x] Optimización de tokens (40% reducción)
- [ ] Caché de respuestas de IA
- [ ] Análisis de progreso con gráficos
- [ ] Gamificación (logros, rankings)
- [ ] Exportación de rutas a PDF
- [ ] Notificaciones de estudio (email/SMS)
- [ ] App móvil (Flutter/React Native)
- [ ] CI/CD con GitHub Actions
- [ ] Despliegue en cloud (AWS/Azure/GCP)

---

## 📄 Licencia

Este proyecto es parte de una tesis académica. Todos los derechos reservados.

---

## 👨‍💻 Autor

**Joshua** - Tesis de Grado
- 📧 Email: (Configurar en perfil)
- 🎓 Universidad: (Configurar)
- 📅 Fecha: Diciembre 2025

---

## 🙏 Agradecimientos

- **Google AI Studio** por acceso a Gemini 1.5 Pro
- **MongoDB Atlas** por tier gratuito
- **OpenAI** por API de Whisper
- **Comunidad de Flask** por excelente documentación
- **Teoría pedagógica**: Vygotsky (ZDP), Bloom (Taxonomía), Csíkszentmihályi (Flow)

---

**¿Necesitas ayuda?** Revisa la sección de [Uso del Sistema](#-uso-del-sistema) o ejecuta tests para validar tu instalación.
