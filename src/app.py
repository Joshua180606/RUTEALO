import os
import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from werkzeug.exceptions import BadRequest
from bson.objectid import ObjectId

# Nota: Para ejecutar la aplicación localmente usa la forma de módulo
# recomendada (por ejemplo `python -m src.app`) o `flask run`.
# No se incluye aquí un parche runtime que modifique `sys.path`.

from src.config import COLS, RAW_DIR, SECRET_KEY, DEBUG
from src.logging_config import setup_logging, get_logger
from src.database import get_database_connection
from src.web_utils import (
    get_db,
    procesar_archivo_web,
    auto_etiquetar_bloom,
    generar_ruta_aprendizaje,
    procesar_multiples_archivos_web,
    obtener_rutas_usuario,
)
from src.models.evaluacion_zdp import (
    evaluar_examen_simple as procesar_respuesta_examen_web,
    obtener_perfil_zdp as obtener_perfil_estudiante_zdp,
)
from src.utils import validate_username, validate_password_strength, crear_carpeta_usuario, listar_archivos_usuario, obtener_ruta_archivo

# Configurar logging
is_production = not DEBUG
setup_logging(log_level="DEBUG" if DEBUG else "INFO", is_production=is_production)
logger = get_logger(__name__)

app = Flask(__name__)
app.secret_key = SECRET_KEY

# Configurar carpeta de subidas temporal
UPLOAD_FOLDER = RAW_DIR / "uploads"
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Inicializar conexión a base de datos
try:
    db_connection = get_database_connection()
    logger.info("Database connection initialized")
except Exception as e:
    logger.error(f"Failed to initialize database: {str(e)}")
    raise

db = get_db()


@app.route("/dump", methods=["GET", "POST"])
def dump_request():
    """Temporary debug endpoint to inspect incoming requests.
    - GET returns a short help message.
    - POST returns headers and form keys (password fields filtered).
    Use only for debugging; remove after diagnosis.
    """
    try:
        if request.method == "POST":
            # safe inspection: don't echo password values
            keys = list(request.form.keys()) if request.form else []
            filtered = [k for k in keys if k.lower() not in ("password", "password_confirm")]
            headers = {k: v for k, v in request.headers.items()}
            return jsonify({
                "method": "POST",
                "form_keys": filtered,
                "content_type": request.content_type,
                "content_length": request.content_length,
                "headers": headers,
            }), 200

        return jsonify({"message": "Dump endpoint active. POST form data to inspect keys."}), 200
    except Exception as e:
        logger.error(f"Error in /dump endpoint: {e}")
        return jsonify({"error": "internal"}), 500



@app.errorhandler(BadRequest)
def log_bad_request(e):
    """Log details about requests that caused a BadRequest before view handling.
    Helps debug malformed or rejected requests (without logging sensitive body data).
    """
    try:
        logger.error("BadRequest exception caught: %s", e)
        # Log useful request metadata (headers/cookies/content info) safely
        try:
            headers = {k: v for k, v in request.headers.items()}
            logger.error("Request headers: %s", headers)
        except Exception as _:
            logger.error("Could not read request headers")

        try:
            logger.error("Request cookies: %s", dict(request.cookies))
        except Exception:
            logger.error("Could not read request cookies")

        try:
            logger.error("Content-Type=%s Content-Length=%s", request.content_type, request.content_length)
        except Exception:
            logger.error("Could not read content metadata")

    except Exception as ex:
        logger.error("Error while logging BadRequest info: %s", ex)

    # Return a simple response; the user already sees 'Bad Request' in the browser.
    return "Bad Request", 400

# --- RUTAS DE AUTENTICACIÓN Y PÁGINAS ---


