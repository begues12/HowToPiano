#!/usr/bin/env python3
"""
Generador de archivos MIDI de prueba
Crea varios archivos MIDI simples para probar HowToPiano
"""
import os
from mido import MidiFile, MidiTrack, Message, MetaMessage

def create_output_dir():
    """Crea directorio para archivos de prueba"""
    os.makedirs('test_midi', exist_ok=True)
    print("✓ Directorio 'test_midi' creado")

def create_simple_scale():
    """Crea escala Do mayor simple"""
    mid = MidiFile()
    track = MidiTrack()
    mid.tracks.append(track)
    
    # Metadata
    track.append(MetaMessage('track_name', name='Escala Do Mayor', time=0))
    track.append(MetaMessage('set_tempo', tempo=500000, time=0))  # 120 BPM
    
    # Escala: C D E F G A B C (60-67)
    notes = [60, 62, 64, 65, 67, 69, 71, 72]
    
    for note in notes:
        track.append(Message('note_on', note=note, velocity=80, time=0))
        track.append(Message('note_off', note=note, velocity=80, time=480))  # Negra
    
    # Guardar
    filepath = 'test_midi/01_escala_do_mayor.mid'
    mid.save(filepath)
    print(f"✓ Creado: {filepath}")
    return filepath

def create_twinkle_twinkle():
    """Crea 'Twinkle Twinkle Little Star' (Estrellita)"""
    mid = MidiFile()
    track = MidiTrack()
    mid.tracks.append(track)
    
    track.append(MetaMessage('track_name', name='Twinkle Twinkle Little Star', time=0))
    track.append(MetaMessage('set_tempo', tempo=500000, time=0))
    
    # Melodía: C C G G A A G - F F E E D D C
    melody = [
        60, 60, 67, 67, 69, 69, 67,  # Twin-kle twin-kle lit-tle star
        65, 65, 64, 64, 62, 62, 60   # How I won-der what you are
    ]
    
    durations = [480] * len(melody)  # Todas negras
    durations[6] = 960  # "star" más larga
    durations[13] = 960  # "are" más larga
    
    for note, duration in zip(melody, durations):
        track.append(Message('note_on', note=note, velocity=80, time=0))
        track.append(Message('note_off', note=note, velocity=80, time=duration))
    
    filepath = 'test_midi/02_twinkle_twinkle.mid'
    mid.save(filepath)
    print(f"✓ Creado: {filepath}")
    return filepath

def create_happy_birthday():
    """Crea 'Happy Birthday'"""
    mid = MidiFile()
    track = MidiTrack()
    mid.tracks.append(track)
    
    track.append(MetaMessage('track_name', name='Happy Birthday', time=0))
    track.append(MetaMessage('set_tempo', tempo=500000, time=0))
    
    # Melodía simplificada en Do mayor
    melody = [
        60, 60, 62, 60, 65, 64,  # Hap-py birth-day to you
        60, 60, 62, 60, 67, 65,  # Hap-py birth-day to you
        60, 60, 72, 69, 65, 64, 62,  # Hap-py birth-day dear [name]
        70, 70, 69, 65, 67, 65   # Hap-py birth-day to you
    ]
    
    # Duraciones (corcheas y negras)
    durations = [
        240, 240, 480, 480, 480, 960,
        240, 240, 480, 480, 480, 960,
        240, 240, 480, 480, 480, 480, 960,
        240, 240, 480, 480, 480, 960
    ]
    
    for note, duration in zip(melody, durations):
        track.append(Message('note_on', note=note, velocity=80, time=0))
        track.append(Message('note_off', note=note, velocity=80, time=duration))
    
    filepath = 'test_midi/03_happy_birthday.mid'
    mid.save(filepath)
    print(f"✓ Creado: {filepath}")
    return filepath

def create_chord_progression():
    """Crea progresión de acordes simple (I-IV-V-I)"""
    mid = MidiFile()
    track = MidiTrack()
    mid.tracks.append(track)
    
    track.append(MetaMessage('track_name', name='Progresión de Acordes', time=0))
    track.append(MetaMessage('set_tempo', tempo=500000, time=0))
    
    # Acordes: C F G C (Do Fa Sol Do)
    chords = [
        [60, 64, 67],  # C (Do-Mi-Sol)
        [65, 69, 72],  # F (Fa-La-Do)
        [67, 71, 74],  # G (Sol-Si-Re)
        [60, 64, 67]   # C (Do-Mi-Sol)
    ]
    
    for chord in chords:
        # Tocar todas las notas del acorde simultáneamente
        for note in chord:
            track.append(Message('note_on', note=note, velocity=80, time=0))
        
        # Mantener el acorde
        for i, note in enumerate(chord):
            time = 960 if i == len(chord) - 1 else 0  # Solo última nota tiene duración
            track.append(Message('note_off', note=note, velocity=80, time=time))
    
    filepath = 'test_midi/04_acordes_basicos.mid'
    mid.save(filepath)
    print(f"✓ Creado: {filepath}")
    return filepath

