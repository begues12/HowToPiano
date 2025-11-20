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
        
        # Reproducir el sample (permitir múltiples instancias del mismo sample)
        # Esto simula un piano real donde puedes tocar la misma nota varias veces
        sound.play()
        self.active_sounds[note] = sound
        
        # Auto-detener después de duration (si se especifica)
        if duration is not None:
            def stop_after():
                import time
                time.sleep(duration)
                self.stop_note(note)
            
            threading.Thread(target=stop_after, daemon=True).start()
    
    def stop_note(self, note):
        """
        Detiene una nota que está sonando
        Para notas muy cortas, simplemente dejar que el sample termine naturalmente
        """
        if note in self.active_sounds:
            # No hacer nada - dejar que el sample de piano suene completamente
            # El piano real tiene resonancia y decay natural
            pass
    
    def stop_all(self):
        """Detiene todas las notas (limpia el registro pero deja que suenen naturalmente)"""
        self.active_sounds.clear()


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
