import os
import datetime
import io
import zipfile
from pymongo import MongoClient
from pymongo.server_api import ServerApi
import gridfs
import pypdf
from docx import Document
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE

# --- 1. CONFIGURACIÓN (ATLAS) ---
MONGO_URI = "mongodb+srv://RUTEALO:aLTEC358036@cluster0.u4eugtp.mongodb.net/?appName=Cluster0"
DB_NAME = "RUTEALO_DB"
COLLECTION_RAW = "materiales_crudos"

def conectar_bd():
    try:
        client = MongoClient(MONGO_URI, server_api=ServerApi('1'))
        client.admin.command('ping')
        db = client[DB_NAME]
        fs = gridfs.GridFS(db)

        # Después de conectarnos, abrir selector de archivos para elegir uno o más archivos a procesar
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        raw_dir = os.path.join(base_dir, "data", "raw")

        try:
            archivos = seleccionar_archivos_gui(initial_dir=raw_dir)
        except Exception:
            archivos = []

        return db[COLLECTION_RAW], fs, archivos
    except Exception as e:
        print(f"❌ Error conectando a Atlas: {e}")
        return None, None, []

# --- 2. FUNCIONES AUXILIARES ---

def guardar_imagen_gridfs(fs, img_bytes, nombre_archivo, pagina_idx, img_idx, ext):
    """Guarda una imagen en GridFS y devuelve su ID y metadatos."""
    try:
        filename = f"{nombre_archivo}_P{pagina_idx}_IMG{img_idx}{ext}"
        file_id = fs.put(
            img_bytes, 
            filename=filename,
            metadata={
                "documento_padre": nombre_archivo,
                "pagina_origen": pagina_idx
            }
        )
        return {
            "gridfs_id": file_id,
            "nombre_archivo": filename,
            "tipo_mime": f"image/{ext.replace('.', '')}"
        }
    except Exception as e:
        print(f"⚠️ Error guardando imagen {filename}: {e}")
        return None

# --- 3. EXTRACTORES POR PÁGINA/DIAPOSITIVA ---

def procesar_pdf(ruta_archivo, fs):
    """Estructura: Lista de Páginas con su texto e imágenes."""
    nombre_doc = os.path.basename(ruta_archivo)
    paginas_estructuradas = []
    
    try:
        reader = pypdf.PdfReader(ruta_archivo)
        for i, page in enumerate(reader.pages):
            idx_pag = i + 1
            texto_pag = page.extract_text() or ""
            
            # Procesar imágenes de ESTA página
            imagenes_pag = []
            for j, img in enumerate(page.images):
                ext = os.path.splitext(img.name)[1]
                img_info = guardar_imagen_gridfs(fs, img.data, nombre_doc, idx_pag, j+1, ext)
                if img_info:
                    imagenes_pag.append(img_info)
            
            # Agregamos la unidad estructurada
            paginas_estructuradas.append({
                "indice": idx_pag,
                "tipo_unidad": "pagina",
                "contenido_texto": texto_pag,
                "imagenes": imagenes_pag,
                "metadata_bloom": None # Placeholder para la Fase 2
            })
                
        return paginas_estructuradas
    except Exception as e:
        print(f"⚠️ Error PDF: {e}")
        return []

def procesar_pptx(ruta_archivo, fs):
    """Estructura: Lista de Diapositivas."""
    nombre_doc = os.path.basename(ruta_archivo)
    diapositivas_estructuradas = []
    
    try:
        prs = Presentation(ruta_archivo)
        for i, slide in enumerate(prs.slides):
            idx_slide = i + 1
            texto_slide = ""
            imagenes_slide = []
            
            # Iterar formas en la diapositiva
            img_count = 0
            for shape in slide.shapes:
                # A. Texto
                if hasattr(shape, "text"):
                    texto_slide += shape.text + "\n"
                
                # B. Imágenes
                if shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
                    img_count += 1
                    image = shape.image
                    ext = f".{image.ext}"
                    img_info = guardar_imagen_gridfs(fs, image.blob, nombre_doc, idx_slide, img_count, ext)
                    if img_info:
                        imagenes_slide.append(img_info)

            diapositivas_estructuradas.append({
                "indice": idx_slide,
                "tipo_unidad": "diapositiva",
                "contenido_texto": texto_slide,
                "imagenes": imagenes_slide,
                "metadata_bloom": None
            })
            
        return diapositivas_estructuradas
    except Exception as e:
        print(f"⚠️ Error PPTX: {e}")
        return []

