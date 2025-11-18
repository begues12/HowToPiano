#!/usr/bin/env python3
"""
Sistema de Sonido de Piano Realista
Genera sonido de piano con armónicos y envelope ADSR profesional
"""
import numpy as np

try:
    import pygame.mixer
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    print("⚠️ pygame no disponible - sonido deshabilitado")


class PianoSound:
    """Sistema de sonido de piano realista con armónicos y múltiples perfiles"""
    
    # Perfiles de sonido de piano
    SOUND_PROFILES = {
        'acoustic': {
            'name': '🎼 Acoustic Grand Piano',
            'harmonics': [(1.00, 1.00), (0.45, 2.00), (0.25, 3.00), (0.15, 4.00), 
                          (0.12, 5.00), (0.09, 6.00), (0.07, 7.00), (0.05, 8.00), (0.03, 9.00)],
            'reverb': 0.15,
            'brightness': 0.90,
            'duration': 0.7  # Más largo para mejor legato
        },
        'grand': {
            'name': '🎹 Piano de Cola',
            'harmonics': [(1.00, 1.00), (0.50, 2.00), (0.30, 3.00), (0.20, 4.00), 
                          (0.15, 5.00), (0.10, 6.00), (0.08, 7.00), (0.05, 8.00)],
            'reverb': 0.12,
            'brightness': 1.0,
            'duration': 0.7
        },
        'bright': {
            'name': '✨ Piano Brillante',
            'harmonics': [(1.00, 1.00), (0.65, 2.00), (0.50, 3.00), (0.35, 4.00), 
                          (0.28, 5.00), (0.22, 6.00), (0.18, 7.00), (0.12, 8.00)],
            'reverb': 0.06,
            'brightness': 1.4,  # Más brillante
            'duration': 0.6  # Balance entre articulación y legato
        },
        'mellow': {
            'name': '🌙 Piano Suave',
            'harmonics': [(1.00, 1.00), (0.35, 2.00), (0.18, 3.00), (0.08, 4.00), 
                          (0.05, 5.00), (0.03, 6.00), (0.02, 7.00), (0.01, 8.00)],
            'reverb': 0.20,  # Más reverb
            'brightness': 0.6,  # Más suave
            'duration': 0.8  # El más largo para máximo legato
        },
        'electric': {
            'name': '⚡ Piano Eléctrico',
            'harmonics': [(1.00, 1.00), (0.70, 2.00), (0.45, 3.00), (0.30, 4.00), 
                          (0.25, 5.00), (0.20, 6.00), (0.15, 7.00), (0.10, 8.00)],
            'reverb': 0.03,  # Casi sin reverb
            'brightness': 1.2,
            'duration': 0.5  # Rhodes mantiene articulación
        }
    }
    
    def __init__(self, volume=0.5, profile='grand'):
        self.enabled = PYGAME_AVAILABLE
        self.volume = volume
        self.sounds = {}
        self.current_profile = profile
        
        if self.enabled:
            try:
                # Mejor calidad de audio: 44.1kHz, 16-bit, estéreo, buffer pequeño
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
                # Aumentar el número de canales de mezcla para acordes grandes
                pygame.mixer.set_num_channels(64)  # Permite hasta 64 notas simultáneas
                print(f"✅ Sistema de audio inicializado (44.1kHz, 64 canales) - {self.SOUND_PROFILES[profile]['name']}")
            except Exception as e:
                print(f"❌ Error inicializando audio: {e}")
                self.enabled = False
    
    def set_profile(self, profile: str):
        """Cambia el perfil de sonido"""
        if profile in self.SOUND_PROFILES:
            self.current_profile = profile
            self.sounds.clear()  # Limpiar caché para regenerar con nuevo perfil
            print(f"🎵 Perfil cambiado a: {self.SOUND_PROFILES[profile]['name']}")
    
    def play_note(self, note: int, velocity: int = 80):
        """
        Genera y reproduce una nota de piano realista con dinámica.
        
        Args:
            note: Número MIDI de la nota (21-108)
            velocity: Velocidad MIDI (0-127) para expresión dinámica
        """
        if not self.enabled or note < 21 or note > 108:
            return
        
        try:
            # Generar clave de caché con nota y velocidad cuantizada
            velocity_level = velocity // 32  # 4 niveles de dinámica
            cache_key = (note, velocity_level)
            
            # Usar caché si ya existe
            if cache_key not in self.sounds:
                self.sounds[cache_key] = self._generate_piano_note(note, velocity)
            
            self.sounds[cache_key].play()
        except Exception as e:
            print(f"❌ Error reproduciendo nota {note}: {e}")
    
    def _generate_piano_note(self, note: int, velocity: int = 80):
        """
        Genera una nota de piano con armónicos, envelope ADSR y dinámica expresiva.
        
        Args:
            note: Número MIDI de la nota
            velocity: Velocidad MIDI (0-127) para expresión
        """
        # Obtener configuración del perfil actual
        profile = self.SOUND_PROFILES[self.current_profile]
        
        # Calcular frecuencia fundamental
        freq = 440.0 * (2.0 ** ((note - 69) / 12.0))
        
        # Configuración del perfil
        duration = profile['duration']
        sample_rate = 44100
        t = np.linspace(0, duration, int(sample_rate * duration))
        
        # NORMALIZAR Y REALZAR VELOCIDAD para mejor expresión
        # Muchos MIDIs usan rango medio (40-100), necesitamos expandirlo
        vel_normalized = velocity / 127.0
        
        # Aplicar curva para realzar dinámicas medias
        # Velocidades bajas (<40): mantener suaves
        # Velocidades medias (40-90): expandir a rango más amplio
        # Velocidades altas (>90): mantener fuertes
        if velocity < 40:
            vel_factor = vel_normalized * 0.8  # Suaves: 0-0.25
        elif velocity < 90:
            # Expandir rango medio
            vel_factor = 0.25 + ((vel_normalized - 0.31) * 1.5)  # Medias: 0.25-0.85
        else:
            vel_factor = 0.85 + ((vel_normalized - 0.71) * 0.5)  # Fuertes: 0.85-1.0
        
        vel_factor = max(0.2, min(1.0, vel_factor))  # Clamp entre 0.2-1.0
        
        # ARMÓNICOS DEL PERFIL (ajustados por velocidad y brillo)
        # Notas fuertes tienen más armónicos agudos (más brillantes)
        # Notas suaves tienen sonido más cálido
        base_brightness = profile['brightness']
        brightness = base_brightness * (0.7 + (vel_factor * 0.3))  # 0.7-1.0 del perfil
        
        # Usar armónicos del perfil
        harmonics = []
        for amp, harmonic_num in profile['harmonics']:
            adjusted_amp = amp * brightness
            if harmonic_num > 6:
                # Armónicos altos solo en notas fuertes
                adjusted_amp *= vel_factor
            harmonics.append((adjusted_amp, harmonic_num))
        
        # Generar onda compleja
        wave = np.zeros_like(t)
        for amplitude, harmonic in harmonics:
            wave += amplitude * np.sin(2 * np.pi * freq * harmonic * t)
        
        # Normalizar
        wave = wave / np.max(np.abs(wave))
        
        # ENVELOPE ADSR CON MEJOR LEGATO
        # Notas se conectan mejor para dar más ritmo y fluidez
        attack_time = 0.002 + (0.004 * (1 - vel_factor))  # 2-6ms (rápido pero suave)
        decay_time = 0.03 + (0.05 * vel_factor)           # 30-80ms (transición suave)
        sustain_level = 0.25 + (0.35 * vel_factor)        # 25-60% (más sostenido para legato)
        release_time = 0.15 + (0.20 * vel_factor)         # 0.15-0.35s (release más largo para conectar notas)
        
        attack_samples = int(sample_rate * attack_time)
        decay_samples = int(sample_rate * decay_time)
        release_samples = int(sample_rate * release_time)
        sustain_samples = len(t) - attack_samples - decay_samples - release_samples
        
        # Construir envelope
        envelope = np.ones_like(t)
        
        # Attack: 0 → 1 (rápido)
        if attack_samples > 0:
            envelope[:attack_samples] = np.linspace(0, 1, attack_samples)
        
        # Decay: 1 → sustain_level
        if decay_samples > 0:
            decay_start = attack_samples
            decay_end = decay_start + decay_samples
            envelope[decay_start:decay_end] = np.linspace(1, sustain_level, decay_samples)
        
        # Sustain: mantener nivel
        if sustain_samples > 0:
            sustain_start = attack_samples + decay_samples
            sustain_end = sustain_start + sustain_samples
            envelope[sustain_start:sustain_end] = sustain_level
        
        # Release: decay exponencial (más natural)
        if release_samples > 0:
            release_start = len(t) - release_samples
            release_curve = np.exp(-3 * np.linspace(0, 1, release_samples))
            envelope[release_start:] = sustain_level * release_curve
        
        # Aplicar envelope, velocidad y volumen
        wave = wave * envelope * vel_factor * self.volume
        
        # Añadir reverberación del perfil (más reverb en notas suaves)
        reverb_delay = int(sample_rate * 0.035)  # 35ms
        reverb_base = profile['reverb']
        reverb_amount = reverb_base + (0.08 * (1 - vel_factor))  # Ajustar por dinámica
        if len(wave) > reverb_delay:
            wave[reverb_delay:] += wave[:-reverb_delay] * reverb_amount
        
        # Añadir ligera variación estéreo (más natural)
        wave_left = wave * (0.98 + 0.02 * np.random.random())
        wave_right = wave * (0.98 + 0.02 * np.random.random())
        
        # Convertir a 16-bit stereo con variación
        wave_left = np.clip(wave_left, -1.0, 1.0)
        wave_right = np.clip(wave_right, -1.0, 1.0)
        wave_left = np.int16(wave_left * 32767)
        wave_right = np.int16(wave_right * 32767)
        
        return pygame.mixer.Sound(np.column_stack((wave_left, wave_right)))
    
    def set_volume(self, volume: float):
        """Ajusta el volumen (0.0 a 1.0)"""
        self.volume = max(0.0, min(1.0, volume))
        # Regenerar sonidos con nuevo volumen
        self.sounds.clear()
    
    def clear_cache(self):
        """Limpia la caché de sonidos"""
        self.sounds.clear()


if __name__ == "__main__":
    # Test del sistema de sonido
    print("🎹 Test de PianoSound")
    piano = PianoSound(volume=0.5)
    
    if piano.enabled:
        import time
        print("Tocando escala de Do mayor...")
        scale = [60, 62, 64, 65, 67, 69, 71, 72]  # C D E F G A B C
        for note in scale:
            print(f"  ♪ Nota {note}")
            piano.play_note(note)
            time.sleep(0.5)
        print("✅ Test completado")
    else:
        print("❌ Sistema de audio no disponible")
