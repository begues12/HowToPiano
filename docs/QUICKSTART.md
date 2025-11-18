# Guía de Inicio Rápido - HowToPiano

## ⚡ Instalación en 5 minutos

### En Raspberry Pi:

```bash
# 1. Clonar proyecto
cd ~
git clone https://github.com/tu-usuario/HowToPiano.git
cd HowToPiano

# 2. Ejecutar instalador
sudo bash install.sh

# 3. Probar LEDs
sudo python3 main.py --test

# 4. ¡Listo! Conectar USB con MIDIs y ejecutar
sudo python3 main.py
```

## 🔌 Conexiones Mínimas

```
Raspberry Pi      →    Tira LED WS2812B
Pin 12 (GPIO 18)  →    DIN (Data)
Pin 6 (GND)       →    GND
                       +5V ← Fuente externa 5V 5A
```

## 🎹 Uso Básico

### 🎓 Modo Aprendizaje (Recomendado):
```bash
sudo python3 main.py
# Selecciona opción 3 → Elige canción → Elige modo (1, 2 o 3)
```

### Modo interactivo:
```bash
sudo python3 main.py
```

### Reproducir archivo directo:
```bash
sudo python3 main.py --file /media/pi/USB/cancion.mid
```

### Aprender archivo específico:
```bash
sudo python3 main.py --learn /media/pi/USB/cancion.mid
```

### Test de instalación:
```bash
python3 utils/test_install.py
```

## 📚 Más Info

- Documentación completa: `README.md`
- Guía de hardware: `docs/hardware_setup.md`
- Problemas: `docs/troubleshooting.md`
- Alineación LEDs: `docs/led_alignment.md`

## 💡 Comandos Útiles

```bash
# Teclado de 61 teclas
sudo python3 main.py --keyboard keyboard_61 --leds 61

# Ajustar brillo
sudo python3 main.py --brightness 0.5

# Modo simulación (pruebas sin hardware)
python3 main.py --simulate

# Ver ayuda
python3 main.py --help
```

¡Disfruta tu piano iluminado! 🎹✨
