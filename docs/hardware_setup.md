# 🔧 Guía de Conexiones Hardware

## Esquema de conexión completo

### Raspberry Pi Zero W/W2 → Tira LED WS2812B

```
                    RASPBERRY PI ZERO W
                    ┌─────────────────────┐
                    │                     │
                    │  ┌───┐          ┌───┐
                    │  │ 1 │──────────│ 2 │  (5V - Opcional)
                    │  └───┘          └───┘
                    │  ┌───┐          ┌───┐
                    │  │ 3 │──────────│ 4 │  (5V)
                    │  └───┘          └───┘
                    │  ┌───┐          ┌───┐
                    │  │ 5 │──────────│ 6 │  (GND)
                    │  └───┘          └───┘
                    │  ┌───┐          ┌───┐
                    │  │ 7 │──────────│ 8 │
                    │  └───┘          └───┘
                    │  ┌───┐          ┌───┐
         GND ───────│  │ 9 │──────────│10 │
                    │  └───┘          └───┘
                    │  ┌───┐          ┌───┐
                    │  │11 │──────────│12 │ ◄── GPIO 18 (PWM0)
                    │  └───┘          └───┘      SEÑAL LED
                    │                     │
                    └─────────────────────┘

                         ↓ GPIO 18 (Pin 12)
                         ↓
                    [Convertidor de nivel]
                    [   3.3V → 5V        ]
                         ↓
                         ↓
                    ┌────────────┐
                    │ LED Strip  │
                    │  WS2812B   │
                    ├────────────┤
                    │ DIN  ←─────┼──── Señal convertida
                    │ +5V  ←─────┼──── Fuente externa 5V
                    │ GND  ←─────┼──── GND común
                    └────────────┘
```

---

## 🔌 Conexiones Detalladas

### 1. Raspberry Pi → Convertidor de Nivel

| Pin Raspberry Pi | Función | Conexión |
|------------------|---------|----------|
| Pin 12 (GPIO 18) | Señal PWM | → Convertidor (LV) |
| Pin 1 (3.3V) | Alimentación LV | → Convertidor (VCC LV) |
| Pin 6 o 9 (GND) | Tierra | → GND común |

### 2. Convertidor de Nivel → Tira LED

| Convertidor | Tira LED WS2812B |
|-------------|------------------|
| HV (salida 5V) | → DIN (Data In) |
| GND | → GND |

### 3. Fuente Externa → Tira LED

| Fuente 5V | Tira LED |
|-----------|----------|
| +5V | → +5V / VCC |
| GND | → GND |

**⚠️ IMPORTANTE:** Conecta todos los GND juntos (Raspberry, convertidor, LEDs, fuente).

---

## 🛠️ Convertidor de Nivel 3.3V → 5V

### Opción 1: Convertidor Bidireccional (Recomendado)

**Modelo:** Logic Level Converter 4 canales

```
    LV (3.3V)          HV (5.0V)
    ┌──────────────────────────┐
    │ LV    LV1   LV2   LV3  LV│
    │ GND   ───   ───   ───  GND│
    │                          │
    │ HV    HV1   HV2   HV3  HV│
    └──────────────────────────┘

Conexiones:
- LV (lado izq.) → 3.3V Raspberry
- LV1 → GPIO 18
- GND → GND común
- HV (lado der.) → 5V fuente
- HV1 → DIN tira LED
```

**Precio:** $2-5 USD

### Opción 2: Resistencia Pull-Up (Método simple)

Si no tienes convertidor, puedes usar una resistencia de 330-470Ω entre GPIO18 y DIN:

```
GPIO 18 ──┬─── 330Ω ───┬─── DIN
          │            │
          └── 10kΩ ────┘─── +5V
```

⚠️ Este método funciona con tiras cortas, pero no es óptimo.

### Opción 3: Sin convertidor (Solo para pruebas)

Algunos usuarios reportan que WS2812B acepta 3.3V directamente:

```
GPIO 18 ───────────► DIN
```

✅ Funciona en muchos casos  
⚠️ Fuera de especificación (WS2812B requiere >3.5V)  
❌ Puede causar fallos intermitentes  

---

## ⚡ Fuente de Alimentación

### Cálculo de corriente

Cada LED WS2812B consume:
- **Máximo (blanco brillante):** ~60 mA
- **Promedio (uso normal):** ~20-30 mA

**Ejemplo para piano de 88 teclas:**

```
88 LEDs × 30 mA = 2.64 A
88 LEDs × 60 mA = 5.28 A (máximo)
```

**Fuente recomendada:** 5V 5A (con margen de seguridad)

### Especificaciones fuente

- **Voltaje:** 5V DC regulado
- **Corriente:** Mínimo 5A para 88 LEDs
- **Tipo:** Switching power supply
- **Conector:** Jack DC o terminales

**⚠️ NO alimentes los LEDs desde Raspberry Pi** - Los pines de 5V solo pueden dar ~500mA.

---

## 🔩 Materiales Adicionales