def create_ode_to_joy():
    """Crea 'Ode to Joy' (Himno de la Alegría)"""
    mid = MidiFile()
    track = MidiTrack()
    mid.tracks.append(track)
    
    track.append(MetaMessage('track_name', name='Ode to Joy', time=0))
    track.append(MetaMessage('set_tempo', tempo=500000, time=0))
    
    # Primera frase del Himno de la Alegría
    melody = [
        64, 64, 65, 67, 67, 65, 64, 62,  # E E F G G F E D
        60, 60, 62, 64, 64, 62, 62,      # C C D E E D D
        64, 64, 65, 67, 67, 65, 64, 62,  # E E F G G F E D
        60, 60, 62, 64, 62, 60, 60       # C C D E D C C
    ]
    
    durations = [480] * len(melody)
    durations[12] = 720  # Nota con puntillo
    durations[13] = 240  # Corchea
    durations[27] = 720
    durations[28] = 240
    
    for note, duration in zip(melody, durations):
        track.append(Message('note_on', note=note, velocity=80, time=0))
        track.append(Message('note_off', note=note, velocity=80, time=duration))
    
    filepath = 'test_midi/05_ode_to_joy.mid'
    mid.save(filepath)
    print(f"✓ Creado: {filepath}")
    return filepath

def create_two_hands_simple():
    """Crea ejercicio simple con dos manos"""
    mid = MidiFile()
    track = MidiTrack()
    mid.tracks.append(track)
    
    track.append(MetaMessage('track_name', name='Ejercicio Dos Manos', time=0))
    track.append(MetaMessage('set_tempo', tempo=500000, time=0))
    
    # Mano derecha: Escala ascendente
    # Mano izquierda: Acordes (bajo)
    
    right_hand = [60, 62, 64, 65, 67, 69, 71, 72]  # Do mayor ascendente
    left_hand = [48, 48, 53, 53, 55, 55, 48, 48]   # Bajo: C C F F G G C C
    
    for rh, lh in zip(right_hand, left_hand):
        # Tocar ambas manos simultáneamente
        track.append(Message('note_on', note=lh, velocity=70, time=0))  # Bajo más suave
        track.append(Message('note_on', note=rh, velocity=80, time=0))  # Melodía
        
        track.append(Message('note_off', note=rh, velocity=80, time=0))
        track.append(Message('note_off', note=lh, velocity=70, time=480))  # Duración
    
    filepath = 'test_midi/06_dos_manos_simple.mid'
    mid.save(filepath)
    print(f"✓ Creado: {filepath}")
    return filepath

def create_chromatic_scale():
    """Crea escala cromática (todas las teclas)"""
    mid = MidiFile()
    track = MidiTrack()
    mid.tracks.append(track)
    
    track.append(MetaMessage('track_name', name='Escala Cromática', time=0))
    track.append(MetaMessage('set_tempo', tempo=500000, time=0))
    
    # Una octava cromática: C C# D D# E F F# G G# A A# B
    for note in range(60, 72):
        track.append(Message('note_on', note=note, velocity=80, time=0))
        track.append(Message('note_off', note=note, velocity=80, time=240))  # Corcheas rápidas
    
    filepath = 'test_midi/07_escala_cromatica.mid'
    mid.save(filepath)
    print(f"✓ Creado: {filepath}")
    return filepath

