import os
import datetime
import gridfs
import pypdf
import logging
from docx import Document
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from werkzeug.utils import secure_filename
from src.config import DB_NAME, COLS, RAW_DIR, get_genai_model
from src.database import get_database
from src.utils import retry, validate_exam_responses, validate_exam_structure

# Importaciones para IA y lógica de negocio
import pandas as pd
import json
import re

logger = logging.getLogger(__name__)

# --- CONFIGURACIÓN GENERATIVA (Centralizada) ---
model = get_genai_model()

# Constantes de Lógica Educativa
JERARQUIA_BLOOM = ["Recordar", "Comprender", "Aplicar", "Analizar", "Evaluar", "Crear"]
COL_EXAM_INI = "examen_inicial"
COL_RUTAS = "rutas_aprendizaje"
COL_RAW = "materiales_crudos"

# --- CONEXIÓN BD ---
def get_db(db_name: str = DB_NAME):
    """Get database using centralized connection."""
    return get_database(db_name)
    

# --- LÓGICA DE INGESTA (Existente) ---
def guardar_imagen_gridfs(fs, img_bytes, nombre_archivo, pagina_idx, img_idx, ext, usuario):
    filename = f"{usuario}_{nombre_archivo}_P{pagina_idx}_IMG{img_idx}{ext}"
    file_id = fs.put(
        img_bytes, 
        filename=filename,
        metadata={"documento_padre": nombre_archivo, "pagina_origen": pagina_idx, "usuario_propietario": usuario}
    )
    return {"gridfs_id": file_id, "nombre_archivo": filename}

def procesar_archivo_web(ruta_archivo, usuario, db):
    """Procesa un archivo subido y lo guarda en MongoDB."""
    fs = gridfs.GridFS(db)
    collection = db[COLS["RAW"]]
    
    nombre = os.path.basename(ruta_archivo)
    ext = os.path.splitext(nombre)[1].lower()
    unidades_contenido = []

    logger.info(f"🌐 Procesando web: {nombre} para {usuario}")

    try:
        if ext == '.pdf':
            reader = pypdf.PdfReader(ruta_archivo)
            for i, page in enumerate(reader.pages):
                texto = page.extract_text() or ""
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

        if unidades_contenido:
            doc_data = {
                "usuario_propietario": usuario,
                "nombre_archivo": nombre,
                "tipo_archivo": ext.replace('.', ''),
                "fecha_ingesta": datetime.datetime.utcnow(),
                "unidades_contenido": unidades_contenido,
                "estado_procesamiento": "PENDIENTE"
            }
            collection.replace_one(
                {"nombre_archivo": nombre, "usuario_propietario": usuario}, 
                doc_data, 
                upsert=True
            )
            return True, len(unidades_contenido)
            
    except Exception as e:
        logger.error(f"Error procesando archivo: {e}")
        return False, str(e)
    
    return False, "Formato no soportado o error desconocido"

# --- LÓGICA DE ETIQUETADO BLOOM (Automática) ---
def auto_etiquetar_bloom(usuario, db):
    """Busca documentos PENDIENTES del usuario y les aplica Bloom con Gemini."""
    col = db[COLS["RAW"]]
    docs = list(col.find({"usuario_propietario": usuario, "estado_procesamiento": "PENDIENTE"}))
    
    contexto_bloom = "Reglas de Bloom: Recordar, Comprender, Aplicar, Analizar, Evaluar, Crear."

    count = 0
    for doc in docs:
        unidades = doc.get("unidades_contenido", [])
        unidades_updated = []
        
        for u in unidades:
            texto = u.get("contenido_texto", "")[:1000]
            if not texto.strip():
                u["Categoria_Bloom"] = "Otro"
                u["Pedagogia_Detalle"] = {"justificacion": "Sin texto"}
                unidades_updated.append(u)
                continue

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

# --- NUEVA LÓGICA: GENERADOR DE RUTAS (MOTOR PROMPTING ADAPTADO) ---

def obtener_contexto_usuario(db, usuario):
    """Recopila todo el texto procesado de este usuario, agrupado por categoría Bloom."""
    # Buscamos en la colección RAW usando la constante definida o importada
    col_raw = db[COLS["RAW"]]
    docs = col_raw.find({"usuario_propietario": usuario, "estado_procesamiento": "BLOOM_COMPLETADO"})
    
    contenido_por_nivel = {nivel: [] for nivel in JERARQUIA_BLOOM}
    contenido_total = ""

    for doc in docs:
        for unidad in doc.get("unidades_contenido", []):
            cat = unidad.get("Categoria_Bloom", "Otro")
            texto = unidad.get("contenido_texto", "")
            
            # Mapeo simple por si la IA usó sinónimos o mayúsculas
            for nivel in JERARQUIA_BLOOM:
                if nivel.lower() in cat.lower():
                    contenido_por_nivel[nivel].append(texto)
                    contenido_total += texto + "\n"
                    break
    
    return contenido_por_nivel, contenido_total

