import os
import json
import pandas as pd
import logging
import google.generativeai as genai
import re
import tkinter as tk
from tkinter import simpledialog
from src.config import DB_NAME, COLS, get_genai_model
from src.database import get_database
import gridfs
from PIL import Image
import io

logger = logging.getLogger(__name__)

# --- 1. CONFIGURACIÓN (Centralizada en src.config) ---
COLLECTION_RAW = COLS["RAW"]

# Modelo Gemini (configuración centralizada)
model = get_genai_model()

# --- 2. INTERFAZ DE USUARIO Y CONEXIÓN ---


def pedir_usuario_gui():
    """Abre un input dialog para pedir el nombre del usuario."""
    try:
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)

        nombre = simpledialog.askstring("Identificación", "Ingresa tu nombre de usuario para procesar tus archivos:")

        root.destroy()
        return nombre
    except Exception:
        return input("Ingresa tu nombre de usuario: ")


def conectar_bd():
    try:
        db = get_database(DB_NAME)
        fs = gridfs.GridFS(db)
        return db[COLLECTION_RAW], fs
    except Exception as e:
        logger.error(f"❌ Error BD: {e}")
        return None, None


def cargar_instrucciones_bloom():
    """Carga el CSV de reglas pedagógicas."""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ruta_csv = os.path.join(base_dir, "data", "processed", "df_bloom.csv")

    if not os.path.exists(ruta_csv):
        return ""

    try:
        df = pd.read_csv(ruta_csv)
        contexto = ""
        for _, row in df.iterrows():
            contexto += f"NIVEL: {row.get('cat_bloom', 'N/A')} | Desc: {row.get('proc_desc', '')}\n"
        return contexto
    except Exception:
        return ""


def recuperar_imagen(fs, gridfs_id):
    try:
        archivo = fs.get(gridfs_id)
        img_bytes = archivo.read()
        return Image.open(io.BytesIO(img_bytes))
    except Exception:
        return None


# --- 3. LÓGICA DE CLASIFICACIÓN CON IA ---


def clasificar_unidad(texto, imagenes_pil, contexto_bloom):
    """
    Clasifica estrictamente en JSON. Si falla o no aplica, retorna 'Otro'.
    """
    prompt_sistema = f"""
    Eres un motor de clasificación estricto. Tu tarea es asignar una categoría de la Taxonomía de Bloom basándote en el siguiente contexto.

    CONTEXTO DE REGLAS (NO INVENTAR CATEGORÍAS):
    {contexto_bloom}

    INSTRUCCIONES:
    1. Analiza el texto e imágenes.
    2. Si el contenido coincide con una regla, asigna la "Categoria_Bloom".
    3. Si el contenido es irrelevante, no educativo, o no coincide con ninguna regla, la categoría DEBE ser "Otro".
    4. NO generes explicaciones previas, NO uses markdown, SOLO devuelve el objeto JSON crudo.

    FORMATO DE SALIDA OBLIGATORIO:
    {{
        "Categoria_Bloom": "NombreDeLaCategoria_o_Otro",
        "Justificacion": "Breve explicación",
        "Keywords": ["keyword1", "keyword2"]
    }}
    """

    contenido_usuario = ["--- CONTENIDO ---", texto]
    if imagenes_pil:
        contenido_usuario.append("--- IMÁGENES ---")
        contenido_usuario.extend(imagenes_pil)

    try:
        response = model.generate_content([prompt_sistema] + contenido_usuario)

        texto_limpio = response.text.strip()
        # Eliminar posibles bloques de markdown si la IA desobedece
        texto_limpio = re.sub(r"```json|```", "", texto_limpio).strip()

        return json.loads(texto_limpio)

    except Exception as e:
        # Fallback por error técnico
        return {"Categoria_Bloom": "Otro", "Justificacion": f"Error técnico o de parseo: {str(e)}", "Keywords": []}


# --- 4. PROCESO PRINCIPAL ---


def procesar_documentos():
    # 1. Identificar Usuario
    usuario = pedir_usuario_gui()
    if not usuario:
        logger.error("❌ Usuario requerido.")
        return

    logger.info(f"👤 Buscando archivos para: {usuario}")

    # 2. Conexión y Contexto
    col_raw, fs = conectar_bd()
    if col_raw is None:
        return

    contexto_bloom = cargar_instrucciones_bloom()

    # 3. Query Filtrado por Usuario
    query = {"usuario_propietario": usuario, "estado_procesamiento": {"$in": ["PENDIENTE", "INGESTADO"]}}

    documentos = list(col_raw.find(query))

    if not documentos:
        logger.info("ℹ️ No hay documentos pendientes para este usuario.")
        return

    # 4. Procesamiento
    for doc in documentos:
        logger.info(f"📘 {doc['nombre_archivo']}...")

        unidades = doc.get("unidades_contenido", [])
        unidades_actualizadas = []
        modificado = False

        for i, unidad in enumerate(unidades):
            logger.debug(f"Pág {unidad.get('indice', i+1)}/{len(unidades)}")

            texto = unidad.get("contenido_texto", "").strip()

            # Recuperar imágenes
            imagenes_pil = []
            for img_ref in unidad.get("imagenes", []):
                if "gridfs_id" in img_ref:
                    img_obj = recuperar_imagen(fs, img_ref["gridfs_id"])
                    if img_obj:
                        imagenes_pil.append(img_obj)

            # Si no hay nada, es "Otro" automáticamente
            if not texto and not imagenes_pil:
                unidad["Categoria_Bloom"] = "Otro"
                unidad["Pedagogia_Detalle"] = {"justificacion": "Página vacía", "keywords": []}
                unidades_actualizadas.append(unidad)
                modificado = True
                continue

            # Clasificación IA
            resultado = clasificar_unidad(texto, imagenes_pil, contexto_bloom)

            # Validación final del resultado
            cat = resultado.get("Categoria_Bloom", "Otro")
            if cat not in contexto_bloom and cat != "Otro":
                # Si la IA alucina una categoría que no está en el CSV, forzamos a Otro o mantenemos bajo riesgo
                # Aquí asumimos que confiamos en la IA o forzamos 'Otro' si es muy estricto
                pass

            unidad["Categoria_Bloom"] = cat
            unidad["Pedagogia_Detalle"] = {
                "justificacion": resultado.get("Justificacion", ""),
                "keywords": resultado.get("Keywords", []),
            }
            modificado = True

            unidades_actualizadas.append(unidad)

        logger.info("✅")

        if modificado:
            col_raw.update_one(
                {"_id": doc["_id"]},
                {
                    "$set": {
                        "unidades_contenido": unidades_actualizadas,
                        "estado_procesamiento": "BLOOM_COMPLETADO",
                        "fecha_procesamiento_ia": pd.Timestamp.now().isoformat(),
                    }
                },
            )
            logger.info("💾 Guardado.")


if __name__ == "__main__":
    procesar_documentos()