def create_readme():
    """Crea README con información de los archivos"""
    readme_content = """# 🎹 Archivos MIDI de Prueba

Archivos generados automáticamente para probar HowToPiano.

## 📁 Archivos Incluidos

1. **01_escala_do_mayor.mid** - Escala simple (C D E F G A B C)
   - Dificultad: ⭐ Muy Fácil
   - Notas: 8
   - Manos: Solo derecha
   - Ideal para: Primera prueba del sistema

2. **02_twinkle_twinkle.mid** - Twinkle Twinkle Little Star
   - Dificultad: ⭐ Muy Fácil
   - Notas: 14
   - Manos: Solo derecha
   - Ideal para: Aprender canciones simples

3. **03_happy_birthday.mid** - Happy Birthday
   - Dificultad: ⭐⭐ Fácil
   - Notas: 25
   - Manos: Solo derecha
   - Ideal para: Practicar ritmos

4. **04_acordes_basicos.mid** - Progresión I-IV-V-I
   - Dificultad: ⭐⭐ Fácil
   - Acordes: 4
   - Manos: Ambas (acordes)
   - Ideal para: Probar acordes simultáneos

5. **05_ode_to_joy.mid** - Himno de la Alegría (Beethoven)
   - Dificultad: ⭐⭐ Fácil
   - Notas: 29
   - Manos: Solo derecha
   - Ideal para: Pieza clásica simple

6. **06_dos_manos_simple.mid** - Ejercicio bimanual
   - Dificultad: ⭐⭐⭐ Medio
   - Notas: 16 (8 por mano)
   - Manos: Ambas
   - Ideal para: Coordinación de manos

7. **07_escala_cromatica.mid** - Escala cromática
   - Dificultad: ⭐⭐ Fácil
   - Notas: 12
   - Manos: Solo derecha
   - Ideal para: Probar todas las teclas (blancas y negras)

## 🚀 Cómo Usar

### Método 1: Desde la GUI
```
1. Abrir HowToPiano: python test_gui.py
2. Click "🔍 Buscar MIDI"
3. Navegar a: HowToPiano/test_midi/
4. Seleccionar archivo
5. Click en modo de aprendizaje
```

### Método 2: Línea de comandos
```bash
cd HowToPiano
python main.py --song test_midi/02_twinkle_twinkle.mid --mode practice
```

## 📊 Rangos de Notas

```
Archivo                  | Nota Más Grave | Nota Más Aguda | Rango
-------------------------|----------------|----------------|-------
01_escala_do_mayor      | C4 (60)        | C5 (72)        | 1 octava
02_twinkle_twinkle      | C4 (60)        | A4 (69)        | 10 notas
03_happy_birthday       | C4 (60)        | C5 (72)        | 1 octava
04_acordes_basicos      | C3 (48)        | D5 (74)        | 2+ octavas
05_ode_to_joy           | C4 (60)        | G4 (67)        | 8 notas
06_dos_manos_simple     | C3 (48)        | C5 (72)        | 2 octavas
07_escala_cromatica     | C4 (60)        | B4 (71)        | 1 octava
```

## 🎯 Orden Recomendado de Práctica

Para principiantes:
1. `01_escala_do_mayor.mid` - Familiarízate con el sistema
2. `02_twinkle_twinkle.mid` - Primera canción completa
3. `07_escala_cromatica.mid` - Teclas blancas y negras
4. `05_ode_to_joy.mid` - Pieza más larga
5. `03_happy_birthday.mid` - Ritmos variados
6. `04_acordes_basicos.mid` - Primeros acordes
7. `06_dos_manos_simple.mid` - Coordinación avanzada

## 🔧 Regenerar Archivos

Si necesitas recrear estos archivos:
```bash
python generate_test_midi.py
```

## 📝 Notas Técnicas

- **Tempo**: 120 BPM (uniforme en todos)
- **Velocity**: 70-80 (volumen medio)
- **Formato**: MIDI Type 0 (una pista)
- **Compatible con**: Todos los reproductores MIDI estándar

## 🎹 Mapeo de Notas MIDI

```
Nota MIDI | Nombre | Frecuencia
----------|--------|------------
48        | C3     | 130.81 Hz
60        | C4     | 261.63 Hz (Do central)
72        | C5     | 523.25 Hz
```

## 💡 Tips

- **Modo Alumno**: Usa "Esperar cada 2-4 acordes" para estos archivos
- **Velocidad**: Estos están a tempo normal, puedes ralentizar en configuración
- **LEDs**: Perfecto para calibrar tu mapeo LED→Tecla

## 🐛 Problemas Comunes

**"Archivo no se carga"**
→ Verifica que `mido` esté instalado: `pip install mido`

**"No veo las notas"**
→ Estos archivos son simples, si no aparecen revisa la configuración de tu teclado

**"LEDs no iluminan"**
→ Verifica que el rango de notas (48-74) esté dentro de tu configuración

---

Generado por: `generate_test_midi.py`
"""
    
    with open('test_midi/README.md', 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print("✓ Creado: test_midi/README.md")

def main():
    """Genera todos los archivos de prueba"""
    print("\n" + "=" * 60)
    print("🎹 GENERADOR DE ARCHIVOS MIDI DE PRUEBA")
    print("=" * 60 + "\n")
    
    try:
        # Crear directorio
        create_output_dir()
        print()
        
        # Generar archivos
        print("Generando archivos MIDI...\n")
        create_simple_scale()
        create_twinkle_twinkle()
        create_happy_birthday()
        create_chord_progression()
        create_ode_to_joy()
        create_two_hands_simple()
        create_chromatic_scale()
        
        print()
        create_readme()
        
        print("\n" + "=" * 60)
        print("✅ COMPLETADO")
        print("=" * 60)
        print(f"\n📁 Archivos creados en: test_midi/")
        print(f"📄 Total: 7 archivos MIDI + 1 README")
        print(f"\n🚀 Uso:")
        print(f"   python test_gui.py")
        print(f"   → Click '🔍 Buscar MIDI'")
        print(f"   → Selecciona archivo de test_midi/")
        print("\n💡 Empieza con: 01_escala_do_mayor.mid")
        print()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Verifica que 'mido' esté instalado: pip install mido")

if __name__ == "__main__":
    main()
