# Perfiles de Instrumentos

Esta carpeta contiene los perfiles de sonido para diferentes tipos de piano.

## 📁 Estructura

```
instruments/
├── acoustic/     # Piano acústico estándar
├── grand/        # Piano de cola
├── bright/       # Piano brillante (agudos pronunciados)
├── mellow/       # Piano suave (graves cálidos)
├── electric/     # Piano eléctrico
└── custom/       # Perfiles personalizados
```

## 🎹 Formatos Soportados

Cada carpeta puede contener:

### Opción 1: Archivos WAV individuales (Recomendado)
```
acoustic/
├── note_21.wav   # A0
├── note_22.wav   # A#0
├── note_23.wav   # B0
...
├── note_108.wav  # C8
```

### Opción 2: Configuración JSON
```json
{
  "name": "Acoustic Grand Piano",
  "type": "sampled",
  "samples": {
    "21": "note_21.wav",
    "22": "note_22.wav",
    ...
  },
  "sustain": 0.8,
  "release": 0.3
}
```

### Opción 3: Síntesis (Por defecto)
Si no hay archivos WAV, el sistema usa síntesis paramétrica:
```json
{
  "name": "Synthesized Piano",
  "type": "synthetic",
  "waveform": "complex",
  "harmonics": [1.0, 0.5, 0.3, 0.2],
  "envelope": {
    "attack": 0.01,
    "decay": 0.1,
    "sustain": 0.7,
    "release": 0.3
  }
}
```

## 🔧 Crear Perfil Personalizado

1. **Crear carpeta:**
   ```
   assets/instruments/mi_piano/
   ```

2. **Añadir samples (88 archivos WAV):**
   ```
   mi_piano/
   ├── note_21.wav
   ├── note_22.wav
   ...
   └── note_108.wav
   ```

3. **Opcional: Añadir config.json:**
   ```json
   {
     "name": "Mi Piano Personalizado",
     "description": "Piano con samples reales",
     "type": "sampled"
   }
   ```

4. **Reiniciar la aplicación**

## 📥 Descargar Samples

### Fuentes de samples de piano gratuitos:

1. **Freesound.org**
   - https://freesound.org/search/?q=piano+note

2. **Philharmonia Orchestra**
   - https://philharmonia.co.uk/resources/sound-samples/

3. **University of Iowa MIS**
   - http://theremin.music.uiowa.edu/MIS.html

4. **Salamander Grand Piano**
   - https://archive.org/details/SalamanderGrandPianoV3

## ⚙️ Parámetros de Config

### Samples Completos
```json
{
  "name": "Nombre del Piano",
  "type": "sampled",
  "format": "wav",
  "sample_rate": 44100,
  "bit_depth": 16,
  "interpolation": "linear"
}
```

### Síntesis Paramétrica
```json
{
  "name": "Piano Sintético",
  "type": "synthetic",
  "waveform": "complex",
  "harmonics": [1.0, 0.5, 0.3, 0.2, 0.1],
  "envelope": {
    "attack": 0.01,
    "decay": 0.1,
    "sustain": 0.7,
    "release": 0.3
  },
  "filter": {
    "type": "lowpass",
    "cutoff": 8000,
    "resonance": 1.0
  }
}
```

## 🎚️ Perfiles Predefinidos

### Acoustic
Piano acústico estándar con síntesis compleja. Balance entre graves y agudos.

### Grand
Piano de cola con samples de calidad (si están disponibles). Sonido rico y profundo.

### Bright
Piano con agudos pronunciados. Ideal para música pop y contemporánea.

### Mellow
Piano suave con graves cálidos. Perfecto para baladas y jazz.

### Electric
Piano eléctrico estilo Rhodes/Wurlitzer. Sonido vintage.

## 💡 Tips

1. **Nombrado de archivos**: Los archivos deben llamarse `note_XX.wav` donde XX es el número MIDI (21-108)

2. **Calidad de audio**: Se recomienda 44.1kHz, 16-bit WAV para mejor rendimiento

3. **Tamaño**: Un conjunto completo de 88 samples puede ocupar 50-200 MB según la calidad

4. **Velocidad**: El sistema carga los samples al iniciar, así que cuantos menos perfiles mejor performance

5. **Fallback**: Si falta un sample, el sistema usa síntesis automática para esa nota
