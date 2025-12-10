"""
Verificar estado de la base de datos para usuario FELIPE
"""
from src.database import get_database
from src.config import DB_NAME, COLS

db = get_database(DB_NAME)
usuario = "FELIPE"

print(f"\n📊 ESTADO DE LA BASE DE DATOS PARA: {usuario}")
print("=" * 70)

# Materiales crudos
col_raw = db[COLS["RAW"]]
count_raw = col_raw.count_documents({"usuario": usuario})
count_bloom = col_raw.count_documents({"usuario": usuario, "bloom_etiquetado": True})
print(f"\n📦 Materiales Crudos:")
print(f"   Total: {count_raw}")
print(f"   Con etiqueta Bloom: {count_bloom}")

if count_raw > 0:
    sample = col_raw.find_one({"usuario": usuario})
    print(f"   Muestra:")
    print(f"   - ID: {sample['_id']}")
    print(f"   - Archivo: {sample.get('nombre_archivo', 'N/A')}")
    print(f"   - Bloom: {sample.get('nivel_bloom', 'N/A')}")
    print(f"   - Etiquetado: {sample.get('bloom_etiquetado', False)}")

# Examen inicial
col_exam = db[COLS["EXAM_INI"]]
exam = col_exam.find_one({"usuario": usuario})
print(f"\n📋 Examen Inicial:")
if exam:
    contenido = exam.get("contenido", {})
    examenes = contenido.get("EXAMENES", {})
    preguntas = examenes.get("EXAMEN_INICIAL", [])
    print(f"   Estado: {exam.get('estado', 'N/A')}")
    print(f"   Origen: {exam.get('origen', 'N/A')}")
    print(f"   Preguntas: {len(preguntas)}")
    if len(preguntas) > 0:
        print(f"   Primera pregunta: {preguntas[0].get('pregunta', 'N/A')[:80]}...")
        print(f"   Opciones: {len(preguntas[0].get('opciones', []))}")
else:
    print("   ❌ No existe")

# Rutas
col_rutas = db[COLS["RUTAS"]]
ruta = col_rutas.find_one({"usuario": usuario})
print(f"\n🛤️ Ruta de Aprendizaje:")
if ruta:
    print(f"   Nombre: {ruta.get('nombre_ruta', 'N/A')}")
    print(f"   Descripción: {ruta.get('descripcion', 'N/A')}")
    print(f"   Estado: {ruta.get('estado', 'N/A')}")
    archivos = ruta.get('archivos_fuente', [])
    print(f"   Archivos fuente: {len(archivos)}")
    if len(archivos) > 0:
        print(f"   - {archivos[0].get('nombre_archivo', 'N/A')}")
else:
    print("   ❌ No existe")

print("\n" + "=" * 70)
