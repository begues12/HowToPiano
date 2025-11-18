"""
Script de demostración - Muestra efectos visuales sin MIDI
"""
import time
import sys
sys.path.append('..')

from src.led_controller import LEDController
from src.note_mapper import NoteMapper

def demo_effects():
    """Ejecuta varios efectos de demostración"""
    
    print("=" * 60)
    print("🎹 HowToPiano - Demo de Efectos LED")
    print("=" * 60)
    
    # Inicializar (modo simulación para pruebas)
    controller = LEDController(num_leds=88, brightness=0.3, simulate=True)
    mapper = NoteMapper('piano_88')
    
    print("\nPresiona Ctrl+C para saltar al siguiente efecto")
    print("=" * 60)
    
    try:
        # Efecto 1: Onda ascendente
        print("\n[Efecto 1] Onda ascendente...")
        for i in range(mapper.num_leds):
            controller.set_led_on(i)
            time.sleep(0.03)
        time.sleep(0.5)
        controller.clear_all()
        time.sleep(0.5)
        
        # Efecto 2: Onda descendente
        print("\n[Efecto 2] Onda descendente...")
        for i in range(mapper.num_leds - 1, -1, -1):
            controller.set_led_on(i)
            time.sleep(0.03)
        time.sleep(0.5)
        controller.clear_all()
        time.sleep(0.5)
        
        # Efecto 3: Solo teclas blancas
        print("\n[Efecto 3] Solo teclas blancas...")
        white_keys = mapper.get_white_key_indices()
        for idx in white_keys:
            controller.set_led(idx, (255, 255, 255))
        time.sleep(2)
        controller.clear_all()
        time.sleep(0.5)
        
        # Efecto 4: Solo teclas negras
        print("\n[Efecto 4] Solo teclas negras...")
        black_keys = mapper.get_black_key_indices()
        for idx in black_keys:
            controller.set_led(idx, (100, 100, 255))
        time.sleep(2)
        controller.clear_all()
        time.sleep(0.5)
        
        # Efecto 5: Onda de color
        print("\n[Efecto 5] Onda de color (arcoíris)...")
        for j in range(256):
            for i in range(min(20, mapper.num_leds)):
                pixel_index = (i * 256 // 20) + j
                color = controller._wheel(pixel_index & 255)
                controller.set_led(i, color)
            time.sleep(0.05)
        controller.clear_all()
        time.sleep(0.5)
        
        # Efecto 6: Pulso respiración
        print("\n[Efecto 6] Pulso respiración...")
        for _ in range(3):
            # Fade in
            for step in range(0, 100, 5):
                brightness = step / 100.0
                controller.set_brightness(brightness * 0.5)
                controller.set_all((255, 100, 0))
                time.sleep(0.05)
            # Fade out
            for step in range(100, 0, -5):
                brightness = step / 100.0
                controller.set_brightness(brightness * 0.5)
                time.sleep(0.05)
        controller.set_brightness(0.3)
        controller.clear_all()
        time.sleep(0.5)
        
        # Efecto 7: Efecto piano roll
        print("\n[Efecto 7] Simulación piano roll...")
        notes = [60, 64, 67, 72, 76, 79, 84]  # Acorde de C mayor en diferentes octavas
        for note in notes:
            led = mapper.note_to_led(note)
            if led is not None:
                controller.set_led_on(led)
                time.sleep(0.3)
        time.sleep(1)
        for note in notes:
            led = mapper.note_to_led(note)
            if led is not None:
                controller.set_led_off(led)
                time.sleep(0.2)
        
        # Efecto 8: Flash completo
        print("\n[Efecto 8] Flash completo...")
        for _ in range(5):
            controller.set_all((255, 255, 255))
            time.sleep(0.1)
            controller.clear_all()
            time.sleep(0.1)
        
        print("\n" + "=" * 60)
        print("✓ Demo completada")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n\n⏹ Demo interrumpida")
    finally:
        controller.cleanup()

if __name__ == "__main__":
    demo_effects()
