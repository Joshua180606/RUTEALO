# test_app_smoke.ps1
# Ejecuta la app en background, hace un GET a /, y detiene la app.

param(
    [int]$WaitSeconds = 5
)

$pythonPath = "C:/Users/joshu/Documents/Joshua/Tesis/RUTEALO/.venv/Scripts/python.exe"
$projectRoot = "C:\Users\joshu\Documents\Joshua\Tesis\RUTEALO"

# Cambiar al directorio del proyecto
Push-Location $projectRoot

# Ejecutar app en background con FLASK_ENV=development
Write-Host "[*] Levantando app Flask en background..."
$env:FLASK_ENV = "development"
$env:FLASK_APP = "src.app:app"

# Iniciar el proceso Python ejecutando src/app.py
$appProcess = Start-Process -FilePath $pythonPath -ArgumentList "-m", "flask", "run", "--host", "127.0.0.1", "--port", "5000" -PassThru -NoNewWindow -ErrorAction Continue

Write-Host "[*] Esperando $WaitSeconds segundos para que la app arranque..."
Start-Sleep -Seconds $WaitSeconds

# Intentar hacer un GET a /
try {
    Write-Host "[*] Haciendo GET a http://127.0.0.1:5000/"
    $response = Invoke-WebRequest -Uri "http://127.0.0.1:5000/" -Method Get -TimeoutSec 5 -ErrorAction Stop
    Write-Host "[OK] Respuesta HTTP: $($response.StatusCode)"
    Write-Host "[OK] Primer 200 chars del body:"
    Write-Host $response.Content.Substring(0, [Math]::Min(200, $response.Content.Length))
} catch {
    Write-Host "[ERR] Error en GET: $($_.Exception.Message)"
}

# Detener app
Write-Host "[*] Deteniendo app..."
if ($appProcess) {
    Stop-Process -InputObject $appProcess -Force -ErrorAction Continue
    Write-Host "[OK] App detenida"
}

# Verificar logs/
Write-Host "[*] Comprobando directorio logs/:"
if (Test-Path "logs") {
    Get-ChildItem -Path "logs" -Recurse | ForEach-Object { Write-Host "  $_" }
} else {
    Write-Host "  [WARN] logs/ no existe aun"
}

Pop-Location
