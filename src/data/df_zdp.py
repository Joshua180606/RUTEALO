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
ruta_in = r"C:\Users\joshu\Documents\Joshua\Tesis\RUTEALO\data\raw\ZonaDeDesarrolloProximo.pdf"
dir_out = r"C:\Users\joshu\Documents\Joshua\Tesis\RUTEALO\data\processed"
file_out = "df_zdp.csv"


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


# --- 3. PROCESAR (Minado de Principios ZDP) ---
def get_df_zdp(raw):
    # Limpieza: quitamos saltos de línea para facilitar regex
    t = raw.replace("\n", " ")

    data = []

    # Mapeo: Principio ZDP -> Categoría Bloom Sugerida
    # Estos son los "Atributos del Aprendizaje Desarrollador" listados en el PDF
    principios_map = {
        "Es un proceso dialéctico": "Analizar",  # Requiere contrastar ideas
        "Es un proceso de apropiación individual": "Comprender",  # Internalización
        "Se extiende a lo largo de toda la vida": "Transversal",  # Actitud continua
        "Se aprende en la actividad": "Aplicar",  # Aprender haciendo
        "Este proceso siempre es regulado": "Evaluar",  # Metacognición/Autocontrol
        "Es un proceso constructivo": "Crear",  # Reestructuración personal
        "El aprendizaje debe ser significativo": "Recordar",  # Conectar con lo previo
        "Es un proceso mediado": "Comprender",  # Rol del profesor/guía
        "Es cooperativo": "Aplicar",  # Interacción social
        "El aprendizaje siempre es contextualizado": "Analizar",  # Vínculo con realidad
        "Debe ser desarrollador": "Crear",  # Crecimiento integral
    }

    # Regex:
    # El PDF usa viñetas o frases clave. Buscaremos la frase exacta y capturaremos hasta el siguiente punto aparte o frase clave.
    # Patrón: "Frase Clave" + (contenido) + (Lookahead para siguiente frase o fin)

    # Usamos enumerate para generar el ID (i) comenzando desde 1
    for i, (titulo, bloom) in enumerate(principios_map.items(), 1):
        # Buscamos la frase literal, ignorando mayúsculas/minúsculas y símbolos previos (como Π)
        # permitimos caracteres raros antes del título con .?
        pat = rf"(?:Π|•|-)?\s*{re.escape(titulo)}[:\s]*(.*?)(?=(?:Π|•|-)\s*[A-Z]|(?:2\.\s+La zona)|$)"

        m = re.search(pat, t, re.IGNORECASE)

        if m:
            contenido_bruto = m.group(1).strip()
            # Limpieza básica
            contenido_bruto = re.sub(r"\s+", " ", contenido_bruto)

            # División Heurística:
            # 1. Definición: Suele ser lo que está antes de los dos puntos (si los hay) o la primera frase.
            # En este texto, a veces la definición sigue a dos puntos ":".

            if ":" in contenido_bruto[:10]:  # Si hay dos puntos al inicio (ej "Es un proceso: ...")
                contenido_bruto = contenido_bruto.split(":", 1)[1].strip()

            parts = re.split(r"(?<=[.!?])\s+", contenido_bruto)

            # Asumimos primera oración como definición corta
            definicion = parts[0]

            # El resto es desarrollo
            desarrollo = " ".join(parts[1:])

            # NOTA: Se ha eliminado la extracción de evidencia según solicitud.

            data.append(
                {
                    "id_zdp": i,  # ID agregado
                    "principio_zdp": titulo,
                    "cat_bloom_sugerida": bloom,
                    "txt_definicion": definicion[:300],  # Recorte para vista previa
                    "txt_desarrollo": desarrollo[:300] + "..." if len(desarrollo) > 300 else desarrollo,
                    # txt_evidencia eliminado
                }
            )
        else:
            data.append(
                {
                    "id_zdp": i,  # ID agregado
                    "principio_zdp": titulo,
                    "cat_bloom_sugerida": bloom,
                    "txt_definicion": "No encontrado (Revisar OCR/Texto)",
                    "txt_desarrollo": "",
                    # txt_evidencia eliminado
                }
            )

    return pd.DataFrame(data)


# --- 4. MAIN ---
logger.info(f"1. Leyendo {ruta_in}...")
txt = get_txt(ruta_in)

if txt and "Err" not in txt:
    logger.info("2. Minando Principios de ZDP...")
    df = get_df_zdp(txt)

    logger.info("\n--- DF ZDP (Vista Previa) ---")
    pd.set_option("display.max_colwidth", 50)
    # Mostramos id_zdp al inicio y ocultamos evidencia
    logger.info("%s", df[["id_zdp", "principio_zdp", "cat_bloom_sugerida", "txt_definicion"]].head(11))

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
