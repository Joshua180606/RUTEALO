import os
import json
import datetime
import tkinter as tk
from tkinter import messagebox, ttk
import google.generativeai as genai
import logging

# Cargar variables de entorno desde src.config
from src.config import DB_NAME, COLS, get_genai_model
from src.database import get_database
from src.utils import retry

logger = logging.getLogger(__name__)

# --- 1. CONFIGURACIÓN ---
# Colecciones MongoDB
COL_RAW = "materiales_crudos"  # Entrada (docs procesados)
COL_PERFIL = "usuario_perfil"  # Perfil del estudiante
COL_EXAM_INI = "examen_inicial"  # Diagnóstico (ZDP)
COL_RUTAS = "rutas_aprendizaje"  # Ruta (Flow + Bloom)

# Modelo Gemini (configuración centralizada)
model = get_genai_model()

# Jerarquía estricta de Bloom para la ruta
JERARQUIA_BLOOM = ["Recordar", "Comprender", "Aplicar", "Analizar", "Evaluar", "Crear"]

# --- 2. GESTIÓN DE BASES DE DATOS ---


def conectar_bd():
    try:
        db = get_database(DB_NAME)
        return db
    except Exception as e:
        logger.error(f"❌ Error conectando a BD: {e}")
        return None


# --- 3. INTERFAZ DE USUARIO (PERFILADO) ---


