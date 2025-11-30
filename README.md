# RUTEALO

## Instalación ⚙️

Puedes instalar las dependencias del proyecto usando pip con el archivo `requirements.txt` incluido en la raíz del repositorio.

Usando pip directamente (sistema global o en un venv ya activado):

```powershell
pip install -r requirements.txt
```

Para un flujo recomendado en Windows (crea una virtualenv y instala allí automáticamente), ejecuta el script de PowerShell provisto:

```powershell
.\install_requirements.ps1
```

Esto creará una carpeta `.venv` por defecto y luego instalará las dependencias listadas en `requirements.txt`.

## Ejecutar el procesador de archivos 🗂️

Al ejecutar `src/data/ingesta_datos.py` desde la línea de comando, el script abre una ventana del gestor de archivos para que selecciones manualmente uno o más archivos para procesar (PDF, DOCX o PPTX). Esto evita que el script escanee automáticamente una carpeta y te da control directo sobre qué archivos ingestar.

Ejemplo para ejecutar desde la raíz del proyecto (suponiendo que ya activaste `.venv`):

```powershell
python src/data/ingesta_datos.py
```

Al finalizar el proceso verás en consola el resultado de la ingesta y si un archivo ya existía en la colección de MongoDB.
