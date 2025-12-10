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

# NUEVO: Importar funciones centralizadas de web_utils
from src.web_utils import (
    obtener_contexto_usuario,
    generar_examen_inicial,
    cargar_marcos_pedagogicos,
    generar_ruta_aprendizaje
)

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


# --- 4. MOTOR DE PROMPTING: LÓGICA ---
# NOTA: Las siguientes funciones ahora se importan de web_utils para centralizar lógica:
# - obtener_contexto_usuario(db, usuario)
# - generar_examen_inicial(contenido_total)
# - generar_ruta_aprendizaje(usuario, db)
# - cargar_marcos_pedagogicos()


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

    # 3. NUEVO: Usar función centralizada de web_utils para generar ruta completa
    # Esta función ahora maneja:
    # - Obtención de contexto
    # - Generación de examen inicial con CSV
    # - Lectura de perfil ZDP
    # - Generación de ruta optimizada con estrategias diferenciadas
    logger.info("🛤️ Generando ruta de aprendizaje completa con ZDP y CSV...")
    
    resultado = generar_ruta_aprendizaje(usuario_id, db)

    logger.info("\n✨ ¡PROCESO COMPLETADO!")
    logger.info(f"   - Perfil actualizado")
    logger.info(f"   - {resultado}")
    messagebox.showinfo("Éxito", f"La Ruta de Aprendizaje ha sido generada correctamente.\n\n{resultado}")


if __name__ == "__main__":
    procesar_motor()