@app.route("/")
def index():
    # Si el usuario ya está logueado, va al dashboard
    if "usuario" in session:
        return redirect(url_for("dashboard"))
    # Si no, mostramos la nueva Landing Page
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # Debug: registrar metadatos de la request para diagnosticar 'Bad Request'
        try:
            logger.debug(f"Register POST content_type={request.content_type} content_length={request.content_length}")
            # Mostrar las claves recibidas, sin incluir campos de contraseña
            keys = list(request.form.keys()) if request.form else []
            filtered = [k for k in keys if k not in ("password", "password_confirm")]
            logger.debug(f"Register POST form keys (sin password): {filtered}")
        except Exception:
            logger.debug("Error al intentar leer metadatos de la request de registro")

        # Obtener datos personales
        usuario = request.form.get("usuario", "").strip()
        password = request.form.get("password", "").strip()
        password_confirm = request.form.get("password_confirm", "").strip()
        nombres = request.form.get("nombres", "").strip()
        apellidos = request.form.get("apellidos", "").strip()
        email = request.form.get("email", "").strip()
        telefono = request.form.get("telefono", "").strip()
        
        # Obtener preferencias
        tiempo_diario = request.form.get("tiempo_diario", "").strip()
        dia_descanso = request.form.get("dia_descanso", "").strip()
        
        # Validar términos
        terms = request.form.get("terms")

        # VALIDACIONES
        if not terms:
            flash("Debes aceptar los términos y condiciones", "danger")
            return redirect(url_for("register"))

        # Validar username
        if not validate_username(usuario):
            flash("Usuario debe tener entre 3 y 50 caracteres", "danger")
            logger.warning(f"Invalid username attempt: {usuario}")
            return redirect(url_for("register"))

        # Validar contraseña
        is_valid, msg = validate_password_strength(password)
        if not is_valid:
            flash(f"Contraseña débil: {msg}", "danger")
            logger.warning(f"Weak password attempt for user: {usuario}")
            return redirect(url_for("register"))

        # Validar que las contraseñas coinciden
        if password != password_confirm:
            flash("Las contraseñas no coinciden", "danger")
            return redirect(url_for("register"))

        # Validar datos personales
        if not nombres or not apellidos:
            flash("Nombres y apellidos son requeridos", "danger")
            return redirect(url_for("register"))

        if not email or "@" not in email:
            flash("Correo electrónico válido es requerido", "danger")
            return redirect(url_for("register"))

        if not telefono or not telefono.isdigit() or len(telefono) < 7:
            flash("Teléfono válido es requerido (mínimo 7 dígitos)", "danger")
            return redirect(url_for("register"))

        # Validar tiempo diario
        try:
            tiempo_diario_int = int(tiempo_diario)
            if tiempo_diario_int < 15 or tiempo_diario_int > 480:
                flash("Tiempo diario debe estar entre 15 y 480 minutos", "danger")
                return redirect(url_for("register"))
        except ValueError:
            flash("Tiempo diario debe ser un número válido", "danger")
            return redirect(url_for("register"))

        if not dia_descanso:
            flash("Debe seleccionar un día de descanso", "danger")
            return redirect(url_for("register"))

        # Verificar si el usuario ya existe
        if db[COLS["PERFIL"]].find_one({"usuario": usuario}):
            flash("El usuario ya existe", "danger")
            logger.warning(f"Registration attempt with existing user: {usuario}")
            return redirect(url_for("register"))

        # Verificar si el email ya existe
        if db[COLS["PERFIL"]].find_one({"datos_personales.email": email}):
            flash("Este correo ya está registrado", "danger")
            logger.warning(f"Registration attempt with existing email: {email}")
            return redirect(url_for("register"))

        # Crear usuario con todos los datos
        try:
            from datetime import datetime, timezone
            
            hashed_pw = generate_password_hash(password)
            
            user_doc = {
                "usuario": usuario,
                "password": hashed_pw,
                "datos_personales": {
                    "nombres": nombres,
                    "apellidos": apellidos,
                    "email": email,
                    "telefono": telefono,
                },
                "preferencias": {
                    "tiempo_diario": str(tiempo_diario_int),  # En minutos como string (convertible a horas)
                    "dia_descanso": dia_descanso,
                    "nivel_actual_bloom": "No iniciado",
                    "ultima_actualizacion": datetime.now(timezone.utc),
                },
                "archivos_subidos": 0,
                "fecha_registro": datetime.now(timezone.utc),
            }
            
            db[COLS["PERFIL"]].insert_one(user_doc)
            flash("Registro exitoso. Por favor inicia sesión.", "success")
            logger.info(f"User registered successfully: {usuario} ({email})")
            return redirect(url_for("login"))
            
        except Exception as e:
            flash("Error durante el registro. Intenta de nuevo.", "danger")
            logger.error(f"Registration error for {usuario}: {str(e)}")
            return redirect(url_for("register"))

    return render_template("register.html")



@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form.get("usuario", "").strip()
        password = request.form.get("password", "").strip()

        # Validar entrada básica
        if not usuario or not password:
            flash("Usuario y contraseña son requeridos", "danger")
            logger.warning("Login attempt with missing credentials")
            return redirect(url_for("login"))

        try:
            user_data = db[COLS["PERFIL"]].find_one({"usuario": usuario})

            if user_data and check_password_hash(user_data.get("password", ""), password):
                session["usuario"] = usuario
                session["nombre"] = user_data.get("datos_personales", {}).get("nombres", usuario)
                logger.info(f"User logged in successfully: {usuario}")
                return redirect(url_for("dashboard"))
            else:
                flash("Usuario o contraseña incorrectos", "danger")
                logger.warning(f"Failed login attempt for user: {usuario}")
        except Exception as e:
            flash("Error durante el login. Intenta de nuevo.", "danger")
            logger.error(f"Login error for {usuario}: {str(e)}")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))  # Redirige a la landing page al salir


# --- RUTAS PRINCIPALES ---


@app.route("/dashboard")
def dashboard():
    if "usuario" not in session:
        return redirect(url_for("login"))

    # Obtener archivos del usuario
    docs = list(
        db[COLS["RAW"]].find(
            {"usuario_propietario": session["usuario"]},
            {"nombre_archivo": 1, "estado_procesamiento": 1, "fecha_ingesta": 1},
        )
    )

    return render_template("dashboard.html", usuario=session["usuario"], nombre=session["nombre"], archivos=docs)


