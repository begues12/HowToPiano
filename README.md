# Piano Teacher

A Python application that acts as a piano teacher, connecting to an Arduino via USB and displaying professional sheet music.

## Features
- **Professional Score View**: Interactive musical staff with real-time note highlighting using Bravura font.
- **Asynchronous Loading System**: Non-blocking song loading with progress dialog and cancel button - UI stays responsive.
- **Automatic Timing Synchronization**: AI-powered system that measures and adjusts audio-visual sync in real-time.
- **Widget-Based Notes**: 6 musical figure types (whole, half, quarter, eighth, sixteenth, thirtysecond) with precise rendering.
- **Grand Piano Synthesis**: Professional piano sound with 12 harmonics, inharmonicity modeling, and multi-string chorus.
- **MIDI Keyboard Support**: Automatic detection and threaded input handling for external MIDI keyboards (DMK25, etc).
- **Arduino Connection**: Connects to your digital piano or Arduino interface via USB.
- **Teaching Modes**:
    - **Master (Maestro)**: Displays the score and plays automatically - just watch and learn.
    - **Student (Estudiante)**: The program plays 4 chords, then you repeat them - call and response training.
    - **Practice (Práctica)**: Keys light up on the piano, you press them to advance - guided step-by-step.
    - **Corrector (Errores)**: Reviews your previous mistakes and makes you correct them - focused improvement.
- **High-Quality Audio**: Maestro Concert Grand Piano samples (440 samples, 88 notes) with EQ, compression, and reverb.

## Requirements
- Python 3.8+
- PyQt6
- Verovio
- Music21
- PyFluidsynth
- Pyserial
- Mido

## Setup
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. **SoundFont**: Place a `.sf2` soundfont file in `assets/soundfonts/default.sf2`. You can download free SoundFonts like "FluidR3_GM" online.
3. **MIDI Keyboard** (Optional): Connect any MIDI keyboard via USB. The application will auto-detect it on startup.
   - Threaded input processing ensures zero lag
   - Supports all standard MIDI devices
   - Visual feedback with cyan color for MIDI input
