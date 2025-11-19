# Gestión de Perfiles de Instrumentos

## 📋 Descripción General

HowToPiano ahora incluye un sistema completo de gestión de perfiles de instrumentos que permite:
- ✅ **Síntesis de audio** para perfiles sin samples
- ✅ **Reproducción de WAV** para perfiles con samples reales
- ✅ **Modo híbrido** (mezcla síntesis + samples)
- ✅ **Auto-detección** de perfiles personalizados
- ✅ **Recarga en caliente** sin reiniciar la app

## 🎹 Perfiles Incluidos

### Perfiles por Defecto (Síntesis)
1. **acoustic** - Piano acústico balanceado
   - Armónicos: [1.0, 0.5, 0.3, 0.2, 0.1, 0.05]
   - Reverb: 15%
   - Uso: Práctica general

2. **grand** - Piano de cola rico
   - Armónicos: [1.0, 0.6, 0.4, 0.3, 0.15, 0.08, 0.04]
   - Reverb: 12%
   - Uso: Interpretaciones expresivas

3. **bright** - Piano brillante
   - Armónicos: [1.0, 0.7, 0.5, 0.4, 0.3, 0.2, 0.1]
   - Reverb: 6%
   - Uso: Piezas alegres y rápidas

4. **mellow** - Piano suave
   - Armónicos: [1.0, 0.4, 0.25, 0.15, 0.08, 0.03]
   - Reverb: 20%
   - Uso: Baladas y piezas lentas

5. **electric** - Piano eléctrico (Rhodes)
   - Armónicos: [1.0, 0.7, 0.45, 0.3, 0.25, 0.2, 0.15, 0.1]
   - Chorus: Sí
   - Uso: Jazz y música moderna

## 📂 Estructura de Archivos

```
assets/instruments/
├── acoustic/
│   └── config.json          # Solo síntesis
├── grand/
│   └── config.json
├── bright/
│   └── config.json
├── mellow/
│   └── config.json
├── electric/
│   └── config.json
├── custom/
│   ├── note_21.wav          # Samples opcionales (A0)
│   ├── note_22.wav          # A#0
│   ├── ...
│   ├── note_108.wav         # C8
│   └── config.json          # Configuración opcional
└── README.md
```

## 🔧 Gestor de Perfiles (InstrumentProfileManager)

### Ubicación
`src/instrument_profiles.py`

### Funcionalidades

#### Detección Automática
```python
from src.instrument_profiles import get_profile_manager

manager = get_profile_manager()
profiles = manager.get_profile_list()
# Devuelve:
# [
#   {
#     'id': 'acoustic',
#     'name': 'Acoustic Grand Piano',
#     'type': 'synthetic',
#     'has_samples': False
#   },
#   {
#     'id': 'custom',
#     'name': 'Custom Profile',
#     'type': 'sampled',
#     'has_samples': True
#   }
# ]
```

#### Obtener Configuración
```python
config = manager.get_profile_config('acoustic')
# Devuelve:
# {
#   'name': 'Acoustic Grand Piano',
#   'type': 'synthetic',
#   'harmonics': [1.0, 0.5, 0.3, ...],
#   'envelope': {'attack': 0.01, 'decay': 0.1, 'sustain': 0.7, 'release': 0.3},
#   'filter': {...},
#   'reverb': {...}
# }
```

#### Verificar Samples
```python
has_samples = manager.has_samples('custom')
sample_path = manager.get_sample_path('custom', 60)  # nota MIDI 60 (C4)
```

#### Estadísticas
```python
stats = manager.get_profile_stats('custom')
# Devuelve:
# {
#   'name': 'Custom Profile',
#   'type': 'sampled',
#   'has_config': True,
#   'has_samples': True,
#   'num_samples': 45,
#   'coverage': 51.14  # Porcentaje (45/88)
# }
```

#### Recarga
```python
manager.reload_profiles()  # Recarga todos los perfiles
```

## 🎵 Integración con PianoSound

### Cambios en src/piano_sound.py

#### Inicialización
```python
piano = PianoSound(volume=0.5, profile='grand')
# Ahora detecta automáticamente si hay samples WAV disponibles
```

#### Reproducción
```python
piano.play_note(60, velocity=80)
# Lógica:
# 1. Si profile tiene note_60.wav → Usa WAV
# 2. Si no → Usa síntesis con config.json
```

#### Cambio de Perfil
```python
piano.set_profile('custom')
# ✅ Limpia cache
# ✅ Verifica samples
# ✅ Reporta modo (WAV/Síntesis)
```

#### Obtener Perfiles Disponibles
```python
profiles = piano.get_available_profiles()
# Incluye perfiles built-in + custom detectados
```

## ⚙️ Configuración en GUI

### Settings Dialog (src/gui/settings.py)

