import pandas as pd
import pypdf
import re
import os
import logging

logger = logging.getLogger(__name__)

# Variables de entorno cargadas (centralizado en src.config)
# Solo usamos rutas locales en este archivo

# --- 1. CONFIG ---
# Rutas
ruta_in = r"C:\Users\joshu\Documents\Joshua\Tesis\RUTEALO\data\raw\TaxonomiaDeBloom.pdf"
dir_out = r"C:\Users\joshu\Documents\Joshua\Tesis\RUTEALO\data\processed"
file_out = "df_bloom.csv"


# --- 2. LEER PDF ---
def get_txt(path):
    try:
        reader = pypdf.PdfReader(path)
        t = ""  # Acumulador texto
        for p in reader.pages:
            t += p.extract_text() + "\n"
        return t
    except Exception as e:
        return f"Error: {e}"


# --- 3. PROCESAR DATOS ---
def get_df(raw):
    # Aplanar texto (quitar saltos de línea)
    t = raw.replace("\n", " ")
    data = {}

    # Categorías (IDs)
    cats = ["Recordar", "Comprender", "Aplicar", "Analizar", "Evaluar", "Crear"]

    # Patrones Regex: Descripciones
    p_desc = {
        "Recordar": r"Recuperar el conocimiento.*?largo plazo",
        "Comprender": r"Construir el significado.*?grá(?:f|fi)ca",
        "Aplicar": r"Llevar a cabo.*?situación\s+dada",
        "Analizar": r"Dividir el material.*?propósito",
        "Evaluar": r"Hacer juicios.*?estándares",
        "Crear": r"Poner elementos juntos.*?estructura",
    }

    # Patrones Regex: Subtipos (ej. 1.1)
    p_sub = {
        "Recordar": r"1\.\d\s+[A-ZÁÉÍÓÚa-zñ]+",
        "Comprender": r"2\.\d\s+[A-ZÁÉÍÓÚa-zñ]+",
        "Aplicar": r"3\.\d\s+[A-ZÁÉÍÓÚa-zñ]+",
        "Analizar": r"4\.\d\s+[A-ZÁÉÍÓÚa-zñ]+",
        "Evaluar": r"5\.\d\s+[A-ZÁÉÍÓÚa-zñ]+",
        "Crear": r"6\.\d\s+[A-ZÁÉÍÓÚa-zñ]+",
    }

    # Mapa Conocimiento (Tipo + Letra clave)
    map_c = {
        "Recordar": {"tipo": "Conocimiento Factual", "let": "A"},
        "Comprender": {"tipo": "Conocimiento Conceptual", "let": "B"},
        "Aplicar": {"tipo": "Conocimiento Procedimental", "let": "C"},
        "Analizar": {"tipo": "Conocimiento Metacognitivo", "let": "D"},
    }

    # Ciclo por categoría
    for c in cats:
        row = {}

        # A. Desc Proceso (Busca patrón en texto)
        m = re.search(p_desc[c], t, re.IGNORECASE)
        row["proc_desc"] = m.group(0).strip() if m else "No found"

        # B. Subs Proceso (Lista de verbos)
        row["proc_subs"] = re.findall(p_sub[c], t)

        # C. Datos Conocimiento (Si aplica)
        if c in map_c:
            info = map_c[c]
            row["conoc_tipo"] = info["tipo"]
            l = info["let"]

            # Regex: Busca desde Letra (A.a) hasta sig letra o fin
            p_conoc = rf"{l}\.[a-z]\s+.*?(?=(?:[A-D]\.[a-z]|Revista|$))"

            subs = re.findall(p_conoc, t)
            row["conoc_subs"] = [s.strip() for s in subs]
            row["conoc_desc"] = "Auto-extracted"  # Placeholder
        else:
            # Evaluar/Crear no tienen tipos en Fig 2
            row["conoc_tipo"] = None
            row["conoc_desc"] = None
            row["conoc_subs"] = None

        data[c] = row

    return pd.DataFrame.from_dict(data, orient="index")


# --- 4. MAIN ---
logger.info(f"1. Leyendo {ruta_in}...")
txt = get_txt(ruta_in)

if txt and "Error" not in txt:
    logger.info("2. Procesando...")
    df = get_df(txt)

    df.index.name = "cat_bloom"
    logger.info("\n--- DF RESULTADO ---")
    logger.info("%s", df)

    logger.info(f"\n3. Guardando en {dir_out}...")
    try:
        # Crea carpeta si no existe
        if not os.path.exists(dir_out):
            os.makedirs(dir_out)

        # Ruta completa
        full_path = os.path.join(dir_out, file_out)

        # Guardar CSV (utf-8-sig para Excel)
        df.to_csv(full_path, encoding="utf-8-sig")
        logger.info(f"OK: {full_path}")

    except Exception as e:
        logger.error(f"Error save: {e}")
else:
    logger.error(txt)
