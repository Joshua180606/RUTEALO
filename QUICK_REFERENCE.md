# 🛠️ QUICK REFERENCE - Comandos Útiles RUTEALO

**Última actualización:** 9 Dic 2025  
**Estado:** ✅ Proyecto completado

---

## 🚀 Startup Rápido

```powershell
# 1. Activar virtualenv
cd C:\Users\joshu\Documents\Joshua\Tesis\RUTEALO
.venv\Scripts\activate

# 2. Levantar Flask
set FLASK_ENV=development
python -m flask run

# 3. Acceder
# http://localhost:5000
```

---

## ✅ Testing

```powershell
# Ejecutar todos los tests
pytest tests/ -v

# Ejecutar test específico
pytest tests/test_app.py -v

# Ver cobertura
pytest tests/ --cov=src --cov-report=html

# Smoke test rápido
powershell -File test_app_smoke.ps1
```

---

## 📊 Code Quality

```powershell
# Linting
flake8 src/ --max-line-length=120

# Formateo automático
black src/ --line-length=120

# Análisis profundo (opcional)
pylint src/ --disable=C0111,R0914
```

---

## 📝 Logging & Monitoreo

```powershell
# Ver logs en tiempo real
Get-Content -Path "logs/application.log" -Tail 20 -Wait

# Ver errores
Get-Content -Path "logs/errors.log" -Tail 20

# Limpiar logs (mantener último backup)
Copy-Item logs/application.log logs/application.log.bak
"" | Set-Content logs/application.log
```

---

## 🔐 Credenciales

```powershell
# Verificar que no hay credenciales en código
grep -r "AIzaSy\|mongodb\+srv\|password" src/

# Expected: 0 matches (todas en claves.env)
```

---

## 📦 Dependencias

```powershell
# Instalar nuevas dependencias
pip install [nombre-librería]

# Actualizar requirements.txt
pip freeze > requirements.txt

# Ver instaladas
pip list
```

---

## 🗄️ Base de Datos

```powershell
# Verificar conexión a MongoDB
python -c "from src.database import get_database; db = get_database(); print(db.list_collection_names())"

# Conectar a MongoDB manualmente (si necesitas)
# https://cloud.mongodb.com/v2/[CLUSTER_ID]
```

---

## 📁 Estructura Importante

```
RUTEALO/
├── src/
│   ├── app.py                  ← Flask app principal
│   ├── config.py               ← Configuración (lee claves.env)
│   ├── database.py             ← DB singleton
│   ├── logging_config.py       ← Logger centralizado
│   ├── utils.py                ← Decoradores y validadores
│   └── models/                 ← Modelos de AI
├── tests/
│   ├── test_app.py             ← 6 tests Flask
│   ├── test_database.py        ← 5 tests DB
│   └── test_utils.py           ← 29 tests utils
├── logs/
│   ├── application.log         ← Logs normales
│   └── errors.log              ← Solo errores
├── claves.env                  ← SECRETO (gitignored)
├── requirements.txt            ← Dependencias
└── pytest.ini                  ← Configuración pytest
```

---

## 🔄 Git Workflow

```powershell
# Ver cambios
git status
git diff

# Hacer commit
git add .
git commit -m "feat: descripción del cambio"

# Ver historial
git log --oneline -10

# Push a remoto
git push origin main
```

---

## 🆘 Troubleshooting

### App no inicia
```powershell
# 1. Verificar venv
.venv\Scripts\activate

# 2. Reinstalar dependencias
pip install -r requirements.txt

# 3. Verificar claves.env existe
Test-Path claves.env

# 4. Ver logs
Get-Content logs/errors.log -Tail 50
```

### Tests fallan
```powershell
# 1. Limpiar caché
Remove-Item -Recurse -Force src/__pycache__
Remove-Item -Recurse -Force tests/__pycache__

# 2. Ejecutar con verbose
pytest tests/ -vv

# 3. Ver error específico
pytest tests/test_app.py::test_register -vv
```

### MongoDB no conecta
```powershell
# 1. Verificar credenciales en claves.env
Get-Content claves.env | Select-String "MONGO"

# 2. Verificar que IP está en whitelist (MongoDB Atlas)

# 3. Ver logs de conexión
Get-Content logs/errors.log | Select-String "mongo\|database"
```

---

## 📊 Arquitectura en 30 Segundos

```
1. ENTRADA → app.py (Flask routes)
   ↓
2. VALIDACIÓN → utils.py (validators)
   ↓
3. PROCESAMIENTO → models/ (Gemini API)
   ├─→ @retry (backoff automático si falla)
   ├─→ Logger (logs estructurados)
   ├─→ get_genai_model() (config centralizada)
   └─→ get_database() (DB singleton + pooling)
   ↓
4. ALMACENAMIENTO → MongoDB (via src/database.py)
   ↓
5. RESPUESTA → JSON (con status codes)
```

---

## 📚 Documentación

| Archivo | Propósito |
|---------|-----------|
| `PROYECTO_COMPLETADO.md` | 1-page project summary |
| `PROYECTO_FINAL_FASE4.md` | Detailed phase completion |
| `CHECKLIST_IMPLEMENTACION.md` | 40/40 tasks status |
| `ANALISIS_INCONGRUENCIAS_Y_OPTIMIZACIONES.md` | Issue analysis |
| `SISTEMA_ZDP_DOCUMENTACION.md` | Business logic |
| `README.md` | Setup instructions |

---

## ⚡ One-Liners Útiles

```powershell
# Activar venv + iniciar app
.venv\Scripts\activate; python -m flask run

# Correr tests + ver cobertura
pytest tests/ -q ; pytest tests/ --cov=src

# Verificar salud del proyecto
flake8 src/ --count ; pytest tests/ -q

# Limpiar y reinstalar
Remove-Item -Recurse -Force src/__pycache__ ; pip install -r requirements.txt --force-reinstall

# Backup de logs
Copy-Item logs/ logs_backup_$(Get-Date -Format yyyyMMdd_HHmmss) -Recurse
```

---

## 🎯 Checklist Diario

- [ ] ¿Actualicé `requirements.txt` si instalé nuevas librerías?
- [ ] ¿Corrí `pytest` antes de hacer commit?
- [ ] ¿Verifiqué que `flake8` no tiene issues críticos?
- [ ] ¿Verifiqué que `black` formateó el código?
- [ ] ¿Reviewé los logs antes de mergear?
- [ ] ¿Hice backup de la BD si cambié schema?

---

**Última revisión:** 9 Diciembre 2025  
**Status:** ✅ Proyecto en Producción
