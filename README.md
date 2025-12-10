# RUTEALO

## 🚀 Novedades: Chatbot Tutor Multilingüe

**¡Nuevo!** RUTEALO ahora incluye un chatbot tutor inteligente con:
- 🎙️ **Transcripción de audio** en 3 idiomas (Español, Inglés, Quechua)
- 🤖 **Respuestas contextuales** basadas en tus materiales de estudio
- 🌍 **Soporte multilingüe** con prompts pedagógicos especializados
- 📊 **Integración con ZDP** para respuestas adaptadas a tu nivel

**Guías de inicio rápido**:
- 📋 **[CHECKLIST_RAPIDO.md](./CHECKLIST_RAPIDO.md)** - Activación en 5 minutos
- 📖 **[INSTRUCCIONES_CHATBOT.md](./INSTRUCCIONES_CHATBOT.md)** - Guía completa de uso
- 📝 **[RESUMEN_IMPLEMENTACION.md](./RESUMEN_IMPLEMENTACION.md)** - Detalles técnicos

---

## Instalación ⚙️

Puedes instalar las dependencias del proyecto usando pip con el archivo `requirements.txt` incluido en la raíz del repositorio.

Usando pip directamente (sistema global o en un venv ya activado):

```powershell
pip install -r requirements.txt
```

Para un flujo recomendado en Windows (crea una virtualenv y instala allí automáticamente), ejecuta el script de PowerShell provisto:

```powershell
.\install_requirements.ps1
```

Esto creará una carpeta `.venv` por defecto y luego instalará las dependencias listadas en `requirements.txt`.

### ⚡ Configuración Adicional para el Chatbot

Para usar el chatbot tutor con transcripción de audio:

1. **Instala la dependencia de OpenAI**:
   ```powershell
   pip install openai>=1.0.0
   ```

2. **Configura tu API key de OpenAI**:
   - Obtén tu clave en: https://platform.openai.com/api-keys
   - Edita el archivo `claves.env` y agrega:
     ```env
     OPENAI_API_KEY="tu_clave_openai_aqui"
     ```

3. **¡Listo!** Inicia el servidor y el chatbot estará disponible en el dashboard.

Ver **[CHECKLIST_RAPIDO.md](./CHECKLIST_RAPIDO.md)** para instrucciones paso a paso.

## Ejecutar el procesador de archivos 🗂️

Al ejecutar `src/data/ingesta_datos.py` desde la línea de comando, el script abre una ventana del gestor de archivos para que selecciones manualmente uno o más archivos para procesar (PDF, DOCX o PPTX). Esto evita que el script escanee automáticamente una carpeta y te da control directo sobre qué archivos ingestar.

Ejemplo para ejecutar desde la raíz del proyecto (suponiendo que ya activaste `.venv`):

```powershell
python src/data/ingesta_datos.py
```

Al finalizar el proceso verás en consola el resultado de la ingesta y si un archivo ya existía en la colección de MongoDB.

---

## 📚 Documentación del Proyecto

### Chatbot Tutor Multilingüe (NUEVO)
- **[CHECKLIST_RAPIDO.md](./CHECKLIST_RAPIDO.md)** - ⚡ Activación en 5 minutos
- **[INSTRUCCIONES_CHATBOT.md](./INSTRUCCIONES_CHATBOT.md)** - 📖 Guía completa de uso y testing
- **[RESUMEN_IMPLEMENTACION.md](./RESUMEN_IMPLEMENTACION.md)** - 📝 Detalles técnicos y arquitectura
- **[PLAN_CHATBOT_MULTILINGUE.md](./PLAN_CHATBOT_MULTILINGUE.md)** - 📋 Plan de implementación (7 fases)

