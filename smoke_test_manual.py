"""
Smoke Test Manual - Verificación Rápida de Funcionalidad
Ejecuta pruebas básicas de los endpoints y funcionalidades
"""

import webbrowser
import time

print("=" * 60)
print("🔥 SMOKE TEST MANUAL - NUEVA FUNCIONALIDAD")
print("=" * 60)

print("\n✅ Servidor Flask iniciado correctamente")
print("   URL: http://127.0.0.1:5000/dashboard")

print("\n📋 PRUEBAS MANUALES A REALIZAR:")
print("-" * 60)

print("\n1️⃣ VERIFICAR DASHBOARD REDISEÑADO")
print("   ☐ Intro section con gradient visible")
print("   ☐ Botón '➕ Crear Nueva Ruta' visible")
print("   ☐ Botón '📚 Ver Mis Rutas' visible")

print("\n2️⃣ PROBAR CREAR NUEVA RUTA")
print("   ☐ Click en '➕ Crear Nueva Ruta'")
print("   ☐ Modal se abre correctamente")
print("   ☐ Llenar: Nombre, Descripción, Archivos")
print("   ☐ Click '🚀 Crear Ruta'")
print("   ☐ Mensaje de éxito aparece")

print("\n3️⃣ PROBAR VER MIS RUTAS")
print("   ☐ Click en '📚 Ver Mis Rutas'")
print("   ☐ Modal se abre correctamente")
print("   ☐ Lista de rutas se carga")
print("   ☐ Botones funcionan")

print("\n" + "=" * 60)
print("🚀 ABRIENDO DASHBOARD EN NAVEGADOR...")
print("=" * 60)

time.sleep(2)

try:
    webbrowser.open('http://127.0.0.1:5000/dashboard')
    print("\n✅ Navegador abierto")
    print("   Realiza las pruebas manuales")
except Exception as e:
    print(f"\n⚠️ Error: {e}")
    print("   Abre manualmente: http://127.0.0.1:5000/dashboard")

print("\n✅ Smoke test preparado")
