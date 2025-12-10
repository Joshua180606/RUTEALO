"""
Script de migración de esquema MongoDB - FASE 1.1
Agrega campos faltantes a rutas_aprendizaje y crea índices necesarios
"""

import sys
from datetime import datetime
from pymongo import ASCENDING, DESCENDING
from src.database import get_database

def migrate_schema():
    """
    Ejecuta la migración del esquema:
    1. Agrega campos faltantes (nombre_ruta, descripcion, estado, archivos_fuente, fecha_creacion)
    2. Crea índices (usuario, nombre_ruta) UNIQUE y (usuario, fecha_actualizacion) DESC
    3. Migra documentos existentes sin nombre_ruta
    """
    print("=" * 70)
    print("🔄 INICIANDO MIGRACIÓN DE ESQUEMA v2")
    print("=" * 70)
    
    try:
        db = get_database()
        collection = db["rutas_aprendizaje"]
        
        # ===== PASO 1: Agregar campos faltantes a documentos existentes =====
        print("\n[1/3] Agregando campos faltantes a documentos existentes...")
        
        # Encontrar documentos sin nombre_ruta
        docs_without_nombre = collection.find({"nombre_ruta": {"$exists": False}})
        docs_without_nombre_list = list(docs_without_nombre)
        
        if docs_without_nombre_list:
            print(f"     ℹ️ Encontrados {len(docs_without_nombre_list)} documentos sin nombre_ruta")
            
            # Actualizar cada documento
            for idx, doc in enumerate(docs_without_nombre_list, 1):
                doc_id = doc.get("_id")
                usuario = doc.get("usuario", "unknown")
                
                # Generar nombre automático basado en fecha de creación
                fecha_ingesta = doc.get("fecha_ingesta")
                if isinstance(fecha_ingesta, str):
                    nombre_auto = f"Ruta {fecha_ingesta[:10]}"
                else:
                    nombre_auto = f"Ruta {idx}"
                
                update_data = {
                    "nombre_ruta": nombre_auto,
                    "descripcion": doc.get("descripcion", "Importada automáticamente"),
                    "estado": doc.get("estado", "ACTIVA"),
                    "archivos_fuente": doc.get("archivos_ingesta", []),
                    "fecha_creacion": doc.get("fecha_ingesta", datetime.utcnow())
                }
                
                result = collection.update_one(
                    {"_id": doc_id},
                    {"$set": update_data}
                )
                
                if result.modified_count > 0:
                    print(f"     ✓ [{idx}] Actualizado: {doc_id} → '{nombre_auto}'")
                else:
                    print(f"     ⚠️ [{idx}] No se modificó: {doc_id}")
        else:
            print("     ✓ Todos los documentos ya tienen nombre_ruta")
        
        # ===== PASO 2: Crear índice UNIQUE (usuario, nombre_ruta) =====
        print("\n[2/3] Creando índice UNIQUE (usuario, nombre_ruta)...")
        try:
            idx_name = collection.create_index(
                [("usuario", ASCENDING), ("nombre_ruta", ASCENDING)],
                unique=True,
                background=True
            )
            print(f"     ✓ Índice creado: {idx_name}")
        except Exception as e:
            if "already exists" in str(e):
                print(f"     ℹ️ El índice ya existe")
            else:
                print(f"     ❌ Error al crear índice: {e}")
                raise
        
        # ===== PASO 3: Crear índice (usuario, fecha_actualizacion) DESC =====
        print("\n[3/3] Creando índice (usuario, fecha_actualizacion) DESC...")
        try:
            idx_name = collection.create_index(
                [("usuario", ASCENDING), ("fecha_actualizacion", DESCENDING)],
                background=True
            )
            print(f"     ✓ Índice creado: {idx_name}")
        except Exception as e:
            if "already exists" in str(e):
                print(f"     ℹ️ El índice ya existe")
            else:
                print(f"     ❌ Error al crear índice: {e}")
                raise
        
        # ===== VERIFICACIÓN FINAL =====
        print("\n" + "=" * 70)
        print("📊 RESUMEN DE MIGRACIÓN")
        print("=" * 70)
        
        total_docs = collection.count_documents({})
        docs_con_nombre = collection.count_documents({"nombre_ruta": {"$exists": True}})
        indices = collection.list_indexes()
        
        print(f"\n✓ Total de documentos: {total_docs}")
        print(f"✓ Documentos con nombre_ruta: {docs_con_nombre}")
        print(f"✓ Índices en la colección: {list(indices.keys()) if hasattr(indices, 'keys') else 'N/A'}")
        
        print("\n" + "=" * 70)
        print("✅ MIGRACIÓN COMPLETADA EXITOSAMENTE")
        print("=" * 70)
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR EN MIGRACIÓN: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = migrate_schema()
    sys.exit(0 if success else 1)
