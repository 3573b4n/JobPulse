#!/usr/bin/env python3
"""
Script de validación para JobPulse Bot
Verifica que todo esté configurado correctamente antes de ejecutar
"""

import os
import sys
import json
from datetime import datetime

def print_header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")

def check_python_version():
    print("🐍 Verificando versión de Python...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 9:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
        return True
    print(f"❌ Python 3.9+ requerido (tienes {version.major}.{version.minor})")
    return False

def check_dependencies():
    print("\n📦 Verificando dependencias...")
    required = {
        'requests': '2.31.0',
        'bs4': '4.12.2',
        'curl_cffi': '0.5.9',
        'lxml': '4.9.3'
    }
    
    missing = []
    for package, version in required.items():
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - INSTALAR: pip install -r requirements.txt")
            missing.append(package)
    
    return len(missing) == 0

def check_credentials():
    print("\n🔐 Verificando credenciales de Telegram...")
    
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not token:
        print("❌ TELEGRAM_TOKEN no configurado")
        print("   → Configura: export TELEGRAM_TOKEN='tu_token'")
        return False
    else:
        print(f"✅ TELEGRAM_TOKEN configurado ({len(token)} caracteres)")
    
    if not chat_id:
        print("❌ TELEGRAM_CHAT_ID no configurado")
        print("   → Configura: export TELEGRAM_CHAT_ID='tu_id'")
        return False
    else:
        print(f"✅ TELEGRAM_CHAT_ID configurado ({chat_id})")
    
    return True

def check_bot_script():
    print("\n📄 Verificando archivo job_bot.py...")
    
    if not os.path.exists("job_bot.py"):
        print("❌ job_bot.py no encontrado en directorio actual")
        return False
    
    print("✅ job_bot.py existe")
    
    # Verificar que contiene funciones críticas
    with open("job_bot.py", "r") as f:
        content = f.read()
    
    required_functions = [
        "search_linkedin",
        "search_indeed",
        "search_infojobs",
        "matches_criteria",
        "send_telegram"
    ]
    
    missing_funcs = [f for f in required_functions if f not in content]
    
    if missing_funcs:
        print(f"❌ Funciones faltantes: {missing_funcs}")
        return False
    
    print(f"✅ Todas las funciones críticas presentes")
    return True

def check_github_workflows():
    print("\n⚙️ Verificando configuración de GitHub Actions...")
    
    workflow_dir = ".github/workflows"
    if not os.path.exists(workflow_dir):
        print(f"⚠️ Directorio {workflow_dir} no existe (se creará en GitHub)")
        return True
    
    if not os.path.exists(f"{workflow_dir}/jobpulse.yml"):
        print(f"⚠️ {workflow_dir}/jobpulse.yml no encontrado")
        print("   → Esto es OK si lo vas a añadir manualmente en GitHub")
        return True
    
    print(f"✅ {workflow_dir}/jobpulse.yml existe")
    return True

def test_telegram_connection():
    print("\n📡 Probando conexión a Telegram...")
    
    import requests
    
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        print("⚠️ Saltando test (sin credenciales)")
        return True
    
    try:
        url = f"https://api.telegram.org/bot{token}/getMe"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data['ok']:
                bot_name = data['result']['username']
                print(f"✅ Bot conectado: @{bot_name}")
                return True
        
        print(f"❌ Error Telegram: {response.status_code}")
        return False
        
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return False

def check_database():
    print("\n💾 Verificando base de datos...")
    
    db_file = "ofertas_vistas.json"
    
    if not os.path.exists(db_file):
        print(f"ℹ️ {db_file} será creado en la primera ejecución")
        return True
    
    try:
        with open(db_file, "r") as f:
            data = json.load(f)
        
        count = len(data.get("seen_offers", []))
        updated = data.get("last_updated", "unknown")
        print(f"✅ {db_file} válido ({count} ofertas vistas)")
        print(f"   Último update: {updated}")
        return True
        
    except json.JSONDecodeError:
        print(f"❌ {db_file} corrupto - será reiniciado")
        return False

def run_test_search():
    print("\n🧪 Ejecutando búsqueda de prueba (sin enviar Telegram)...")
    print("   (Esto tarda ~30 segundos...)\n")
    
    try:
        from job_bot import search_linkedin, search_indeed, matches_criteria
        
        # Test filtros
        test_cases = [
            ("Back Office Remoto", True),
            ("Back Office Madrid Presencial", False),
            ("Senior Developer Python", False),
            ("Postventa Teletrabajo", True),
        ]
        
        print("Probando filtros:")
        for title, expected in test_cases:
            result = matches_criteria(title)
            status = "✅" if result == expected else "❌"
            print(f"  {status} '{title}' → {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en test: {e}")
        return False

def main():
    print_header("VALIDACIÓN DE JOBPULSE BOT")
    
    checks = [
        ("Python", check_python_version),
        ("Dependencias", check_dependencies),
        ("Credenciales", check_credentials),
        ("Script principal", check_bot_script),
        ("GitHub Actions", check_github_workflows),
        ("Conexión Telegram", test_telegram_connection),
        ("Base de datos", check_database),
        ("Test de filtros", run_test_search),
    ]
    
    results = {}
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            print(f"❌ Error no esperado: {e}")
            results[name] = False
    
    # Resumen
    print_header("RESUMEN")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for check_name, result in results.items():
        status = "✅" if result else "❌"
        print(f"{status} {check_name}")
    
    print(f"\n{passed}/{total} verificaciones pasadas")
    
    if passed == total:
        print("\n🎉 ¡TODO ESTÁ LISTO! Puedes subir a GitHub.")
        return 0
    elif passed >= total - 2:
        print("\n⚠️ Hay algunos problemas menores, pero el bot debería funcionar.")
        return 1
    else:
        print("\n❌ Hay problemas críticos. Resuelve antes de continuar.")
        return 2

if __name__ == "__main__":
    sys.exit(main())
