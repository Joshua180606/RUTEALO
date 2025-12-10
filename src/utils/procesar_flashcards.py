"""
Script para procesar imágenes de flashcards: remover fondo y crear versiones transparentes.

Uso:
    python src/utils/procesar_flashcards.py

Procesará todos los PNG en data/raw/flashcard/ y guardará versiones con fondo transparente
en data/processed/flashcard/
"""

import os
from pathlib import Path
from PIL import Image, ImageFilter
import numpy as np

# Rutas
BASE_DIR = Path(__file__).resolve().parent.parent.parent
INPUT_DIR = BASE_DIR / "data" / "raw" / "flashcard"
OUTPUT_DIR = BASE_DIR / "data" / "processed" / "flashcard"

def remover_fondo_blanco(imagen_path, threshold=240):
    """
    Remueve fondo blanco de una imagen y lo reemplaza con transparencia.
    
    Args:
        imagen_path (Path): Ruta de la imagen de entrada
        threshold (int): Umbral para detectar color blanco (0-255)
    
    Returns:
        Image: Imagen con fondo transparente
    """
    # Cargar imagen
    img = Image.open(imagen_path)
    
    # Convertir a RGBA si no lo es
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    # Convertir a numpy array para procesamiento
    data = np.array(img)
    
    # Obtener canales RGB
    r, g, b, a = data.T
    
    # Detectar píxeles blancos o casi blancos
    # Un píxel es "blanco" si R, G y B son mayores al threshold
    white_areas = (r > threshold) & (g > threshold) & (b > threshold)
    
    # Hacer transparentes los píxeles blancos
    data[..., 3][white_areas.T] = 0  # Canal alpha a 0 (transparente)
    
    # Convertir de vuelta a imagen PIL
    img_transparent = Image.fromarray(data)
    
    return img_transparent


def aplicar_antialiasing(img):
    """Aplica suavizado para mejorar bordes"""
    return img.filter(ImageFilter.SMOOTH)


def procesar_todas_las_imagenes():
    """Procesa todas las imágenes en el directorio de entrada"""
    
    # Crear directorio de salida si no existe
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    print("🎨 Iniciando procesamiento de imágenes de flashcards...")
    print(f"📂 Entrada: {INPUT_DIR}")
    print(f"📁 Salida: {OUTPUT_DIR}\n")
    
    # Obtener todos los archivos PNG
    imagenes = list(INPUT_DIR.glob("*.png"))
    
    if not imagenes:
        print("⚠️ No se encontraron imágenes PNG en el directorio de entrada")
        return
    
    resultados = []
    
    for img_path in imagenes:
        try:
            nombre_base = img_path.stem
            print(f"⚙️ Procesando: {img_path.name}...")
            
            # Remover fondo
            img_sin_fondo = remover_fondo_blanco(img_path, threshold=240)
            
            # Aplicar suavizado
            img_final = aplicar_antialiasing(img_sin_fondo)
            
            # Guardar versión transparente
            output_path = OUTPUT_DIR / f"{nombre_base}_transparent.png"
            img_final.save(output_path, 'PNG', optimize=True)
            
            # Verificar tamaño
            size_kb = output_path.stat().st_size / 1024
            
            print(f"   ✅ Guardado: {output_path.name} ({size_kb:.1f} KB)")
            
            resultados.append({
                'original': img_path.name,
                'procesado': output_path.name,
                'size_kb': size_kb
            })
            
        except Exception as e:
            print(f"   ❌ Error procesando {img_path.name}: {e}")
            continue
    
    print(f"\n🎉 Procesamiento completado!")
    print(f"📊 {len(resultados)}/{len(imagenes)} imágenes procesadas exitosamente")
    print(f"\n📋 Resumen:")
    for r in resultados:
        print(f"   • {r['original']} → {r['procesado']} ({r['size_kb']:.1f} KB)")


if __name__ == "__main__":
    procesar_todas_las_imagenes()