@app.route("/upload", methods=["POST"])
def upload_file():
    if "usuario" not in session:
        return redirect(url_for("login"))

    if "file" not in request.files:
        flash("No se seleccionó archivo", "warning")
        return redirect(url_for("dashboard"))

    file = request.files["file"]
    if file.filename == "":
        flash("Nombre de archivo vacío", "warning")
        return redirect(url_for("dashboard"))

    # Validar tipo de archivo
    ALLOWED_EXTENSIONS = {".pdf", ".docx", ".pptx"}
    file_ext = os.path.splitext(file.filename)[1].lower()

    if file_ext not in ALLOWED_EXTENSIONS:
        flash(f'Tipo de archivo no permitido. Se aceptan: {", ".join(ALLOWED_EXTENSIONS)}', "danger")
        logger.warning(f"Upload attempt with invalid file type: {file_ext} by {session['usuario']}")
        return redirect(url_for("dashboard"))

    # Validar tamaño máximo (50MB)
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)

    if file_size > MAX_FILE_SIZE:
        flash(f"Archivo demasiado grande (máx: 50MB, subiste: {file_size / 1024 / 1024:.1f}MB)", "danger")
        logger.warning(f"Upload attempt with oversized file by {session['usuario']}: {file_size} bytes")
        return redirect(url_for("dashboard"))

    if file:
        try:
            # Crear carpeta del usuario si no existe
            usuario = session["usuario"]
            crear_carpeta_usuario(usuario, str(app.config["UPLOAD_FOLDER"]))
            
            # Guardar archivo en la carpeta del usuario
            filename = secure_filename(file.filename)
            usuario_folder = os.path.join(str(app.config["UPLOAD_FOLDER"]), usuario)
            filepath = os.path.join(usuario_folder, filename)
            file.save(filepath)

            # 1. Ingesta (Extraer texto e imágenes)
            ok, msg = procesar_archivo_web(filepath, usuario, db)

            if ok:
                flash(f"Archivo subido e ingestado correctamente ({msg} unidades).", "info")
                logger.info(f"File uploaded successfully by {usuario}: {filename}")

                # 2. Etiquetado Automático Bloom (IA)
                flash("Iniciando análisis con IA (Bloom)... esto puede tardar unos segundos.", "warning")
                try:
                    processed_count = auto_etiquetar_bloom(usuario, db)
                    flash(f"Análisis IA completado: {processed_count} documentos etiquetados.", "success")
                    logger.info(f"Bloom tagging completed for {usuario}: {processed_count} items")

                    # Generar ruta de aprendizaje y examen inicial con el nuevo material
                    try:
                        msg_ruta = generar_ruta_aprendizaje(usuario, db)
                        flash(msg_ruta, "info")
                        logger.info(f"Ruta/aprendizaje generada para {usuario}: {msg_ruta}")
                    except Exception as ex:
                        flash(f"No se pudo generar la ruta/aprendizaje: {ex}", "warning")
                        logger.error(f"Error generando ruta para {usuario}: {ex}")
                except Exception as e:
                    flash(f"Error en análisis IA: {e}", "danger")
                    logger.error(f"Bloom tagging error for {usuario}: {str(e)}")
            else:
                flash(f"Error procesando archivo: {msg}", "danger")
                logger.error(f"File processing error for {usuario}: {msg}")

        except Exception as e:
            flash(f"Error durante la carga: {str(e)}", "danger")
            logger.error(f"Upload error for {session['usuario']}: {str(e)}")

    return redirect(url_for("dashboard"))


@app.route("/files")
def list_user_files():
    """
    Retorna JSON con lista de archivos del usuario.
    Endpoint GET para obtener archivos del usuario autenticado.
    """
    if "usuario" not in session:
        return {"error": "Unauthorized"}, 401

    usuario = session["usuario"]
    archivos = listar_archivos_usuario(usuario, str(app.config["UPLOAD_FOLDER"]))
    
    return {
        "usuario": usuario,
        "archivos": archivos,
        "total": len(archivos)
    }, 200


@app.route("/download/<archivo>")
def download_file(archivo):
    """
    Descarga un archivo del usuario.
    Valida que el usuario tenga acceso al archivo antes de descargarlo.
    """
    if "usuario" not in session:
        return redirect(url_for("login"))

    usuario = session["usuario"]
    ruta_archivo = obtener_ruta_archivo(usuario, archivo, str(app.config["UPLOAD_FOLDER"]))
    
    if not ruta_archivo:
        flash("No tienes acceso a este archivo", "danger")
        logger.warning(f"Unauthorized download attempt by {usuario} for {archivo}")
        return redirect(url_for("dashboard"))

    try:
        from flask import send_file
        logger.info(f"Download initiated by {usuario}: {archivo}")
        return send_file(ruta_archivo, as_attachment=True)
    except Exception as e:
        flash(f"Error descargando archivo: {str(e)}", "danger")
        logger.error(f"Download error for {usuario}: {str(e)}")
        return redirect(url_for("dashboard"))


@app.route("/ruta/estado")
def estado_ruta():
    if "usuario" not in session:
        return {"error": "Unauthorized"}, 401

    usuario = session["usuario"]

    # Perfil ZDP
    perfil = obtener_perfil_estudiante_zdp(usuario)

    # Examen inicial
    exam_doc = db[COLS["EXAM_INI"]].find_one({"usuario": usuario})
    examen_pendiente = not exam_doc or exam_doc.get("estado") != "COMPLETADO"

    # Ruta
    ruta_doc = db[COLS["RUTAS"]].find_one({"usuario": usuario}) or {}

    return {
        "usuario": usuario,
        "examen_pendiente": examen_pendiente,
        "examen_generado": bool(exam_doc),
        "perfil_zdp": perfil,
        "ruta": {
            "estructura": ruta_doc.get("estructura_ruta"),
            "metadatos": ruta_doc.get("metadatos_ruta"),
        },
    }, 200


