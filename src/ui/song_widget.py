"""
Contenedor y gestor de canción con todas las notas.
Maneja tempo, time signature, y el conjunto completo de notas como widgets.
"""

from typing import List, Tuple, Optional
from PyQt6.QtGui import QPainter
from PyQt6.QtCore import QRectF
from .note_widget import NoteWidget, NoteType


class TimeSignature:
    """Representa una armadura de compás (time signature)"""
    def __init__(self, numerator: int = 4, denominator: int = 4):
        self.numerator = numerator  # Número de beats por compás
        self.denominator = denominator  # Tipo de nota que cuenta como un beat
    
    def beats_per_measure(self) -> int:
        """Retorna el número de beats por compás"""
        return self.numerator
    
    def beat_duration(self) -> float:
        """Retorna la duración de un beat en términos de quarter notes"""
        return 4.0 / self.denominator
    
    def __repr__(self):
        return f"{self.numerator}/{self.denominator}"


class SongWidget:
    """
    Contenedor principal de la canción con gestión completa de notas.
    Maneja tempo, time signature, y todas las operaciones sobre el conjunto de notas.
    """
    
    def __init__(self, tempo: float = 120.0, time_signature: Optional[TimeSignature] = None):
        """
        Inicializa el widget de canción.
        
        Args:
            tempo: Tempo en BPM (beats per minute)
            time_signature: Armadura de compás (por defecto 4/4)
        """
        self.tempo = tempo
        self.time_signature = time_signature or TimeSignature(4, 4)
        self.notes: List[NoteWidget] = []
        
        # Configuración de visualización
        self.pixels_per_second = 200.0  # Píxeles por segundo (se ajusta con zoom)
        self.zoom_scale = 1.0
        
        # Información de la canción
        self.total_duration = 0.0
        self._notes_sorted = True  # Optimización: evitar ordenar si ya está ordenado
    
    def set_tempo(self, tempo: float):
        """
        Cambia el tempo de la canción.
        Actualiza todas las notas existentes.
        
        Args:
            tempo: Nuevo tempo en BPM
        """
        old_tempo = self.tempo
        self.tempo = tempo
        
        # Recalcular duraciones de notas en beats
        tempo_ratio = tempo / old_tempo
        for note in self.notes:
            note.tempo = tempo
            note.duration_beats = (note.duration * tempo) / 60.0
            # Puede cambiar el tipo de nota visual si la duración cambia mucho
            note.note_type = NoteType.from_duration(note.duration_beats)
    
    def set_time_signature(self, numerator: int, denominator: int):
        """Cambia la armadura de compás"""
        self.time_signature = TimeSignature(numerator, denominator)
    
    def set_zoom(self, zoom: float):
        """
        Cambia el nivel de zoom de la visualización.
        
        Args:
            zoom: Factor de zoom (1.0 = normal, 2.0 = doble, 0.5 = mitad)
        """
        self.zoom_scale = max(0.1, min(zoom, 5.0))  # Limitar entre 0.1x y 5x
        self._update_pixels_per_second()
    
    def _update_pixels_per_second(self):
        """Actualiza los píxeles por segundo basándose en tempo y zoom"""
        # Base: 200 px/s a 120 BPM
        tempo_factor = self.tempo / 120.0
        self.pixels_per_second = 200.0 * tempo_factor * self.zoom_scale
    
    def get_pixels_per_beat(self) -> float:
        """Retorna cuántos píxeles representa un beat"""
        # Un beat = 60/tempo segundos
        seconds_per_beat = 60.0 / self.tempo
        return self.pixels_per_second * seconds_per_beat
    
    def convert_time_to_position(self, time_seconds: float) -> float:
        """
        Convierte tiempo en segundos a posición X en píxeles.
        
        Args:
            time_seconds: Tiempo en segundos
            
        Returns:
            Posición X en píxeles
        """
        return time_seconds * self.pixels_per_second
    
    def convert_position_to_time(self, x_pixels: float) -> float:
        """
        Convierte posición X en píxeles a tiempo en segundos.
        
        Args:
            x_pixels: Posición X en píxeles
            
        Returns:
            Tiempo en segundos
        """
        return x_pixels / self.pixels_per_second
    
    def add_note(
        self,
        pitch: int,
        start_time: float,
        duration: float,
        velocity: int = 64,
        note_type: Optional[str] = None
    ) -> NoteWidget:
        """
        Añade una nota a la canción.
        
        Args:
            pitch: Nota MIDI (0-127)
            start_time: Tiempo de inicio en segundos
            duration: Duración en segundos
            velocity: Velocidad MIDI (0-127)
            note_type: Tipo de figura musical (opcional)
            
        Returns:
            La nota widget creada
        """
        note = NoteWidget(
            pitch=pitch,
            start_time=start_time,
            duration=duration,
            velocity=velocity,
            note_type=note_type,
            tempo=self.tempo
        )
        
        self.notes.append(note)
        self._notes_sorted = False
        
        # Actualizar duración total
        note_end = start_time + duration
        if note_end > self.total_duration:
            self.total_duration = note_end
        
        return note
    
    def add_note_widget(self, note: NoteWidget):
        """
        Añade un NoteWidget ya creado.
        
        Args:
            note: Widget de nota a añadir
        """
        self.notes.append(note)
        self._notes_sorted = False
        
        note_end = note.start_time + note.duration
        if note_end > self.total_duration:
            self.total_duration = note_end
    
    def remove_note(self, note: NoteWidget) -> bool:
        """
        Elimina una nota de la canción.
        
        Args:
            note: Nota a eliminar
            
        Returns:
            True si se eliminó correctamente
        """
        if note in self.notes:
            self.notes.remove(note)
            return True
        return False
    
    def clear_notes(self):
        """Elimina todas las notas"""
        self.notes.clear()
        self.total_duration = 0.0
        self._notes_sorted = True
    
    def get_notes_at_time(self, time: float, tolerance: float = 0.01) -> List[NoteWidget]:
        """
        Obtiene todas las notas que están sonando en un tiempo específico.
        
        Args:
            time: Tiempo en segundos
            tolerance: Tolerancia en segundos para considerar una nota activa
            
        Returns:
            Lista de notas activas en ese tiempo
        """
        active_notes = []
        for note in self.notes:
            if (note.start_time - tolerance) <= time <= (note.get_end_time() + tolerance):
                active_notes.append(note)
        return active_notes
    
    def get_notes_in_range(self, start_time: float, end_time: float) -> List[NoteWidget]:
        """
        Obtiene todas las notas en un rango de tiempo.
        
        Args:
            start_time: Tiempo de inicio en segundos
            end_time: Tiempo de fin en segundos
            
        Returns:
            Lista de notas en ese rango
        """
        notes_in_range = []
        for note in self.notes:
            # Nota comienza o termina dentro del rango, o abarca todo el rango
            if (start_time <= note.start_time <= end_time or
                start_time <= note.get_end_time() <= end_time or
                (note.start_time <= start_time and note.get_end_time() >= end_time)):
                notes_in_range.append(note)
        return notes_in_range
    
    def get_notes_in_viewport(
        self,
        viewport_left: float,
        viewport_right: float,
        preparation_time: float = 3.0
    ) -> List[NoteWidget]:
        """
        Obtiene las notas visibles en el viewport actual.
        
        Args:
            viewport_left: Posición X izquierda del viewport
            viewport_right: Posición X derecha del viewport
            preparation_time: Tiempo de preparación en segundos
            
        Returns:
            Lista de notas visibles
        """
        # Convertir posiciones a tiempo
        time_left = self.convert_position_to_time(viewport_left) - preparation_time
        time_right = self.convert_position_to_time(viewport_right) - preparation_time
        
        return self.get_notes_in_range(time_left, time_right)
    
    def _ensure_sorted(self):
        """Asegura que las notas estén ordenadas por tiempo de inicio"""
        if not self._notes_sorted:
            self.notes.sort(key=lambda n: (n.start_time, n.pitch))
            self._notes_sorted = True
    
    def render_all(
        self,
        painter: QPainter,
        current_time: float,
        staff_lines_y: List[float],
        viewport_bounds: QRectF,
        preparation_time: float = 3.0
    ):
        """
        Renderiza todas las notas visibles.
        
        Args:
            painter: QPainter para dibujar
            current_time: Tiempo actual de reproducción
            staff_lines_y: Posiciones Y de las líneas del pentagrama
            viewport_bounds: Límites del viewport visible
            preparation_time: Tiempo de preparación en segundos
        """
        self._ensure_sorted()
        
        # Calcular notas visibles
        visible_notes = self.get_notes_in_viewport(
            viewport_bounds.left(),
            viewport_bounds.right(),
            preparation_time
        )
        
        # Renderizar cada nota
        for note in visible_notes:
            # Calcular posición X basándose en tiempo + preparación
            x = self.convert_time_to_position(note.start_time + preparation_time)
            
            # Calcular posición Y basándose en el pitch
            # (Aquí necesitamos la lógica del staff widget para mapear MIDI note a Y)
            y = self._calculate_note_y_position(note.pitch, staff_lines_y)
            
            # Verificar si está visible
            if note.is_visible(x, viewport_bounds.left(), viewport_bounds.right()):
                note.render(painter, x, y)
    
    def _calculate_note_y_position(self, midi_note: int, staff_lines_y: List[float]) -> float:
        """
        Calcula la posición Y de una nota en el pentagrama.
        
        Args:
            midi_note: Nota MIDI (0-127)
            staff_lines_y: Posiciones Y de las líneas del pentagrama
            
        Returns:
            Posición Y en píxeles
        """
        # Esta es una simplificación - el cálculo real debería venir de StaffWidget
        # Por ahora, usar una aproximación lineal
        
        if len(staff_lines_y) < 5:
            # Fallback si no hay líneas del pentagrama
            return 300.0 - (midi_note - 60) * 3.5
        
        # Usar el centro del pentagrama como referencia (línea del medio = D4 = MIDI 62)
        middle_line_y = staff_lines_y[2]  # Tercera línea (B4 = 71)
        reference_midi = 71  # B4 en la línea del medio
        
        # Cada semitono = medio espacio entre líneas
        line_spacing = staff_lines_y[1] - staff_lines_y[0]
        pixels_per_semitone = line_spacing / 2.0
        
        # Calcular offset desde la referencia
        semitone_offset = midi_note - reference_midi
        y = middle_line_y - (semitone_offset * pixels_per_semitone)
        
        return y
    
    def get_stats(self) -> dict:
        """Retorna estadísticas de la canción"""
        self._ensure_sorted()
        
        note_types_count = {}
        for note in self.notes:
            note_types_count[note.note_type] = note_types_count.get(note.note_type, 0) + 1
        
        return {
            'total_notes': len(self.notes),
            'duration_seconds': self.total_duration,
            'duration_measures': self.total_duration / (60.0 / self.tempo * self.time_signature.beats_per_measure()),
            'tempo': self.tempo,
            'time_signature': str(self.time_signature),
            'note_types': note_types_count,
            'pitch_range': (
                min(n.pitch for n in self.notes) if self.notes else 0,
                max(n.pitch for n in self.notes) if self.notes else 0
            )
        }
    
    def __repr__(self):
        return f"SongWidget(notes={len(self.notes)}, tempo={self.tempo}, " \
               f"time_sig={self.time_signature}, duration={self.total_duration:.2f}s)"
