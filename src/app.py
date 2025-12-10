import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from werkzeug.exceptions import BadRequest

# Nota: Para ejecutar la aplicación localmente usa la forma de módulo
# recomendada (por ejemplo `python -m src.app`) o `flask run`.
# No se incluye aquí un parche runtime que modifique `sys.path`.

from src.config import COLS, RAW_DIR, SECRET_KEY, DEBUG
from src.logging_config import setup_logging, get_logger
from src.database import get_database_connection
from src.web_utils import get_db, procesar_archivo_web, auto_etiquetar_bloom
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


@app.teardown_appcontext
def shutdown_database(exception=None):
    """
    Note: We do NOT close the database connection here.
    The singleton DatabaseConnection is designed to persist across requests
    and handle reconnection if the connection drops.
    Connection will be closed when the app process itself terminates.
    """
    pass


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
