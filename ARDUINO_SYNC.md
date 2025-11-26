# Comunicación Arduino-Python Actualizada

## ✅ Cambios Realizados

### 1. **Arduino** (`arduino/ws2812b_piano_leds/ws2812b_piano_leds.ino`)
- ✅ Baudrate: **115200** (comunicación USB rápida)
- ✅ Señal "READY" al iniciar
- ✅ Respuesta "PONG" al comando "PING"
- ✅ Feedback detallado para cada comando
- ✅ Comandos optimizados para FastLED

### 2. **Python** (`src/core/arduino_conn.py`)
- ✅ Baudrate: **115200** (sincronizado con Arduino)
- ✅ Espera señal "READY" con timeout de 5 segundos
- ✅ Fallback a "PING/PONG" si no recibe "READY"
- ✅ Métodos adicionales:
  - `send_led_rgb()` - Control RGB completo
  - `send_batch_leds()` - Actualización múltiple eficiente
  - `clear_all_leds()` - Apagar todo
  - `set_brightness()` - Brillo global
  - `test_leds()` - Animación de prueba
  - `ping()` - Verificar conexión

### 3. **Interfaz** (`src/ui/main_window.py`)
- ✅ Detección automática mejorada con mayor timeout
- ✅ Múltiples intentos de verificación (READY, PING, TEST)
- ✅ Baudrate por defecto: **115200**
- ✅ Comandos corregidos (sin double-escape de `\n`)

### 4. **Configuración** (`src/ui/settings_dialog.py`)
- ✅ Test de conexión con animación de escala
- ✅ Feedback visual en tiempo real
- ✅ Baudrate 115200

### 5. **Test Tools** (`test_arduino.py`)
- ✅ Baudrate por defecto: **115200**

## 🎯 Protocolo de Comunicación

### Python → Arduino

| Comando | Formato | Descripción |
|---------|---------|-------------|
| LED ON | `ON:note:brightness\n` | Encender LED (brightness 0-100) |
| LED OFF | `OFF:note\n` | Apagar LED |
| RGB | `LED:note,r,g,b\n` | Color RGB personalizado (0-255) |
| BATCH | `BATCH:n1,r,g,b;n2,r,g,b\n` | Múltiples LEDs a la vez |
| CLEAR | `CLEAR\n` | Apagar todos los LEDs |
| BRIGHTNESS | `BRIGHTNESS:value\n` | Brillo global (0-255) |
| TEST | `TEST\n` | Animación de prueba |
| PING | `PING\n` | Verificar conexión |

### Arduino → Python

| Respuesta | Formato | Cuándo |
|-----------|---------|--------|
| READY | `READY\n` | Al iniciar (después de startup animation) |
| LED ON | `LED ON: C4 (MIDI 60, LED index 39)\n` | Confirmación de encendido |
| LED OFF | `LED OFF: C4 (MIDI 60)\n` | Confirmación de apagado |
| LED RGB | `LED: C4 RGB(255,0,0)\n` | Confirmación de color |
| PONG | `PONG\n` | Respuesta a PING |
| Test | `Running test animation...\n` | Durante TEST |

## 🧪 Cómo Probar la Conexión

### Opción 1: Script de Prueba Rápida (RECOMENDADO)

```bash
python quick_arduino_test.py
```

Este script:
- 🔍 Busca automáticamente puertos Arduino
- ⏱️ Espera el tiempo correcto para inicialización
- 📡 Prueba comandos PING, ON, OFF
- ✅ Verifica respuestas del Arduino
- 💡 Da feedback detallado

### Opción 2: Aplicación Principal

```bash
python main.py
```

La aplicación:
- 🔍 Detecta automáticamente el Arduino al iniciar
- 🔌 Se conecta a 115200 baud
- 🎹 Controla LEDs al tocar teclas del piano virtual
- 📊 Consola Arduino (click en indicador 🔌) para ver comunicación en tiempo real

### Opción 3: Test Manual desde Python

