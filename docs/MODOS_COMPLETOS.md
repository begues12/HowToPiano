# 🎓 Modos de Aprendizaje - Guía Completa

## 📋 Resumen de Modos

| Modo | Nivel | Velocidad | Feedback | Ideal Para |
|------|-------|-----------|----------|------------|
| 👨‍🎓 Alumno | Principiante | Pausada | Espera respuesta | Aprender paso a paso |
| 🎹 Práctica | Intermedio | Normal | Visual continuo | Mejorar velocidad |
| 🎼 Maestro | Avanzado | Tu ritmo | Solo visual | Tocar libremente |

---

## 👨‍🎓 Modo Alumno

### Descripción
El modo más guiado. El sistema muestra un grupo de notas y **espera** que las toques antes de continuar.

### Cómo Funciona

```
1. Sistema ilumina 4 notas (configurable 1-16)
   ┌─────────────────────────────────┐
   │ 🔴 🔴 🔴 🔴 ⚫ ⚫ ⚫ ⚫        │ ← Partitura
   │  C   D   E   F                  │
   └─────────────────────────────────┘
   
2. Teclado virtual muestra teclas iluminadas
   ┌────────────────────────────────┐
   │ [🟢C] [🟢D] [🟢E] [🟢F] ... │ ← Teclado
   └────────────────────────────────┘

3. LEDs físicos encienden (Raspberry Pi)
   🟢🟢🟢🟢⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫

4. ESPERA que toques las 4 notas
   (Simula 2 segundos por nota = 8s total)

5. Apaga LEDs y muestra siguiente grupo
   🟢🟢🟢🟢⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫
   ⚫⚫⚫⚫🟢🟢🟢🟢⚫⚫⚫⚫⚫⚫⚫⚫

6. Repite hasta completar canción
```

### Configuración

**Esperar cada X acordes:**
- `1`: Una nota a la vez (muy lento)
- `2-4`: Ideal para principiantes
- `4-8`: Intermedio
- `8-16`: Frases musicales completas

### Ejemplo de Uso

```python
# Cargar canción
app.load_song("twinkle_twinkle.mid")

# Configurar espera
app.wait_chords_var.set(4)  # 4 notas por bloque

# Iniciar modo
app.start_student_mode()

# Resultado:
# Bloque 1: C C G G (iluminado) → Espera 8s → Apaga
# Bloque 2: A A G - (iluminado) → Espera 6s → Apaga
# Bloque 3: F F E E (iluminado) → Espera 8s → Apaga
# ...continúa hasta el final
```

### Progreso Visual

```
Barra: ████████████░░░░░░░░ 60%
Partitura: 🔴🔴🔴🔴 ⚫⚫⚫⚫⚫⚫ (actuales en rojo)
Teclado: Teclas verdes iluminadas
Status: "▶ Modo Alumno - Toca las notas iluminadas"
```

### Tips
- ✅ Empieza con 2-3 acordes si nunca has tocado piano
- ✅ Aumenta gradualmente conforme mejores
- ✅ Usa canciones lentas (Twinkle Twinkle, Ode to Joy)
- ✅ Practica hasta que no necesites mirar el teclado

---

## 🎹 Modo Práctica

### Descripción
Ilumina las teclas automáticamente siguiendo el tempo de la canción. **NO espera**, continúa al ritmo.

### Cómo Funciona

```
1. Lee timing de archivo MIDI
   Nota C: 0.5 segundos
   Nota D: 0.5 segundos
   Nota E: 0.3 segundos
   Nota F: 0.7 segundos

2. Ilumina cada nota según duración
   🟡C (0.5s) → apaga → 🟡D (0.5s) → apaga → 🟡E (0.3s)...

3. Partitura avanza automáticamente
   🔴 ⚫⚫⚫⚫  →  ⚫🔴⚫⚫⚫  →  ⚫⚫🔴⚫⚫

4. NO ESPERA tu input
   Continúa aunque no toques
   
5. TÚ debes seguir el ritmo
```

### Timing Real

