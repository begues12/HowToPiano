# 🚀 Inicio Rápido - Interfaz Gráfica

## Windows (Desarrollo/Test)

```bash
# 1. Instalar dependencias mínimas
pip install mido

# 2. Ejecutar GUI
python test_gui.py
```

## Raspberry Pi (Producción)

```bash
# 1. Clonar proyecto
cd /home/pi
git clone <tu-repo> HowToPiano
cd HowToPiano

# 2. Instalar dependencias
sudo pip3 install mido
sudo pip3 install rpi-ws281x adafruit-circuitpython-neopixel

# 3. Ejecutar
sudo python3 gui_app.py
```

## ✨ Características Principales

### Panel Izquierdo - Partituras
```
┌──────────────────┐
│ 🔍 Buscar MIDI   │ ← Buscar archivos locales
│ 📂 USB           │ ← Escanear memoria USB
├──────────────────┤
│ ⏱ Recientes      │
│  Fur Elise.mid   │ ← Doble click para cargar
│  Moonlight.mid   │
│  Canon.mid       │
└──────────────────┘
```

### Panel Derecho - Control

```
┌─────────────────────────────────────┐
│   🎹 Fur Elise.mid                  │
│   📍 /media/pi/USB/Fur_Elise.mid    │
├─────────────────────────────────────┤
│ 🎓 Modos de Aprendizaje             │
│                                     │
│ [👨‍🎓 Modo Alumno]    Espera cada 4  │
│ [🎹 Modo Práctica]   acordes        │
│ [🎼 Modo Maestro]                   │
├─────────────────────────────────────┤
│  Teclado Virtual (88 teclas)       │
│  ▓░▓░▓░░▓░▓░▓░▓░░▓░▓░▓░░▓░▓...    │
│  ▓ = Tecla negra iluminada         │
│  ░ = Tecla blanca iluminada        │
├─────────────────────────────────────┤
│        [⏹ DETENER]                  │
│  Progreso: ████████░░░░ 45%        │
└─────────────────────────────────────┘
```

## 🎯 Uso Típico

### Escenario 1: Primera Vez

1. **Abrir GUI**: `python test_gui.py` (Windows) o `sudo python3 gui_app.py` (Pi)
2. **Click ⚙ Configuración**
   - Número de teclas: `88` (o el tuyo)
   - Número de LEDs: `88` (o los que tengas)
   - Modo LED: `Full`
   - Click `✓ Guardar`
3. **Click 🔍 Buscar MIDI**
   - Selecciona un archivo `.mid`
4. **Click 👨‍🎓 Modo Alumno**
   - ¡Empieza a aprender!

### Escenario 2: Uso Diario

1. Abrir GUI
2. Doble click en canción reciente
3. Click en modo deseado
4. Practicar

### Escenario 3: USB con Múltiples Canciones

1. Insertar USB con archivos `.mid`
2. Click `📂 USB`
3. Aparece popup con lista de archivos
4. Seleccionar canción
5. Click modo de aprendizaje

## ⚙️ Configuración Detallada

### Mapeo LED Inteligente

El sistema ajusta automáticamente los LEDs disponibles:

```
Ejemplo 1: 88 teclas, 88 LEDs
→ Mapeo 1:1 (un LED por tecla)

Ejemplo 2: 61 teclas, 88 LEDs
→ Mapeo proporcional, sobrantes apagados

Ejemplo 3: 88 teclas, 60 LEDs
→ Distribución uniforme
  Tecla 0 → LED 0
  Tecla 1 → LED 0
  Tecla 2 → LED 1
  Tecla 3 → LED 2
  ...
```

### Modos LED

**Full (Completo)**
- Usa todos los LEDs disponibles
- Distribución uniforme en el teclado

**Compact (Compacto)**
- Usa solo LEDs necesarios
- Resto apagados

**Custom (Personalizado)**
- Define rangos manualmente
- Avanzado

## 🎨 Digitación con Colores

Si activas "Sugerencia de Digitación" en configuración:

