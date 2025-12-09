import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from src.config import COLS, RAW_DIR, SECRET_KEY, DEBUG
from src.logging_config import setup_logging, get_logger
from src.database import get_database_connection
from src.web_utils import get_db, procesar_archivo_web, auto_etiquetar_bloom
from src.utils import validate_username, validate_password_strength

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
        usuario = request.form.get("usuario", "").strip()
        password = request.form.get("password", "").strip()
        nombre = request.form.get("nombre", "").strip()

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

        # Validar nombre no vacío
        if not nombre:
            flash("El nombre es requerido", "danger")
            return redirect(url_for("register"))

        # Verificar si existe
        if db[COLS["PERFIL"]].find_one({"usuario": usuario}):
            flash("El usuario ya existe", "danger")
            logger.warning(f"Registration attempt with existing user: {usuario}")
            return redirect(url_for("register"))

        # Crear usuario con password hasheado
        try:
            hashed_pw = generate_password_hash(password)
            db[COLS["PERFIL"]].insert_one(
                {
                    "usuario": usuario,
                    "password": hashed_pw,
                    "datos_personales": {"nombres": nombre},
                    "archivos_subidos": 0,
                }
            )
            flash("Registro exitoso. Por favor inicia sesión.", "success")
            logger.info(f"User registered successfully: {usuario}")
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
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(filepath)

            # 1. Ingesta (Extraer texto e imágenes)
            ok, msg = procesar_archivo_web(filepath, session["usuario"], db)

            if ok:
                flash(f"Archivo subido e ingestado correctamente ({msg} unidades).", "info")
                logger.info(f"File uploaded successfully by {session['usuario']}: {filename}")

                # 2. Etiquetado Automático Bloom (IA)
                flash("Iniciando análisis con IA (Bloom)... esto puede tardar unos segundos.", "warning")
                try:
                    processed_count = auto_etiquetar_bloom(session["usuario"], db)
                    flash(f"Análisis IA completado: {processed_count} documentos etiquetados.", "success")
                    logger.info(f"Bloom tagging completed for {session['usuario']}: {processed_count} items")
                except Exception as e:
                    flash(f"Error en análisis IA: {e}", "danger")
                    logger.error(f"Bloom tagging error for {session['usuario']}: {str(e)}")
            else:
                flash(f"Error procesando archivo: {msg}", "danger")
                logger.error(f"File processing error for {session['usuario']}: {msg}")

        except Exception as e:
            flash(f"Error durante la carga: {str(e)}", "danger")
            logger.error(f"Upload error for {session['usuario']}: {str(e)}")

    return redirect(url_for("dashboard"))


@app.teardown_appcontext
def shutdown_database(exception=None):
    """Close database connection on app shutdown."""
    try:
        db_connection.close()
        logger.info("Database connection closed")
    except Exception as e:
        logger.error(f"Error closing database: {str(e)}")


if __name__ == "__main__":
    try:
        app.run(debug=DEBUG, port=5000)
    except KeyboardInterrupt:
        logger.info("App interrupted by user")
    except Exception as e:
        logger.error(f"App error: {str(e)}")
        raise