def procesar_docx(ruta_archivo, fs):
    """
    Nota: DOCX no tiene 'páginas' fijas. Se tratará como una secuencia de párrafos.
    Para mantener consistencia, crearemos una única 'unidad' grande o segmentaremos por títulos si es necesario.
    Aquí optamos por crear una única unidad para no fragmentar el contexto, salvo que detectemos saltos de página explícitos.
    """
    nombre_doc = os.path.basename(ruta_archivo)
    
    # En Word, las imágenes son difíciles de vincular a un párrafo exacto sin XML parsing complejo.
    # Usaremos el método ZIP para extraer todas las imágenes y las asociaremos a la unidad principal.
    imagenes_globales = []
    try:
        with zipfile.ZipFile(ruta_archivo) as z:
            img_count = 0
            for file_info in z.infolist():
                if file_info.filename.startswith('word/media/'):
                    img_count += 1
                    img_data = z.read(file_info)
                    ext = os.path.splitext(file_info.filename)[1]
                    img_info = guardar_imagen_gridfs(fs, img_data, nombre_doc, 1, img_count, ext)
                    if img_info:
                        imagenes_globales.append(img_info)
    except:
        pass # Si falla extracción de imágenes, seguimos con texto

    try:
        doc = Document(ruta_archivo)
        texto_completo = "\n".join([p.text for p in doc.paragraphs])
        
        return [{
            "indice": 1,
            "tipo_unidad": "documento_completo", # Word es fluido
            "contenido_texto": texto_completo,
            "imagenes": imagenes_globales,
            "metadata_bloom": None
        }]
    except Exception as e:
        print(f"⚠️ Error DOCX: {e}")
        return []

# --- 4. PROCESO PRINCIPAL ---

def ingestar_archivo(ruta_archivo, collection, fs):
    if not os.path.exists(ruta_archivo):
        return

    nombre = os.path.basename(ruta_archivo)
    ext = os.path.splitext(nombre)[1].lower()
    print(f"🔄 Procesando estructuradamente: {nombre}...")

    unidades_contenido = []

    if ext == '.pdf':
        unidades_contenido = procesar_pdf(ruta_archivo, fs)
    elif ext == '.pptx':
        unidades_contenido = procesar_pptx(ruta_archivo, fs)
    elif ext == '.docx':
        unidades_contenido = procesar_docx(ruta_archivo, fs)
    else:
        print(f"⚠️ Formato no soportado: {ext}")
        return

    if not unidades_contenido:
        print("⚠️ No se extrajo contenido.")
        return

    # Crear Documento Maestro
    documento = {
        "nombre_archivo": nombre,
        "tipo_archivo": ext.replace('.', ''),
        "fecha_ingesta": datetime.datetime.utcnow(),
        "total_unidades": len(unidades_contenido),
        "unidades_contenido": unidades_contenido, # <-- AQUÍ ESTÁ LA MAGIA (Array de páginas)
        "estado_procesamiento": "PENDIENTE",
        "metadata": {
            "tamano_bytes": os.path.getsize(ruta_archivo),
            "version_modelo": "v3.0_paginado"
        }
    }

    try:
        res = collection.insert_one(documento)
        print(f"✅ Ingesta exitosa. {len(unidades_contenido)} unidades (páginas/slides) guardadas.")
    except Exception as e:
        print(f"❌ Error guardando en MongoDB: {e}")


def seleccionar_archivos_gui(initial_dir=None):
    """Abre una ventana del gestor de archivos para que el usuario seleccione uno o más archivos.
    Devuelve una lista de rutas seleccionadas (puede estar vacía si se cancela).
    """
    try:
        import tkinter as tk
        from tkinter import filedialog
    except Exception as e:
        print(f"⚠️ No se puede abrir el selector de archivos (tkinter no disponible): {e}")
        return []

    root = tk.Tk()
    # No mostrar la ventana principal
    root.withdraw()
    # Forzar que el diálogo esté al frente
    try:
        root.attributes('-topmost', True)
    except Exception:
        pass

    filetypes = [("Documentos", ("*.pdf", "*.docx", "*.pptx")), ("Todos los archivos", "*.*")]
    paths = filedialog.askopenfilenames(title='Seleccionar archivo(s) a procesar', initialdir=initial_dir or '.', filetypes=filetypes)
    root.destroy()

    # filedialog devuelve tupla; convertir a lista para consistencia
    return list(paths)

# --- 5. EJECUCIÓN ---
if __name__ == "__main__":
    col, fs, archivos_seleccionados = conectar_bd()
    
    if col is not None:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        raw_dir = os.path.join(base_dir, "data", "raw")

        if not archivos_seleccionados:
            print("⚠️ No se seleccionaron archivos. Saliendo.")
        else:
            for ruta in archivos_seleccionados:
                # Opcional: Verificar si ya existe para no duplicar
                archivo = os.path.basename(ruta)
                if col.find_one({"nombre_archivo": archivo}):
                    print(f"⏩ {archivo} ya existe.")
                else:
                    ingestar_archivo(ruta, col, fs)