"""
Motor de audio basado en samples del Maestro Concert Grand Piano
Usa los samples FLAC directamente (pygame soporta FLAC)
"""
import pygame.mixer
from pathlib import Path
import threading


class MaestroSampler:
    """Reproductor de samples de piano real con 5 capas de velocidad"""
    
    def __init__(self, samples_dir="piano_samples"):
        self.samples_dir = Path(samples_dir)
        self.samples = {}  # {nota_midi: {velocity_layer: Sound}}
        self.active_sounds = {}  # {nota_midi: Sound actualmente sonando}
        self.active_channels = {}  # {nota_midi: Channel object}
        import time
        self.note_start_times = {}  # {nota_midi: timestamp} para rastrear cuándo empezó cada nota
        
        # Mapeo de capas de velocidad (igual que convert_samples.py)
        self.velocity_layers = {
            'p': (0, 29),       # piano
            'mp': (30, 59),     # mezzo-piano
            'mf': (60, 89),     # mezzo-forte
            'f': (90, 108),     # forte
            'ff': (109, 127)    # fortissimo
        }
        
        # Nombres de carpetas
        self.layer_folders = {
            'p': 'piano',
            'mp': 'mezzo_piano',
            'mf': 'mezzo_forte',
            'f': 'forte',
            'ff': 'fortissimo'
        }
        
        self._load_samples()
    
    def _load_samples(self):
        """Carga todos los samples FLAC en memoria"""
        print("Cargando samples del Maestro Concert Grand Piano...")
        
        for layer, folder in self.layer_folders.items():
            layer_path = self.samples_dir / folder
            if not layer_path.exists():
                print(f"⚠ No se encuentra la carpeta: {layer_path}")
                continue
            
            # Cargar todos los archivos .flac de esta capa
            flac_files = list(layer_path.glob("note_*.flac"))
            
            for flac_file in flac_files:
                # Extraer número de nota del nombre: "note_21.flac" -> 21
                try:
                    note_num = int(flac_file.stem.split('_')[1])
                    
                    # Cargar el sample
                    sound = pygame.mixer.Sound(str(flac_file))
                    
                    # Pre-ajustar volumen para mejor rango dinámico
                    sound.set_volume(0.9)
                    
                    # Guardar en estructura: samples[nota][layer]
                    if note_num not in self.samples:
                        self.samples[note_num] = {}
                    
                    self.samples[note_num][layer] = sound
                    
                except (ValueError, IndexError) as e:
                    print(f"⚠ Error parseando {flac_file.name}: {e}")
        
        # Resumen
        loaded_notes = len(self.samples)
        total_samples = sum(len(layers) for layers in self.samples.values())
        print(f"✓ Cargados {total_samples} samples para {loaded_notes} notas")
    
    def _get_velocity_layer(self, velocity):
        """Determina qué capa de velocidad usar según la velocidad MIDI (0-127)"""
        for layer, (min_vel, max_vel) in self.velocity_layers.items():
            if min_vel <= velocity <= max_vel:
                return layer
        return 'mf'  # Fallback a mezzo-forte
    
    def play_note(self, note, velocity=64, duration=None):
        """
        Reproduce una nota con el sample correspondiente
        
        Args:
            note (int): Número MIDI de la nota (21-108)
            velocity (int): Velocidad MIDI (0-127)
            duration (float): Duración en segundos (None = hasta stop)
        """
        if note not in self.samples:
            print(f"⚠ No hay sample para nota {note}")
            return
        
        # Seleccionar capa de velocidad
        layer = self._get_velocity_layer(velocity)
        
        # Obtener sample (fallback a otras capas si no existe)
        sound = None
        for fallback_layer in [layer, 'mf', 'mp', 'f', 'p', 'ff']:
            if fallback_layer in self.samples[note]:
                sound = self.samples[note][fallback_layer]
                break
        
        if sound is None:
            print(f"⚠ No se encontró sample para nota {note}")
            return
        
        # Si la misma nota ya está sonando, detenerla primero
        if note in self.active_channels:
            try:
                self.active_channels[note].stop()
            except:
                pass
        
        # Reproducir el sample
        try:
            import time
            # Limitar duración del sample a 4 segundos para liberar canales más rápido
            channel = sound.play(maxtime=4000)  # Máximo 4 segundos
            
            if channel is not None:
                self.active_sounds[note] = sound
                self.active_channels[note] = channel
                self.note_start_times[note] = time.time()
            else:
                # No hay canales disponibles - forzar liberación de notas viejas
                self._cleanup_old_notes()
                # Intentar de nuevo
                channel = sound.play(maxtime=4000)
                if channel is not None:
                    self.active_sounds[note] = sound
                    self.active_channels[note] = channel
                    self.note_start_times[note] = time.time()
        except Exception as e:
            print(f"⚠ Error reproduciendo nota {note}: {e}")
        
        # Auto-detener después de duration (si se especifica)
        if duration is not None:
            def stop_after():
                import time
                time.sleep(duration)
                self.stop_note(note)
            
            threading.Thread(target=stop_after, daemon=True).start()
    
    def _cleanup_old_notes(self, max_age=2.0):
        """
        Limpia notas que llevan sonando más de max_age segundos
        """
        import time
        current_time = time.time()
        notes_to_remove = []
        
        for note, start_time in list(self.note_start_times.items()):
            if current_time - start_time > max_age:
                notes_to_remove.append(note)
        
        for note in notes_to_remove:
            try:
                if note in self.active_channels:
                    self.active_channels[note].fadeout(250)  # Fadeout más suave
                    del self.active_channels[note]
                if note in self.active_sounds:
                    del self.active_sounds[note]
                if note in self.note_start_times:
                    del self.note_start_times[note]
            except:
                pass
    
    def stop_note(self, note):
        """
        Detiene una nota que está sonando
        """
        try:
            if note in self.active_channels:
                self.active_channels[note].fadeout(250)  # Fadeout más suave
                del self.active_channels[note]
            if note in self.active_sounds:
                del self.active_sounds[note]
            if note in self.note_start_times:
                del self.note_start_times[note]
        except Exception as e:
            pass
    
    def stop_all(self):
        """Detiene todas las notas"""
        try:
            # Detener todos los canales activos
            for channel in self.active_channels.values():
                try:
                    channel.stop()
                except:
                    pass
            
            self.active_sounds.clear()
            self.active_channels.clear()
            self.note_start_times.clear()
            
            # Detener todos los canales de pygame
            pygame.mixer.stop()
        except Exception as e:
            print(f"⚠ Error deteniendo todas las notas: {e}")
    
    def get_channel_info(self):
        """Obtiene información sobre el uso de canales (para debug)"""
        try:
            total = pygame.mixer.get_num_channels()
            busy = sum(1 for i in range(total) if pygame.mixer.Channel(i).get_busy())
            return f"Canales: {busy}/{total} ocupados"
        except:
            return "Info no disponible"


# Test standalone
if __name__ == "__main__":
    import time
    
    print("Inicializando pygame.mixer...")
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
    
    print("Creando sampler...")
    sampler = MaestroSampler()
    
    print("\nProbando algunas notas...")
    
    # Do central (C4 = MIDI 60) con diferentes velocidades
    print("Do central - pianissimo")
    sampler.play_note(60, velocity=20)
    time.sleep(2)
    
    print("Do central - fortissimo")
    sampler.play_note(60, velocity=120)
    time.sleep(2)
    
    # Acorde (C-E-G)
    print("Acorde Do Mayor")
    sampler.play_note(60, velocity=80)  # C
    sampler.play_note(64, velocity=80)  # E
    sampler.play_note(67, velocity=80)  # G
    time.sleep(3)
    
    sampler.stop_all()
    print("\n✓ Test completado")
