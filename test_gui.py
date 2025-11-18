#!/usr/bin/env python3
"""
Test de la GUI en Windows (sin hardware)
"""
import sys
import os

# Agregar directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Mock de módulos hardware
class MockMidiReader:
    def __init__(self, filepath):
        self.filepath = filepath
    
    def play(self):
        """Simula reproducción MIDI"""
        # Retornar eventos MIDI de ejemplo
        return [
            {'type': 'note_on', 'note': 60, 'velocity': 80, 'time': 0},
            {'type': 'note_off', 'note': 60, 'velocity': 0, 'time': 480},
            {'type': 'note_on', 'note': 62, 'velocity': 80, 'time': 0},
            {'type': 'note_off', 'note': 62, 'velocity': 0, 'time': 480},
        ]

class MockLEDController:
    def __init__(self, **kwargs):
        self.num_leds = kwargs.get('num_leds', 88)
    
    def set_brightness(self, brightness):
        pass
    
    def set_led(self, index, color):
        """Simula encender LED"""
        r, g, b = color
        print(f"  LED[{index}] = RGB({r}, {g}, {b})")
    
    def clear_all(self):
        """Simula apagar todos los LEDs"""
        print("  Todos los LEDs apagados")

class MockNoteMapper:
    def __init__(self, **kwargs):
        self.keyboard_type = kwargs.get('keyboard_type', 'piano_88')
    
    def note_to_led(self, note):
        """Mapea nota MIDI a índice LED (simplificado)"""
        # Mapeo simple: MIDI 21-108 → LED 0-87
        if 21 <= note <= 108:
            return note - 21
        return None

# Crear módulos mock
midi_module = type('module', (), {'MidiReader': MockMidiReader})()
led_module = type('module', (), {'LEDController': MockLEDController})()
mapper_module = type('module', (), {'NoteMapper': MockNoteMapper})()

# Inyectar mocks
sys.modules['src.midi_reader'] = midi_module
sys.modules['src.led_controller'] = led_module
sys.modules['src.note_mapper'] = mapper_module

# Ahora importar la GUI
from gui_app import HowToPianoGUI

if __name__ == "__main__":
    print("🎹 Iniciando HowToPiano GUI (Modo Test Windows)")
    print("=" * 60)
    print("✓ Interfaz gráfica funcionando")
    print("✓ Teclado virtual clickeable")
    print("✓ Partitura visual con notas iluminadas")
    print("⚠ Hardware simulado (LEDs se muestran en consola)")
    print("✓ Puedes probar toda la interfaz")
    print("=" * 60)
    print("\n💡 Prueba esto:")
    print("  1. Click en teclas del teclado virtual")
    print("  2. Abre Configuración → Test LED")
    print("  3. La partitura se actualiza con las notas")
    print("=" * 60 + "\n")
    
    app = HowToPianoGUI()
    app.run()
