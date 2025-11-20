"""
Sistema de widgets de notas musicales para renderizado y gestión individual.
Cada nota es un objeto independiente con su propia lógica de dibujo y comportamiento.
"""

from PyQt6.QtCore import QRectF, QPointF, QObject, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QPainterPath
from dataclasses import dataclass
from typing import Optional, Tuple, List
import math


@dataclass
class NoteProperties:
    """Propiedades de configuración visual de una nota"""
    width: float = 20.0
    height: float = 12.0
    stem_height: float = 35.0
    stem_width: float = 2.0
    flag_width: float = 12.0
    flag_height: float = 15.0
    beam_thickness: float = 3.5


class NoteType:
    """Tipos de figuras musicales con sus duraciones relativas"""
    WHOLE = "whole"           # Redonda - 4 beats
    HALF = "half"             # Blanca - 2 beats
    QUARTER = "quarter"       # Negra - 1 beat
    EIGHTH = "eighth"         # Corchea - 0.5 beats
    SIXTEENTH = "sixteenth"   # Semicorchea - 0.25 beats
    THIRTYSECOND = "thirtysecond"  # Fusa - 0.125 beats
    
    @staticmethod
    def get_duration_in_beats(note_type: str) -> float:
        """Retorna la duración en beats para cada tipo de nota"""
        durations = {
            NoteType.WHOLE: 4.0,
            NoteType.HALF: 2.0,
            NoteType.QUARTER: 1.0,
            NoteType.EIGHTH: 0.5,
            NoteType.SIXTEENTH: 0.25,
            NoteType.THIRTYSECOND: 0.125
        }
        return durations.get(note_type, 1.0)
    
    @staticmethod
    def from_duration(duration_beats: float) -> str:
        """Determina el tipo de nota según la duración en beats"""
        if duration_beats >= 3.5:
            return NoteType.WHOLE
        elif duration_beats >= 1.5:
            return NoteType.HALF
        elif duration_beats >= 0.75:
            return NoteType.QUARTER
        elif duration_beats >= 0.375:
            return NoteType.EIGHTH
        elif duration_beats >= 0.1875:
            return NoteType.SIXTEENTH
        else:
            return NoteType.THIRTYSECOND


