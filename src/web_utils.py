import os
import datetime
import gridfs
import pypdf
from docx import Document
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pymongo import MongoClient
from werkzeug.utils import secure_filename
from src.config import MONGO_URI, DB_NAME, COLS, RAW_DIR, GOOGLE_API_KEY

# Importar lógica de bloom existente o re-implementar la función de clasificación
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import pandas as pd
import json
import re
import zipfile

# --- CONFIGURACIÓN GENERATIVA ---
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")

# --- CONEXIÓN BD ---
def get_db():
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    return db

# --- LÓGICA DE INGESTA (Adaptada para Web) ---
def guardar_imagen_gridfs(fs, img_bytes, nombre_archivo, pagina_idx, img_idx, ext, usuario):
    filename = f"{usuario}_{nombre_archivo}_P{pagina_idx}_IMG{img_idx}{ext}"
    file_id = fs.put(
        img_bytes, 
        filename=filename,
        metadata={"documento_padre": nombre_archivo, "pagina_origen": pagina_idx, "usuario_propietario": usuario}
    )
    return {"gridfs_id": file_id, "nombre_archivo": filename}

def procesar_archivo_web(ruta_archivo, usuario, db):
    """
    Procesa un archivo subido y lo guarda en MongoDB.
    """
    fs = gridfs.GridFS(db)
    collection = db[COLS["RAW"]]
    
    nombre = os.path.basename(ruta_archivo)
    ext = os.path.splitext(nombre)[1].lower()
    unidades_contenido = []

    print(f"🌐 Procesando web: {nombre} para {usuario}")

    try:
        if ext == '.pdf':
            reader = pypdf.PdfReader(ruta_archivo)
            for i, page in enumerate(reader.pages):
                texto = page.extract_text() or ""
                # (Simplificado: extracción de imágenes omitida para brevedad, puedes copiarla del original)
                unidades_contenido.append({
                    "indice": i + 1,
                    "tipo_unidad": "pagina",
                    "contenido_texto": texto,
                    "imagenes": [],
                    "metadata_bloom": None
                })
        
        elif ext == '.docx':
            doc = Document(ruta_archivo)
            texto = "\n".join([p.text for p in doc.paragraphs])
            unidades_contenido.append({
                "indice": 1,
                "tipo_unidad": "documento_completo",
                "contenido_texto": texto,
                "imagenes": [],
                "metadata_bloom": None
            })
        
        elif ext == '.pptx':
            prs = Presentation(ruta_archivo)
            for i, slide in enumerate(prs.slides):
                texto = ""
                for shape in slide.shapes:
                    if hasattr(shape, "text"): texto += shape.text + "\n"
                unidades_contenido.append({
                    "indice": i + 1,
                    "tipo_unidad": "diapositiva",
                    "contenido_texto": texto,
                    "imagenes": [],
                    "metadata_bloom": None
                })

        # Guardar en Mongo
        if unidades_contenido:
            doc_data = {
                "usuario_propietario": usuario,
                "nombre_archivo": nombre,
                "tipo_archivo": ext.replace('.', ''),
                "fecha_ingesta": datetime.datetime.utcnow(),
                "unidades_contenido": unidades_contenido,
                "estado_procesamiento": "PENDIENTE" # Importante para el siguiente paso
            }
            collection.replace_one(
                {"nombre_archivo": nombre, "usuario_propietario": usuario}, 
                doc_data, 
                upsert=True
            )
            return True, len(unidades_contenido)
            
    except Exception as e:
        print(f"Error procesando archivo: {e}")
        return False, str(e)
    
    return False, "Formato no soportado o error desconocido"

# --- LÓGICA DE ETIQUETADO BLOOM (Automática) ---
def auto_etiquetar_bloom(usuario, db):
    """
    Busca documentos PENDIENTES del usuario y les aplica Bloom con Gemini.
    """
    col = db[COLS["RAW"]]
    docs = list(col.find({"usuario_propietario": usuario, "estado_procesamiento": "PENDIENTE"}))
    
    # Cargar contexto Bloom (Simplificado: Hardcoded o leer CSV)
    contexto_bloom = "Reglas de Bloom: Recordar, Comprender, Aplicar, Analizar, Evaluar, Crear."

    count = 0
    for doc in docs:
        unidades = doc.get("unidades_contenido", [])
        unidades_updated = []
        
        for u in unidades:
            texto = u.get("contenido_texto", "")[:1000] # Limite tokens
            
            prompt = f"""
            Clasifica este texto educativo según la Taxonomía de Bloom.
            Texto: {texto}
            Reglas: {contexto_bloom}
            Responde SOLO JSON: {{"Categoria_Bloom": "Nivel", "Justificacion": "Breve"}}
            Si no es educativo, categoria "Otro".
            """
            
            try:
                res = model.generate_content(prompt)
                json_res = json.loads(re.sub(r"```json|```", "", res.text).strip())
                u["Categoria_Bloom"] = json_res.get("Categoria_Bloom", "Otro")
                u["Pedagogia_Detalle"] = {"justificacion": json_res.get("Justificacion", "")}
            except:
                u["Categoria_Bloom"] = "Otro"
                u["Pedagogia_Detalle"] = {"error": "Fallo IA"}
            
            unidades_updated.append(u)
        
        col.update_one(
            {"_id": doc["_id"]},
            {"$set": {"unidades_contenido": unidades_updated, "estado_procesamiento": "BLOOM_COMPLETADO"}}
        )
        count += 1
    
    return count