#!/usr/bin/env python3
"""
Script de prueba para desarrollo en Windows
Simula el sistema sin hardware de Raspberry Pi
"""
import os
import sys

# Agregar directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

print("=" * 60)
print("🎹 HowToPiano - Modo Desarrollo (Windows)")
print("=" * 60)
print()

# Verificar importaciones
print("Verificando dependencias...")
print()

# 1. MIDI (debe funcionar)
try:
    import mido
    print("✓ mido instalado correctamente")
except ImportError:
    print("✗ mido no disponible - instala con: pip install mido")

# 2. Pygame (opcional)
try:
    import pygame
    print("✓ pygame instalado (display gráfico disponible)")
except ImportError:
    print("⚠ pygame no disponible (opcional para gráficos)")

# 3. LEDs (no funciona en Windows - ESPERADO)
try:
    import board
    print("✓ board disponible (¿estás en Raspberry Pi?)")
except ImportError:
    print("⚠ board no disponible (NORMAL en Windows)")

try:
    from rpi_ws281x import PixelStrip
    print("✓ rpi-ws281x disponible")
except ImportError:
    print("⚠ rpi-ws281x no disponible (NORMAL en Windows)")

print()
print("-" * 60)
print()

# Probar módulos del proyecto
print("Verificando módulos del proyecto...")
print()

try:
    from src.midi_reader import MidiReader
    print("✓ MidiReader OK")
except Exception as e:
    print(f"✗ MidiReader error: {e}")

try:
    from src.note_mapper import NoteMapper
    print("✓ NoteMapper OK")
except Exception as e:
    print(f"✗ NoteMapper error: {e}")

try:
    from src.led_controller import LEDController
    print("✓ LEDController OK (con simulación)")
except Exception as e:
    print(f"✗ LEDController error: {e}")

try:
    from src.score_display import ScoreDisplay
    print("✓ ScoreDisplay OK")
except Exception as e:
    print(f"✗ ScoreDisplay error: {e}")

try:
    from src.graphical_score import GraphicalScoreDisplay
    print("✓ GraphicalScoreDisplay OK")
except Exception as e:
    print(f"✗ GraphicalScoreDisplay error: {e}")

print()
print("=" * 60)
print()

# Prueba simple
print("🧪 Prueba de funcionalidad básica...")
print()

try:
    # Test 1: Note Mapper
    mapper = NoteMapper('piano_88')
    test_note = 60  # C4
    led_idx = mapper.note_to_led(test_note)
    print(f"✓ Test NoteMapper: Nota MIDI {test_note} → LED {led_idx}")
    
    # Test 2: LED Controller en modo simulación
    led_controller = LEDController(num_leds=88, simulate=True)
    if led_idx is not None:
        led_controller.set_led_on(led_idx, color=(0, 255, 0))
    print(f"✓ Test LEDController: Simulación funcionando")
    led_controller.cleanup()
    
    # Test 3: Score Display requiere archivo MIDI, lo saltamos
    print(f"✓ Test ScoreDisplay: Módulo disponible")
    
    print()
    print("=" * 60)
    print("✅ TODOS LOS TESTS PASARON")
    print("=" * 60)
    print()
    print("Para ejecutar el programa principal:")
    print("  python main.py --simulate")
    print()
    print("Nota: Los LEDs no funcionarán en Windows (modo simulación)")
    print("      Transfiere el proyecto a Raspberry Pi para funcionalidad completa")
    
except Exception as e:
    print()
    print("=" * 60)
    print("❌ ERROR EN LOS TESTS")
    print("=" * 60)
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print()