### Lista de Compras

| Componente | Cantidad | Precio |
|------------|----------|--------|
| Raspberry Pi Zero W/W2 | 1 | $15-20 |
| Tira LED WS2812B 88 LEDs | 1 | $15-25 |
| Fuente 5V 5A | 1 | $10-15 |
| Convertidor nivel lógico | 1 | $2-5 |
| Adaptador micro USB a USB-A (OTG) | 1 | $3-5 |
| Cables jumper macho-hembra | 5 | $2 |
| Capacitor 1000µF 10V | 1 | $1 |
| Resistencias varias | 1 set | $2 |
| **TOTAL** | | **~$50-70** |

### Herramientas

- Soldador (opcional)
- Multímetro (recomendado)
- Destornillador
- Alicates
- Cinta aislante / termoretráctil

---

## 📐 Montaje Físico

### Opción 1: Soporte Impreso 3D

Diseña/descarga un soporte que:
- Mantenga LEDs centrados sobre cada tecla
- Separe LEDs a 23 mm (ancho tecla blanca)
- Eleve la tira ~2-5 cm sobre las teclas

### Opción 2: Canal de Aluminio

- Compra perfil de aluminio en U
- Pega tira LED dentro
- Fija sobre el piano con velcro/clips

### Opción 3: Barra Acrílica

- Usa tubo acrílico translúcido
- Inserta tira LED dentro
- Actúa como difusor de luz

---

## 🧪 Prueba de Conexiones

### Test 1: Verificar voltajes

```bash
# Con multímetro:
# - Entre +5V y GND: debe medir ~5.0V
# - Entre 3.3V y GND: debe medir ~3.3V
```

### Test 2: LED de prueba

```bash
sudo python3 main.py --test
```

Debe recorrer todos los LEDs uno por uno.

### Test 3: Primer LED

```python
import board
import neopixel

pixels = neopixel.NeoPixel(board.D18, 1, brightness=0.3)
pixels[0] = (255, 0, 0)  # Rojo
```

Si el primer LED se enciende rojo, todo está correcto.

---

## ⚠️ Seguridad

### ✅ Hacer

- Conectar GND común primero
- Usar fuente adecuada (5V regulada)
- Agregar capacitor 1000µF cerca de la tira
- Verificar voltajes antes de conectar
- Desconectar alimentación al cablear

### ❌ NO hacer

- Alimentar LEDs desde Raspberry Pi
- Invertir polaridad de la fuente
- Conectar/desconectar con alimentación
- Superar 5.5V en la tira LED
- Cortocircuitar señales

---

## 🔧 Troubleshooting Hardware

### Problema: LEDs no se encienden

1. Verifica voltaje en VCC de tira (debe ser 5V)
2. Comprueba GND común
3. Verifica señal en DIN con osciloscopio/lógica
4. Prueba con otro GPIO (GPIO 10, 12, 21)

### Problema: Solo se enciende el primer LED

- Cable DIN → DOUT cortado/suelto
- Tira dañada en segundo LED
- Señal muy débil (usa convertidor)

### Problema: Parpadeo/glitches

- Fuente insuficiente → Usa 5V 10A
- Cable largo → Acorta o usa cable más grueso
- Interferencia → Agrega capacitor 1000µF
- Señal ruidosa → Usa convertidor + resistencia

### Problema: Colores incorrectos

- Orden de píxeles incorrecto
- Edita `led_controller.py`:
```python
pixel_order=neopixel.RGB  # o GRB, RGBW
```

---

## 📊 Diagrama Eléctrico Completo

```
    ┌──────────────────────────┐
    │   Raspberry Pi Zero W    │
    │                          │
    │  GPIO 18 ────────┐       │
    │  3.3V ───────┐   │       │
    │  GND ────┐   │   │       │
    └──────────┼───┼───┼───────┘
               │   │   │
               │   │   └─────────────────┐
               │   │                     │
               │   │   ┌─────────────────┼──────┐
               │   │   │  Convertidor    │      │
               │   └───┤ VCC_LV          │      │
               │       │ LV1             │      │
               ├───────┤ GND   VCC_HV    ├──────┤
               │       │       HV1       │      │
               │       └─────────┬───────┘      │
               │                 │              │
               │                 │              │
   ┌───────────┴─────────┐       │              │
   │  Fuente 5V 5-10A    │       │              │
   │                     │       │              │
   │  +5V ───────────────┼───────┴──────────────┼─────┐
   │  GND ───────────────┼──────────────────────┤     │
   └─────────────────────┘                      │     │
                                                │     │
                          ┌─────────────────────┼─────┼───┐
                          │  Tira LED WS2812B   │     │   │
                          │                     │     │   │
                          │  DIN  ──────────────┘     │   │
                          │  +5V  ────────────────────┘   │
                          │  GND  ────────────────────────┘
                          └───────────────────────────────┘
```

---

¡Con estas conexiones tu sistema debería funcionar perfectamente! 🎹✨