@app.route("/ruta/<ruta_id>/contenido")
def obtener_contenido_ruta(ruta_id):
    """Obtener contenido de una ruta específica por ID"""
    if "usuario" not in session:
        return {"error": "Unauthorized"}, 401

    usuario = session["usuario"]

    try:
        from bson import ObjectId
        ruta_obj_id = ObjectId(ruta_id)
    except Exception:
        return {"error": "ID de ruta inválido"}, 400

    # Buscar ruta y verificar ownership
    ruta_doc = db[COLS["RUTAS"]].find_one({"_id": ruta_obj_id, "usuario": usuario})
    if not ruta_doc:
        return {"error": "Ruta no encontrada"}, 404

    # Adjuntar información del test inicial (para decidir qué omitir o no)
    exam_doc = db[COLS["EXAM_INI"]].find_one({"usuario": usuario})
    test_info = None
    if exam_doc:
        examenes = exam_doc.get("contenido", {}).get("EXAMENES", {})
        exam_inicial = examenes.get("EXAMEN_INICIAL") if isinstance(examenes, dict) else None
        test_info = {
            "estado": exam_doc.get("estado", "PENDIENTE"),
            "origen": exam_doc.get("origen", "desconocido"),
            "fecha_generacion": exam_doc.get("fecha_generacion"),
            "preguntas": len(exam_inicial) if isinstance(exam_inicial, list) else 0,
        }

    return {
        "ruta_id": str(ruta_doc["_id"]),
        "nombre": ruta_doc.get("nombre_ruta", "Sin nombre"),
        "descripcion": ruta_doc.get("descripcion", ""),
        "estado": ruta_doc.get("estado", "ACTIVA"),
        "estructura": ruta_doc.get("estructura_ruta"),
        "metadatos": ruta_doc.get("metadatos_ruta"),
        "archivos_fuente": ruta_doc.get("archivos_fuente", []),
        "fecha_creacion": ruta_doc.get("fecha_creacion"),
        "fecha_actualizacion": ruta_doc.get("fecha_actualizacion"),
        "test_inicial": test_info,
    }, 200


@app.route("/examen-inicial")
def obtener_examen_inicial():
    if "usuario" not in session:
        return {"error": "Unauthorized"}, 401

    usuario = session["usuario"]
    exam_doc = db[COLS["EXAM_INI"]].find_one({"usuario": usuario})
    if not exam_doc:
        return {"error": "No hay examen generado"}, 404

    return {
        "usuario": usuario,
        "estado": exam_doc.get("estado", "PENDIENTE"),
        "contenido": exam_doc.get("contenido", {}),
        "fecha_generacion": exam_doc.get("fecha_generacion"),
    }, 200


@app.route("/examen-inicial/responder", methods=["POST"])
def responder_examen_inicial():
    if "usuario" not in session:
        return {"error": "Unauthorized"}, 401

    usuario = session["usuario"]
    data = request.get_json(silent=True) or {}
    respuestas = data.get("respuestas")

    if not respuestas or not isinstance(respuestas, list):
        return {"error": "Faltan respuestas"}, 400

    exam_doc = db[COLS["EXAM_INI"]].find_one({"usuario": usuario})
    if not exam_doc:
        return {"error": "No hay examen inicial generado"}, 404

    resultado = procesar_respuesta_examen_web(usuario, respuestas, exam_doc.get("contenido", {}))

    # Normalizar posibles errores
    if resultado.get("status", 200) != 200 or resultado.get("error"):
        status = resultado.get("status", 500)
        return {"error": resultado.get("error", "Error evaluando examen")}, status

    # Marcar examen como completado
    try:
        import datetime

        db[COLS["EXAM_INI"]].update_one(
            {"usuario": usuario},
            {"$set": {"estado": "COMPLETADO", "fecha_completado": datetime.datetime.utcnow()}},
        )
    except Exception as e:
        logger.error(f"No se pudo marcar examen como completado para {usuario}: {e}")
    
    # NUEVO: Actualizar metadata de ruta con información ZDP
    try:
        # Extraer niveles competentes del resultado
        competentes = [
            nivel for nivel, datos in resultado.get("resumen_por_nivel", {}).items()
            if datos.get("competente", False)
        ]
        
        zona_proxima = resultado.get("zona_proxima", [])
        
        # Actualizar metadata de la ruta del usuario
        db[COLS["RUTAS"]].update_one(
            {"usuario": usuario},
            {
                "$set": {
                    "metadatos_ruta.niveles_competentes": competentes,
                    "metadatos_ruta.zona_proxima": zona_proxima,
                    "metadatos_ruta.personalizada_zdp": True,
                    "metadatos_ruta.fecha_evaluacion_zdp": datetime.datetime.utcnow()
                }
            }
        )
        logger.info(f"✅ Metadata ZDP actualizada para {usuario}: competentes={competentes}, ZDP={zona_proxima}")
    except Exception as e:
        logger.error(f"⚠️ No se pudo actualizar metadata ZDP en ruta: {e}")

    return {"resultado": resultado}, 200


# --- NUEVOS ENDPOINTS PARA REDISEÑO DASHBOARD ---