### Dashboard (Recientes)
- **[IMPLEMENTACION_WEB_FASE1_2.md](./IMPLEMENTACION_WEB_FASE1_2.md)** - 🆕 Integración web completa de Fases 1 y 2 (Dashboard ZDP, modales enriquecidos)
- **[QUICK_REFERENCE_DASHBOARD_20251210.md](./QUICK_REFERENCE_DASHBOARD_20251210.md)** - Referencia rápida de cambios implementados
- **[RESUMEN_EJECUTIVO_DASHBOARD_20251210.md](./RESUMEN_EJECUTIVO_DASHBOARD_20251210.md)** - Resumen ejecutivo de mejoras
- **[GUIA_VISUAL_DASHBOARD_20251210.md](./GUIA_VISUAL_DASHBOARD_20251210.md)** - Mockups y guías visuales
- **[PLAN_IMPLEMENTACION_DASHBOARD_COMPLETO.md](./PLAN_IMPLEMENTACION_DASHBOARD_COMPLETO.md)** - Plan completo con 10 fases futuras

### Sistema ZDP y Generadores Pedagógicos
- **[RESUMEN_EJECUTIVO_FASES_1_2.md](./RESUMEN_EJECUTIVO_FASES_1_2.md)** - 🆕 Resumen completo de optimización ZDP y generadores especializados
- **[IMPLEMENTACION_FASE2_GENERADORES.md](./IMPLEMENTACION_FASE2_GENERADORES.md)** - 🆕 Generadores pedagógicos con teoría enriquecida (150+ palabras)
- **[IMPLEMENTACION_FASE1_ZDP_RUTAS.md](./IMPLEMENTACION_FASE1_ZDP_RUTAS.md)** - 🆕 Optimización de rutas con omisión inteligente (40% ahorro tokens)
- **[SISTEMA_ZDP_DOCUMENTACION.md](./SISTEMA_ZDP_DOCUMENTACION.md)** - Documentación completa del sistema de evaluación ZDP

---

## ⚠️ Notas Importantes

### Security
- ✅ Credenciales migradas a variables de entorno
- ⚠️ **PENDIENTE:** Regenerar MongoDB + Google API keys (fueron expuestas previamente)
- 📝 Ver `RESUMEN_EJECUTIVO.md` para detalles

### Performance
- 📌 Se recomienda implementar las optimizaciones en `PLAN_IMPLEMENTACION_OPTIMIZACIONES.md`
- 🔧 Priority: Database connection pooling (FASE 2)

---

## 🚀 Roadmap

- [x] Implementación básica de ZDP
- [x] Integración con Gemini AI
- [x] Sistema de evaluación y scoring
- [ ] Logging estructurado (en progreso)
- [ ] Error handling robusto (próximamente)
- [ ] Tests automatizados (próximamente)
- [ ] CI/CD integration (futuro)

---

## 📞 Soporte

Para preguntas sobre:
- **Arquitectura pedagógica:** Ver `SISTEMA_ZDP_DOCUMENTACION.md`
- **Code quality:** Ver `ANALISIS_INCONGRUENCIAS_Y_OPTIMIZACIONES.md`
- **Implementación:** Ver `PLAN_IMPLEMENTACION_OPTIMIZACIONES.md`
 
---

## Ejecutar la aplicación (Recomendado)

Para ejecutar la aplicación web localmente se recomienda iniciar el intérprete como módulo desde la raíz del proyecto o usar `flask run`.

- PowerShell (recomendado):

```powershell
# Activar el virtualenv creado con el instalador
.\.venv\Scripts\Activate.ps1

# Ejecutar como módulo (mantiene la importación de paquetes)
python -m src.app
```

- Alternativa con Flask CLI (PowerShell):

```powershell
.\.venv\Scripts\Activate.ps1
# $env:FLASK_APP = 'src.app'  # opcional para flask CLI
# $env:FLASK_ENV = 'development'
flask run --port 5000
```

- Windows CMD:

```bat
\.venv\Scripts\activate.bat
python -m src.app
```

Nota: Evita ejecutar `python src/app.py` directamente desde la carpeta `src/`, ya que Python no añade automáticamente la raíz del proyecto a `sys.path` y eso puede provocar errores de importación. Se eliminó el parche que modificaba `sys.path` en tiempo de ejecución para mantener un comportamiento predecible y más seguro.

Comprobar tests:

```powershell
.\.venv\Scripts\Activate.ps1
pytest -q
```