def obtener_datos_usuario_gui():
    """Ventana para capturar datos del perfil del usuario."""
    datos = {}

    def guardar():
        if not entry_user.get() or not entry_tiempo.get():
            messagebox.showerror("Error", "Usuario y Tiempo son obligatorios")
            return
        datos["usuario"] = entry_user.get().strip()
        datos["nombres"] = entry_nombres.get().strip()
        datos["apellidos"] = entry_apellidos.get().strip()
        datos["email"] = entry_email.get().strip()
        datos["telefono"] = entry_tel.get().strip()
        datos["tiempo_diario_min"] = entry_tiempo.get().strip()
        datos["dia_descanso"] = combo_descanso.get()
        root.destroy()

    root = tk.Tk()
    root.title("Configuración de Ruta de Aprendizaje")
    root.geometry("400x550")

    tk.Label(root, text="Usuario (ID Único)", font=("Arial", 10, "bold")).pack(pady=5)
    entry_user = tk.Entry(root)
    entry_user.pack()

    tk.Label(root, text="Nombres").pack(pady=5)
    entry_nombres = tk.Entry(root)
    entry_nombres.pack()

    tk.Label(root, text="Apellidos").pack(pady=5)
    entry_apellidos = tk.Entry(root)
    entry_apellidos.pack()

    tk.Label(root, text="Email").pack(pady=5)
    entry_email = tk.Entry(root)
    entry_email.pack()

    tk.Label(root, text="Teléfono").pack(pady=5)
    entry_tel = tk.Entry(root)
    entry_tel.pack()

    tk.Label(root, text="Tiempo diario (minutos)").pack(pady=5)
    entry_tiempo = tk.Entry(root)
    entry_tiempo.pack()

    tk.Label(root, text="Día de Descanso").pack(pady=5)
    combo_descanso = ttk.Combobox(
        root, values=["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    )
    combo_descanso.current(4)  # Viernes por defecto
    combo_descanso.pack()

    tk.Button(root, text="Generar Ruta", command=guardar, bg="#4CAF50", fg="white").pack(pady=20)

    root.mainloop()
    return datos


# --- 4. MOTOR DE PROMPTING: LOGICA ---


def obtener_contexto_usuario(db, usuario):
    """Recopila todo el texto procesado de este usuario, agrupado por categoría Bloom."""
    docs = db[COL_RAW].find({"usuario_propietario": usuario, "estado_procesamiento": "BLOOM_COMPLETADO"})

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
    """
    Genera un examen diagnóstico para determinar la Zona de Desarrollo Próximo (ZDP).
    Se reintenta automáticamente si falla.
    """
    if not contenido_total:
        return {}

    prompt = f"""
    Actúa como un psicopedagogo experto. Basado en el siguiente contenido educativo, genera un EXAMEN DE DIAGNÓSTICO INICIAL.
    
    OBJETIVO: Identificar la Zona de Desarrollo Próximo del estudiante.
    ESTRATEGIA: Genera 5 preguntas de dificultad incremental (desde 'Recordar' hasta 'Analizar').
    
    CONTENIDO BASE (Resumido):
    {contenido_total[:15000]}  # Limitamos caracteres para no saturar token
    
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
                }},
                ... (hasta 5 preguntas)
            ]
        }}
    }}
    """
    try:
        res = model.generate_content(prompt)
        return json.loads(res.text)
    except Exception as e:
        logger.error(f"⚠️ Error generando examen inicial: {e}")
        return {}


@retry(max_attempts=3, delay=2.0, backoff=2.0, exceptions=(Exception,))
def generar_bloque_ruta(nivel_bloom, textos_nivel):
    """
    Genera Flashcards y Exámenes para un nivel específico de Bloom (Teoría del Flow).
    Se reintenta automáticamente si falla.
    """
    if not textos_nivel:
        return None

    texto_combinado = "\n".join(textos_nivel)[:10000]  # Contexto limitado

    prompt = f"""
    Crea material de estudio para el Nivel Cognitivo: {nivel_bloom}.
    
    TEORÍA DEL FLOW:
    - El contenido debe ser desafiante pero alcanzable.
    - Usa un tono dinámico y motivador.
    
    TAREAS:
    1. Genera 3-5 FLASHCARDS clave para este nivel.
    2. Genera 1 EXAMEN PROCEDIMENTAL (3 preguntas) que valide este nivel específico.
    
    CONTENIDO:
    {texto_combinado}
    
    FORMATO JSON OBLIGATORIO:
    {{
        "FLASHCARDS": [
            {{"id": 1, "frente": "Concepto/Pregunta", "reverso": "Explicación breve", "visto": false}}
        ],
        "EXAMENES": [
            {{
                "id": 1,
                "pregunta": "Pregunta procedimental...",
                "opciones": ["...", "..."],
                "respuesta_correcta": "...",
                "realizado": false
            }}
        ]
    }}
    """
    try:
        res = model.generate_content(prompt)
        return json.loads(res.text)
    except Exception as e:
        logger.error(f"⚠️ Error generando bloque {nivel_bloom}: {e}")
        return None


# --- 5. ORQUESTADOR PRINCIPAL ---


def procesar_motor():
    # 1. Obtener Datos Usuario
    datos_usuario = obtener_datos_usuario_gui()
    if not datos_usuario:
        return
    usuario_id = datos_usuario["usuario"]

    db = conectar_bd()
    if db is None:
        return

    logger.info(f"🚀 Iniciando Motor de Prompting para: {usuario_id}")

    # 2. Guardar/Actualizar Perfil (USUARIO_PERFIL)
    perfil_doc = {
        "usuario": usuario_id,
        "datos_personales": {
            "nombres": datos_usuario["nombres"],
            "apellidos": datos_usuario["apellidos"],
            "email": datos_usuario["email"],
            "telefono": datos_usuario["telefono"],
        },
        "preferencias": {
            "tiempo_diario": datos_usuario["tiempo_diario_min"],
            "dia_descanso": datos_usuario["dia_descanso"],
        },
        "nivel_actual_bloom": "No iniciado",  # Se actualiza tras examen inicial
        "ultima_actualizacion": datetime.datetime.utcnow(),
    }
    db[COL_PERFIL].replace_one({"usuario": usuario_id}, perfil_doc, upsert=True)
    logger.info("✅ Perfil guardado.")

    # 3. Obtener Contexto de Documentos Ingestados
    contenido_bloom, contenido_total_raw = obtener_contexto_usuario(db, usuario_id)

    if not contenido_total_raw:
        messagebox.showwarning("Alerta", f"No se encontró contenido procesado (Bloom) para el usuario {usuario_id}.")
        return

    # 4. Generar Examen Inicial (EXAMEN_INICIAL)
    logger.info("🧠 Generando Examen Diagnóstico (ZDP)...")
    examen_ini_data = generar_examen_inicial(contenido_total_raw)

    if examen_ini_data:
        doc_examen_ini = {
            "usuario": usuario_id,
            "contenido": examen_ini_data,
            "estado": "PENDIENTE",
            "fecha_generacion": datetime.datetime.utcnow(),
        }
        db[COL_EXAM_INI].replace_one({"usuario": usuario_id}, doc_examen_ini, upsert=True)
        logger.info("✅ Examen Inicial generado y guardado.")

    # 5. Generar Ruta de Aprendizaje (RUTAS_APRENDIZAJE)
    logger.info("🛤️ Diseñando Ruta de Aprendizaje (Flow Theory)...")

    ruta_completa = {}
    secuencia_id = 1

    # Iteramos la jerarquía Bloom. Si no se supera el anterior, no se ve el siguiente (lógica de frontend, aquí generamos la estructura)
    for nivel in JERARQUIA_BLOOM:
        textos = contenido_bloom.get(nivel, [])
        if not textos:
            logger.debug(f"   ℹ️ Saltando nivel {nivel} (sin contenido origen).")
            continue

        logger.debug(f"   ⚡ Procesando Nivel: {nivel}...")
        bloque_generado = generar_bloque_ruta(nivel, textos)

        if bloque_generado:
            # Añadimos metadatos de control
            ruta_completa[nivel] = {
                "id_orden": secuencia_id,
                "bloqueado": True if secuencia_id > 1 else False,  # El primero desbloqueado
                "contenido": bloque_generado,
            }
            secuencia_id += 1

    # Estructura final para Mongo
    doc_ruta = {
        "usuario": usuario_id,
        "estructura_ruta": {
            "usuario": usuario_id,
            "examenes": {nivel: data["contenido"].get("EXAMENES", []) for nivel, data in ruta_completa.items()},
            "flashcards": {nivel: data["contenido"].get("FLASHCARDS", []) for nivel, data in ruta_completa.items()},
        },
        "metadatos_ruta": {
            "niveles_incluidos": list(ruta_completa.keys()),
            "progreso_global": 0,
            "estado_niveles": {
                nivel: "BLOQUEADO" if data["bloqueado"] else "DISPONIBLE" for nivel, data in ruta_completa.items()
            },
        },
        "fecha_creacion": datetime.datetime.utcnow(),
    }

    db[COL_RUTAS].replace_one({"usuario": usuario_id}, doc_ruta, upsert=True)

    logger.info("\n✨ ¡PROCESO COMPLETADO!")
    logger.info(f"   - Perfil actualizado")
    logger.info(
        f"   - Examen Inicial creado ({len(examen_ini_data.get('EXAMENES', {}).get('EXAMEN_INICIAL', []))} preguntas)"
    )
    logger.info(f"   - Ruta de aprendizaje generada con {len(ruta_completa)} niveles Bloom.")
    messagebox.showinfo("Éxito", "La Ruta de Aprendizaje ha sido generada correctamente en MongoDB.")


if __name__ == "__main__":
    procesar_motor()