```python
# Ejemplo: Escala Do Mayor
Notas con duración extraída del MIDI:
┌──────┬──────┬──────┬──────┬──────┬──────┬──────┬──────┐
│ C:0.5│ D:0.5│ E:0.5│ F:0.5│ G:0.5│ A:0.5│ B:0.5│ C:1.0│
└──────┴──────┴──────┴──────┴──────┴──────┴──────┴──────┘

Timeline:
0.0s  [🟡C] ──┐
0.5s  [⚫C]    [🟡D] ──┐
1.0s           [⚫D]    [🟡E] ──┐
1.5s                    [⚫E]    [🟡F] ──┐
2.0s                             [⚫F]    [🟡G]...
```

### Ventajas
- ✅ Practicas velocidad real
- ✅ Mejoras coordinación temporal
- ✅ Aprendes el ritmo de la pieza
- ✅ Preparación para tocar sin ayuda

### Desventajas
- ❌ Puede ser rápido al principio
- ❌ No hay feedback si te equivocas
- ❌ Continúa aunque no sigas

### Progreso Visual

```
Barra: ████████████████░░░░ 80%
Partitura: 🔴 ⚫⚫⚫⚫⚫⚫⚫⚫⚫ (nota actual en rojo)
Teclado: Una tecla amarilla a la vez
Status: "▶ Modo Práctica - Sigue el ritmo"
Color: 🟡 Amarillo (#ffaa00)
```

### Estrategia Recomendada

```
Día 1-3: Modo Alumno (4 acordes)
Día 4-7: Modo Alumno (8 acordes)
Día 8+:  Modo Práctica ← Aquí empiezas
```

---

## 🎼 Modo Maestro

### Descripción
Modo libre. La partitura se muestra pero **tú decides cuándo tocar**. Las teclas se iluminan cuando las presionas.

### Cómo Funciona

```
1. Muestra partitura completa (primeras 10 notas)
   ⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫
   C D E F G A B C D E

2. NO ilumina teclas automáticamente
   ⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫

3. TÚ tocas (click en teclado virtual o MIDI)
   Click C → [🟡C] (ilumina 300ms) → [⚫C]
   Click D → [🟡D] (ilumina 300ms) → [⚫D]

4. Sistema verifica si es correcto
   ✓ Correcto: Ilumina verde
   ✗ Incorrecto: Ilumina rojo

5. Continúa hasta que presiones DETENER
```

### Feedback Visual

```
Tú tocas: C
┌────────────────────────────┐
│ Sistema espera: C          │ ✓ Correcto
│ Tú tocaste: C              │ 🟢 Ilumina verde
└────────────────────────────┘

Tú tocas: E (pero debía ser D)
┌────────────────────────────┐
│ Sistema espera: D          │ ✗ Incorrecto
│ Tú tocaste: E              │ 🔴 Ilumina rojo
└────────────────────────────┘
```

### Ventajas
- ✅ Total libertad de velocidad
- ✅ Practicas a tu ritmo
- ✅ Ideal para piezas conocidas
- ✅ Perfecto para "tocar de oído"

### Uso con Teclado Virtual

```python
# En Windows (sin piano físico):
1. Abre modo Maestro
2. Ve la partitura en pantalla
3. Haz CLICK en las teclas del teclado virtual
4. Cada click ilumina y "toca" la nota
5. Practicas la secuencia visualmente
```

### Uso con Teclado MIDI

```python
# En Raspberry Pi (con piano MIDI conectado):
1. Abre modo Maestro
2. Conecta teclado MIDI vía USB
3. Ve la partitura en pantalla
4. Toca las teclas del piano real
5. Sistema detecta y valida tus notas
6. LEDs iluminan las teclas que presionas
```

---

## 🔄 Comparación Práctica

### Misma Canción (Twinkle Twinkle)

#### Modo Alumno:
```
[Muestra: C C G G]  ← Espera ~8s
[Tú tocas las 4]
[Muestra: A A G -]  ← Espera ~6s
[Tú tocas las 3]
...
Tiempo total: ~5 minutos
```