class NoteWidget:
    """
    Widget individual para una nota musical.
    Maneja su propio renderizado, posición y propiedades.
    """
    
    def __init__(
        self,
        pitch: int,
        start_time: float,
        duration: float,
        velocity: int = 64,
        note_type: Optional[str] = None,
        tempo: float = 120.0
    ):
        """
        Inicializa un widget de nota.
        
        Args:
            pitch: Nota MIDI (0-127)
            start_time: Tiempo de inicio en segundos
            duration: Duración en segundos
            velocity: Velocidad MIDI (0-127)
            note_type: Tipo de figura musical (opcional, se calcula automáticamente)
            tempo: Tempo en BPM para calcular beats
        """
        self.pitch = pitch
        self.start_time = start_time
        self.duration = duration
        self.velocity = velocity
        self.tempo = tempo
        
        # Calcular duración en beats (quarter notes)
        self.duration_beats = (duration * tempo) / 60.0
        
        # Determinar tipo de nota
        if note_type:
            self.note_type = note_type
        else:
            self.note_type = NoteType.from_duration(self.duration_beats)
        
        # Propiedades visuales
        self.props = NoteProperties()
        
        # Estado visual
        self.is_played = False
        self.is_correct = None  # None, True (verde), False (rojo)
        self.finger = None  # Número de dedo sugerido
        
        # Posición calculada (se actualiza en render)
        self._x = 0.0
        self._y = 0.0
    
    def get_end_time(self) -> float:
        """Retorna el tiempo de finalización de la nota"""
        return self.start_time + self.duration
    
    def get_bounds(self, x: float, y: float) -> QRectF:
        """
        Retorna el rectángulo delimitador de la nota.
        
        Args:
            x: Posición X en píxeles
            y: Posición Y en píxeles
        """
        # Incluir cabeza de nota, plica y corchetes/banderas
        width = self.props.width
        height = self.props.height + self.props.stem_height + 10
        
        # Para corcheas y semicorcheas, añadir espacio para banderas
        if self.note_type in [NoteType.EIGHTH, NoteType.SIXTEENTH, NoteType.THIRTYSECOND]:
            width += self.props.flag_width
        
        return QRectF(x - width/2, y - height, width, height)
    
    def is_visible(self, x: float, viewport_left: float, viewport_right: float) -> bool:
        """
        Verifica si la nota es visible en el viewport actual.
        
        Args:
            x: Posición X de la nota
            viewport_left: Límite izquierdo del viewport
            viewport_right: Límite derecho del viewport
        """
        note_width = self.props.width * 1.5  # Margen extra
        return (x - note_width) <= viewport_right and (x + note_width) >= viewport_left
    
    def render(
        self,
        painter: QPainter,
        x: float,
        y: float,
        color: Optional[QColor] = None
    ):
        """
        Renderiza la nota en la posición especificada.
        
        Args:
            painter: QPainter para dibujar
            x: Posición X en píxeles
            y: Posición Y en píxeles (centro de la línea del pentagrama)
            color: Color personalizado (opcional)
        """
        self._x = x
        self._y = y
        
        # Determinar color según estado
        if color:
            note_color = color
        elif self.is_correct is True:
            note_color = QColor(0, 255, 0, 180)  # Verde
        elif self.is_correct is False:
            note_color = QColor(255, 0, 0, 180)  # Rojo
        elif self.is_played:
            note_color = QColor(100, 100, 255, 200)  # Azul tocada
        else:
            note_color = QColor(138, 43, 226, 200)  # Púrpura (default)
        
        # Configurar painter
        painter.setPen(QPen(note_color, 2))
        painter.setBrush(QBrush(note_color))
        
        # Dibujar según tipo de nota
        if self.note_type == NoteType.WHOLE:
            self._draw_whole_note(painter, x, y)
        elif self.note_type == NoteType.HALF:
            self._draw_half_note(painter, x, y)
        elif self.note_type == NoteType.QUARTER:
            self._draw_quarter_note(painter, x, y)
        elif self.note_type == NoteType.EIGHTH:
            self._draw_eighth_note(painter, x, y)
        elif self.note_type == NoteType.SIXTEENTH:
            self._draw_sixteenth_note(painter, x, y)
        else:  # THIRTYSECOND
            self._draw_thirtysecond_note(painter, x, y)
        
        # Dibujar número de dedo si está asignado
        if self.finger is not None:
            self._draw_finger_number(painter, x, y)
    
    def _draw_whole_note(self, painter: QPainter, x: float, y: float):
        """Dibuja una redonda (whole note)"""
        # Óvalo hueco horizontal
        rect = QRectF(
            x - self.props.width / 2,
            y - self.props.height / 2,
            self.props.width,
            self.props.height
        )
        
        # Dibujar borde
        painter.setBrush(QBrush())  # Sin relleno
        painter.drawEllipse(rect)
        
        # Dibujar óvalo interno (más pequeño)
        inner_rect = rect.adjusted(3, 2, -3, -2)
        painter.drawEllipse(inner_rect)
    
    def _draw_half_note(self, painter: QPainter, x: float, y: float):
        """Dibuja una blanca (half note)"""
        # Cabeza hueca
        rect = QRectF(
            x - self.props.width / 2,
            y - self.props.height / 2,
            self.props.width,
            self.props.height
        )
        painter.setBrush(QBrush())  # Sin relleno
        painter.drawEllipse(rect)
        
        # Plica (stem) hacia arriba o abajo según posición
        stem_x = x + self.props.width / 2 if y < 250 else x - self.props.width / 2
        stem_direction = -1 if y < 250 else 1
        stem_end_y = y + stem_direction * self.props.stem_height
        
        painter.setPen(QPen(painter.pen().color(), self.props.stem_width))
        painter.drawLine(QPointF(stem_x, y), QPointF(stem_x, stem_end_y))
    
    def _draw_quarter_note(self, painter: QPainter, x: float, y: float):
        """Dibuja una negra (quarter note)"""
        # Cabeza llena
        rect = QRectF(
            x - self.props.width / 2,
            y - self.props.height / 2,
            self.props.width,
            self.props.height
        )
        painter.drawEllipse(rect)
        
        # Plica (stem)
        stem_x = x + self.props.width / 2 if y < 250 else x - self.props.width / 2
        stem_direction = -1 if y < 250 else 1
        stem_end_y = y + stem_direction * self.props.stem_height
        
        painter.setPen(QPen(painter.pen().color(), self.props.stem_width))
        painter.drawLine(QPointF(stem_x, y), QPointF(stem_x, stem_end_y))
    
    def _draw_eighth_note(self, painter: QPainter, x: float, y: float):
        """Dibuja una corchea (eighth note)"""
        # Cabeza llena
        rect = QRectF(
            x - self.props.width / 2,
            y - self.props.height / 2,
            self.props.width,
            self.props.height
        )
        painter.drawEllipse(rect)
        
        # Plica y bandera
        stem_x = x + self.props.width / 2 if y < 250 else x - self.props.width / 2
        stem_direction = -1 if y < 250 else 1
        stem_end_y = y + stem_direction * self.props.stem_height
        
        painter.setPen(QPen(painter.pen().color(), self.props.stem_width))
        painter.drawLine(QPointF(stem_x, y), QPointF(stem_x, stem_end_y))
        
        # Bandera (flag) curva
        self._draw_flag(painter, stem_x, stem_end_y, stem_direction, 1)
    
    def _draw_sixteenth_note(self, painter: QPainter, x: float, y: float):
        """Dibuja una semicorchea (sixteenth note)"""
        # Cabeza llena
        rect = QRectF(
            x - self.props.width / 2,
            y - self.props.height / 2,
            self.props.width,
            self.props.height
        )
        painter.drawEllipse(rect)
        
        # Plica y dos banderas
        stem_x = x + self.props.width / 2 if y < 250 else x - self.props.width / 2
        stem_direction = -1 if y < 250 else 1
        stem_end_y = y + stem_direction * self.props.stem_height
        
        painter.setPen(QPen(painter.pen().color(), self.props.stem_width))
        painter.drawLine(QPointF(stem_x, y), QPointF(stem_x, stem_end_y))
        
        # Dos banderas
        self._draw_flag(painter, stem_x, stem_end_y, stem_direction, 2)
    
    def _draw_thirtysecond_note(self, painter: QPainter, x: float, y: float):
        """Dibuja una fusa (thirty-second note)"""
        # Similar a semicorchea pero con 3 banderas
        rect = QRectF(
            x - self.props.width / 2,
            y - self.props.height / 2,
            self.props.width,
            self.props.height
        )
        painter.drawEllipse(rect)
        
        stem_x = x + self.props.width / 2 if y < 250 else x - self.props.width / 2
        stem_direction = -1 if y < 250 else 1
        stem_end_y = y + stem_direction * self.props.stem_height
        
        painter.setPen(QPen(painter.pen().color(), self.props.stem_width))
        painter.drawLine(QPointF(stem_x, y), QPointF(stem_x, stem_end_y))
        
        # Tres banderas
        self._draw_flag(painter, stem_x, stem_end_y, stem_direction, 3)
    
    def _draw_flag(self, painter: QPainter, stem_x: float, stem_end_y: float, direction: int, count: int):
        """Dibuja banderas (flags) en la plica"""
        flag_spacing = 6  # Espaciado entre banderas
        
        for i in range(count):
            offset = i * flag_spacing * direction
            flag_y = stem_end_y + offset
            
            # Curva de la bandera usando QPainterPath
            path = QPainterPath()
            path.moveTo(stem_x, flag_y)
            
            # Control points para la curva Bézier
            if direction < 0:  # Bandera hacia arriba
                path.cubicTo(
                    stem_x + self.props.flag_width * 0.3, flag_y,
                    stem_x + self.props.flag_width, flag_y + self.props.flag_height * 0.3,
                    stem_x + self.props.flag_width, flag_y + self.props.flag_height
                )
            else:  # Bandera hacia abajo
                path.cubicTo(
                    stem_x - self.props.flag_width * 0.3, flag_y,
                    stem_x - self.props.flag_width, flag_y - self.props.flag_height * 0.3,
                    stem_x - self.props.flag_width, flag_y - self.props.flag_height
                )
            
            painter.drawPath(path)
    
    def _draw_finger_number(self, painter: QPainter, x: float, y: float):
        """Dibuja el número de dedo sugerido"""
        # Círculo pequeño con número
        circle_radius = 10
        circle_y = y - self.props.stem_height - 15
        
        # Guardar configuración anterior
        old_pen = painter.pen()
        old_brush = painter.brush()
        
        # Dibujar círculo
        painter.setPen(QPen(QColor(255, 140, 0), 2))  # Naranja
        painter.setBrush(QBrush(QColor(255, 255, 255, 200)))
        painter.drawEllipse(QPointF(x, circle_y), circle_radius, circle_radius)
        
        # Dibujar número
        painter.setPen(QPen(QColor(0, 0, 0)))
        font = painter.font()
        font.setPointSize(10)
        font.setBold(True)
        painter.setFont(font)
        
        text_rect = QRectF(x - circle_radius, circle_y - circle_radius, 
                          circle_radius * 2, circle_radius * 2)
        painter.drawText(text_rect, 0x0004 | 0x0080, str(self.finger))  # Qt.AlignCenter
        
        # Restaurar configuración
        painter.setPen(old_pen)
        painter.setBrush(old_brush)
    
    def should_trigger_at_time(self, current_time: float, tolerance: float = 0.025) -> bool:
        """
        Determina si la nota debe sonar en el tiempo actual.
        
        Args:
            current_time: Tiempo actual de reproducción
            tolerance: Tolerancia hacia atrás (para compensación de latencia)
        
        Returns:
            True si la nota debe sonar ahora
        """
        # CRÍTICO: La nota se activa cuando current_time >= start_time (con pequeña tolerancia hacia atrás)
        # Sin límite superior para asegurar que NUNCA se salte una nota
        # Si ya está tocada, no volver a activar
        if self.is_played:
            return False
        
        # Activar si el tiempo actual alcanzó o superó el start_time de la nota
        # Tolerancia negativa permite compensar pequeños adelantos por latencia de audio
        return current_time >= (self.start_time - tolerance)
    
    def __repr__(self):
        return f"NoteWidget(pitch={self.pitch}, time={self.start_time:.2f}s, " \
               f"duration={self.duration:.2f}s, type={self.note_type})"


