#!/usr/bin/env python3
"""
HowToPiano - Sistema de iluminación LED sincronizado con MIDI
Versión Raspberry Pi Zero W/W2

Carga archivos MIDI desde USB y sincroniza LEDs con las notas
Similar al sistema Keysnake pero con Raspberry Pi
"""
import os
import sys
import time
import signal
from pathlib import Path
from typing import Optional

# Importar módulos del proyecto
from src.midi_reader import MidiReader
from src.led_controller import LEDController
from src.note_mapper import NoteMapper
from src.score_display import ScoreDisplay, InteractiveLearning
from src.midi_input_detector import MidiInputDetector, KeyboardInputDetector

# Importar display gráfico (opcional)
try:
    from src.graphical_score import GraphicalScoreDisplay, TkinterScoreDisplay
    GRAPHICAL_AVAILABLE = True
except ImportError:
    GRAPHICAL_AVAILABLE = False


class HowToPiano:
    """Sistema principal de iluminación LED sincronizada con MIDI"""
    
    def __init__(self, keyboard_type: str = 'piano_88', 
                 num_leds: int = 88,
                 brightness: float = 0.3,
                 simulate: bool = False):
        """
        Inicializa el sistema HowToPiano
        
        Args:
            keyboard_type: Tipo de teclado ('piano_88', 'keyboard_61', etc.)
            num_leds: Número de LEDs en la tira
            brightness: Brillo inicial (0.0 a 1.0)
            simulate: Modo simulación (sin hardware real)
        """
        print("=" * 60)
        print("🎹 HowToPiano - Sistema de iluminación LED + MIDI")
        print("=" * 60)
        
        # Inicializar componentes
        print("\n[1/3] Inicializando lector MIDI...")
        self.midi_reader = MidiReader()
        
        print("\n[2/3] Inicializando controlador LED...")
        self.led_controller = LEDController(
            num_leds=num_leds,
            brightness=brightness,
            simulate=simulate
        )
        
        print("\n[3/3] Inicializando mapeador de notas...")
        self.note_mapper = NoteMapper(config_name=keyboard_type)
        
        # Variables de estado
        self.running = False
        self.current_song: Optional[str] = None
        
        # Configurar señales para salida limpia
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        print("\n✓ Sistema inicializado correctamente\n")
    
    def _signal_handler(self, sig, frame):
        """Manejador de señales para salida limpia"""
        print("\n\n⚠ Señal de interrupción recibida...")
        self.stop()
        sys.exit(0)
    
    def list_available_songs(self) -> list:
        """
        Lista archivos MIDI disponibles en el USB
        
        Returns:
            Lista de rutas a archivos MIDI
        """
        print("🔍 Buscando archivos MIDI en USB...")
        songs = self.midi_reader.list_midi_files()
        
        if not songs:
            print("⚠ No se encontraron archivos MIDI")
        else:
            print(f"\n📁 Archivos MIDI encontrados ({len(songs)}):")
            for i, song in enumerate(songs, 1):
                print(f"  {i}. {os.path.basename(song)}")
        
        return songs
    
    def load_song(self, file_path: str) -> bool:
        """
        Carga un archivo MIDI
        
        Args:
            file_path: Ruta al archivo MIDI
            
        Returns:
            True si se cargó correctamente
        """
        if self.midi_reader.load_midi_file(file_path):
            self.current_song = file_path
            
            # Obtener información del archivo
            info = self.midi_reader.get_midi_info()
            note_range = self.midi_reader.get_note_range()
            
            # Validar compatibilidad
            validation = self.note_mapper.validate_midi_file_range(
                note_range[0], note_range[1]
            )
            
            print(f"\n📊 Información del archivo:")
            print(f"  • Duración: {info['duration']:.2f} segundos")
            print(f"  • Pistas: {info['tracks']}")
            print(f"  • Rango: {note_range[0]} - {note_range[1]}")
            print(f"  • Notas: {self.note_mapper.get_note_name(note_range[0])} - "
                  f"{self.note_mapper.get_note_name(note_range[1])}")
            
            if not validation['compatible']:
                print(f"\n⚠ ADVERTENCIA: {validation['total_out_of_range']} "
                      f"notas fuera del rango del teclado")
                if validation['notes_below_range'] > 0:
                    print(f"  • {validation['notes_below_range']} notas demasiado graves")
                if validation['notes_above_range'] > 0:
                    print(f"  • {validation['notes_above_range']} notas demasiado agudas")
            else:
                print(f"✓ Archivo compatible con el teclado")
            
            return True
        return False
    
    def play_song(self, show_progress: bool = True):
        """
        Reproduce la canción cargada con sincronización LED
        
        Args:
            show_progress: Mostrar progreso en consola
        """
        if not self.current_song:
            print("✗ No hay canción cargada")
            return
        
        print(f"\n▶ Reproduciendo: {os.path.basename(self.current_song)}")
        print("  (Presiona Ctrl+C para detener)\n")
        
        # Limpiar LEDs antes de empezar
        self.led_controller.clear_all()
        
        self.running = True
        note_count = 0
        active_notes = set()  # Notas actualmente activas
        
        try:
            for msg in self.midi_reader.play_midi_events():
                if not self.running:
                    break
                
                # Procesar mensaje MIDI
                if msg.type == 'note_on' and msg.velocity > 0:
                    # Nota activada
                    led_index = self.note_mapper.note_to_led(msg.note)
                    if led_index is not None:
                        self.led_controller.set_led_on(led_index)
                        active_notes.add(msg.note)
                        note_count += 1
                        
                        if show_progress and note_count % 10 == 0:
                            print(f"  ♪ Notas tocadas: {note_count} | "
                                  f"Activas: {len(active_notes)}", end='\r')
                
                elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                    # Nota desactivada
                    led_index = self.note_mapper.note_to_led(msg.note)
                    if led_index is not None:
                        self.led_controller.set_led_off(led_index)
                        active_notes.discard(msg.note)
            
            print(f"\n\n✓ Reproducción completada ({note_count} notas)")
            
        except KeyboardInterrupt:
            print("\n\n⏸ Reproducción interrumpida")
        except Exception as e:
            print(f"\n\n✗ Error durante reproducción: {e}")
        finally:
            # Limpiar LEDs al finalizar
            self.led_controller.clear_all()
            self.running = False
    
    def test_leds(self):
        """Ejecuta secuencia de prueba de LEDs"""
        print("\n🧪 Ejecutando prueba de LEDs...")
        self.led_controller.test_sequence(delay=0.02)
        print("✓ Prueba completada\n")
    
    def practice_mode(self):
        """Modo aprendizaje interactivo"""
        if not self.current_song:
            print("✗ No hay canción cargada")
            songs = self.list_available_songs()
            if songs:
                try:
                    idx = int(input("\nSelecciona canción para practicar (número): ")) - 1
                    if 0 <= idx < len(songs):
                        if not self.load_song(songs[idx]):
                            return
                    else:
                        print("✗ Número inválido")
                        return
                except (ValueError, KeyboardInterrupt):
                    return
            else:
                return
        
        print("\n" + "=" * 60)
        print("🎓 MODO APRENDIZAJE")
        print("=" * 60)
        print("1. Práctica guiada (consola simple)")
        print("2. Práctica con interfaz visual (terminal)")
        print("3. Práctica con detección MIDI (teclado conectado)")
        print("0. Volver")
        print("=" * 60)
        
        choice = input("\nSelecciona modo: ").strip()
        
        try:
            # Crear display de partitura
            score_display = ScoreDisplay(
                self.midi_reader.current_file,
                self.note_mapper
            )
            
            if choice == '1':
                # Modo consola simple
                print("\n🎓 Modo Práctica - Consola")
                print("Presiona Enter después de tocar cada nota\n")
                input("Presiona Enter para comenzar...")
                
                while True:
                    score_display.print_console_display()
                    current = score_display.get_current_note()
                    
                    if not current:
                        print("\n🎉 ¡Felicidades! Completaste la partitura")
                        break
                    
                    # Iluminar LED
                    led_idx = self.note_mapper.note_to_led(current.note)
                    if led_idx is not None:
                        self.led_controller.set_led_on(led_idx)
                    
                    # Esperar input
                    resp = input("👆 Toca la nota y presiona Enter (o 'q' para salir): ")
                    if resp.lower() == 'q':
                        break
                    
                    score_display.advance_note()
                    
                    if led_idx is not None:
                        self.led_controller.set_led_off(led_idx)
                
                self.led_controller.clear_all()
            
            elif choice == '2':
                # Modo interfaz visual
                import curses
                learning = InteractiveLearning(
                    score_display,
                    self.led_controller
                )
                learning.practice_mode_terminal_ui()
            
            elif choice == '3':
                # Modo con detección MIDI
                print("\n🎹 Conectando teclado MIDI...")
                detector = MidiInputDetector()
                
                if not detector.port:
                    print("\n⚠ No se detectó teclado MIDI")
                    print("¿Usar teclado de computadora? (a=C, s=D, d=E, etc.) [y/n]")
                    if input("> ").lower() == 'y':
                        detector = KeyboardInputDetector()
                    else:
                        return
                
                print("\n🎓 Modo Práctica con Detección")
                input("Presiona Enter para comenzar...")
                
                while True:
                    score_display.print_console_display()
                    current = score_display.get_current_note()
                    
                    if not current:
                        print("\n🎉 ¡Felicidades! Completaste la partitura")
                        break
                    
                    # Iluminar LED
                    led_idx = self.note_mapper.note_to_led(current.note)
                    if led_idx is not None:
                        self.led_controller.set_led_on(led_idx)
                    
                    # Esperar nota correcta
                    print(f"\n👆 Esperando que toques: {current.note_name}")
                    correct = detector.wait_for_note(current.note)
                    
                    if correct:
                        print("✓ ¡Correcto!")
                        score_display.advance_note()
                    else:
                        print("✗ Nota incorrecta, intenta de nuevo")
                    
                    if led_idx is not None:
                        self.led_controller.set_led_off(led_idx)
                    
                    time.sleep(0.5)
                
                self.led_controller.clear_all()
                
                if hasattr(detector, 'close'):
                    detector.close()
            
        except KeyboardInterrupt:
            print("\n\n⏸ Práctica interrumpida")
            self.led_controller.clear_all()
        except Exception as e:
            print(f"\n✗ Error en modo práctica: {e}")
            self.led_controller.clear_all()
    
    def _show_graphical_score(self):
        """Muestra partitura gráfica (requiere pygame/tkinter)"""
        if not self.current_song:
            print("✗ No hay canción cargada. Carga una canción primero.")
            return
        
        print("\n🎼 DISPLAY GRÁFICO")
        print("=" * 60)
        print("Opciones disponibles:")
        print("1. Pygame - Partitura con pentagrama")
        print("2. Piano Roll visual (Synthesia)")
        print("3. Tkinter - Vista simple")
        print("0. Cancelar")
        
        choice = input("\nSelecciona display: ").strip()
        
        if choice == '1':
            self._show_pygame_staff()
        elif choice == '2':
            self._show_piano_roll()
        elif choice == '3':
            self._show_tkinter_simple()
    
    def _show_pygame_staff(self):
        """Muestra pentagrama con pygame"""
        try:
            display = GraphicalScoreDisplay()
            notes = self._extract_notes_from_song()
            
            print("\n🎵 Mostrando partitura...")
            display.draw_staff()
            
            for i, note in enumerate(notes[:10]):  # Primeras 10 notas
                display.draw_note(note, i % 7, i == 0)
                time.sleep(0.5)
            
            input("\nPresiona Enter para cerrar...")
            display.close()
            
        except Exception as e:
            print(f"✗ Error: {e}")
    
    def _show_piano_roll(self):
        """Muestra piano roll estilo Synthesia"""
        try:
            display = GraphicalScoreDisplay()
            
            # Extraer notas con timing
            reader = MidiReader(self.current_song)
            notes_data = []
            
            current_time = 0
            for event in reader.play():
                if event['type'] == 'note_on':
                    notes_data.append((
                        event['note'],
                        current_time,
                        event.get('duration', 0.5)
                    ))
                current_time += event.get('delta_time', 0)
            
            display.display_piano_roll(notes_data[:50])
            
        except Exception as e:
            print(f"✗ Error: {e}")
    
    def _show_tkinter_simple(self):
        """Vista simple con Tkinter"""
        try:
            display = TkinterScoreDisplay()
            notes = self._extract_notes_from_song()
            
            for i, note in enumerate(notes[:20]):
                display.update_display(note, notes[i+1:i+6])
                time.sleep(1)
            
            display.run()
            
        except Exception as e:
            print(f"✗ Error: {e}")
    
    def _extract_notes_from_song(self):
        """Extrae nombres de notas de la canción actual"""
        if not self.current_song:
            return []
        
        reader = MidiReader(self.current_song)
        notes = []
        
        for event in reader.play():
            if event['type'] == 'note_on':
                note_name = self._midi_to_name(event['note'])
                notes.append(note_name)
                
                if len(notes) >= 100:  # Límite
                    break
        
        return notes
    
    @staticmethod
    def _midi_to_name(midi_note: int) -> str:
        """Convierte número MIDI a nombre de nota"""
        names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        octave = (midi_note // 12) - 1
        note = names[midi_note % 12]
        return f"{note}{octave}"
    
    def interactive_mode(self):
        """Modo interactivo con menú"""
        while True:
            print("\n" + "=" * 60)
            print("🎹 MENÚ PRINCIPAL")
            print("=" * 60)
            print("1. Listar archivos MIDI disponibles")
            print("2. Cargar y reproducir canción (demo)")
            print("3. 🎓 MODO APRENDIZAJE (práctica guiada)")
            print("4. Reproducir última canción")
            print("5. Prueba de LEDs")
            print("6. Ajustar brillo")
            print("7. Mostrar información del sistema")
            if GRAPHICAL_AVAILABLE:
                print("8. 🎼 Ver partitura gráfica (requiere display)")
            print("0. Salir")
            print("=" * 60)
            
            choice = input("\nSelecciona una opción: ").strip()
            
            if choice == '1':
                self.list_available_songs()
            
            elif choice == '2':
                songs = self.list_available_songs()
                if songs:
                    try:
                        idx = int(input("\nNúmero de canción: ")) - 1
                        if 0 <= idx < len(songs):
                            if self.load_song(songs[idx]):
                                input("\nPresiona Enter para reproducir (demo automático)...")
                                self.play_song()
                        else:
                            print("✗ Número inválido")
                    except ValueError:
                        print("✗ Entrada inválida")
            
            elif choice == '3':
                self.practice_mode()
            
            elif choice == '4':
                if self.current_song:
                    input(f"\nReproduciendo: {os.path.basename(self.current_song)}\n"
                          f"Presiona Enter para continuar...")
                    self.play_song()
                else:
                    print("✗ No hay canción cargada")
            
            elif choice == '5':
                self.test_leds()
            
            elif choice == '6':
                try:
                    brightness = float(input("Nuevo brillo (0.0 - 1.0): "))
                    self.led_controller.set_brightness(brightness)
                except ValueError:
                    print("✗ Valor inválido")
            
            elif choice == '7':
                self._show_system_info()
            
            elif choice == '8' and GRAPHICAL_AVAILABLE:
                self._show_graphical_score()
            
            elif choice == '0':
                print("\n👋 Saliendo...")
                break
            
            else:
                print("✗ Opción no válida")
    
    def _show_system_info(self):
        """Muestra información del sistema"""
        print("\n" + "=" * 60)
        print("ℹ INFORMACIÓN DEL SISTEMA")
        print("=" * 60)
        print(f"Tipo de teclado: {self.note_mapper.KEYBOARD_CONFIGS.get(
            'piano_88', {}).get('name', 'Personalizado')}")
        print(f"Número de LEDs: {self.note_mapper.num_leds}")
        print(f"Rango de notas: {self.note_mapper.first_note} - {self.note_mapper.last_note}")
        print(f"Brillo actual: {self.led_controller.brightness * 100:.0f}%")
        print(f"Canción cargada: {os.path.basename(self.current_song) if self.current_song else 'Ninguna'}")
        print("=" * 60)
    
    def stop(self):
        """Detiene la reproducción y limpia recursos"""
        self.running = False
        self.led_controller.cleanup()
        print("✓ Sistema detenido correctamente")


