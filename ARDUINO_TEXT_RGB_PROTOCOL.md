# Arduino Text Protocol with RGB Support

## Overview
Sistema mejorado que combina la simplicidad del protocolo texto con soporte completo para colores RGB y brillo personalizable.

## Características

### ✅ Protocol Features
- **Text-based** - Fácil de debuggear y leer
- **RGB colors** - 16.7 millones de colores (0-255 por canal)
- **Brightness control** - Individual (por comando) y global (0-255)
- **Batch updates** - Múltiples LEDs en un solo comando
- **Fast** - 115200 baud, sin delays en el loop
- **Reliable** - Newline terminated, parsing robusto

### 🎨 Command Set

#### 1. ON - LED con brillo (verde por defecto)
```
ON:note:brightness\n
```
- `note`: MIDI note (21-108)
- `brightness`: 0-100 (porcentaje)

**Ejemplo:**
```python
ser.write(b"ON:60:100\n")  # Middle C, full brightness (green)
ser.write(b"ON:60:50\n")   # Middle C, 50% brightness (green)
```

#### 2. LED - Color RGB personalizado
```
LED:note,r,g,b\n
```
- `note`: MIDI note (21-108)
- `r, g, b`: 0-255 cada uno

**Ejemplos:**
```python
ser.write(b"LED:60,255,0,0\n")    # Red
ser.write(b"LED:62,0,255,0\n")    # Green
ser.write(b"LED:64,0,0,255\n")    # Blue
ser.write(b"LED:65,255,255,0\n")  # Yellow
ser.write(b"LED:67,255,0,255\n")  # Magenta
ser.write(b"LED:69,0,255,255\n")  # Cyan
ser.write(b"LED:71,255,128,0\n")  # Orange
```

#### 3. OFF - Apagar LED
```
OFF:note\n
```

**Ejemplo:**
```python
ser.write(b"OFF:60\n")  # Turn off middle C
```

#### 4. BATCH - Múltiples LEDs (ULTRA FAST)
```
BATCH:note1,r,g,b;note2,r,g,b;note3,r,g,b\n
```
- Un solo comando para actualizar varios LEDs
- Un solo `FastLED.show()` al final
- **Máximo rendimiento** para acordes

**Ejemplo:**
```python
# C major chord (red, green, blue)
ser.write(b"BATCH:60,255,0,0;64,0,255,0;67,0,0,255\n")

# Rainbow on multiple notes
ser.write(b"BATCH:60,255,0,0;62,255,127,0;64,255,255,0;65,0,255,0;67,0,0,255;69,75,0,130\n")
```

#### 5. CLEAR - Apagar todos
```
CLEAR\n
```

**Ejemplo:**
```python
ser.write(b"CLEAR\n")
```

#### 6. BRIGHTNESS - Brillo global
```
BRIGHTNESS:value\n
```
- `value`: 0-255
- Afecta todos los LEDs

**Ejemplo:**
```python
ser.write(b"BRIGHTNESS:128\n")  # 50% brightness
ser.write(b"BRIGHTNESS:255\n")  # Full brightness
ser.write(b"BRIGHTNESS:64\n")   # 25% brightness
```

#### 7. TEST - Animación de prueba
```
TEST\n
```
- Sweep RGB por todos los LEDs
- Útil para verificar funcionamiento

**Ejemplo:**
```python
ser.write(b"TEST\n")
```

#### 8. PING - Test de conexión
```
PING\n
```
- Arduino responde: `PONG\n`

**Ejemplo:**
```python
ser.write(b"PING\n")
response = ser.readline()  # b"PONG\n"
```

## Python API (ArduinoWorker)

### Métodos Principales

#### send_note_on()
```python
# Con brillo (verde por defecto)
worker.send_note_on(60, brightness=100)

# Con color RGB personalizado
worker.send_note_on(60, r=255, g=0, b=0)  # Red
worker.send_note_on(62, r=0, g=255, b=0)  # Green
worker.send_note_on(64, r=0, g=0, b=255)  # Blue
```

#### send_note_off()
```python
worker.send_note_off(60)
```

#### send_led_rgb()
```python
worker.send_led_rgb(60, 255, 0, 0)    # Red
worker.send_led_rgb(62, 0, 255, 0)    # Green
worker.send_led_rgb(64, 0, 0, 255)    # Blue
```

#### send_batch_leds()
```python
# C major chord with colors
leds = [
    (60, 255, 0, 0),   # C - Red
    (64, 0, 255, 0),   # E - Green
    (67, 0, 0, 255),   # G - Blue
]
worker.send_batch_leds(leds)
```

#### clear_all_leds()
```python
worker.clear_all_leds()
```

#### set_brightness()
```python
worker.set_brightness(128)  # 50%
worker.set_brightness(255)  # 100%
```

#### test_leds()
```python
worker.test_leds()
```

#### ping()
```python
worker.ping()
```

## Ventajas del Protocolo Texto

