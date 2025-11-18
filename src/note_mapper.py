"""
Note Mapper - Mapea notas MIDI a índices de LED
"""
from typing import Optional, Dict


class NoteMapper:
    """Mapea notas MIDI a posiciones de LED en el teclado"""
    
    # Configuraciones predefinidas de teclados
    KEYBOARD_CONFIGS = {
        'piano_88': {
            'name': 'Piano de 88 teclas',
            'first_note': 21,   # A0
            'last_note': 108,   # C8
            'num_keys': 88
        },
        'keyboard_61': {
            'name': 'Teclado de 61 teclas',
            'first_note': 36,   # C2
            'last_note': 96,    # C7
            'num_keys': 61
        },
        'keyboard_49': {
            'name': 'Teclado de 49 teclas',
            'first_note': 36,   # C2
            'last_note': 84,    # C6
            'num_keys': 49
        },
        'keyboard_25': {
            'name': 'Mini teclado 25 teclas',
            'first_note': 48,   # C3
            'last_note': 72,    # C5
            'num_keys': 25
        }
    }
    
    # Nombres de notas MIDI
    NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    
    def __init__(self, config_name: str = 'piano_88', 
                 first_note: Optional[int] = None,
                 last_note: Optional[int] = None):
        """
        Inicializa el mapeador de notas
        
        Args:
            config_name: Nombre de configuración predefinida
            first_note: Nota MIDI inicial (sobreescribe config)
            last_note: Nota MIDI final (sobreescribe config)
        """
        if config_name in self.KEYBOARD_CONFIGS:
            config = self.KEYBOARD_CONFIGS[config_name]
            self.first_note = first_note or config['first_note']
            self.last_note = last_note or config['last_note']
            self.num_leds = self.last_note - self.first_note + 1
            print(f"✓ Configuración: {config['name']}")
        else:
            # Configuración manual
            self.first_note = first_note or 21
            self.last_note = last_note or 108
            self.num_leds = self.last_note - self.first_note + 1
            print(f"✓ Configuración personalizada")
        
        print(f"  Rango: Nota {self.first_note} a {self.last_note}")
        print(f"  LEDs requeridos: {self.num_leds}")
        
        # Caché de mapeo para optimización
        self._note_to_led_cache: Dict[int, int] = {}
        self._build_cache()
    
    def _build_cache(self):
        """Construye caché de mapeo nota → LED"""
        for note in range(self.first_note, self.last_note + 1):
            led_index = note - self.first_note
            self._note_to_led_cache[note] = led_index
    
    def note_to_led(self, note: int) -> Optional[int]:
        """
        Convierte una nota MIDI a índice de LED
        
        Args:
            note: Número de nota MIDI (0-127)
            
        Returns:
            Índice de LED (0 a num_leds-1) o None si está fuera de rango
        """
        if note in self._note_to_led_cache:
            return self._note_to_led_cache[note]
        return None
    
    def led_to_note(self, led_index: int) -> Optional[int]:
        """
        Convierte un índice de LED a nota MIDI
        
        Args:
            led_index: Índice del LED (0 a num_leds-1)
            
        Returns:
            Número de nota MIDI o None si está fuera de rango
        """
        if 0 <= led_index < self.num_leds:
            return self.first_note + led_index
        return None
    
    def is_note_in_range(self, note: int) -> bool:
        """
        Verifica si una nota está en el rango del teclado
        
        Args:
            note: Número de nota MIDI
            
        Returns:
            True si la nota está en rango
        """
        return self.first_note <= note <= self.last_note
    
    def get_note_name(self, note: int) -> str:
        """
        Obtiene el nombre de una nota MIDI
        
        Args:
            note: Número de nota MIDI (0-127)
            
        Returns:
            Nombre de nota con octava (ej: "C4", "A#3")
        """
        note_index = note % 12
        octave = (note // 12) - 1
        return f"{self.NOTE_NAMES[note_index]}{octave}"
    
    def get_led_info(self, led_index: int) -> dict:
        """
        Obtiene información completa de un LED
        
        Args:
            led_index: Índice del LED
            
        Returns:
            Diccionario con nota MIDI, nombre, etc.
        """
        note = self.led_to_note(led_index)
        if note is None:
            return {}
        
        return {
            'led_index': led_index,
            'midi_note': note,
            'note_name': self.get_note_name(note),
            'is_white_key': self._is_white_key(note)
        }
    
    def _is_white_key(self, note: int) -> bool:
        """
        Determina si una nota corresponde a tecla blanca
        
        Args:
            note: Número de nota MIDI
            
        Returns:
            True si es tecla blanca (C, D, E, F, G, A, B)
        """
        # Teclas blancas: C, D, E, F, G, A, B (0, 2, 4, 5, 7, 9, 11)
        white_keys = {0, 2, 4, 5, 7, 9, 11}
        return (note % 12) in white_keys
    
    def get_white_key_indices(self) -> list:
        """
        Obtiene índices de LEDs correspondientes a teclas blancas
        
        Returns:
            Lista de índices de LED para teclas blancas
        """
        white_indices = []
        for led_idx in range(self.num_leds):
            note = self.led_to_note(led_idx)
            if note and self._is_white_key(note):
                white_indices.append(led_idx)
        return white_indices
    
    def get_black_key_indices(self) -> list:
        """
        Obtiene índices de LEDs correspondientes a teclas negras
        
        Returns:
            Lista de índices de LED para teclas negras
        """
        black_indices = []
        for led_idx in range(self.num_leds):
            note = self.led_to_note(led_idx)
            if note and not self._is_white_key(note):
                black_indices.append(led_idx)
        return black_indices
    
    def print_mapping_table(self, limit: int = 20):
        """
        Imprime tabla de mapeo nota → LED
        
        Args:
            limit: Número máximo de filas a mostrar
        """
        print("\n=== Tabla de Mapeo ===")
        print(f"{'LED':<6} {'Nota':<6} {'Nombre':<8} {'Tipo':<8}")
        print("-" * 35)
        
        for led_idx in range(min(limit, self.num_leds)):
            info = self.get_led_info(led_idx)
            key_type = "Blanca" if info['is_white_key'] else "Negra"
            print(f"{info['led_index']:<6} {info['midi_note']:<6} "
                  f"{info['note_name']:<8} {key_type:<8}")
        
        if self.num_leds > limit:
            print(f"... ({self.num_leds - limit} más)")
    
    def validate_midi_file_range(self, min_note: int, max_note: int) -> dict:
        """
        Valida si un archivo MIDI es compatible con el teclado
        
        Args:
            min_note: Nota mínima en el archivo MIDI
            max_note: Nota máxima en el archivo MIDI
            
        Returns:
            Diccionario con información de compatibilidad
        """
        notes_below = max(0, self.first_note - min_note)
        notes_above = max(0, max_note - self.last_note)
        
        compatible = (notes_below == 0 and notes_above == 0)
        
        result = {
            'compatible': compatible,
            'midi_range': (min_note, max_note),
            'keyboard_range': (self.first_note, self.last_note),
            'notes_below_range': notes_below,
            'notes_above_range': notes_above,
            'total_out_of_range': notes_below + notes_above
        }
        
        return result


if __name__ == "__main__":
    # Ejemplos de uso
    print("=== Test del mapeador de notas ===\n")
    
    # Piano completo de 88 teclas
    print("1. Piano de 88 teclas")
    mapper_88 = NoteMapper('piano_88')
    print(f"   LED 0 → Nota {mapper_88.led_to_note(0)} ({mapper_88.get_note_name(21)})")
    print(f"   Nota 60 (C4) → LED {mapper_88.note_to_led(60)}")
    
    # Teclado de 61 teclas
    print("\n2. Teclado de 61 teclas")
    mapper_61 = NoteMapper('keyboard_61')
    print(f"   LED 0 → Nota {mapper_61.led_to_note(0)} ({mapper_61.get_note_name(36)})")
    print(f"   Nota 60 (C4) → LED {mapper_61.note_to_led(60)}")
    
    # Tabla de mapeo
    print("\n3. Tabla de mapeo (primeros 15):")
    mapper_88.print_mapping_table(limit=15)
    
    # Validar rango MIDI
    print("\n4. Validación de archivo MIDI:")
    validation = mapper_88.validate_midi_file_range(21, 108)
    print(f"   Compatible: {validation['compatible']}")
    print(f"   Rango MIDI: {validation['midi_range']}")
    print(f"   Notas fuera de rango: {validation['total_out_of_range']}")
    
    print("\n✓ Test completado")
