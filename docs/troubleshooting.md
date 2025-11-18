# 🐛 Solución de Problemas - HowToPiano

## 📋 Índice de Problemas

1. [Problemas con LEDs](#problemas-con-leds)
2. [Problemas con MIDI](#problemas-con-midi)
3. [Problemas con USB](#problemas-con-usb)
4. [Errores de Software](#errores-de-software)
5. [Problemas de Rendimiento](#problemas-de-rendimiento)
6. [Problemas de Hardware](#problemas-de-hardware)

---

## 🔴 Problemas con LEDs

### Los LEDs no se encienden en absoluto

**Diagnóstico:**
```bash
# Verificar permisos GPIO
sudo python3 -c "import RPi.GPIO as GPIO; print('GPIO OK')"

# Test simple
sudo python3 main.py --test
```

**Soluciones:**

1. **Ejecutar con sudo**
   ```bash
   sudo python3 main.py
   ```
   Los pines GPIO requieren permisos de superusuario.

2. **Verificar SPI habilitado**
   ```bash
   sudo raspi-config
   # → Interface Options → SPI → Enable
   sudo reboot
   ```

3. **Comprobar conexiones físicas**
   - GND común conectado
   - DIN conectado a GPIO 18
   - Fuente 5V conectada a tira LED

4. **Verificar librerías instaladas**
   ```bash
   sudo pip3 install --upgrade rpi_ws281x adafruit-circuitpython-neopixel
   ```

---

### Solo el primer LED funciona

**Causa:** Conexión entre LEDs interrumpida

**Soluciones:**

1. Verifica soldadura/contactos en la tira LED
2. Comprueba que DOUT del primer LED conecte a DIN del segundo
3. Prueba con menos LEDs para aislar el problema
4. Reemplaza primer LED si está dañado

---

### LEDs parpadean o tienen glitches

**Causa:** Fuente insuficiente o señal ruidosa

**Soluciones:**

1. **Usar fuente más potente**
   ```
   Mínimo: 5V 5A para 88 LEDs
   Recomendado: 5V 10A
   ```

2. **Agregar capacitor**
   - 1000µF entre VCC y GND de la tira
   - Lo más cerca posible del primer LED

3. **Mejorar señal**
   - Usa convertidor de nivel 3.3V → 5V
   - Cable corto (<30 cm) entre Raspberry y tira
   - Resistencia 330Ω en serie con DIN

4. **Reducir brillo**
   ```bash
   sudo python3 main.py --brightness 0.2
   ```

---

### Colores incorrectos

**Causa:** Orden de píxeles incorrecto

**Solución:**

Edita `src/led_controller.py` línea ~35:

```python
# Prueba diferentes órdenes:
pixel_order=neopixel.GRB  # Por defecto
pixel_order=neopixel.RGB  # Alternativo
pixel_order=neopixel.GRBW # Si son RGBW
```

---

### LEDs se apagan aleatoriamente

**Causa:** Caída de voltaje o sobrecalentamiento

**Soluciones:**

1. Usa cable más grueso (AWG 18-20)
2. Inyecta voltaje en múltiples puntos (cada 30-50 LEDs)
3. Mejora ventilación
4. Reduce brillo máximo

---

## 🎵 Problemas con MIDI

### No encuentra archivos MIDI

**Diagnóstico:**
```bash
# Verificar punto de montaje USB
ls /media/pi/

# Buscar archivos manualmente
find /media -name "*.mid" 2>/dev/null
```

**Soluciones:**

1. **Verifica extensión de archivos**
   - Debe ser `.mid` o `.midi` (minúsculas)
   - Renombra si es necesario

2. **Comprueba permisos**
   ```bash
   sudo chmod -R 755 /media/pi/
   ```

3. **Monta USB manualmente**
   ```bash
   sudo mkdir -p /media/pi/usb
   sudo mount /dev/sda1 /media/pi/usb
   ```

4. **Cambia punto de montaje en código**
   Edita `src/midi_reader.py` línea ~9:
   ```python
   self.usb_mount_point = "/media/pi"  # Cambia aquí
   ```

---

### Error al cargar archivo MIDI

**Mensaje:** `Error cargando archivo MIDI: ...`

**Soluciones:**

1. **Archivo corrupto**
   - Abre el MIDI en PC con software MIDI
   - Re-exporta desde DAW
   - Prueba con otro archivo

2. **Formato no soportado**
   - Solo MIDI tipo 0, 1 y 2
   - Algunos MIDI viejos pueden fallar

3. **Reinstalar mido**
   ```bash
   pip3 install --upgrade mido
   ```

---

### Notas fuera de rango

**Mensaje:** `X notas fuera del rango del teclado`

**Solución:**

Ajusta configuración de teclado:

```bash
# Piano completo (21-108)
sudo python3 main.py --keyboard piano_88

# Teclado 61 teclas (36-96)
sudo python3 main.py --keyboard keyboard_61

# Personalizado
# Edita config/config.json
```

---

### Timing incorrecto (muy rápido/lento)

**Causa:** Carga del sistema

**Soluciones:**

1. **Cierra procesos innecesarios**
   ```bash
   sudo systemctl stop bluetooth
   sudo systemctl stop avahi-daemon
   ```

2. **Aumenta prioridad del proceso**
   ```bash
   sudo nice -n -20 python3 main.py
   ```

3. **Overclocking moderado** (opcional)
   Edita `/boot/config.txt`:
   ```
   arm_freq=1000
   ```

---

## 💾 Problemas con USB

### USB no detectado

**Diagnóstico:**
```bash
# Listar dispositivos USB
lsusb

# Ver puntos de montaje
lsblk

# Logs del sistema
dmesg | tail -20
```

**Soluciones:**

1. **Verifica conexión física**
   - Usa adaptador OTG correcto
   - Prueba con otro pendrive

2. **Formatea USB correctamente**
   - Formato: FAT32 o exFAT
   - Etiqueta: sin espacios

3. **Monta manualmente**
   ```bash
   sudo mount /dev/sda1 /media/pi/usb -o uid=pi,gid=pi
   ```

4. **Activa USB OTG**
   Edita `/boot/config.txt`:
   ```
   dtoverlay=dwc2
   ```
   
   Edita `/boot/cmdline.txt` (agrega):
   ```
   modules-load=dwc2,g_ether
   ```

---

## 💻 Errores de Software

### `ImportError: No module named 'mido'`

**Solución:**
```bash
pip3 install mido
# O con sudo:
sudo pip3 install mido
```

---

### `ImportError: No module named 'neopixel'`

**Solución:**
```bash
sudo pip3 install rpi-ws281x adafruit-circuitpython-neopixel
```

---

### `PermissionError: [Errno 13]`

**Causa:** Sin permisos GPIO

**Solución:**
```bash
# Ejecutar con sudo
sudo python3 main.py

# O agregar usuario a grupo gpio
sudo usermod -a -G gpio pi
sudo reboot
```

---

### `RuntimeError: ws2811_init failed`

**Causa:** PWM ya en uso o SPI deshabilitado

**Soluciones:**

1. **Deshabilitar audio PWM**
   Edita `/boot/config.txt`:
   ```
   # Comenta esta línea:
   # dtparam=audio=on
   ```

2. **Usar otro GPIO**
   Edita `config/config.json`:
   ```json
   "gpio_pin": 10
   ```
   Pines compatibles: 10, 12, 18, 21

3. **Habilitar SPI**
   ```bash
   sudo raspi-config
   # → Interface Options → SPI → Enable
   ```

---

## ⚡ Problemas de Rendimiento

### Sistema lento/lag

**Soluciones:**

1. **Liberar RAM**
   ```bash
   sudo apt-get clean
   sudo systemctl disable bluetooth
   ```

2. **Usar Raspberry Pi Zero 2 W** (recomendado)
   - 4 núcleos vs 1 núcleo
   - Mejor para procesamiento MIDI

3. **Reducir procesos en background**
   ```bash
   sudo raspi-config
   # → Boot Options → CLI (sin escritorio)
   ```

---

### Latencia entre MIDI y LEDs

**Causa:** Carga CPU

**Soluciones:**

1. Usa modo ligero:
   ```python
   # En led_controller.py
   auto_write=False  # Línea 24
   ```

2. Reduce complejidad visual (sin efectos extra)

3. Overclocking:
   ```
   # /boot/config.txt
   arm_freq=1000
   over_voltage=2
   ```

---

## 🔧 Problemas de Hardware

### Raspberry Pi no enciende

1. Verifica fuente 5V 2.5A mínimo
2. Comprueba cable micro-USB (que sea de datos)
3. LED rojo debe estar fijo
4. LED verde debe parpadear

---

### Tira LED se calienta mucho

**Normal:** Calor moderado es normal

**Solución si es excesivo:**
1. Reduce brillo máximo
2. Mejora ventilación
3. Usa disipador/perfil aluminio
4. Comprueba no hay cortocircuito

---

### Convertidor de nivel no funciona

**Test:**
```bash
# Medir con multímetro:
# Entrada (LV1): ~3.3V cuando GPIO activo
# Salida (HV1): ~5.0V cuando GPIO activo
```

**Si falla:**
1. Verifica VCC correctamente conectado (3.3V y 5V)
2. Comprueba GND común
3. Prueba otro canal del convertidor
4. Reemplaza convertidor

---

## 📞 Ayuda Adicional

### Información para reportar bugs

Si nada funciona, proporciona:

```bash
# Información del sistema
uname -a
python3 --version
cat /etc/os-release

# Librerías instaladas
pip3 list | grep -E "(mido|neopixel|rpi)"

# Logs
sudo dmesg | tail -50
journalctl -xe | tail -30

# Estado GPIO
gpio readall
```

### Comunidad

- GitHub Issues: [Reporta problemas]
- Foros Raspberry Pi
- Reddit: r/raspberry_pi
- Discord de proyectos MIDI

---

## ✅ Checklist de Diagnóstico

Antes de pedir ayuda, verifica:

- [ ] Ejecutas con `sudo python3 main.py`
- [ ] SPI habilitado en `raspi-config`
- [ ] Librerías instaladas (`mido`, `neopixel`)
- [ ] Conexiones físicas correctas (diagrama)
- [ ] GND común entre todos los componentes
- [ ] Fuente 5V adecuada (5A+)
- [ ] USB montado correctamente
- [ ] Archivos `.mid` válidos
- [ ] Probado con `--test` exitosamente
- [ ] No hay otros procesos usando GPIO 18

---

**¿Sigues con problemas? Abre un issue en GitHub con todos los detalles.** 🐛