@retry(max_attempts=3, delay=2.0, backoff=2.0, exceptions=(Exception,))
def generar_examen_inicial(contenido_total):
    """Genera un examen diagnóstico para determinar la Zona de Desarrollo Próximo (ZDP).
    Se reintenta automáticamente si falla."""
    if not contenido_total:
        return {}

    prompt = f"""
    Actúa como un psicopedagogo experto. Basado en el siguiente contenido educativo, genera un EXAMEN DE DIAGNÓSTICO INICIAL.
    
    OBJETIVO: Identificar la Zona de Desarrollo Próximo del estudiante.
    ESTRATEGIA: Genera 5 preguntas de dificultad incremental (desde 'Recordar' hasta 'Analizar').
    
    CONTENIDO BASE (Resumido):
    {contenido_total[:15000]}
    
    FORMATO JSON OBLIGATORIO:
    {{
        "EXAMENES": {{
            "EXAMEN_INICIAL": [
                {{
                    "id": 1,
                    "pregunta": "¿...?",
                    "opciones": ["a", "b", "c", "d"],
                    "respuesta_correcta": "a",
                    "nivel_bloom_evaluado": "Recordar"
                }}
            ]
        }}
    }}
    """
    try:
        res = model.generate_content(prompt)
        text_clean = re.sub(r"```json|```", "", res.text).strip()
        return json.loads(text_clean)
    except Exception as e:
        logger.error(f"⚠️ Error generando examen inicial: {e}")
        return {}

@retry(max_attempts=3, delay=2.0, backoff=2.0, exceptions=(Exception,))
def generar_bloque_ruta(nivel_bloom, textos_nivel):
    """Genera Flashcards y Exámenes para un nivel específico de Bloom.
    Se reintenta automáticamente si falla."""
    if not textos_nivel:
        return None

    texto_combinado = "\n".join(textos_nivel)[:10000]

    prompt = f"""
    Crea material de estudio para el Nivel Cognitivo: {nivel_bloom}.
    
    TEORÍA DEL FLOW:
    - El contenido debe ser desafiante pero alcanzable.
    - Usa un tono dinámico y motivador.
    
    TAREAS:
    1. Genera 3 FLASHCARDS clave para este nivel.
    2. Genera 1 EXAMEN PROCEDIMENTAL (3 preguntas).
    
    CONTENIDO:
    {texto_combinado}
    
    FORMATO JSON OBLIGATORIO:
    {{
        "FLASHCARDS": [
            {{"id": 1, "frente": "Pregunta", "reverso": "Respuesta", "visto": false}}
        ],
        "EXAMENES": [
            {{
                "id": 1,
                "pregunta": "...",
                "opciones": ["..."],
                "respuesta_correcta": "...",
                "realizado": false
            }}
        ]
    }}
    """
    try:
        res = model.generate_content(prompt)
        text_clean = re.sub(r"```json|```", "", res.text).strip()
        return json.loads(text_clean)
    except Exception as e:
        logger.error(f"⚠️ Error generando bloque {nivel_bloom}: {e}")
        return None

def generar_ruta_aprendizaje(usuario, db):
    """
    Orquestador principal: Lee todo el material del usuario y (re)genera la ruta completa.
    Retorna un mensaje de estado.
    """
    logger.info(f"🛤️ Iniciando generación de ruta para: {usuario}")

    # 1. Obtener Contexto Global
    contenido_bloom, contenido_total_raw = obtener_contexto_usuario(db, usuario)
    
    if not contenido_total_raw:
        return "No se encontró contenido procesado (Bloom) suficiente para generar una ruta."

    # 2. Generar/Actualizar Examen Inicial (ZDP)
    # Siempre regeneramos para incluir el nuevo material en el diagnóstico
    examen_ini_data = generar_examen_inicial(contenido_total_raw)
    
    if examen_ini_data:
        doc_examen_ini = {
            "usuario": usuario,
            "contenido": examen_ini_data,
            "estado": "PENDIENTE",
            "fecha_generacion": datetime.datetime.utcnow()
        }
        # Guardamos en la colección correspondiente
        db[COL_EXAM_INI].replace_one({"usuario": usuario}, doc_examen_ini, upsert=True)

    # 3. Generar Ruta de Aprendizaje (Flow)
    ruta_completa = {}
    secuencia_id = 1
    
    for nivel in JERARQUIA_BLOOM:
        textos = contenido_bloom.get(nivel, [])
        if not textos:
            continue
            
        bloque_generado = generar_bloque_ruta(nivel, textos)
        
        if bloque_generado:
            ruta_completa[nivel] = {
                "id_orden": secuencia_id,
                "bloqueado": True if secuencia_id > 1 else False, # El primero desbloqueado
                "contenido": bloque_generado
            }
            secuencia_id += 1

    # 4. Guardar Estructura Final en Mongo
    doc_ruta = {
        "usuario": usuario,
        "estructura_ruta": {
            "usuario": usuario,
            "examenes": {nivel: data["contenido"].get("EXAMENES", []) for nivel, data in ruta_completa.items()},
            "flashcards": {nivel: data["contenido"].get("FLASHCARDS", []) for nivel, data in ruta_completa.items()}
        },
        "metadatos_ruta": {
            "niveles_incluidos": list(ruta_completa.keys()),
            "progreso_global": 0,
            "estado_niveles": {nivel: "BLOQUEADO" if data["bloqueado"] else "DISPONIBLE" for nivel, data in ruta_completa.items()}
        },
        "fecha_actualizacion": datetime.datetime.utcnow()
    }

    db[COL_RUTAS].replace_one({"usuario": usuario}, doc_ruta, upsert=True)
    
    return f"Ruta regenerada con {len(ruta_completa)} niveles y Examen Diagnóstico actualizado."