@app.route("/api/perfil-zdp")
def obtener_perfil_zdp_api():
    """
    Retorna el perfil ZDP del usuario autenticado.
    
    Response:
        200: {
            "nivel_actual": str | null,
            "zona_proxima": [str],
            "niveles_competentes": [str],
            "brechas": [str],
            "puntaje_total": float
        }
        401: { "error": "Unauthorized" }
    """
    if "usuario" not in session:
        return {"error": "Unauthorized"}, 401
    
    usuario = session["usuario"]
    
    try:
        perfil = obtener_perfil_estudiante_zdp(usuario)
        
        # Si no hay evaluación previa, retornar vacío
        if not perfil or perfil.get("estado") == "Sin evaluación realizada":
            return {
                "nivel_actual": None,
                "zona_proxima": [],
                "niveles_competentes": [],
                "brechas": [],
                "puntaje_total": 0
            }, 200
        
        # Extraer niveles competentes (>= 70%)
        competentes = [
            nivel for nivel, datos in perfil.get("competencias", {}).items()
            if datos.get("competente", False)
        ]
        
        # Extraer brechas (< 70%)
        brechas = [
            nivel for nivel, datos in perfil.get("competencias", {}).items()
            if not datos.get("competente", False)
        ]
        
        return {
            "nivel_actual": perfil.get("nivel_actual"),
            "zona_proxima": perfil.get("zona_proxima", []),
            "niveles_competentes": competentes,
            "brechas": brechas,
            "puntaje_total": perfil.get("puntaje", 0),
            "recomendaciones": perfil.get("recomendaciones", [])
        }, 200
    
    except Exception as e:
        logger.error(f"Error obteniendo perfil ZDP para {usuario}: {e}")
        return {"error": "Error obteniendo perfil ZDP"}, 500


@app.route("/rutas/lista", methods=["GET"])
def listar_rutas():
    """
    Retorna lista de rutas del usuario autenticado.
    
    Response:
        200: { "rutas": [...], "total": number }
        401: { "error": "Unauthorized" }
    """
    if "usuario" not in session:
        return {"error": "Unauthorized"}, 401
    
    usuario = session["usuario"]
    
    try:
        rutas = obtener_rutas_usuario(usuario, db)
        
        return {
            "rutas": rutas,
            "total": len(rutas)
        }, 200
    
    except Exception as e:
        logger.error(f"Error listando rutas para {usuario}: {e}")
        return {"error": "Error cargando rutas"}, 500