4. **Arduino** (Optional): Connect your Arduino with WS2812B LED strip for visual piano key feedback.
   - Baudrate: **115200** (fast USB communication)
   - Auto-detection: The application automatically detects Arduino on startup
   - **Protocol**: See [Arduino Communication Protocol](#arduino-communication-protocol) below

## Running
```bash
python main.py
```

## Performance Optimizations

The application includes several performance optimizations for a smooth, professional experience:

### Asynchronous Loading System
- **Non-blocking Operations**: Songs load in background threads, UI stays responsive
- **Progress Feedback**: Modern loading dialog with real-time progress updates
- **Cancellable Operations**: Cancel button allows stopping long-running operations
- **Error Handling**: Robust error handling with clear user messages

See [PERFORMANCE_ASYNC_LOADING.md](PERFORMANCE_ASYNC_LOADING.md) for detailed documentation.

### Benefits
✅ UI never freezes during song loading
✅ Visual feedback shows exactly what's happening
✅ Can cancel operations at any time
✅ Professional look and feel

## Troubleshooting
- If `verovio` fails to load, ensure the python package is installed correctly.
- If audio is silent, check if `fluidsynth` is installed and a SoundFont is present.
- If loading seems slow, check file size - large MIDI files take longer to parse.

## Automatic Timing Synchronization

The application includes an intelligent timing synchronization system that automatically maintains perfect sync between audio and visuals:

### How It Works
1. **Measurement**: Records timing data for every note played (scheduled time vs actual time)
2. **Analysis**: Calculates statistical offset using median and standard deviation
3. **Adjustment**: Automatically adjusts audio latency compensation when drift exceeds 3ms
4. **Adaptation**: Continuously refines sync over time for rock-solid accuracy

### Features
- **Tolerance**: Notes activate within 8ms (sub-frame precision at 60 FPS)
- **Auto-correction**: Adjusts every ~1 second if needed
- **Statistics tracking**: Mean, median, std dev of timing offsets
- **Manual override**: Set custom latency if needed

### Accessing Sync Stats
The `StaffWidget` provides methods to inspect synchronization:
```python
# Print sync statistics
staff_widget.print_sync_stats()

# Get statistics dict
stats = staff_widget.get_sync_statistics()

# Manual control
staff_widget.set_manual_latency(15.0)  # 15ms
staff_widget.enable_sync_system()
staff_widget.disable_sync_system()
staff_widget.reset_sync_system()
```

## Arduino Communication Protocol

The application uses a fast, efficient serial protocol at **115200 baud** for real-time LED control of piano keys.

### Python → Arduino Commands

| Command | Format | Description | Example |
|---------|--------|-------------|---------|
| **LED ON** | `ON:note:brightness\n` | Turn on LED for a note | `ON:60:100\n` (Middle C, full brightness) |
| **LED OFF** | `OFF:note\n` | Turn off LED for a note | `OFF:60\n` (Middle C off) |
| **RGB Color** | `LED:note,r,g,b\n` | Set custom RGB color | `LED:60,255,0,0\n` (Red) |
| **Batch Update** | `BATCH:n1,r,g,b;n2,r,g,b\n` | Update multiple LEDs at once | `BATCH:60,0,255,0;62,0,255,0\n` |
| **Clear All** | `CLEAR\n` | Turn off all LEDs | `CLEAR\n` |
| **Brightness** | `BRIGHTNESS:value\n` | Set global brightness (0-255) | `BRIGHTNESS:128\n` |
| **Test** | `TEST\n` | Run test animation | `TEST\n` |
| **Ping** | `PING\n` | Check connection | `PING\n` |

### Arduino → Python Responses

| Response | Format | Description | Example |
|----------|--------|-------------|---------|
| **Ready** | `READY\n` | Arduino initialized | `READY\n` |
| **LED Feedback** | `LED ON: C4 (MIDI 60, LED index 39)\n` | Confirmation | - |
| **Pong** | `PONG\n` | Response to PING | `PONG\n` |

### MIDI Note Mapping
- Piano range: MIDI notes **21-108** (A0 to C8, 88 keys)
- LED index: `led_index = midi_note - 21` (0-87)
- Example: Middle C (MIDI 60) → LED index 39

### RGB Gradient Mode (Play & Master)

In **Play** and **Master** modes, LEDs display a beautiful full-spectrum RGB gradient:
- **Bass (low notes)**: Dark blue/purple tones
- **Middle range**: Cyan → Green → Yellow progression
- **Treble (high notes)**: Orange → Red bright tones
- **Velocity sensitivity**: Brightness adjusts with note velocity
- **Reversible gradient**: Settings option to reverse direction (treble dark, bass bright)

Other training modes (Practice, Student, Corrector) use traditional green LED colors for clarity.

**Configuration Options** (Settings → LedTeacher):
- ✅ **"Reverse gradient"**: Inverts color direction (treble dark, bass bright)
- ✅ **"Reverse LED index"**: Check if LED strip starts from right side of keyboard
  - Useful when Arduino/LED strip is positioned on the right side
  - Automatically maps MIDI notes to correct LED positions

### Automatic LED Cleanup

The application includes intelligent LED management to prevent stuck LEDs:
- **Orphaned key detection**: Runs every 100ms to find LEDs that shouldn't be lit
- **Auto-cleanup on stop**: Sends `CLEAR` command when stopping playback
- **Manual cleanup on pause**: All LEDs turn off when pausing
- **Thread-safe operations**: Prevents race conditions with mutex locks

This ensures LEDs always match the current playback state without manual intervention.

### Performance Optimizations
- **Batch commands** for updating multiple LEDs simultaneously
- **FastLED library** with 120 Hz refresh rate
- **No delays** in Arduino loop - instant USB response
- **Buffer optimization** for smooth animations
- **RGB gradient calculation** optimized for real-time performance

### Hardware Requirements
- Arduino Uno/Nano/Mega
- WS2812B LED strip (88 LEDs for full piano)
- FastLED library installed
- USB connection at 115200 baud

See `arduino/ws2812b_piano_leds/ws2812b_piano_leds.ino` for the complete Arduino code.

---

Sistema de iluminación LED sincronizado con archivos MIDI, similar a Keysnake, diseñado para **Raspberry Pi Zero W/W2**.

Lee archivos MIDI desde una memoria USB y controla una tira LED WS2812B para iluminar las teclas del piano en tiempo real.

---

## 🚀 Características

✔ **Lee archivos MIDI desde USB** - Sin módulos extra  
✔ **Control de tiras LED WS2812B/WS2813** - Hasta 88 LEDs (piano completo)  
✔ **🎓 Modo Aprendizaje Interactivo** - Aprende paso a paso con guía visual  
✔ **📚 Tutorial Interactivo** - Sistema modular que guía a nuevos usuarios  
✔ **📊 Muestra partituras en pantalla** - Terminal curses + display gráfico opcional  
✔ **🎼 Display gráfico (opcional)** - Pentagrama, Piano Roll con pygame/tkinter  
✔ **🎹 Detección de teclado MIDI** - Verifica que toques correctamente  
✔ **🎵 Sistema de Perfiles de Instrumentos** - Síntesis + samples WAV personalizables  
✔ **⚙️ Configuración completa** - Ajusta todo desde la GUI  
✔ **Sincronización perfecta** - El timing MIDI es manejado automáticamente  
✔ **Múltiples configuraciones** - Piano 88, teclados 61, 49, 25 teclas  
✔ **Modo interactivo** - Menú fácil de usar  
✔ **Validación automática** - Comprueba compatibilidad de archivos MIDI  
✔ **Modo simulación** - Prueba sin hardware  

---

## 🧩 Hardware Necesario

| Componente | Descripción | Precio aprox. |
|------------|-------------|---------------|
| **Raspberry Pi Zero W/W2** | Cerebro del sistema | $15-20 USD |
| **Tira LED WS2812B** | 88 LEDs para piano completo | $15-25 USD |
| **Fuente 5V 5-10A** | Para alimentar los LEDs | $10-15 USD |
| **Convertidor 3.3V→5V** | Nivel lógico (recomendado) | $2-5 USD |
| **Pendrive USB** | Para archivos MIDI | Ya tienes |
| **Adaptador OTG** | USB micro a USB-A | $3-5 USD |
| **Cables** | Jumpers, conectores | $5 USD |

**Total: ~$50-70 USD** ✨

---

## 📐 Conexiones

```
Raspberry Pi Zero W          Tira LED WS2812B
┌──────────────┐            ┌────────────────┐
│              │            │                │
│   GPIO 18 ───┼────────────┼───> DIN (Data) │
│   (Pin 12)   │            │                │
│              │            │                │
│   GND ───────┼────────────┼───> GND        │
│              │            │                │
└──────────────┘            └────────────────┘
                                    │
                            Fuente 5V (5-10A)
                                    │
                                   VCC
```

**Notas importantes:**
- GPIO 18 = Pin físico 12 en el header
- Usa un convertidor de nivel lógico 3.3V → 5V entre GPIO18 y DIN (opcional pero recomendado)
- La tira LED debe tener su propia fuente de alimentación (5V 5-10A según cantidad de LEDs)
- Conecta GND común entre Raspberry y fuente de LEDs

---

## 🛠️ Instalación

### 1. Preparar Raspberry Pi

```bash
# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Python 3 y dependencias
sudo apt install python3 python3-pip git -y

# Habilitar SPI (requerido para LEDs)
sudo raspi-config
# Interfacing Options → SPI → Enable
```

### 2. Clonar o copiar el proyecto

```bash
cd ~
git clone https://github.com/tu-usuario/HowToPiano.git
cd HowToPiano
```

### 3. Instalar librerías Python

```bash
# Instalar dependencias
pip3 install -r requirements.txt

# Si tienes problemas con rpi_ws281x:
sudo pip3 install rpi_ws281x adafruit-circuitpython-neopixel
```

### 4. Configurar montaje automático del USB

Edita `/etc/fstab` o usa `udev` para montar automáticamente el pendrive en `/media/pi/`.

Alternativamente, usa el punto de montaje por defecto de Raspberry Pi OS.

---

## 🎼 Uso

### Modo interactivo (recomendado)

```bash
sudo python3 main.py
```

Menú interactivo:
1. Listar archivos MIDI
2. Cargar y reproducir canción (demo automático)
3. **🎓 MODO APRENDIZAJE** - Práctica guiada paso a paso
4. Reproducir última canción
5. Prueba de LEDs
6. Ajustar brillo
7. Info del sistema

### 🎓 Modo Aprendizaje (¡NUEVO!)

El modo aprendizaje te guía nota por nota:

```bash
# Desde el menú
sudo python3 main.py
# Selecciona opción 3

# O directamente:
sudo python3 main.py --learn /media/pi/USB/cancion.mid

# O modo práctica:
sudo python3 main.py --practice
```

**3 modos disponibles:**
1. **Práctica guiada** - Presiona Enter después de cada nota
2. **Interfaz visual** - Pantalla completa con curses
3. **Con detección MIDI** - Detecta automáticamente cuando tocas

Ver guía completa: `docs/learning_mode.md`

### Reproducir archivo directo

```bash
sudo python3 main.py --file /media/pi/USB/cancion.mid
```

### Prueba de LEDs

```bash
sudo python3 main.py --test
```

### Modo simulación (sin hardware)

```bash
python3 main.py --simulate
```

### Opciones avanzadas

```bash
# Teclado de 61 teclas
sudo python3 main.py --keyboard keyboard_61 --leds 61

# Ajustar brillo inicial
sudo python3 main.py --brightness 0.5

# Ayuda
python3 main.py --help
```

---

## 📁 Estructura del Proyecto

```
HowToPiano/
├── main.py                  # Programa principal
├── requirements.txt         # Dependencias Python
├── README.md               # Este archivo
├── config/
│   └── config.json         # Configuración del sistema
├── src/
│   ├── __init__.py
│   ├── midi_reader.py      # Lector de archivos MIDI
│   ├── led_controller.py   # Controlador de LEDs
│   └── note_mapper.py      # Mapeo nota → LED
├── docs/
│   ├── hardware_setup.md   # Guía de conexiones
│   ├── led_alignment.md    # Alineación física
│   └── troubleshooting.md  # Solución de problemas
└── utils/
    └── (utilidades futuras)
```

---

## 🎹 Configuraciones de Teclado

### Piano de 88 teclas (por defecto)
```bash
sudo python3 main.py --keyboard piano_88 --leds 88
```
- Rango: A0 (nota 21) → C8 (nota 108)
- 88 LEDs necesarios

### Teclado de 61 teclas
```bash
sudo python3 main.py --keyboard keyboard_61 --leds 61
```
- Rango: C2 (nota 36) → C7 (nota 96)
- 61 LEDs necesarios

### Teclado de 49 teclas
```bash
sudo python3 main.py --keyboard keyboard_49 --leds 49
```
- Rango: C2 (nota 36) → C6 (nota 84)

### Mini teclado 25 teclas
```bash
sudo python3 main.py --keyboard keyboard_25 --leds 25
```
- Rango: C3 (nota 48) → C5 (nota 72)

---

## 📏 Alineación de LEDs con Teclas

### Dimensiones típicas:
- **Tecla blanca**: ~23 mm de ancho
- **LED WS2812**: Separación típica 16-17 mm en tira estándar

### Soluciones:

1. **Imprimir soporte 3D** - Espaciado personalizado a 23 mm
2. **Tira flexible** - Separar/recortar segmentos manualmente
3. **Difusor acrílico** - Colocar sobre la tira para expandir luz

Ver `docs/led_alignment.md` para diseños 3D.

---

## ⚡ Ventajas vs Arduino

| Característica | Raspberry Pi Zero W | Arduino Uno |
|----------------|---------------------|-------------|
| Lee USB sin extras | ✅ Nativo | ❌ Necesita USB Host Shield |
| Lenguaje | ✅ Python fácil | C/C++ complejo |
| Archivos MIDI | ✅ Librerías robustas | ⚠️ Difícil |
| Timing preciso | ✅ Perfecto | ⚠️ Complicado |
| WiFi integrado | ✅ Sí | ❌ No |
| Precio | ~$15 | ~$25 con shield |

---

## 🐛 Solución de Problemas

### Los LEDs no se encienden
- Verifica que GPIO 18 esté habilitado
- Comprueba conexiones (GND común, VCC a 5V)
- Ejecuta con `sudo` (permisos GPIO)
- Prueba: `sudo python3 main.py --test`

### No encuentra archivos MIDI
- Verifica que el USB esté montado: `ls /media/pi/`
- Comprueba permisos del USB
- Los archivos deben tener extensión `.mid` o `.midi`

### Error "ImportError: neopixel"
```bash
sudo pip3 install rpi_ws281x adafruit-circuitpython-neopixel
```

### Parpadeo/flickering de LEDs
- Usa fuente de alimentación adecuada (5V 5-10A)
- Agrega capacitor 1000µF entre VCC y GND
- Usa convertidor de nivel lógico 3.3V→5V

### Notas fuera de rango
- El sistema te avisará si hay notas incompatibles
- Ajusta configuración: `--keyboard keyboard_61`
- O edita `config/config.json`

---

## 🔮 Mejoras Futuras

- [ ] Pantalla LCD para mostrar información
- [ ] Botones físicos para control
- [ ] Control por WiFi / WebUI
- [ ] Efectos visuales avanzados
- [ ] Soporte para múltiples canales MIDI
- [ ] Grabación de sesiones
- [ ] App móvil de control

---

## 📚 Documentación Completa

### Guías de Usuario
- **[QUICKSTART.md](QUICKSTART.md)** - Guía rápida de inicio
- **[FEATURES.md](FEATURES.md)** - Características principales
- **[docs/learning_mode.md](docs/learning_mode.md)** - Modo aprendizaje detallado
- **[docs/TUTORIAL_SYSTEM.md](docs/TUTORIAL_SYSTEM.md)** - 🆕 Sistema de tutorial interactivo
- **[docs/graphical_display.md](docs/graphical_display.md)** - Displays gráficos opcionales
- **[docs/PROFILE_SYSTEM_README.md](docs/PROFILE_SYSTEM_README.md)** - 🆕 Sistema de perfiles de instrumentos

### Documentación Técnica
- **[docs/hardware_setup.md](docs/hardware_setup.md)** - Conexiones y configuración
- **[docs/led_alignment.md](docs/led_alignment.md)** - Alineación física LEDs
- **[docs/troubleshooting.md](docs/troubleshooting.md)** - Solución de problemas
- **[docs/INSTRUMENT_PROFILES.md](docs/INSTRUMENT_PROFILES.md)** - 🆕 API de perfiles de instrumentos
- **[docs/ARQUITECTURA_MODULAR.md](docs/ARQUITECTURA_MODULAR.md)** - Arquitectura modular de la GUI
- **[docs/advanced_examples.md](docs/advanced_examples.md)** - Uso avanzado

### Herramientas de Desarrollo
- **[utils/demo_tutorial.py](utils/demo_tutorial.py)** - Demo independiente del sistema de tutorial

### Recursos Externos
- [Documentación oficial WS2812B](https://cdn-shop.adafruit.com/datasheets/WS2812B.pdf)
- [GPIO Raspberry Pi](https://pinout.xyz/)
- [Formato MIDI](https://www.midi.org/specifications)
- [Librería mido](https://mido.readthedocs.io/)

---

## 📝 Licencia

MIT License - Libre para usar, modificar y distribuir.

---

## 👨‍💻 Contribuciones

¡Contribuciones bienvenidas!

1. Fork el proyecto
2. Crea una rama (`git checkout -b feature/mejora`)
3. Commit (`git commit -m 'Agrega nueva funcionalidad'`)
4. Push (`git push origin feature/mejora`)
5. Abre un Pull Request

---

## ⭐ Agradecimientos

Inspirado en sistemas comerciales tipo Keysnake/Piano Marvel, pero completamente open-source y DIY.

---

## 📧 Soporte

¿Problemas? Abre un issue en GitHub o consulta `docs/troubleshooting.md`.

---

**¡Disfruta tu piano iluminado! 🎹✨**
