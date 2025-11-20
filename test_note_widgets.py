"""
Script de prueba para el sistema de widgets de notas.
Crea una canción de ejemplo y la renderiza.
"""

import sys
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtGui import QPainter, QColor
from PyQt6.QtCore import Qt, QRectF, QTimer
from src.ui.note_widget import NoteWidget, NoteType
from src.ui.song_widget import SongWidget


class TestWidget(QWidget):
    """Widget de prueba para renderizar notas"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Test - Sistema de Widgets de Notas")
        self.resize(1200, 600)
        self.setStyleSheet("background-color: white;")
        
        # Crear canción de prueba
        self.song = SongWidget(tempo=120.0)
        self._create_test_song()
        
        # Tiempo de reproducción simulado
        self.current_time = 0.0
        self.is_playing = True
        
        # Timer para animar
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_time)
        self.timer.start(16)  # 60 FPS
        
        # Líneas del pentagrama (simplificado)
        self.staff_lines_y = [200, 220, 240, 260, 280]
    
    def _create_test_song(self):
        """Crea una canción de ejemplo con diferentes tipos de notas"""
        
        print("Creando canción de prueba...")
        
        # Escala de Do mayor (C4 a C5) con diferentes duraciones
        scale_notes = [60, 62, 64, 65, 67, 69, 71, 72]  # C4 a C5
        time = 0.0
        
        # Redondas (4 beats = 2 segundos a 120 BPM)
        for i, pitch in enumerate(scale_notes[:2]):
            self.song.add_note(pitch, time, 2.0, 100)
            time += 2.0
        
        # Blancas (2 beats = 1 segundo)
        for i, pitch in enumerate(scale_notes[2:4]):
            self.song.add_note(pitch, time, 1.0, 90)
            time += 1.0
        
        # Negras (1 beat = 0.5 segundos)
        for i, pitch in enumerate(scale_notes[4:6]):
            self.song.add_note(pitch, time, 0.5, 80)
            time += 0.5
        
        # Corcheas (0.5 beats = 0.25 segundos)
        for i, pitch in enumerate(scale_notes[:4]):
            self.song.add_note(pitch, time, 0.25, 70)
            time += 0.25
        
        # Semicorcheas (0.25 beats = 0.125 segundos)
        for i, pitch in enumerate(scale_notes[4:]):
            self.song.add_note(pitch, time, 0.125, 60)
            time += 0.125
        
        # Acorde (tres notas simultáneas)
        chord_time = time + 0.5
        for offset in [0, 4, 7]:  # Acorde de Do mayor
            self.song.add_note(60 + offset, chord_time, 1.0, 100)
        
        time = chord_time + 1.5
        
        # Patrón rítmico complejo
        rhythm_pattern = [
            (64, 0.25),   # Corchea
            (65, 0.125),  # Semicorchea
            (67, 0.125),  # Semicorchea
            (69, 0.5),    # Negra
            (67, 0.25),   # Corchea
            (65, 0.25),   # Corchea
            (64, 1.0),    # Blanca
        ]
        
        for pitch, duration in rhythm_pattern:
            self.song.add_note(pitch, time, duration, 85)
            time += duration
        
        stats = self.song.get_stats()
        print(f"\nEstadísticas de la canción:")
        print(f"  Total notas: {stats['total_notes']}")
        print(f"  Duración: {stats['duration_seconds']:.2f}s")
        print(f"  Tempo: {stats['tempo']} BPM")
        print(f"  Compás: {stats['time_signature']}")
        print(f"  Tipos de notas:")
        for note_type, count in stats['note_types'].items():
            print(f"    - {note_type}: {count}")
        print(f"  Rango de notas: MIDI {stats['pitch_range'][0]}-{stats['pitch_range'][1]}")
        print()
    
    def _update_time(self):
        """Actualiza el tiempo de reproducción"""
        if self.is_playing:
            self.current_time += 0.016  # 16ms por frame (60 FPS)
            
            # Loop al final
            if self.current_time > self.song.total_duration + 2.0:
                self.current_time = 0.0
            
            self.update()  # Redibuja
    
    def paintEvent(self, event):
        """Renderiza la canción"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Fondo blanco
        painter.fillRect(self.rect(), QColor(255, 255, 255))
        
        # Dibujar líneas del pentagrama
        painter.setPen(QColor(0, 0, 0))
        for y in self.staff_lines_y:
            painter.drawLine(0, int(y), self.width(), int(y))
        
        # Dibujar línea roja (posición actual de reproducción)
        red_line_x = 150
        painter.setPen(QColor(255, 0, 0, 200))
        painter.drawLine(red_line_x, 0, red_line_x, self.height())
        
        # Calcular scroll offset
        preparation_time = 3.0
        scroll_offset = -(self.current_time + preparation_time) * self.song.pixels_per_second + red_line_x
        
        # Trasladar para scroll
        painter.translate(scroll_offset, 0)
        
        # Viewport bounds (en coordenadas del canvas)
        viewport_left = -scroll_offset
        viewport_right = viewport_left + self.width()
        viewport_bounds = QRectF(viewport_left, 0, self.width(), self.height())
        
        # Renderizar todas las notas visibles
        self.song.render_all(
            painter,
            self.current_time,
            self.staff_lines_y,
            viewport_bounds,
            preparation_time
        )
        
        # Restaurar transformación
        painter.resetTransform()
        
        # Información en pantalla
        painter.setPen(QColor(0, 0, 0))
        info_text = f"Tiempo: {self.current_time:.2f}s / {self.song.total_duration:.2f}s | "
        info_text += f"Tempo: {self.song.tempo} BPM | "
        info_text += f"Notas: {len(self.song.notes)}"
        
        painter.drawText(10, 20, info_text)
        
        # Instrucciones
        painter.drawText(10, self.height() - 40, "Controles:")
        painter.drawText(10, self.height() - 20, "Espacio: Pausar/Reanudar | R: Reiniciar | Q: Salir")
    
    def keyPressEvent(self, event):
        """Maneja eventos de teclado"""
        if event.key() == Qt.Key.Key_Space:
            self.is_playing = not self.is_playing
            print(f"Reproducción: {'Activa' if self.is_playing else 'Pausada'}")
        
        elif event.key() == Qt.Key.Key_R:
            self.current_time = 0.0
            print("Reiniciado")
        
        elif event.key() == Qt.Key.Key_Q:
            self.close()
        
        elif event.key() == Qt.Key.Key_Plus or event.key() == Qt.Key.Key_Equal:
            self.song.set_zoom(self.song.zoom_scale * 1.2)
            print(f"Zoom: {self.song.zoom_scale:.2f}x")
        
        elif event.key() == Qt.Key.Key_Minus:
            self.song.set_zoom(self.song.zoom_scale / 1.2)
            print(f"Zoom: {self.song.zoom_scale:.2f}x")


def main():
    """Punto de entrada principal"""
    app = QApplication(sys.argv)
    
    print("=" * 60)
    print("Sistema de Widgets de Notas - Prueba")
    print("=" * 60)
    
    window = TestWidget()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