@app.route("/crear-ruta", methods=["POST"])
def crear_ruta():
    """
    Crea una nueva ruta de aprendizaje con múltiples archivos.
    
    Form Data:
        nombre_ruta: str (required, max 100)
        descripcion: str (optional, max 500)
        archivos: FileStorage[] (required, 1+)
    
    Response:
        201: { "ruta_id": "...", "nombre_ruta": "...", "estado": "...", "mensaje": "..." }
        400: { "error": "..." }
        409: { "error": "Nombre ya existe" }
    """
    if "usuario" not in session:
        return {"error": "Unauthorized"}, 401
    
    usuario = session["usuario"]
    nombre_ruta = request.form.get("nombre_ruta", "").strip()
    descripcion = request.form.get("descripcion", "").strip()
    
    # VALIDACIONES
    # 1. Validar nombre
    if not nombre_ruta:
        return {"error": "Nombre de ruta requerido"}, 400
    
    if len(nombre_ruta) > 100:
        return {"error": "Nombre muy largo (máx 100 caracteres)"}, 400
    
    # 2. Validar descripción
    if len(descripcion) > 500:
        return {"error": "Descripción muy larga (máx 500 caracteres)"}, 400
    
    # 3. Validar archivos
    if "archivos" not in request.files:
        return {"error": "No se seleccionaron archivos"}, 400
    
    archivos = request.files.getlist("archivos")
    if not archivos or all(f.filename == "" for f in archivos):
        return {"error": "Al menos un archivo requerido"}, 400
    
    # 4. Validar nombre único por usuario
    col_rutas = db[COLS["RUTAS"]]
    if col_rutas.find_one({"usuario": usuario, "nombre_ruta": nombre_ruta}):
        return {"error": "Ya existe una ruta con ese nombre"}, 409
    
    # PROCESAR ARCHIVOS
    archivos_procesados = []
    archivos_rutas = []
    ALLOWED_EXTENSIONS = {".pdf", ".docx", ".pptx"}
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    
    try:
        # Crear carpeta usuario si no existe
        crear_carpeta_usuario(usuario, str(app.config["UPLOAD_FOLDER"]))
        usuario_folder = os.path.join(str(app.config["UPLOAD_FOLDER"]), usuario)
        
        # Procesar cada archivo
        for archivo in archivos:
            # Validar nombre
            if archivo.filename == "":
                continue
            
            # Validar extensión
            filename = secure_filename(archivo.filename)
            ext = os.path.splitext(filename)[1].lower()
            
            if ext not in ALLOWED_EXTENSIONS:
                return {
                    "error": f"Tipo de archivo no permitido: {ext}"
                }, 400
            
            # Validar tamaño
            archivo.seek(0, os.SEEK_END)
            file_size = archivo.tell()
            archivo.seek(0)
            
            if file_size > MAX_FILE_SIZE:
                return {
                    "error": f"Archivo {filename} demasiado grande (máx 50MB)"
                }, 400
            
            # Guardar archivo
            filepath = os.path.join(usuario_folder, filename)
            archivo.save(filepath)
            
            # Registrar para procesamiento
            archivos_rutas.append(filepath)
            archivos_procesados.append({
                "nombre_archivo": filename,
                "tamaño": file_size / 1024 / 1024,  # MB
                "fecha_subida": datetime.datetime.utcnow(),
                "tipo": ext.replace(".", "")
            })
        
        if not archivos_rutas:
            return {"error": "No se pudieron procesar los archivos"}, 400
        
        # Crear carpeta específica para esta ruta
        nombre_ruta_safe = secure_filename(nombre_ruta.replace(" ", "_"))
        ruta_folder = os.path.join(str(app.config["UPLOAD_FOLDER"]), usuario, nombre_ruta_safe)
        os.makedirs(ruta_folder, exist_ok=True)
        
        # Mover archivos a la carpeta de la ruta
        archivos_rutas_final = []
        for i, archivo_path in enumerate(archivos_rutas):
            nuevo_path = os.path.join(ruta_folder, os.path.basename(archivo_path))
            os.rename(archivo_path, nuevo_path)
            archivos_rutas_final.append(nuevo_path)
            archivos_procesados[i]["ruta_relativa"] = f"{usuario}/{nombre_ruta_safe}/{os.path.basename(archivo_path)}"
        
        # PROCESAR CONTENIDO (multiple files)
        ok, resultados, msg_ingesta = procesar_multiples_archivos_web(
            archivos_rutas_final, usuario, db
        )
        
        if not ok:
            return {
                "error": f"Error procesando archivos: {msg_ingesta}"
            }, 400
        
        # ETIQUETADO BLOOM
        try:
            processed_count = auto_etiquetar_bloom(usuario, db)
            logger.info(f"Bloom tagging: {processed_count} documentos para {usuario}")
        except Exception as e:
            logger.warning(f"Bloom tagging error para {usuario}: {e}")
        
        # GENERAR RUTA Y EXAMEN
        try:
            msg_ruta = generar_ruta_aprendizaje(usuario, db)
            logger.info(f"Ruta generada para {usuario}: {msg_ruta}")
        except Exception as e:
            return {
                "error": f"Error generando ruta: {str(e)}"
            }, 500
        
        # CREAR/ACTUALIZAR DOCUMENTO DE RUTA CON METADATA
        ruta_existente = col_rutas.find_one({"usuario": usuario})
        
        ruta_doc = {
            "usuario": usuario,
            "nombre_ruta": nombre_ruta,
            "descripcion": descripcion,
            "estado": "ACTIVA",
            "archivos_fuente": archivos_procesados,
            "fecha_creacion": datetime.datetime.utcnow(),
            "fecha_actualizacion": datetime.datetime.utcnow(),
        }
        
        # Agregar estructura y metadatos existentes si hay
        if ruta_existente:
            ruta_doc["estructura_ruta"] = ruta_existente.get("estructura_ruta", {})
            ruta_doc["metadatos_ruta"] = ruta_existente.get("metadatos_ruta", {})
            ruta_doc["progreso_global"] = ruta_existente.get("progreso_global", 0)
        
        resultado = col_rutas.replace_one(
            {"usuario": usuario},
            ruta_doc,
            upsert=True
        )
        
        # Obtener ruta_id
        if resultado.upserted_id:
            ruta_id = str(resultado.upserted_id)
        else:
            ruta_id = str(ruta_existente["_id"])
        
        # Verificar si hay test inicial pendiente
        exam_doc = db[COLS["EXAM_INI"]].find_one({"usuario": usuario})
        estado_examen = "TEST_PENDIENTE" if not exam_doc or exam_doc.get("estado") != "COMPLETADO" else "ACTIVA"
        
        return {
            "ruta_id": ruta_id,
            "nombre_ruta": nombre_ruta,
            "estado": estado_examen,
            "mensaje": msg_ruta,
            "archivos_procesados": len(archivos_procesados)
        }, 201
    
    except Exception as e:
        logger.error(f"Error creando ruta para {usuario}: {e}")
        return {
            "error": f"Error al crear ruta: {str(e)}"
        }, 500


