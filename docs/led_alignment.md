# 📏 Alineación de LEDs con Teclas

## El Problema

Las teclas de un piano/teclado tienen un ancho específico, mientras que las tiras LED estándar tienen LEDs equiespaciados:

- **Tecla blanca:** ~23 mm de ancho
- **Tecla negra:** ~13 mm de ancho
- **LED WS2812B estándar:** Separación de 16-17 mm en tira de 60 LEDs/metro

**Resultado:** Los LEDs no se alinean perfectamente con las teclas.

---

## 🎯 Soluciones

### 1. Soporte Impreso en 3D (Recomendado)

Imprime un soporte personalizado que mantenga cada LED centrado sobre su tecla.

#### Características del diseño:

```
Vista lateral:
                ┌─────────────────┐
                │  LED 0  LED 1   │  ← Soporte
                └────┬─────┬──────┘
                     │     │
    ╔═══════╦═══════╦═══════╦═════════╗
    ║   C   ║   D   ║   E   ║    F    ║  ← Teclas
    ╚═══════╩═══════╩═══════╩═════════╝
```

#### Parámetros de diseño:

- **Separación entre LEDs:** 23 mm (ancho tecla blanca)
- **Altura sobre teclas:** 20-40 mm
- **Material:** PLA o PETG
- **Difusor:** Opcional (acrílico translúcido)

#### Archivo STL de ejemplo:

```
led_holder_88keys.stl
├── Largo total: ~1260 mm (88 teclas × 23mm ≈ 2024mm)
├── Agujeros para LEDs: diámetro 12mm, cada 23mm
├── Canales para cables
└── Puntos de fijación con velcro
```

**Modelos 3D disponibles:**
- Thingiverse: buscar "piano led holder"
- Printables: "keyboard LED guide"
- O diseña el tuyo en Fusion 360/Tinkercad

---

### 2. Recortar y Espaciar Tira LED

Para tiras WS2812B que se pueden cortar:

#### Paso a paso:

1. **Identificar puntos de corte**
   - Busca líneas de cobre entre LEDs (suelen tener símbolo ✂)

2. **Cortar segmentos individuales**
   - Un LED por segmento
   - Deja pads de soldadura visibles

3. **Soldar cables entre segmentos**
   ```
   LED1                    LED2
   ┌────┐                ┌────┐
   │ DO ├───[cable]──────┤ DI │
   │ 5V ├───[cable]──────┤ 5V │
   │GND ├───[cable]──────┤GND │
   └────┘                └────┘
     ↕                     ↕
    23 mm de separación
   ```

4. **Fijar a base rígida**
   - Regla de aluminio
   - Perfil en U
   - Listón de madera

**Pros:** Alineación perfecta  
**Contras:** Mucho trabajo de soldadura (88 LEDs = 264 soldaduras)

---

### 3. Canal Difusor

Usa un difusor acrílico que expanda la luz de cada LED.

```
Vista en corte:

    ╔═══════════════════╗  ← Difusor acrílico (translúcido)
    ║   ◉    ◉    ◉    ║  ← LEDs dentro
    ║─────────────────║
    ╚═══════════════════╝
    │                 │
    │    ~~~  ~~~    │  ← Luz expandida
    │   ~~~  ~~~    │
   ┌┴────┴────┴────┴──┐
   │  C   D   E   F   │  ← Teclas
   └──────────────────┘
```

#### Materiales:

- **Tubo acrílico cuadrado:** 15×15 mm, translúcido
- **Perfil LED de aluminio:** Con tapa difusora
- **Largo:** ~125-130 cm para 88 teclas

#### Montaje:

1. Pega tira LED dentro del tubo/canal
2. Coloca difusor
3. Fija sobre el piano con soportes ajustables

**Pros:** Fácil, luz uniforme  
**Contras:** Menos precisión en iluminación individual

---

### 4. Tira Flexible Moldeada

Para tiras flexibles en PCB flexible:

1. **Crear plantilla de 23 mm**
   - Imprime regla con marcas cada 23 mm
   - O usa cinta métrica

2. **Doblar suavemente la tira**
   - Forma de zigzag ligero
   - NO doblar en ángulos cerrados (daña LEDs)

3. **Pegar con cinta de doble cara**
   - Centra cada LED sobre cada tecla

**Pros:** Rápido, sin soldadura  
**Contras:** Menos duradero, estéticamente menos limpio

---

## 📐 Diseño Recomendado: Soporte 3D Modular

### Módulo de 12 teclas (una octava)

```
Diseño modular para facilitar impresión:

Módulo (12 teclas) = 276 mm de largo

┌────────────────────────────────────────────┐
│  O   O   O   O   O   O   O   O   O   O   O │  ← Agujeros LED
│  ─   ─   ─   ─   ─   ─   ─   ─   ─   ─   ─│
│ [clip]                            [clip]  │  ← Sistema encastre
└────────────────────────────────────────────┘

88 teclas = 7 módulos completos + 1 parcial
```

