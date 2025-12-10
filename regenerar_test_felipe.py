"""
Script para regenerar el test diagnóstico del usuario FELIPE
Esto forzará la regeneración del test con preguntas basadas en el material subido
"""

import sys
from src.database import get_database
from src.config import DB_NAME
from src.web_utils import generar_ruta_aprendizaje

def main():
    usuario = "FELIPE"
    
    print(f"🔄 Regenerando test diagnóstico para usuario: {usuario}")
    print("⏳ Esto puede tardar 20-40 segundos mientras Gemini procesa el contenido...")
    print()
    
    try:
        # Conectar a la base de datos
        db = get_database(DB_NAME)
        print("✅ Conectado a MongoDB")
        
        # Eliminar test actual para forzar regeneración
        from src.config import COLS
        col_exam = db[COLS["EXAM_INI"]]
        result = col_exam.delete_one({"usuario": usuario})
        if result.deleted_count > 0:
            print(f"✅ Test anterior eliminado")
        else:
            print("ℹ️  No había test anterior")
        
        # Marcar contenido como no etiquetado para reprocesar
        col_raw = db[COLS["RAW"]]
        result_raw = col_raw.update_many(
            {"usuario": usuario},
            {"$set": {"bloom_etiquetado": False}}
        )
        print(f"✅ Marcados {result_raw.matched_count} documentos para reprocesar")
        
        # Forzar etiquetado Bloom
        from src.web_utils import auto_etiquetar_bloom
        count = auto_etiquetar_bloom(usuario, db)
        print(f"✅ Etiquetados {count} documentos con taxonomía Bloom")
        print("⏳ Generando nuevo test con Gemini...")
        
        # Regenerar ruta y test
        resultado = generar_ruta_aprendizaje(usuario, db)
        
        print()
        print("=" * 60)
        print("✅ TEST REGENERADO EXITOSAMENTE")
        print("=" * 60)
        print(f"Resultado: {resultado}")
        print()
        print("📋 El nuevo test diagnóstico incluye:")
        print("   • Preguntas basadas en el contenido específico del material")
        print("   • Opción 'e) No lo sé / Omitir' en todas las preguntas")
        print("   • 8-10 preguntas de dificultad incremental")
        print()
        print("🎯 Ahora puedes ir al dashboard y hacer clic en 'Ver Mis Rutas' → 'Continuar Ruta'")
        print()
        
    except Exception as e:
        print()
        print("=" * 60)
        print("❌ ERROR AL REGENERAR TEST")
        print("=" * 60)
        print(f"Error: {str(e)}")
        print()
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