### 🔍 Debugging
```python
# Fácil de ver en Serial Monitor
"LED:60,255,0,0\n"      # Claro y legible
"BATCH:60,255,0,0;62,0,255,0\n"  # Se entiende inmediatamente
```

### 📊 Performance
- **115200 baud** - Rápido y confiable
- **No delays** - Arduino loop procesa instantáneamente
- **Batch support** - Un solo show() para múltiples LEDs
- **FastLED optimizations** - 120 Hz refresh rate

### 🛠️ Extensibilidad
```python
# Fácil agregar nuevos comandos
"FADE:note,r1,g1,b1,r2,g2,b2,duration\n"
"PULSE:note,r,g,b,speed\n"
"RAINBOW:start_note,end_note\n"
```

## Ejemplos de Uso

### Ejemplo 1: Nota Simple
```python
# Verde con brillo
arduino.send_note_on(60, brightness=100)
time.sleep(1)
arduino.send_note_off(60)
```

### Ejemplo 2: Colores RGB
```python
# Rojo
arduino.send_note_on(60, r=255, g=0, b=0)
time.sleep(0.5)

# Verde
arduino.send_note_on(62, r=0, g=255, b=0)
time.sleep(0.5)

# Azul
arduino.send_note_on(64, r=0, g=0, b=255)
time.sleep(0.5)

arduino.clear_all_leds()
```

### Ejemplo 3: Acorde con BATCH
```python
# C major chord - rainbow colors
chord = [
    (60, 255, 0, 0),      # C - Red
    (64, 255, 255, 0),    # E - Yellow
    (67, 0, 255, 0),      # G - Green
]
arduino.send_batch_leds(chord)
time.sleep(1)
arduino.clear_all_leds()
```

### Ejemplo 4: Control de Brillo
```python
# LED blanco con diferentes brillos
arduino.send_note_on(60, r=255, g=255, b=255)

for brightness in [255, 192, 128, 64, 32]:
    arduino.set_brightness(brightness)
    time.sleep(0.5)

arduino.clear_all_leds()
```

### Ejemplo 5: Animación
```python
# Rainbow sweep
colors = [
    (255, 0, 0),      # Red
    (255, 127, 0),    # Orange
    (255, 255, 0),    # Yellow
    (0, 255, 0),      # Green
    (0, 0, 255),      # Blue
    (75, 0, 130),     # Indigo
    (148, 0, 211),    # Violet
]

for i, (r, g, b) in enumerate(colors):
    note = 60 + i
    arduino.send_note_on(note, r=r, g=g, b=b)
    time.sleep(0.1)

time.sleep(1)
arduino.clear_all_leds()
```

## Testing

### Test Script
```bash
python test_arduino_rgb.py
```

**Tests incluidos:**
1. PING/PONG
2. ON command (brightness)
3. LED command (RGB colors)
4. OFF command
5. BATCH command (chord)
6. BRIGHTNESS control
7. TEST animation

## Hardware Requirements

- Arduino Uno/Nano/Mega
- WS2812B LED strip (88 LEDs para piano completo)
- FastLED library instalada
- USB connection at 115200 baud

## Migration Guide

### Desde Protocolo Binario

**Antes (Binary):**
```python
worker = ArduinoWorker(port="COM19", baudrate=500000)
worker.send_note_on(60, r=255, g=0, b=0)
```

**Ahora (Text):**
```python
worker = ArduinoWorker(port="COM19", baudrate=115200)
worker.send_note_on(60, r=255, g=0, b=0)  # Mismo API!
```

**Cambios necesarios:**
1. ✅ Subir nuevo sketch Arduino
2. ✅ Cambiar baudrate de 500000 → 115200
3. ✅ API Python permanece igual (compatible)

## Troubleshooting

### LED no enciende
```python
# Verificar conexión
arduino.ping()  # Debe responder PONG

# Verificar rango de notas (21-108)
arduino.send_note_on(60, r=255, g=0, b=0)  # OK
arduino.send_note_on(120, r=255, g=0, b=0)  # IGNORADO (fuera de rango)
```

### Test de hardware
```python
# Test completo
arduino.test_leds()  # RGB sweep
```

### Debug commands
```python
# Monitor serial en Arduino IDE para ver comandos recibidos
# Descomentar líneas de debug en sketch si necesario
```

## Performance Metrics

- **Latency**: <5ms (USB + processing)
- **Throughput**: ~11,520 bytes/sec (115200 baud)
- **Batch efficiency**: 1 show() para N LEDs
- **Command overhead**: ~10-20 bytes per LED

## Conclusion

Este protocolo combina:
- ✅ Simplicidad del texto (fácil debug)
- ✅ Potencia del RGB (16.7M colores)
- ✅ Velocidad del batch (acordes instantáneos)
- ✅ Compatibilidad del API (mismos métodos)

**Resultado:** Sistema flexible, rápido y fácil de usar. 🎹✨