#### Ventajas sistema modular:

✅ Impresión más fácil (piezas más cortas)  
✅ Reemplazo individual si se rompe  
✅ Adaptable a diferentes teclados  
✅ Ensamblaje por clips (sin pegamento)  

#### Parámetros de impresión:

```
Material: PLA
Capa: 0.2 mm
Relleno: 20%
Soportes: No necesarios
Brim/Raft: Recomendado
Tiempo por módulo: ~3-4 horas
```

---

## 🎨 Mejoras Estéticas

### Difusor integrado

Agrega ranura para lámina acrílica:

```
    ┌───────────────────┐
    │                   │  ← Tapa difusora (acrílico 2mm)
    │  ◉    ◉    ◉     │
    │┌─────────────────┐│
    ││   Soporte LED   ││
    │└─────────────────┘│
    └───────────────────┘
```

### Color personalizado

- **Negro mate:** Discreto, profesional
- **Blanco:** Refleja más luz
- **Transparente:** Si el piano es de color

### Iluminación trasera

Opcional: LED strip separado para iluminación ambiental del mueble.

---

## 🔧 Montaje Final

### Opción A: Velcro ajustable

```
Soporte LED
    ↓
[████████████]
    ║ Velcro
    ╠═══════════╣
    ║  Piano   ║
```

**Pros:** Removible, ajustable  
**Contras:** Puede despegarse

### Opción B: Clips/soportes fijos

```
      ┌────┐
      │ LED│
      └──┬─┘
    ┌────┴────┐
    │ Soporte │
    │  Clip   │
    └─────┬───┘
          │
      ╔═══▼═══╗
      ║ Piano ║
      ╚═══════╝
```

**Pros:** Muy estable  
**Contras:** Permanente

### Opción C: Barra telescópica

```
    [████ LEDs ████]
        │      │
        │      │  ← Barras ajustables
    ┌───┴──────┴───┐
    │   Base pie   │  ← Se coloca detrás del piano
    └───────────────┘
```

**Pros:** No daña el piano, muy ajustable  
**Contras:** Más complejo

---

## 📊 Tabla de Distancias

### Piano de 88 teclas

| Teclas | Ancho total | LEDs necesarios | Largo tira (60/m) |
|--------|-------------|-----------------|-------------------|
| 88 | ~123 cm | 88 | 1.47 m (cortar) |

### Teclado 61 teclas

| Teclas | Ancho total | LEDs necesarios | Largo tira |
|--------|-------------|-----------------|------------|
| 61 | ~85 cm | 61 | 1.02 m |

### Espaciado LED personalizado

```python
# Cálculo para soporte 3D
num_teclas = 88
ancho_tecla_blanca = 23  # mm
largo_total = num_teclas * ancho_tecla_blanca
print(f"Largo total necesario: {largo_total} mm = {largo_total/10} cm")

# Resultado: 2024 mm = 202.4 cm
```

---

## 🎓 Tips Avanzados

### LED doble por tecla

Para mayor brillo, usa 2 LEDs por tecla:

```
Tecla 1    Tecla 2
  ◉ ◉        ◉ ◉
  │ │        │ │
 ─┴─┴────────┴─┴─
```

Requiere 176 LEDs para piano 88 teclas.

### Solo teclas blancas

Ahorra LEDs iluminando solo teclas blancas:

- 88 teclas → 52 blancas
- 61 teclas → 36 blancas

```python
# En main.py, filtrar solo blancas:
white_keys = note_mapper.get_white_key_indices()
if led_index in white_keys:
    led_controller.set_led_on(led_index)
```

### Animaciones direccionales

Con LEDs bien alineados, puedes hacer efectos:

```python
# Onda de izquierda a derecha
for i in range(num_leds):
    set_led_on(i)
    time.sleep(0.01)
    set_led_off(i)
```

---

## 📦 Lista de Compras para Montaje

| Material | Cantidad | Uso |
|----------|----------|-----|
| Tira LED WS2812B 60/m | 1.5 m | LEDs principales |
| Filamento PLA | 200g | Soporte 3D |
| Velcro autoadhesivo | 1 m | Fijación |
| Cable 3 hilos 22AWG | 2 m | Extensiones |
| Acrílico translúcido 2mm | 130×5 cm | Difusor |
| Soldador + estaño | 1 | Conexiones |

---

## 🎯 Resultado Final

Con alineación correcta lograrás:

✅ Cada LED centrado sobre su tecla  
✅ Iluminación uniforme y clara  
✅ Aspecto profesional tipo Keysnake  
✅ Fácil identificación de notas  

---

**¡Tu piano iluminado quedará increíble!** 🎹✨