#### Modo Práctica:
```
[C:0.5s] [C:0.5s] [G:0.5s] [G:0.5s]
[A:0.5s] [A:0.5s] [G:1.0s]
[F:0.5s] [F:0.5s] [E:0.5s] [E:0.5s]
...
Tiempo total: ~30 segundos (tempo original)
```

#### Modo Maestro:
```
[Partitura visible toda]
Tú: *click C* *click C* *pausa* *click G* *click G*
    *pausa larga* *click A* *click A* *pausa* *click G*
...
Tiempo total: Indefinido (tu ritmo)
```

---

## 🎯 Flujo de Aprendizaje Recomendado

### Semana 1: Modo Alumno
```
Configuración: 2-3 acordes
Canciones: Twinkle Twinkle, Happy Birthday
Objetivo: Familiarizarte con el sistema
```

### Semana 2: Modo Alumno Avanzado
```
Configuración: 4-8 acordes
Canciones: Ode to Joy, Canon in D (simple)
Objetivo: Memorizar secuencias más largas
```

### Semana 3: Transición a Práctica
```
Mismas canciones en Modo Práctica
Objetivo: Seguir el tempo real
Permite ralentizar si es necesario
```

### Semana 4+: Modo Maestro
```
Tocar sin ayuda continua
Solo partitura como guía
Objetivo: Independencia total
```

---

## 🛠️ Personalización

### Ajustar Velocidad (Modo Práctica)

```python
# En gui_app.py, método _extract_notes_with_timing():

# Línea actual:
duration = msg.time * time_per_tick

# Para más lento (50%):
duration = (msg.time * time_per_tick) * 2.0

# Para más rápido (150%):
duration = (msg.time * time_per_tick) * 0.66
```

### Cambiar Colores por Modo

```python
# Modo Alumno: Verde
highlight_key(note, '#00ff88')

# Modo Práctica: Amarillo  
highlight_key(note, '#ffaa00')

# Modo Maestro: Magenta
highlight_key(note, '#ff00ff')

# Personaliza en cada método:
def start_student_mode():
    color = '#00ff88'  # Cambia aquí
```

### Agregar Sonido (Opcional)

```python
import pygame.mixer

def play_note_sound(note: int):
    """Reproduce sonido de la nota"""
    # Cargar samples de piano
    sound_file = f"sounds/piano_{note}.wav"
    if os.path.exists(sound_file):
        sound = pygame.mixer.Sound(sound_file)
        sound.play()

# Llamar en on_keyboard_click():
self.play_note_sound(clicked_note)
```

---

## 📊 Estadísticas de Práctica

### Información que Muestra el Sistema

```
Modo Alumno:
├── Total de notas: 42
├── Bloques completados: 11
├── Tiempo estimado: 5 min
└── Progreso: 100%

Modo Práctica:
├── Total de notas: 42
├── Duración real: 32 segundos
├── Progreso: 100%
└── Tempo: Original (120 BPM)

Modo Maestro:
├── Notas mostradas: 42
├── Modo: Libre
└── Status: Activo hasta que detengas
```

---

## 🐛 Solución de Problemas

### "Las notas no se iluminan"
→ Verifica que el archivo MIDI tiene notas
→ Revisa configuración de número de LEDs

### "Va muy rápido (Modo Práctica)"
→ Usa Modo Alumno primero
→ O ajusta multiplicador de velocidad

### "No detecta mi teclado MIDI"
→ Conecta antes de iniciar la app
→ Verifica drivers USB-MIDI

### "Partitura no se actualiza"
→ Refresca ventana (redimensionar)
→ Verifica que hay notas cargadas

---

## 💡 Tips Pro

1. **Combina modos**: Usa Alumno para aprender, Práctica para mejorar, Maestro para dominar
2. **Ajusta acordes**: Empieza con 2, sube a 4, luego 8
3. **Graba progreso**: Anota qué canciones completas en cada modo
4. **Practica diario**: 15 minutos al día > 2 horas una vez por semana
5. **Usa click**: El teclado virtual es perfecto para practicar SIN piano físico

---

**¡Ahora los 3 modos están completamente funcionales! 🎉**

Prueba cada uno y encuentra tu ritmo de aprendizaje.
