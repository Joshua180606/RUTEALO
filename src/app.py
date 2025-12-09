import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from src.config import MONGO_URI, DB_NAME, COLS, RAW_DIR, SECRET_KEY
from src.web_utils import get_db, procesar_archivo_web, auto_etiquetar_bloom

# Cargar variables de entorno
load_dotenv('claves.env')

app = Flask(__name__)
app.secret_key = SECRET_KEY

# Configurar carpeta de subidas temporal
UPLOAD_FOLDER = RAW_DIR / "uploads"
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

db = get_db()

# --- RUTAS DE AUTENTICACIÓN Y PÁGINAS ---

@app.route('/')
def index():
    # Si el usuario ya está logueado, va al dashboard
    if 'usuario' in session:
        return redirect(url_for('dashboard'))
    # Si no, mostramos la nueva Landing Page
    return render_template('landing.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        usuario = request.form['usuario']
        password = request.form['password']
        nombre = request.form['nombre']
        
        # Verificar si existe
        if db[COLS["PERFIL"]].find_one({"usuario": usuario}):
            flash('El usuario ya existe', 'danger')
            return redirect(url_for('register'))
        
        # Crear usuario con password hasheado
        hashed_pw = generate_password_hash(password)
        db[COLS["PERFIL"]].insert_one({
            "usuario": usuario,
            "password": hashed_pw,
            "datos_personales": {"nombres": nombre},
            "archivos_subidos": 0
        })
        
        flash('Registro exitoso. Por favor inicia sesión.', 'success')
        return redirect(url_for('login'))
        
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        password = request.form['password']
        
        user_data = db[COLS["PERFIL"]].find_one({"usuario": usuario})
        
        if user_data and check_password_hash(user_data.get('password', ''), password):
            session['usuario'] = usuario
            session['nombre'] = user_data.get('datos_personales', {}).get('nombres', usuario)
            return redirect(url_for('dashboard'))
        else:
            flash('Usuario o contraseña incorrectos', 'danger')
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))  # Redirige a la landing page al salir

# --- RUTAS PRINCIPALES ---

@app.route('/dashboard')
def dashboard():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    # Obtener archivos del usuario
    docs = list(db[COLS["RAW"]].find(
        {"usuario_propietario": session['usuario']},
        {"nombre_archivo": 1, "estado_procesamiento": 1, "fecha_ingesta": 1}
    ))
    
    return render_template('dashboard.html', usuario=session['usuario'], nombre=session['nombre'], archivos=docs)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    if 'file' not in request.files:
        flash('No se seleccionó archivo', 'warning')
        return redirect(url_for('dashboard'))
        
    file = request.files['file']
    if file.filename == '':
        flash('Nombre de archivo vacío', 'warning')
        return redirect(url_for('dashboard'))
        
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # 1. Ingesta (Extraer texto e imágenes)
        ok, msg = procesar_archivo_web(filepath, session['usuario'], db)
        
        if ok:
            flash(f'Archivo subido e ingestado correctamente ({msg} unidades).', 'info')
            
            # 2. Etiquetado Automático Bloom (IA)
            flash('Iniciando análisis con IA (Bloom)... esto puede tardar unos segundos.', 'warning')
            try:
                processed_count = auto_etiquetar_bloom(session['usuario'], db)
                flash(f'Análisis IA completado: {processed_count} documentos etiquetados.', 'success')
            except Exception as e:
                flash(f'Error en análisis IA: {e}', 'danger')
                
        else:
            flash(f'Error procesando archivo: {msg}', 'danger')
            
        # Limpieza (Opcional: borrar archivo temporal)
        # os.remove(filepath)

    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)