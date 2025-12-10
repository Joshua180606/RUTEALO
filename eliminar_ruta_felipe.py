"""
Eliminar completamente la ruta PRUEBA 2 del usuario FELIPE
"""
import os
import shutil
from src.database import get_database
from src.config import DB_NAME, COLS

db = get_database(DB_NAME)
usuario = "FELIPE"

print(f"\n🗑️  ELIMINANDO RUTA COMPLETA PARA: {usuario}")
print("=" * 70)

# 1. Eliminar de rutas_aprendizaje
col_rutas = db[COLS["RUTAS"]]
ruta_doc = col_rutas.find_one({"usuario": usuario})

if ruta_doc:
    print(f"\n📋 Ruta encontrada:")
    print(f"   Nombre: {ruta_doc.get('nombre_ruta', 'N/A')}")
    print(f"   Archivos: {len(ruta_doc.get('archivos_fuente', []))}")
    
    # Obtener nombre de carpeta
    archivos = ruta_doc.get('archivos_fuente', [])
    carpeta_ruta = None
    if archivos:
        # Extraer carpeta de la ruta relativa
        ruta_rel = archivos[0].get('ruta_relativa', '')
        # uploads/FELIPE/NOMBRE_RUTA/archivo.pdf -> NOMBRE_RUTA
        partes = ruta_rel.split('/')
        if len(partes) >= 3:
            carpeta_ruta = partes[2]
    
    # Eliminar documento
    result = col_rutas.delete_one({"usuario": usuario})
    print(f"   ✅ Eliminada de BD: {result.deleted_count} documento(s)")
    
    # Eliminar carpeta física
    if carpeta_ruta:
        carpeta_path = os.path.join("data", "raw", "uploads", usuario, carpeta_ruta)
        if os.path.exists(carpeta_path):
            shutil.rmtree(carpeta_path)
            print(f"   ✅ Carpeta eliminada: {carpeta_path}")
        else:
            print(f"   ⚠️  Carpeta no encontrada: {carpeta_path}")
else:
    print("   ❌ No hay ruta para eliminar")

# 2. Eliminar de examen_inicial (si existe)
col_exam = db[COLS["EXAM_INI"]]
result_exam = col_exam.delete_one({"usuario": usuario})
if result_exam.deleted_count > 0:
    print(f"\n📋 Examen eliminado: {result_exam.deleted_count} documento(s)")

# 3. Eliminar de materiales_crudos (si existen)
col_raw = db[COLS["RAW"]]
result_raw = col_raw.delete_many({"usuario": usuario})
if result_raw.deleted_count > 0:
    print(f"\n📦 Materiales eliminados: {result_raw.deleted_count} documento(s)")

print("\n" + "=" * 70)
print("✅ LIMPIEZA COMPLETADA")
print("\nAhora puedes crear una nueva ruta desde el dashboard:")
print("1. Ve a http://127.0.0.1:5000")
print("2. Clic en 'Crear Nueva Ruta'")
print("3. Sube los archivos PDF de nuevo")
print("4. Espera a que se procesen (30-60 segundos)")
print("5. El test se generará automáticamente con las preguntas del material")
print("=" * 70 + "\n")
