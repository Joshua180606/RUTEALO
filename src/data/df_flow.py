import pandas as pd
import pypdf
import re
import os
import logging

logger = logging.getLogger(__name__)

# Variables de entorno cargadas (centralizado en src.config)
# Solo usamos rutas locales en este archivo

# --- 1. CONFIG ---
# Rutas entorno prueba
ruta_in = r"C:\Users\joshu\Documents\Joshua\Tesis\RUTEALO\data\raw\TeoriaDelFlow.pdf"
dir_out = r"C:\Users\joshu\Documents\Joshua\Tesis\RUTEALO\data\processed"
file_out = "df_flow.csv"


# --- 2. LEER PDF ---
def get_txt(path):
    try:
        r = pypdf.PdfReader(path)
        t = ""
        for p in r.pages:
            t += p.extract_text() + "\n"
        return t
    except Exception as e:
        return f"Err: {e}"


# --- 3. PROCESAR (Minado y Categorización Específica) ---
def get_df_flow_detallado(raw):
    # Aplanamos el texto
    t = raw.replace("\n", " ")

    data = []

    # Mapeo de Dimensiones y Categoría Bloom Sugerida
    dims_map = {
        "Existencia de metas claras": "Recordar",
        "Necesidad de feedback inmediato": "Evaluar",
        "Habilidades personales ajustadas a los retos": "Analizar",
        "Concentración en la actividad": "Comprender",
        "Unión de acción y conciencia": "Aplicar",
        "Control potencial": "Crear",
        "Pérdida de autoconciencia": "Crear",
        "Percepción alterada del espacio temporal": "Transversal",
        "La experiencia se convierte en autotélica": "Transversal",
    }

    for i, (titulo, bloom) in enumerate(dims_map.items(), 1):
        # 1. Extracción del Bloque Completo (Regex original)
        pat = rf"{i}\.\s+{re.escape(titulo)}(.*?)(?=\d\.\s+[A-Z]|2\.1\.3|$)"
        m = re.search(pat, t, re.IGNORECASE)

        if m:
            contenido_bruto = m.group(1).strip()
            # Limpieza de espacios múltiples
            contenido_bruto = re.sub(r"\s+", " ", contenido_bruto)

            # 2. División en Categorías Específicas
            # Dividimos por punto y espacio para obtener oraciones (aproximación heurística)
            # Usamos un lookbehind para no romper en abreviaturas comunes si las hubiera, aunque el PDF es limpio.
            oraciones = re.split(r"(?<=[.!?])\s+", contenido_bruto)

            # A. Definición (Concepto Clave): Asumimos que es la primera oración completa.
            definicion = oraciones[0] if oraciones else ""

            # B. Evidencia (Soporte Científico): Buscamos oraciones con citas tipo (Autor, Año)
            # Regex busca paréntesis con 4 dígitos dentro.
            evidencia = [s for s in oraciones if re.search(r"\([^)]*\d{4}[^)]*\)", s)]
            texto_evidencia = " ".join(evidencia)

            # C. Desarrollo (Explicación): Todo lo que no es definición ni evidencia.
            desarrollo = [s for s in oraciones if s != definicion and s not in evidencia]
            texto_desarrollo = " ".join(desarrollo)

            data.append(
                {
                    "id_flow": i,
                    "dimension": titulo,
                    "cat_bloom": bloom,
                    "txt_definicion": definicion,
                    "txt_desarrollo": texto_desarrollo,
                    "txt_evidencia": texto_evidencia,
                }
            )
        else:
            data.append(
                {
                    "id_flow": i,
                    "dimension": titulo,
                    "cat_bloom": bloom,
                    "txt_definicion": "No encontrado",
                    "txt_desarrollo": "",
                    "txt_evidencia": "",
                }
            )

    return pd.DataFrame(data)


# --- 4. MAIN ---
logger.info(f"1. Leyendo {ruta_in}...")
txt = get_txt(ruta_in)

if txt and "Err" not in txt:
    logger.info("2. Procesando y categorizando contenido...")
    df = get_df_flow_detallado(txt)

    logger.info("\n--- DF DETALLADO (Vista Previa) ---")
    # Mostramos columnas clave para verificar la división
    logger.info("%s", df[["dimension", "txt_definicion", "txt_evidencia"]].head())

    logger.info(f"\n3. Guardando en {dir_out}...")
    try:
        if not os.path.exists(dir_out):
            os.makedirs(dir_out)

        full = os.path.join(dir_out, file_out)
        df.to_csv(full, encoding="utf-8-sig", index=False)
        logger.info(f"OK: {full}")

    except Exception as e:
        logger.error(f"Err save: {e}")
else:
    logger.error(txt)