```python
import serial
import time

# Conectar
ser = serial.Serial('COM19', 115200, timeout=0.5)
time.sleep(3)  # Esperar inicialización

# Leer mensaje READY
while ser.in_waiting > 0:
    print(ser.readline().decode('utf-8').strip())

# Probar PING
ser.write(b"PING\n")
time.sleep(0.1)
print(ser.readline().decode('utf-8').strip())  # Debe decir "PONG"

# Encender LED
ser.write(b"ON:60:100\n")  # Middle C, brillo 100%
time.sleep(0.1)
print(ser.readline().decode('utf-8').strip())

# Apagar LED
ser.write(b"OFF:60\n")
time.sleep(0.1)
print(ser.readline().decode('utf-8').strip())

ser.close()
```

## 🔧 Troubleshooting

### Problema: "No valid response from COM19"

**Causas posibles:**
1. ⏱️ **Timing insuficiente** - El Arduino necesita 3 segundos para inicializar
2. 📟 **Baudrate incorrecto** - Debe ser 115200 en Arduino y Python
3. 🔄 **Arduino no reseteado** - El Arduino se resetea al abrir serial
4. 💾 **Sketch incorrecto** - Verifica que `ws2812b_piano_leds.ino` esté subido

**Soluciones:**

1. **Verificar sketch Arduino:**
   ```cpp
   Serial.begin(115200);  // Debe ser 115200
   Serial.println("READY");  // Debe enviar READY al final de setup()
   ```

2. **Probar manualmente con Arduino IDE:**
   - Abrir Serial Monitor a 115200 baud
   - Deberías ver "READY" después de resetear
   - Escribir "PING" y presionar Enter
   - Deberías ver "PONG"

3. **Verificar puerto:**
   - Windows: Administrador de Dispositivos → Puertos COM
   - El Arduino debe aparecer como "Arduino Uno" o "USB-SERIAL CH340"

4. **Resetear Arduino:**
   - Desconectar USB
   - Esperar 5 segundos
   - Reconectar USB
   - Esperar a que Windows lo reconozca
   - Ejecutar `quick_arduino_test.py`

### Problema: LEDs no se encienden

**Verificar:**
1. ⚡ **Alimentación** - Tira LED necesita fuente externa 5V
2. 📌 **Pin correcto** - GPIO 6 (Pin digital 6)
3. 🔢 **NUM_LEDS** - Debe coincidir con cantidad real de LEDs
4. 📚 **Librería FastLED** - Debe estar instalada en Arduino IDE

### Problema: Comunicación lenta o errática

**Soluciones:**
1. ✅ Usar comandos BATCH para múltiples LEDs
2. ✅ Verificar baudrate = 115200 (no 9600)
3. ✅ Cable USB de buena calidad (algunos solo cargan)
4. ✅ Puerto USB directo (no hub USB de baja calidad)

## 📊 Verificación de Sincronización

El sistema está completamente sincronizado cuando:
- ✅ Baudrate: **115200** (Arduino y Python)
- ✅ Arduino envía "READY" al iniciar
- ✅ Python espera 3 segundos para inicialización
- ✅ PING responde con PONG en <100ms
- ✅ LEDs responden inmediatamente a comandos ON/OFF
- ✅ Consola Arduino muestra feedback de cada comando

## 🎉 Estado Actual

**Todo sincronizado y listo para usar:**
- ✅ Arduino: 115200 baud, protocolo completo
- ✅ Python: 115200 baud, auto-detección mejorada
- ✅ Protocolo: Compatible y documentado
- ✅ Tests: Script de prueba rápida disponible
- ✅ README: Documentación completa

**Próximos pasos:**
1. Ejecutar `quick_arduino_test.py` para verificar conexión
2. Si funciona, ejecutar `main.py` para la aplicación completa
3. Tocar teclas del piano virtual y ver LEDs responder
4. Abrir consola Arduino (click 🔌) para ver comunicación
