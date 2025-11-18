"""
Generador de archivo MIDI de prueba
Crea una escala simple para testing
"""
from mido import MidiFile, MidiTrack, Message

def create_test_midi():
    """Crea archivo MIDI de prueba con escala de C"""
    
    mid = MidiFile()
    track = MidiTrack()
    mid.tracks.append(track)
    
    track.append(Message('program_change', program=0, time=0))
    
    # Escala de C mayor (C4 a C5)
    scale = [60, 62, 64, 65, 67, 69, 71, 72]  # C D E F G A B C
    
    # Tocar cada nota
    for note in scale:
        track.append(Message('note_on', note=note, velocity=64, time=0))
        track.append(Message('note_off', note=note, velocity=64, time=480))
    
    # Acorde final (C mayor)
    chord = [60, 64, 67]  # C E G
    for note in chord:
        track.append(Message('note_on', note=note, velocity=80, time=0))
    for note in chord:
        track.append(Message('note_off', note=note, velocity=80, time=960))
    
    # Guardar
    filename = 'test_scale.mid'
    mid.save(filename)
    print(f"✓ Archivo MIDI de prueba creado: {filename}")
    print(f"  Notas: {len(scale) + len(chord)}")
    print(f"  Duración: {mid.length:.2f} segundos")
    return filename

if __name__ == "__main__":
    create_test_midi()
