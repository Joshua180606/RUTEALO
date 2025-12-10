# RUTEALO

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

## Ejecutar el procesador de archivos 🗂️

Al ejecutar `src/data/ingesta_datos.py` desde la línea de comando, el script abre una ventana del gestor de archivos para que selecciones manualmente uno o más archivos para procesar (PDF, DOCX o PPTX). Esto evita que el script escanee automáticamente una carpeta y te da control directo sobre qué archivos ingestar.

Ejemplo para ejecutar desde la raíz del proyecto (suponiendo que ya activaste `.venv`):

```powershell
python src/data/ingesta_datos.py
```

Al finalizar el proceso verás en consola el resultado de la ingesta y si un archivo ya existía en la colección de MongoDB.

---

## 📚 Documentación del Proyecto

### Dashboard (Recientes)
- **[QUICK_REFERENCE_DASHBOARD_20251210.md](./QUICK_REFERENCE_DASHBOARD_20251210.md)** - Referencia rápida de cambios implementados
- **[RESUMEN_EJECUTIVO_DASHBOARD_20251210.md](./RESUMEN_EJECUTIVO_DASHBOARD_20251210.md)** - Resumen ejecutivo de mejoras
- **[GUIA_VISUAL_DASHBOARD_20251210.md](./GUIA_VISUAL_DASHBOARD_20251210.md)** - Mockups y guías visuales
- **[PLAN_IMPLEMENTACION_DASHBOARD_COMPLETO.md](./PLAN_IMPLEMENTACION_DASHBOARD_COMPLETO.md)** - Plan completo con 10 fases futuras
- **[UPDATE_DASHBOARD_HEIGHT_200px.md](./UPDATE_DASHBOARD_HEIGHT_200px.md)** - Cambios de altura a 200px

### Análisis y Optimizaciones
- **[RESUMEN_EJECUTIVO.md](./RESUMEN_EJECUTIVO.md)** - Hallazgos principales, recomendaciones y estado actual
- **[ANALISIS_INCONGRUENCIAS_Y_OPTIMIZACIONES.md](./ANALISIS_INCONGRUENCIAS_Y_OPTIMIZACIONES.md)** - Análisis técnico detallado de cada issue
- **[PLAN_IMPLEMENTACION_OPTIMIZACIONES.md](./PLAN_IMPLEMENTACION_OPTIMIZACIONES.md)** - Plan paso a paso con código listo para implementar

### Documentación del Sistema
- **[SISTEMA_ZDP_DOCUMENTACION.md](./SISTEMA_ZDP_DOCUMENTACION.md)** - Documentación completa del sistema de evaluación ZDP
- **[SISTEMA_ZDP_DOCUMENTACION.md](./SISTEMA_ZDP_DOCUMENTACION.md)** - Pedagogía, API, ejemplos de uso

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
