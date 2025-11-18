"""
Script de prueba - Verifica instalación y hardware
"""
import sys

print("=" * 60)
print("HowToPiano - Test de Instalación")
print("=" * 60)

# Test 1: Python
print("\n[1/5] Verificando Python...")
print(f"  Versión: {sys.version}")
if sys.version_info >= (3, 7):
    print("  ✓ Python 3.7+ OK")
else:
    print("  ✗ Se requiere Python 3.7 o superior")
    sys.exit(1)

# Test 2: Librerías
print("\n[2/5] Verificando librerías...")
errors = []

try:
    import mido
    print("  ✓ mido instalado")
except ImportError:
    print("  ✗ mido NO instalado")
    errors.append("mido")

try:
    import board
    print("  ✓ board instalado")
except ImportError:
    print("  ⚠ board NO instalado (normal en PC)")

try:
    import neopixel
    print("  ✓ neopixel instalado")
except ImportError:
    print("  ⚠ neopixel NO instalado (normal en PC)")

# Test 3: Módulos del proyecto
print("\n[3/5] Verificando módulos del proyecto...")
try:
    from src.midi_reader import MidiReader
    from src.led_controller import LEDController
    from src.note_mapper import NoteMapper
    print("  ✓ Todos los módulos disponibles")
except ImportError as e:
    print(f"  ✗ Error importando: {e}")
    errors.append("módulos")

# Test 4: Configuración
print("\n[4/5] Verificando configuración...")
import os
if os.path.exists("config/config.json"):
    print("  ✓ Archivo config.json encontrado")
else:
    print("  ✗ config.json no encontrado")
    errors.append("config")

# Test 5: GPIO (solo en Raspberry Pi)
print("\n[5/5] Verificando GPIO...")
try:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(18, GPIO.OUT)
    GPIO.cleanup()
    print("  ✓ GPIO funcional")
except ImportError:
    print("  ⚠ GPIO no disponible (normal en PC)")
except Exception as e:
    print(f"  ⚠ Error GPIO: {e}")

# Resumen
print("\n" + "=" * 60)
if not errors:
    print("✓ INSTALACIÓN CORRECTA")
    print("  Puedes ejecutar: sudo python3 main.py")
else:
    print("✗ ERRORES ENCONTRADOS")
    print("  Falta instalar:")
    for err in errors:
        print(f"    - {err}")
    print("\n  Ejecuta: pip3 install -r requirements.txt")
print("=" * 60)
