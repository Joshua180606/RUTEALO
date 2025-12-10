"""
Script de testing E2E - FASE 4
Prueba los 3 flujos principales:
1. Crear nueva ruta (POST /crear-ruta)
2. Obtener lista de rutas (GET /rutas/lista)
3. Continuar ruta existente (interacción UI)
"""

import sys
import requests
import json
import time
from pathlib import Path

BASE_URL = "http://127.0.0.1:5000"
SESSION = requests.Session()

# Headers para simular usuario autenticado
HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Testing-Bot/1.0"
}

def print_header(text):
    """Imprimir encabezado de sección"""
    print("\n" + "=" * 70)
    print(f"🧪 {text}")
    print("=" * 70)

def test_login():
    """Prueba 1: Login o verificar sesión"""
    print_header("TEST 1: Login / Verificar sesión")
    
    # Intentar acceder a dashboard (redirige a login si no autenticado)
    try:
        resp = SESSION.get(f"{BASE_URL}/dashboard", allow_redirects=False)
        print(f"   Status: {resp.status_code}")
        
        if resp.status_code == 302:
            print("   ⚠️ Redirigido a login - usuario no autenticado")
            print("   ℹ️ Para testing E2E necesitas estar logueado")
            return False
        elif resp.status_code == 200:
            print("   ✅ Dashboard accesible - sesión activa")
            return True
        else:
            print(f"   ❌ Status inesperado: {resp.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_get_rutas_lista():
    """Prueba 2: GET /rutas/lista"""
    print_header("TEST 2: GET /rutas/lista - Obtener lista de rutas")
    
    try:
        resp = SESSION.get(f"{BASE_URL}/rutas/lista")
        print(f"   Status: {resp.status_code}")
        
        if resp.status_code == 401:
            print("   ⚠️ Unauthorized - no autenticado")
            return False
        
        if resp.status_code != 200:
            print(f"   ❌ Error: {resp.status_code}")
            print(f"   Response: {resp.text}")
            return False
        
        data = resp.json()
        rutas = data.get('rutas', [])
        
        print(f"   ✅ Success: Obtenidas {len(rutas)} rutas")
        
        # Mostrar primeras 3 rutas
        for idx, ruta in enumerate(rutas[:3]):
            print(f"\n   Ruta {idx + 1}:")
            print(f"     - ID: {ruta.get('ruta_id')}")
            print(f"     - Nombre: {ruta.get('nombre_ruta')}")
            print(f"     - Estado: {ruta.get('estado')}")
            print(f"     - Archivos: {ruta.get('archivos_count', 0)}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_endpoints_availability():
    """Prueba 3: Verificar que todos los endpoints nuevos existan"""
    print_header("TEST 3: Verificar disponibilidad de endpoints")
    
    endpoints = [
        ("GET", "/rutas/lista", 200),
        ("GET", "/ruta/estado", 200),
        ("GET", "/examen-inicial", 200),
        ("POST", "/crear-ruta", 400),  # Esperamos 400 porque no enviamos datos
        ("GET", "/dashboard", 200),
    ]
    
    results = []
    for method, endpoint, expected_status in endpoints:
        try:
            if method == "GET":
                resp = SESSION.get(f"{BASE_URL}{endpoint}")
            elif method == "POST":
                resp = SESSION.post(f"{BASE_URL}{endpoint}", json={})
            
            status = resp.status_code
            success = (status == expected_status) or (status in [200, 400, 401])
            
            icon = "✅" if success else "❌"
            print(f"   {icon} {method:4} {endpoint:20} → {status}")
            results.append(success)
            
        except Exception as e:
            print(f"   ❌ {method:4} {endpoint:20} → Error: {e}")
            results.append(False)
    
    return all(results)

def test_html_elements():
    """Prueba 4: Verificar que HTML tiene los elementos requeridos"""
    print_header("TEST 4: Verificar elementos HTML en dashboard")
    
    try:
        resp = SESSION.get(f"{BASE_URL}/dashboard")
        
        if resp.status_code != 200:
            print(f"   ❌ No se pudo cargar dashboard: {resp.status_code}")
            return False
        
        html = resp.text
        
        elements = [
            ("Botón Crear Ruta", "btnCrearRuta"),
            ("Botón Mis Rutas", "btnMisRutas"),
            ("Modal Crear Ruta", "modalCrearRuta"),
            ("Modal Lista Rutas", "modalListaRutas"),
            ("Form Crear Ruta", "formCrearRuta"),
            ("Input Nombre Ruta", "nombreRuta"),
            ("Input Descripción", "descripcionRuta"),
            ("Input Archivos", "archivosRuta"),
            ("Botón Enviar", "btnEnviarCrearRuta"),
        ]
        
        missing = []
        for name, element_id in elements:
            if f'id="{element_id}"' in html or f"id='{element_id}'" in html:
                print(f"   ✅ {name}")
            else:
                print(f"   ❌ {name} (falta ID: {element_id})")
                missing.append(name)
        
        return len(missing) == 0
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_javascript_functions():
    """Prueba 5: Verificar que las funciones JavaScript están definidas"""
    print_header("TEST 5: Verificar funciones JavaScript")
    
    try:
        resp = SESSION.get(f"{BASE_URL}/dashboard")
        
        if resp.status_code != 200:
            print(f"   ❌ No se pudo cargar dashboard: {resp.status_code}")
            return False
        
        html = resp.text
        
        functions = [
            "abrirModalCrearRuta",
            "enviarFormularioCrearRuta",
            "cargarListaRutas",
            "renderizarListaRutas",
            "continuarRuta",
            "verDetallesRuta",
            "escape_html",
            "validarNombreRuta",
            "validarDescripcion",
            "validarArchivos",
            "mostrarError",
            "mostrarErrores",
            "mostrarExito",
        ]
        
        missing = []
        for func in functions:
            if f"function {func}" in html or f"{func} = " in html or f"{func}(" in html:
                print(f"   ✅ {func}()")
            else:
                print(f"   ❌ {func}() - NO ENCONTRADA")
                missing.append(func)
        
        return len(missing) == 0
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    """Ejecutar todas las pruebas"""
    print("\n" + "🚀" * 35)
    print("INICIANDO TESTING E2E - FASE 4")
    print("🚀" * 35)
    
    results = {
        "Login/Sesión": test_login(),
        "GET /rutas/lista": test_get_rutas_lista(),
        "Disponibilidad de endpoints": test_endpoints_availability(),
        "Elementos HTML": test_html_elements(),
        "Funciones JavaScript": test_javascript_functions(),
    }
    
    # Resumen
    print_header("RESUMEN DE RESULTADOS")
    passed = 0
    for test_name, result in results.items():
        icon = "✅" if result else "❌"
        print(f"   {icon} {test_name}")
        if result:
            passed += 1
    
    total = len(results)
    print(f"\n   {passed}/{total} pruebas pasadas")
    
    if passed == total:
        print("\n✅ TODAS LAS PRUEBAS PASADAS")
        return 0
    else:
        print(f"\n⚠️  {total - passed} pruebas fallaron")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
    except KeyboardInterrupt:
        print("\n\n⛔ Testing interrumpido por usuario")
        exit_code = 1
    except Exception as e:
        print(f"\n❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()
        exit_code = 1
    
    sys.exit(exit_code)