#### Sección de Instrumentos
- Radio buttons con todos los perfiles detectados
- Iconos indicadores:
  - 🎵 = Tiene samples WAV
  - 🎹 = Solo síntesis
- Info tooltip: "45/88 notas (51%)" para perfiles con samples parciales

#### Botón "Gestionar Perfiles Personalizados"
Abre diálogo con:
- Lista de perfiles custom detectados
- Cobertura de samples (X/88 notas)
- Instrucciones de uso
- Botón "📂 Abrir Carpeta" → abre `assets/instruments/`
- Botón "🔄 Recargar Perfiles" → actualiza sin reiniciar

## 📝 Crear un Perfil Personalizado

### Método 1: Solo Síntesis (Rápido)

1. Crea carpeta: `assets/instruments/mi_piano/`
2. Crea `config.json`:
```json
{
  "name": "Mi Piano Personalizado",
  "type": "synthetic",
  "waveform": "complex",
  "harmonics": [1.0, 0.6, 0.4, 0.2],
  "envelope": {
    "attack": 0.01,
    "decay": 0.1,
    "sustain": 0.7,
    "release": 0.3
  },
  "filter": {
    "type": "lowpass",
    "cutoff": 5000
  },
  "reverb": {
    "room_size": 0.5,
    "damping": 0.5
  }
}
```
3. En la app: Settings → Gestionar Perfiles → Recargar

### Método 2: Samples WAV (Mejor Calidad)

1. Descarga samples de piano (88 notas, A0 a C8)
2. Renombra archivos:
   - note_21.wav (A0)
   - note_22.wav (A#0)
   - ...
   - note_108.wav (C8)
3. Coloca en `assets/instruments/custom/`
4. (Opcional) Crea `config.json` para metadata:
```json
{
  "name": "Steinway D",
  "type": "sampled",
  "description": "Steinway Model D Concert Grand"
}
```
5. En la app: Settings → Gestionar Perfiles → Recargar

### Método 3: Híbrido

Puedes tener **solo algunas notas** en WAV:
- Ejemplo: note_60.wav, note_64.wav, note_67.wav (C, E, G)
- El resto se genera por síntesis usando config.json
- Útil para prototipos o cuando faltan samples

## 🔍 Debugging

### Ver Qué Perfiles se Cargan
```python
from src.instrument_profiles import get_profile_manager

manager = get_profile_manager()
print(manager.get_all_profiles())
```

### Verificar Coverage
```python
for profile_id in manager.get_all_profiles():
    stats = manager.get_profile_stats(profile_id)
    print(f"{profile_id}: {stats['num_samples']}/88 ({stats['coverage']:.1f}%)")
```

### Logs en Consola
Al iniciar la app verás:
```
✅ Perfil cargado: acoustic
✅ Perfil cargado: grand
✅ Perfil cargado: custom
✅ Sistema de audio inicializado (44.1kHz, 64 canales) - Piano de Cola
   🎵 Usando samples WAV del perfil 'custom'
```

## 🌐 Fuentes de Samples

### Gratuitas
1. **Freesound** (freesound.org)
   - Buscar: "piano note C4", "steinway A0"
   - Licencia: CC0 o CC-BY

2. **Salamander Grand Piano** (archive.org)
   - 88 notas de Yamaha C5
   - Licencia: CC-BY

3. **Iowa Piano Library** (theremin.music.uiowa.edu)
   - Samples académicos
   - Gratuitos para educación

### Comerciales
1. **Native Instruments** - Kontakt libraries
2. **Spitfire Audio** - Piano libraries
3. **VSL** - Vienna Symphonic Library

## 📊 Comparación de Modos

| Modo | Tamaño | Calidad | CPU | Configuración |
|------|--------|---------|-----|---------------|
| **Síntesis** | 0 MB | Buena | Baja | JSON |
| **Samples Parciales** | 100-500 MB | Muy Buena | Media | WAV + JSON |
| **Samples Completos** | 1-3 GB | Excelente | Media | 88 WAV |

## 🚀 Roadmap Futuro

- [ ] Auto-pitch samples (tocar cualquier nota desde pocos WAV)
- [ ] Compression (FLAC/OGG en vez de WAV)
- [ ] Velocity layers (3-5 velocidades por nota)
- [ ] Round-robin samples (variaciones)
- [ ] Pedal de sustain samples
- [ ] Importador de SoundFont (SF2)
- [ ] Preset sharing (subir/descargar perfiles)

## 📞 Soporte

Si tienes problemas:
1. Verifica estructura de carpetas
2. Revisa consola para errores
3. Usa "Recargar Perfiles" en Settings
4. Revisa `config.json` con JSONLint
5. Confirma que WAV sean 44.1kHz mono/stereo