# --- INTEGRACIÓN CON SISTEMA ZDP (NUEVO) ---

def procesar_respuesta_examen_web(usuario, respuestas_estudiante, examen_original):
    """
    Procesa las respuestas del examen del estudiante y actualiza su perfil ZDP.
    
    Args:
        usuario (str): ID del estudiante
        respuestas_estudiante (list): Lista de respuestas en formato:
            [
                {"pregunta_id": 1, "respuesta": "a", "tiempo_seg": 45},
                {"pregunta_id": 2, "respuesta": "c", "tiempo_seg": 32},
                ...
            ]
        examen_original (dict): El examen original con respuestas correctas
    
    Returns:
        dict: Resultado de evaluación con puntajes y recomendaciones, o dict con error
    """
    from src.models.evaluacion_zdp import EvaluadorZDP
    
    # Validar estructura de respuestas del estudiante
    is_valid, error_msg = validate_exam_responses(respuestas_estudiante)
    if not is_valid:
        logger.warning(f"Invalid exam responses for {usuario}: {error_msg}")
        return {"error": f"Respuestas inválidas: {error_msg}", "status": 400}
    
    # Validar estructura del examen original
    is_valid, error_msg = validate_exam_structure(examen_original)
    if not is_valid:
        logger.error(f"Invalid exam structure for {usuario}: {error_msg}")
        return {"error": f"Estructura de examen inválida: {error_msg}", "status": 400}
    
    # Validar que el usuario existe
    if not usuario or not isinstance(usuario, str):
        logger.warning(f"Invalid usuario parameter: {usuario}")
        return {"error": "Usuario inválido", "status": 400}
    
    try:
        evaluador = EvaluadorZDP()
        resultado = evaluador.evaluar_examen(usuario, respuestas_estudiante, examen_original)
        logger.info(f"Exam processed successfully for {usuario}")
        return resultado
    except Exception as e:
        logger.error(f"Error procesando examen para {usuario}: {str(e)}")
        return {"error": f"Error procesando examen: {str(e)}", "status": 500}


def obtener_ruta_personalizada_web(usuario, contenido_disponible):
    """
    Obtiene la ruta de aprendizaje personalizada para el estudiante.
    Omite temas donde ya es competente según su evaluación ZDP.
    
    Args:
        usuario (str): ID del estudiante
        contenido_disponible (str): Contenido educativo disponible
    
    Returns:
        dict: Ruta personalizada adaptada a su ZDP
    """
    from src.models.evaluacion_zdp import EvaluadorZDP
    
    try:
        evaluador = EvaluadorZDP()
        ruta = evaluador.generar_ruta_personalizada(usuario, contenido_disponible)
        return ruta
    except Exception as e:
        logger.error(f"❌ Error generando ruta personalizada: {e}")
        return {"error": str(e)}


def obtener_perfil_estudiante_zdp(usuario):
    """
    Obtiene el perfil ZDP actual del estudiante con sus competencias y recomendaciones.
    
    Args:
        usuario (str): ID del estudiante
    
    Returns:
        dict: Perfil ZDP completo
    """
    from src.models.evaluacion_zdp import obtener_perfil_zdp
    
    perfil = obtener_perfil_zdp(usuario)
    if perfil:
        return perfil
    return {
        "usuario": usuario,
        "estado": "Sin evaluación realizada",
        "mensaje": "El estudiante aún no ha completado un examen diagnóstico"
    }