@app.route("/ruta/<ruta_id>/actualizar", methods=["PUT"])
def actualizar_ruta(ruta_id):
    """
    Actualiza nombre y/o descripción de una ruta.
    
    JSON Body:
        { "nombre_ruta": "str (optional)", "descripcion": "str (optional)", "estado": "enum (optional)" }
    
    Response:
        200: { "mensaje": "Actualizado exitosamente" }
        400: { "error": "..." }
        404: { "error": "Ruta no encontrada" }
    """
    if "usuario" not in session:
        return {"error": "Unauthorized"}, 401
    
    usuario = session["usuario"]
    
    try:
        ruta_id_obj = ObjectId(ruta_id)
    except:
        return {"error": "ID de ruta inválido"}, 400
    
    # Obtener datos a actualizar
    data = request.get_json(silent=True) or {}
    updates = {}
    
    # Validar y agregar campos
    if "nombre_ruta" in data:
        nombre = data["nombre_ruta"].strip()
        if not nombre:
            return {"error": "Nombre no puede estar vacío"}, 400
        if len(nombre) > 100:
            return {"error": "Nombre muy largo"}, 400
        updates["nombre_ruta"] = nombre
    
    if "descripcion" in data:
        desc = data["descripcion"].strip()
        if len(desc) > 500:
            return {"error": "Descripción muy larga"}, 400
        updates["descripcion"] = desc
    
    if "estado" in data:
        estado = data["estado"]
        if estado not in ["ACTIVA", "PAUSADA", "COMPLETADA"]:
            return {"error": "Estado inválido"}, 400
        updates["estado"] = estado
    
    if not updates:
        return {"error": "No hay campos para actualizar"}, 400
    
    # Validar que sea propietario
    col_rutas = db[COLS["RUTAS"]]
    ruta = col_rutas.find_one({
        "_id": ruta_id_obj,
        "usuario": usuario
    })
    
    if not ruta:
        return {"error": "Ruta no encontrada"}, 404
    
    # Actualizar
    try:
        updates["fecha_actualizacion"] = datetime.datetime.utcnow()
        
        result = col_rutas.update_one(
            {"_id": ruta_id_obj, "usuario": usuario},
            {"$set": updates}
        )
        
        if result.matched_count == 0:
            return {"error": "Ruta no encontrada"}, 404
        
        return {
            "mensaje": "Ruta actualizada exitosamente",
            "campos_actualizados": list(updates.keys())
        }, 200
    
    except Exception as e:
        logger.error(f"Error actualizando ruta {ruta_id}: {e}")
        return {"error": "Error al actualizar"}, 500


@app.route("/ruta/<ruta_id>", methods=["DELETE"])
def eliminar_ruta(ruta_id):
    """
    Elimina una ruta de aprendizaje.
    
    Response:
        200: { "mensaje": "Ruta eliminada" }
        404: { "error": "Ruta no encontrada" }
    """
    if "usuario" not in session:
        return {"error": "Unauthorized"}, 401
    
    usuario = session["usuario"]
    
    try:
        ruta_id_obj = ObjectId(ruta_id)
    except:
        return {"error": "ID de ruta inválido"}, 400
    
    try:
        col_rutas = db[COLS["RUTAS"]]
        
        result = col_rutas.delete_one({
            "_id": ruta_id_obj,
            "usuario": usuario
        })
        
        if result.deleted_count == 0:
            return {"error": "Ruta no encontrada"}, 404
        
        return {
            "mensaje": "Ruta eliminada exitosamente"
        }, 200
    
    except Exception as e:
        logger.error(f"Error eliminando ruta {ruta_id}: {e}")
        return {"error": "Error al eliminar"}, 500


@app.route("/ruta/<ruta_id>/regenerar-test", methods=["POST"])
def regenerar_test_ruta(ruta_id):
    """Regenera el test diagnóstico de una ruta con las nuevas preguntas basadas en contenido"""
    if "usuario" not in session:
        return {"error": "Unauthorized"}, 401

    usuario = session["usuario"]

    try:
        from bson import ObjectId
        ruta_obj_id = ObjectId(ruta_id)
    except Exception:
        return {"error": "ID de ruta inválido"}, 400

    # Verificar que la ruta existe y pertenece al usuario
    ruta_doc = db[COLS["RUTAS"]].find_one({"_id": ruta_obj_id, "usuario": usuario})
    if not ruta_doc:
        return {"error": "Ruta no encontrada"}, 404

    try:
        # Forzar regeneración del test y ruta
        msg_ruta = generar_ruta_aprendizaje(usuario, db)
        logger.info(f"Test regenerado para usuario {usuario}: {msg_ruta}")
        
        return {
            "mensaje": "Test diagnóstico regenerado exitosamente",
            "detalle": msg_ruta
        }, 200
    
    except Exception as e:
        logger.error(f"Error regenerando test para {ruta_id}: {e}")
        return {"error": f"Error al regenerar test: {str(e)}"}, 500


@app.route("/ruta/<ruta_id>/fuentes")
def obtener_fuentes_ruta(ruta_id):
    """Obtener archivos fuente de una ruta específica"""
    if "usuario" not in session:
        return {"error": "Unauthorized"}, 401

    usuario = session["usuario"]

    try:
        from bson import ObjectId
        ruta_obj_id = ObjectId(ruta_id)
    except Exception:
        return {"error": "ID de ruta inválido"}, 400

    # Buscar ruta y verificar ownership
    ruta_doc = db[COLS["RUTAS"]].find_one({"_id": ruta_obj_id, "usuario": usuario})
    if not ruta_doc:
        return {"error": "Ruta no encontrada"}, 404

    archivos_fuente = ruta_doc.get("archivos_fuente", [])

    return {
        "ruta_id": str(ruta_doc["_id"]),
        "nombre_ruta": ruta_doc.get("nombre_ruta", "Sin nombre"),
        "archivos": archivos_fuente,
        "total": len(archivos_fuente),
    }, 200


@app.teardown_appcontext
def shutdown_database(exception=None):
    """
    Note: We do NOT close the database connection here.
    The singleton DatabaseConnection is designed to persist across requests
    and handle reconnection if the connection drops.
    Connection will be closed when the app process itself terminates.
    """
    pass


