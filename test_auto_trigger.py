"""
Script de prueba para verificar el sistema de triggering automático de notas.
"""

import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from src.ui.note_widget import NoteWidget, NoteType, SongWidget
from src.core.synth import PianoSynth

def test_auto_trigger():
    """Prueba que las notas suenen automáticamente al pasar por su tiempo"""
    
    app = QApplication(sys.argv)
    
    # Crear sintetizador
    synth = PianoSynth()
    
    # Crear canción con 5 notas espaciadas 1 segundo
    song = SongWidget(tempo=120)
    
    notes_data = [
        (60, 0.0, 0.5, NoteType.QUARTER),   # Do central en t=0s
        (62, 1.0, 0.5, NoteType.QUARTER),   # Re en t=1s
        (64, 2.0, 0.5, NoteType.QUARTER),   # Mi en t=2s
        (65, 3.0, 0.5, NoteType.QUARTER),   # Fa en t=3s
        (67, 4.0, 0.5, NoteType.QUARTER),   # Sol en t=4s
    ]
    
    for pitch, start_time, duration, note_type in notes_data:
        note = NoteWidget(
            pitch=pitch,
            start_time=start_time,
            duration=duration,
            velocity=80,
            note_type=note_type
        )
        song.add_note(note)
    
    print(f"🎵 Canción creada: {song}")
    print(f"   Notas: {len(song.notes)}")
    print(f"   Duración: {song.get_duration():.2f}s")
    print()
    
    # Conectar señales a funciones de reproducción
    def on_note_triggered(pitch, velocity):
        print(f"🎹 Tocando nota: pitch={pitch}, velocity={velocity}")
        synth.note_on(pitch, velocity)
    
    def on_note_ended(pitch):
        print(f"🎹 Finalizando nota: pitch={pitch}")
        synth.note_off(pitch)
    
    song.note_triggered.connect(on_note_triggered)
    song.note_ended.connect(on_note_ended)
    
    # Simular tiempo de reproducción
    current_time = 0.0
    dt = 0.016  # 16ms = 60 FPS
    
    def update_playback():
        nonlocal current_time
        
        # Incrementar tiempo
        current_time += dt
        
        # Verificar y triggear notas
        song.check_and_trigger_notes(current_time)
        
        # Mostrar progreso
        if int(current_time * 10) % 10 == 0:  # Cada 1 segundo
            print(f"⏱️  Tiempo: {current_time:.2f}s")
        
        # Detener cuando termine la canción
        if current_time > song.get_duration() + 1.0:
            print("\n✅ Reproducción completada")
            timer.stop()
            QTimer.singleShot(500, app.quit)
    
    # Timer para simular reproducción a 60 FPS
    timer = QTimer()
    timer.timeout.connect(update_playback)
    timer.start(16)  # 16ms = ~60 FPS
    
    print("▶️  Iniciando reproducción automática...")
    print("   (Las notas deberían sonar cada segundo)\n")
    
    sys.exit(app.exec())

if __name__ == '__main__':
    test_auto_trigger()
