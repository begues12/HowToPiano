"""
Script para convertir samples FLAC del Maestro Concert Grand Piano a WAV
y organizarlos por nota MIDI y capa de velocidad
"""
import os
from pathlib import Path

# Instalar pydub si no está: pip install pydub
try:
    from pydub import AudioSegment
except ImportError:
    print("⚠ pydub no instalado. Instalando...")
    import subprocess
    import sys
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'pydub'], check=True)
    from pydub import AudioSegment

# Rutas
source_dir = Path("MaestroConcertGrandPiano/Samples")
output_dir = Path("piano_samples")

# Crear estructura de carpetas
velocity_layers = {
    'p': 'piano',           # 0-29
    'mp': 'mezzo_piano',    # 30-59
    'mf': 'mezzo_forte',    # 60-89
    'f': 'forte',           # 90-108
    'ff': 'fortissimo'      # 109-127
}

# Crear directorios
output_dir.mkdir(exist_ok=True)
for layer_name in velocity_layers.values():
    (output_dir / layer_name).mkdir(exist_ok=True)

print("Convirtiendo samples FLAC a WAV...")
print("=" * 60)

converted = 0
skipped = 0

# Procesar archivos
for flac_file in source_dir.glob("mcg_*.flac"):
    filename = flac_file.stem  # Nombre sin extensión
    
    # Parsear nombre: mcg_LAYER_NOTE.flac
    parts = filename.split('_')
    if len(parts) != 3:
        continue
    
    _, layer, note = parts
    
    # Solo procesar notas (no release samples ni pedales)
    if not note.isdigit():
        continue
    
    # Determinar carpeta de destino
    if layer in velocity_layers:
        output_subdir = output_dir / velocity_layers[layer]
        output_file = output_subdir / f"note_{note}.wav"
        
        # Convertir FLAC a WAV usando pydub
        try:
            # Cargar FLAC
            audio = AudioSegment.from_file(str(flac_file), format="flac")
            
            # Convertir a WAV (44.1kHz, 16-bit, estéreo)
            audio = audio.set_frame_rate(44100).set_channels(2).set_sample_width(2)
            
            # Exportar como WAV
            audio.export(str(output_file), format="wav")
            
            print(f"✓ Convertido: {filename} -> {velocity_layers[layer]}/note_{note}.wav")
            converted += 1
            
        except Exception as e:
            print(f"✗ Error convirtiendo {filename}: {e}")
            skipped += 1

print("=" * 60)
print(f"Conversión completada:")
print(f"  - Convertidos: {converted}")
print(f"  - Omitidos: {skipped}")
print(f"\nArchivos organizados en: {output_dir}/")
print("\nEstructura:")
for layer_name in velocity_layers.values():
    layer_path = output_dir / layer_name
    count = len(list(layer_path.glob("note_*.wav"))) + len(list(layer_path.glob("note_*.flac")))
    print(f"  {layer_name}: {count} samples")