def main():
    """Función principal"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='HowToPiano - Sistema LED + MIDI para Raspberry Pi'
    )
    parser.add_argument(
        '--keyboard', 
        choices=['piano_88', 'keyboard_61', 'keyboard_49', 'keyboard_25'],
        default='piano_88',
        help='Tipo de teclado'
    )
    parser.add_argument(
        '--leds', 
        type=int, 
        default=88,
        help='Número de LEDs'
    )
    parser.add_argument(
        '--brightness', 
        type=float, 
        default=0.3,
        help='Brillo inicial (0.0 - 1.0)'
    )
    parser.add_argument(
        '--simulate', 
        action='store_true',
        help='Modo simulación (sin hardware)'
    )
    parser.add_argument(
        '--file', 
        type=str,
        help='Archivo MIDI a reproducir directamente'
    )
    parser.add_argument(
        '--test', 
        action='store_true',
        help='Ejecutar prueba de LEDs y salir'
    )
    parser.add_argument(
        '--practice',
        action='store_true',
        help='Iniciar modo aprendizaje directamente'
    )
    parser.add_argument(
        '--learn',
        type=str,
        help='Archivo MIDI para modo aprendizaje'
    )
    
    args = parser.parse_args()
    
    # Crear sistema
    system = HowToPiano(
        keyboard_type=args.keyboard,
        num_leds=args.leds,
        brightness=args.brightness,
        simulate=args.simulate
    )
    
    try:
        # Modo prueba
        if args.test:
            system.test_leds()
            return
        
        # Modo aprendizaje con archivo
        if args.learn:
            if os.path.exists(args.learn):
                if system.load_song(args.learn):
                    system.practice_mode()
            else:
                print(f"✗ Archivo no encontrado: {args.learn}")
            return
        
        # Reproducir archivo directo
        if args.file:
            if os.path.exists(args.file):
                if system.load_song(args.file):
                    system.play_song()
            else:
                print(f"✗ Archivo no encontrado: {args.file}")
            return
        
        # Modo aprendizaje directo
        if args.practice:
            system.practice_mode()
            return
        
        # Modo interactivo
        system.interactive_mode()
        
    finally:
        system.stop()


if __name__ == "__main__":
    main()
