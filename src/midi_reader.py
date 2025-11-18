"""
MIDI Reader - Lee archivos MIDI desde USB y procesa eventos
"""
import os
from pathlib import Path
from typing import Generator, Optional, List
from mido import MidiFile, Message


class MidiReader:
    """Clase para leer y procesar archivos MIDI desde USB"""
    
    def __init__(self, usb_mount_point: str = "/media/pi"):
        """
        Inicializa el lector MIDI
        
        Args:
            usb_mount_point: Punto de montaje del USB en Raspberry Pi
        """
        self.usb_mount_point = usb_mount_point
        self.current_file: Optional[MidiFile] = None
        self.current_file_path: Optional[str] = None
        
    def list_midi_files(self) -> List[str]:
        """
        Lista todos los archivos MIDI disponibles en el USB
        
        Returns:
            Lista de rutas completas a archivos .mid
        """
        midi_files = []
        
        # Buscar en el punto de montaje USB
        if os.path.exists(self.usb_mount_point):
            for root, dirs, files in os.walk(self.usb_mount_point):
                for file in files:
                    if file.lower().endswith(('.mid', '.midi')):
                        full_path = os.path.join(root, file)
                        midi_files.append(full_path)
        
        return sorted(midi_files)
    
    def load_midi_file(self, file_path: str) -> bool:
        """
        Carga un archivo MIDI
        
        Args:
            file_path: Ruta al archivo MIDI
            
        Returns:
            True si se cargó correctamente, False en caso contrario
        """
        try:
            self.current_file = MidiFile(file_path)
            self.current_file_path = file_path
            print(f"✓ Archivo MIDI cargado: {os.path.basename(file_path)}")
            print(f"  Duración: {self.current_file.length:.2f} segundos")
            print(f"  Pistas: {len(self.current_file.tracks)}")
            return True
        except Exception as e:
            print(f"✗ Error cargando archivo MIDI: {e}")
            return False
    
    def get_midi_info(self) -> dict:
        """
        Obtiene información del archivo MIDI cargado
        
        Returns:
            Diccionario con información del archivo
        """
        if not self.current_file:
            return {}
        
        return {
            'filename': os.path.basename(self.current_file_path) if self.current_file_path else "Unknown",
            'duration': self.current_file.length,
            'tracks': len(self.current_file.tracks),
            'ticks_per_beat': self.current_file.ticks_per_beat,
            'type': self.current_file.type
        }
    
    def play_midi_events(self) -> Generator[Message, None, None]:
        """
        Genera eventos MIDI en tiempo real con timing correcto
        
        Yields:
            Mensajes MIDI (note_on, note_off, etc.)
        """
        if not self.current_file:
            print("✗ No hay archivo MIDI cargado")
            return
        
        print(f"▶ Reproduciendo: {os.path.basename(self.current_file_path)}")
        
        # play() maneja automáticamente el timing
        for msg in self.current_file.play():
            # Solo procesar mensajes de nota
            if msg.type in ['note_on', 'note_off']:
                yield msg
    
    def get_all_notes(self) -> List[int]:
        """
        Obtiene todas las notas únicas en el archivo MIDI
        Útil para verificar el rango del teclado
        
        Returns:
            Lista de números de nota MIDI (21-108 para piano de 88 teclas)
        """
        if not self.current_file:
            return []
        
        notes = set()
        for track in self.current_file.tracks:
            for msg in track:
                if msg.type in ['note_on', 'note_off']:
                    notes.add(msg.note)
        
        return sorted(list(notes))
    
    def get_note_range(self) -> tuple:
        """
        Obtiene el rango de notas (mínimo y máximo)
        
        Returns:
            Tupla (nota_minima, nota_maxima)
        """
        notes = self.get_all_notes()
        if not notes:
            return (0, 0)
        return (min(notes), max(notes))


if __name__ == "__main__":
    # Ejemplo de uso
    reader = MidiReader()
    
    # Listar archivos MIDI
    print("Archivos MIDI disponibles:")
    files = reader.list_midi_files()
    for i, file in enumerate(files, 1):
        print(f"  {i}. {os.path.basename(file)}")
    
    # Cargar primer archivo si existe
    if files:
        reader.load_midi_file(files[0])
        info = reader.get_midi_info()
        print(f"\nInformación del archivo:")
        for key, value in info.items():
            print(f"  {key}: {value}")
        
        note_range = reader.get_note_range()
        print(f"\nRango de notas: {note_range[0]} - {note_range[1]}")