```python
Mano Izquierda:
  🔴 Rojo      → Pulgar (1)
  🟠 Naranja   → Índice (2)
  🟡 Amarillo  → Medio (3)
  🟢 Verde     → Anular (4)
  🔵 Azul      → Meñique (5)

Mano Derecha:
  💙 Cyan      → Pulgar (1)
  💜 Morado    → Índice (2)
  🔮 Violeta   → Medio (3)
  🌸 Rosa      → Anular (4)
  ⭐ Magenta   → Meñique (5)
```

## 🎓 Modos Explicados

### Modo Alumno 👨‍🎓
```
Perfecto para: Principiantes
Velocidad: Lenta
Feedback: Espera tecla correcta

Cómo funciona:
1. Ilumina próximas 4 notas (configurable)
2. Muestra en pantalla qué tocar
3. Espera hasta que toques correctamente
4. Avanza al siguiente grupo
5. Repite
```

### Modo Práctica 🎹
```
Perfecto para: Práctica de velocidad
Velocidad: Normal/Rápida
Feedback: Visual solo

Cómo funciona:
1. Ilumina teclas en tiempo real
2. Sigue tempo de la canción
3. No espera, continúa automáticamente
4. Tú sigues el ritmo
```

### Modo Maestro 🎼
```
Perfecto para: Nivel avanzado
Velocidad: Tu ritmo
Feedback: Tus teclas iluminadas

Cómo funciona:
1. Pantalla muestra partitura
2. TÚ tocas las teclas
3. LEDs iluminan lo que presionas
4. Sistema verifica si es correcto
5. Estadísticas al final
```

## 🔥 Tips Pro

### Optimizar Aprendizaje
1. **Empieza con 2 acordes** en Modo Alumno
2. **Aumenta gradualmente** a 4, 8, 16
3. **Pasa a Práctica** cuando domines la pieza
4. **Finaliza con Maestro** para perfeccionar

### Configurar USB Automático
```bash
# En Raspberry Pi, editar config:
nano config/config.json

# Cambiar:
"usb_path": "/media/pi/NOMBRE_USB/MIDI/"
```

### Shortcuts Teclado (Futuros)
```
Espacio: Play/Pause
ESC: Stop
←/→: Canción anterior/siguiente
↑/↓: Volumen LEDs
```

## 🐛 Problemas Comunes

### "Sin partitura cargada"
→ Cargas una canción primero con 🔍 o 📂

### "LEDs no funcionan"
→ Verifica conexión GPIO pin 18
→ Ejecuta con `sudo`

### "Ventana muy pequeña"
→ Redimensiona manualmente
→ Teclado se ajusta automáticamente

### "No encuentra archivos USB"
→ Configura ruta correcta en ⚙
→ Windows: `E:\` o letra USB
→ Linux: `/media/pi/`

## 📦 Estructura Archivos

```
HowToPiano/
├── gui_app.py          ← Aplicación principal
├── test_gui.py         ← Test Windows
├── config/
│   ├── config.json     ← Configuración sistema
│   └── recent.json     ← Canciones recientes
├── src/
│   ├── midi_reader.py
│   ├── led_controller.py
│   └── note_mapper.py
└── docs/
    └── GUI_README.md   ← Esta guía
```

## 🚀 Siguiente Paso

Una vez que domines la GUI básica:

1. Lee [docs/learning_mode.md](docs/learning_mode.md) para técnicas avanzadas
2. Consulta [docs/hardware_setup.md](docs/hardware_setup.md) para optimización LEDs
3. Explora [docs/advanced_examples.md](docs/advanced_examples.md) para personalización

## 💡 Ejemplo Completo

```bash
# Día 1: Setup inicial
$ python3 test_gui.py
# Configurar: 61 teclas, 61 LEDs
# Cargar: Twinkle Twinkle Little Star
# Modo Alumno: 2 acordes
# Practicar 15 minutos

# Día 2: Misma canción
# Modo Alumno: 4 acordes
# Practicar hasta dominar

# Día 3: Avanzar
# Modo Práctica
# Seguir tempo real

# Día 4: Maestro
# Tocar sin ayuda
# Solo verificación visual

# Resultado: ¡Canción aprendida en 4 días! 🎉
```

---

**¿Preguntas?** Revisa [troubleshooting.md](docs/troubleshooting.md)

**¿Bugs?** Abre un issue en GitHub

**¿Mejoras?** Pull requests bienvenidos!
