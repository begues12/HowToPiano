## 🖥️ Interfaz Gráfica HowToPiano

### Ejecutar en Windows (Test)

```bash
# Instalar solo dependencias básicas
pip install mido

# Ejecutar GUI
python test_gui.py
```

### Ejecutar en Raspberry Pi (Producción)

```bash
# Instalar todas las dependencias
sudo pip3 install mido pygame
sudo pip3 install rpi-ws281x adafruit-circuitpython-neopixel

# Ejecutar GUI completa
sudo python3 gui_app.py
```

### Características de la GUI

#### 🎯 Pantalla Principal Única
- Panel izquierdo: Navegación de partituras
- Panel derecho: Visualización y controles

#### 📁 Gestión de Partituras
- **Búsqueda local**: Navega archivos MIDI de tu PC
- **Escaneo USB**: Detecta automáticamente archivos en USB
- **Lista recientes**: Acceso rápido a últimas 10 partituras

#### 🎓 Tres Modos de Aprendizaje

**1. Modo Alumno** 👨‍🎓
- Ilumina las teclas progresivamente
- Espera cada X acordes (configurable: 1-16)
- Verifica que toques correctamente
- Perfecto para principiantes

**2. Modo Práctica** 🎹
- Ilumina todas las teclas en tiempo real
- No espera, sigue el ritmo de la canción
- Para practicar velocidad y fluidez

**3. Modo Maestro** 🎼
- Ilumina solo las teclas que TÚ presionas
- Muestra en pantalla qué deberías tocar
- Para nivel avanzado

#### ⚙️ Configuración Completa

**Teclado Físico:**
- Número de teclas: 25, 49, 61, 88
- Número de LEDs disponibles: 25-150
- Modo LED: Full, Compacto, Custom
- El sistema calcula automáticamente el mapeo óptimo

**Visualización:**
- Brillo ajustable: 10%-100%
- Teclado virtual en pantalla
- Barra de progreso en tiempo real

**Digitación (Experimental):**
- Sugerencia de dedos con colores
- Basado en patrones comunes de piano
- Ayuda a desarrollar técnica correcta

### 🎨 Paleta de Colores

```python
# Mano izquierda
Pulgar (1):   #FF4444  # Rojo
Índice (2):   #FF8800  # Naranja
Medio (3):    #FFDD00  # Amarillo
Anular (4):   #88FF00  # Verde claro
Meñique (5):  #00FF88  # Verde

# Mano derecha
Pulgar (1):   #00FFFF  # Cyan
Índice (2):   #0088FF  # Azul claro
Medio (3):    #0044FF  # Azul
Anular (4):   #8800FF  # Morado
Meñique (5):  #FF00FF  # Magenta
```

### 📊 Algoritmo de Mapeo LED

```python
# Ejemplo: 88 teclas, 60 LEDs disponibles
num_keys = 88
num_leds = 60

# Calcular espaciado
spacing = num_leds / num_keys  # = 0.68

# Mapear cada tecla
for key in range(num_keys):
    led_index = int(key * spacing)
    # led_index irá de 0 a 59
```

### 🚀 Accesos Rápidos

| Acción | Atajo | Descripción |
|--------|-------|-------------|
| Doble clic lista recientes | - | Carga canción directamente |
| Botón STOP | - | Detiene cualquier modo activo |
| Popup USB | - | Selección rápida archivos USB |
| Configuración | ⚙ | Ajustes completos del sistema |

### 🔧 Personalización Avanzada

#### Cambiar colores de teclas
```python
# En gui_app.py, método highlight_key():
def highlight_key(self, note: int, finger: int = None):
    if finger:
        colors = {
            1: '#FF4444',  # Pulgar
            2: '#FF8800',  # Índice
            # ... etc
        }
        color = colors.get(finger, '#00ff88')
```

#### Ajustar velocidad de práctica
```python
# En modos de práctica, añadir multiplicador:
tempo_multiplier = 0.5  # 50% más lento
# o
tempo_multiplier = 1.5  # 50% más rápido
```

### 📱 Futuras Mejoras

- [ ] Control por gestos (cámara)
- [ ] Sincronización multi-dispositivo
- [ ] Grabación de sesiones
- [ ] Estadísticas de progreso
- [ ] Modo competición
- [ ] Exportar a video
- [ ] Integración con MIDI online
- [ ] App móvil complementaria

### 🐛 Solución de Problemas

**La GUI no abre:**
```bash
# Verificar tkinter
python -c "import tkinter; print('OK')"

# Si falla en Linux:
sudo apt-get install python3-tk
```

**Archivos USB no aparecen:**
- Verifica la ruta en Configuración
- En Windows: `D:\` o letra de tu USB
- En Linux: `/media/pi/` o `/mnt/usb/`

**LEDs no responden (Raspberry Pi):**
```bash
# Verificar permisos
sudo python3 gui_app.py

# Verificar GPIO
gpio readall
```

**Teclado virtual no se dibuja bien:**
- Redimensiona la ventana
- El canvas se redibuja automáticamente

### 💡 Tips de Uso

1. **Primera vez**: Configura tu teclado primero (⚙ Configuración)
2. **USB**: Coloca archivos .mid en carpeta `/MIDI/` del USB
3. **Aprendizaje**: Empieza con Modo Alumno, espera 4 acordes
4. **Progreso**: Los recientes se guardan automáticamente
5. **Dedos**: Activa sugerencias en Configuración si eres principiante

### 🎯 Workflow Recomendado

```
1. Conecta USB con archivos MIDI
   ↓
2. Inicia GUI: python3 gui_app.py
   ↓
3. Click "📂 USB" → Selecciona partitura
   ↓
4. Configura teclado (primera vez)
   ↓
5. Click "👨‍🎓 Modo Alumno"
   ↓
6. ¡A practicar! 🎹
```

### 🌟 Ejemplo de Sesión

```bash
$ python3 gui_app.py

# 1. Click "📂 USB"
#    → Aparece popup con 15 archivos
#    → Selecciono "Fur_Elise.mid"
#    → ✓ Cargado

# 2. Click "⚙ Configuración"
#    → Teclas: 61
#    → LEDs: 61
#    → Modo: Full
#    → Digitación: ✓
#    → Guardar

# 3. Click "👨‍🎓 Modo Alumno"
#    → Esperar cada: 4 acordes
#    → Inicio

# 4. Practica...
#    [████████░░░░░░░░] 45% completado

# 5. Click "⏹ DETENER" cuando termines
```

### 📚 Documentación Relacionada

- [README.md](../README.md) - Documentación principal
- [hardware_setup.md](../docs/hardware_setup.md) - Conexiones físicas
- [learning_mode.md](../docs/learning_mode.md) - Modos de aprendizaje detallados
- [graphical_display.md](../docs/graphical_display.md) - Opciones de visualización