# ==================== ENDPOINTS DEL CHATBOT MULTILINGÜE ====================

@app.route('/api/transcribir-audio', methods=['POST'])
def transcribir_audio():
    """
    Transcribe audio a texto usando OpenAI Whisper API.
    Soporta 3 idiomas: Español (es), Inglés (en), Quechua (qu)
    """
    if 'user' not in session:
        return jsonify({"error": "No autenticado"}), 401
    
    try:
        # Validar que se envió un archivo
        if 'audio' not in request.files:
            return jsonify({"error": "No se envió archivo de audio"}), 400
        
        audio_file = request.files['audio']
        idioma = request.form.get('idioma', 'es')
        
        if audio_file.filename == '':
            return jsonify({"error": "Archivo vacío"}), 400
        
        # Validar tamaño (max 10MB)
        audio_file.seek(0, 2)  # Ir al final
        size = audio_file.tell()
        audio_file.seek(0)  # Volver al inicio
        
        if size > 10 * 1024 * 1024:
            return jsonify({"error": "Archivo muy grande (máximo 10MB)"}), 413
        
        # Importar OpenAI solo si se usa el endpoint
        try:
            from openai import OpenAI
        except ImportError:
            return jsonify({
                "error": "OpenAI no está instalado. Ejecuta: pip install openai>=1.0.0"
            }), 500
        
        # Mapear idiomas a códigos Whisper
        idioma_map = {
            'es': 'es',  # Español
            'en': 'en',  # Inglés
            'qu': 'qu'   # Quechua
        }
        
        codigo_idioma = idioma_map.get(idioma, 'es')
        
        # Obtener API key de OpenAI
        openai_key = os.getenv('OPENAI_API_KEY')
        if not openai_key:
            return jsonify({
                "error": "OPENAI_API_KEY no configurada."
            }), 500
        
        # Transcribir con Whisper
        client = OpenAI(api_key=openai_key)
        
        try:
            transcription = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language=codigo_idioma
            )
            
            logger.info(f"Audio transcrito ({idioma}): {transcription.text[:100]}...")
            
            return jsonify({
                "texto": transcription.text,
                "idioma_detectado": idioma,
                "exito": True
            })
        
        except Exception as whisper_error:
            logger.error(f"Error en Whisper API: {whisper_error}")
            return jsonify({
                "error": f"Error transcribiendo audio: {str(whisper_error)}"
            }), 500
        
    except Exception as e:
        logger.error(f"Error en transcripción de audio: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/chatbot', methods=['POST'])
def chatbot():
    """
    Chatbot tutor con contexto de ruta en 3 idiomas.
    Usa Google Gemini para generar respuestas pedagógicas.
    """
    if 'user' not in session:
        return jsonify({"error": "No autenticado"}), 401
    
    try:
        data = request.json
        mensaje = data.get('mensaje', '').strip()
        ruta_id = data.get('ruta_id')
        idioma = data.get('idioma', 'es')
        historial = data.get('historial', [])
        
        # Validaciones
        if not mensaje:
            return jsonify({"error": "Mensaje vacío"}), 400
        
        if not ruta_id:
            return jsonify({"error": "No se especificó ruta_id"}), 400
        
        if idioma not in ['es', 'en', 'qu']:
            return jsonify({"error": "Idioma no soportado. Use: es, en, qu"}), 400
        
        # Importar y crear tutor con contexto
        from src.models.chatbot_tutor import TutorVirtual
        
        tutor = TutorVirtual(
            ruta_id=ruta_id,
            usuario=session['user'],
            idioma=idioma
        )
        
        # Verificar que se cargó el contexto
        if not tutor.contexto_ruta:
            errores = {
                'es': "No pude cargar el contexto de tu ruta. Verifica que la ruta exista.",
                'en': "I couldn't load your path context. Verify that the path exists.",
                'qu': "Manan atinichu kargayta ñanniykita. Qawariykuy ñanniyki kasqanta."
            }
            return jsonify({
                "respuesta": errores.get(idioma, errores['es']),
                "idioma": idioma,
                "exito": False
            })
        
        # Generar respuesta
        logger.info(f"Chatbot ({idioma}): {mensaje[:100]}...")
        respuesta = tutor.responder(mensaje, historial)
        
        logger.info(f"Respuesta generada ({idioma}): {respuesta[:100]}...")
        
        return jsonify({
            "respuesta": respuesta,
            "idioma": idioma,
            "exito": True
        })
        
    except Exception as e:
        logger.error(f"Error en chatbot: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    # Compute host/port from environment or defaults so we can print the URL explicitly.
    host = os.getenv("FLASK_RUN_HOST", "127.0.0.1")
    port = int(os.getenv("PORT", os.getenv("FLASK_RUN_PORT", "5000")))

    url = f"http://{host}:{port}"
    # Log and print the URL so it's visible in the terminal (helps when Flask's built-in message is not shown).
    logger.info(f"App will be available at {url}")
    # Also print to stdout to make it obvious in simple terminals
    print(f"==> RUTEALO running at {url} (CTRL+C to stop)")

    try:
        app.run(debug=DEBUG, port=port, host=host)
    except KeyboardInterrupt:
        logger.info("App interrupted by user")
    except Exception as e:
        logger.error(f"App error: {str(e)}")
        raise