class SongWidget(QObject):
    """
    Widget que gestiona una colección de notas musicales y su reproducción.
    Emite señales cuando las notas deben sonar.
    """
    
    # Señales
    note_triggered = pyqtSignal(int, int)  # (pitch, velocity)
    note_ended = pyqtSignal(int)  # (pitch)
    
    def __init__(self, tempo: float = 120.0, time_signature: tuple = (4, 4)):
        super().__init__()
        self.notes: List[NoteWidget] = []
        self.tempo = tempo  # BPM
        self.time_signature = time_signature
        self.pixels_per_second = 200.0
        
        # Control de notas activas
        self._active_notes: set = set()  # IDs de notas que ya sonaron
        self._last_check_time = -1.0
        
        # OPTIMIZACIÓN: Índice de búsqueda para evitar revisar todas las notas
        self._next_note_index = 0  # Próxima nota a revisar para trigger
        self._notes_sorted = False  # Flag para saber si están ordenadas
        
    def add_note(self, note: NoteWidget):
        """Añade una nota a la canción"""
        self.notes.append(note)
        self._notes_sorted = False
        
    def add_notes(self, notes: List[NoteWidget]):
        """Añade múltiples notas a la canción"""
        self.notes.extend(notes)
        self._notes_sorted = False
        
    def clear_notes(self):
        """Limpia todas las notas"""
        self.notes.clear()
        self._active_notes.clear()
        self._last_check_time = -1.0
        self._next_note_index = 0
        self._notes_sorted = False
    
    def _ensure_sorted(self):
        """Asegura que las notas estén ordenadas por tiempo de inicio (OPTIMIZACIÓN)"""
        if not self._notes_sorted and self.notes:
            self.notes.sort(key=lambda n: n.start_time)
            self._notes_sorted = True
            print(f"SongWidget: Sorted {len(self.notes)} notes for optimal performance")
    
    def get_notes_at_time(self, time: float, tolerance: float = 0.1) -> List[NoteWidget]:
        """
        Obtiene las notas que suenan en un tiempo específico.
        
        Args:
            time: Tiempo en segundos
            tolerance: Tolerancia en segundos
        """
        return [
            note for note in self.notes
            if note.start_time - tolerance <= time <= note.start_time + note.duration + tolerance
        ]
    
    def check_and_trigger_notes(self, current_time: float, tolerance: float = 0.016):
        """
        Verifica qué notas deben sonar en el tiempo actual y emite señales.
        OPTIMIZADO: Solo revisa notas cercanas al tiempo actual, no todas.
        
        Args:
            current_time: Tiempo actual de reproducción en segundos
            tolerance: Tolerancia en segundos (16ms por defecto = 1 frame a 60fps)
        """
        # Evitar checks duplicados en el mismo frame
        if abs(current_time - self._last_check_time) < 0.001:
            return
        
        # Asegurar que las notas estén ordenadas para búsqueda eficiente
        self._ensure_sorted()
        
        if not self.notes:
            return
            
        self._last_check_time = current_time
        
        # OPTIMIZACIÓN: Solo revisar notas desde _next_note_index en adelante
        # Las notas anteriores ya fueron procesadas
        total_notes = len(self.notes)
        checked_count = 0
        
        # Revisar notas pendientes desde el índice actual
        i = self._next_note_index
        while i < total_notes:
            note = self.notes[i]
            note_id = id(note)
            checked_count += 1
            
            # Si la nota está muy en el futuro, parar (están ordenadas)
            if note.start_time > current_time + 1.0:  # 1 segundo de lookahead
                break
            
            # Verificar si la nota debe sonar ahora
            if note.should_trigger_at_time(current_time, tolerance):
                if note_id not in self._active_notes:
                    # Marcar nota como tocada y emitir señal
                    note.is_played = True
                    self._active_notes.add(note_id)
                    self.note_triggered.emit(note.pitch, note.velocity)
                    
                    # Avanzar el índice solo cuando activamos una nota
                    if i == self._next_note_index:
                        self._next_note_index = i + 1
                    
            # Verificar si la nota terminó
            elif note.is_played and current_time > note.start_time + note.duration:
                if note_id in self._active_notes:
                    self._active_notes.remove(note_id)
                    self.note_ended.emit(note.pitch)
            
            i += 1
        
        # Debug: mostrar eficiencia cada 100 checks
        if checked_count > 0 and self._next_note_index % 100 == 0:
            percent_checked = (checked_count / total_notes) * 100
            print(f"⚡ Checked {checked_count}/{total_notes} notes ({percent_checked:.1f}%) - Index: {self._next_note_index}")
    
    def reset_playback(self):
        """Resetea el estado de reproducción de todas las notas"""
        for note in self.notes:
            note.is_played = False
            note.is_correct = None
        self._active_notes.clear()
        self._last_check_time = -1.0
        self._next_note_index = 0  # Reiniciar índice de búsqueda
        print("🔄 Playback reset - index reset to 0")
    
    def set_tempo(self, tempo: float):
        """
        Ajusta el tempo de la canción.
        
        Args:
            tempo: Nuevo tempo en BPM
        """
        self.tempo = tempo
        # Recalcular pixels_per_second si es necesario
        self.pixels_per_second = 200.0 * (tempo / 120.0)
    
    def get_pixels_per_beat(self) -> float:
        """Calcula píxeles por beat basado en tempo actual"""
        seconds_per_beat = 60.0 / self.tempo
        return self.pixels_per_second * seconds_per_beat
    
    def get_duration(self) -> float:
        """Retorna la duración total de la canción en segundos"""
        if not self.notes:
            return 0.0
        return max(note.start_time + note.duration for note in self.notes)
    
    def get_note_count(self) -> int:
        """Retorna el número total de notas"""
        return len(self.notes)
    
    def __repr__(self):
        return f"SongWidget(notes={len(self.notes)}, tempo={self.tempo}, duration={self.get_duration():.2f}s)"
