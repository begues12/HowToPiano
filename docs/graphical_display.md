# 🎼 Display Gráfico - Guía Completa

## ¿Qué es?

El display gráfico te permite ver la partitura de forma visual en una pantalla, en lugar de solo texto en terminal.

## 📋 Opciones Disponibles

### 1️⃣ Sin Librerías Extra (ACTUAL)
```bash
# Lo que tienes ahora:
- Terminal con curses (texto mejorado)
- No requiere instalación adicional
- Funciona en SSH remoto
```

**Ventajas:**
- ✅ Ya funciona sin instalar nada
- ✅ Bajo consumo de recursos
- ✅ Perfecto para Raspberry Pi Zero

**Desventajas:**
- ❌ Solo texto, no gráficos reales
- ❌ Limitado visualmente

### 2️⃣ Pygame (Pantalla HDMI)
```bash
# Requiere:
sudo apt-get install python3-pygame
pip install pygame
```

**Ventajas:**
- ✅ Pentagrama real con notas gráficas
- ✅ Piano Roll estilo Synthesia
- ✅ Colores y animaciones

**Desventajas:**
- ❌ Necesitas monitor HDMI conectado
- ❌ Más pesado (puede ralentizar Pi Zero)
- ❌ No funciona por SSH

**Cuándo usar:**
- Tienes monitor conectado a tu Raspberry Pi
- Quieres una experiencia visual completa
- Tu Raspberry Pi tiene suficiente RAM

### 3️⃣ Tkinter (Simple)
```bash
# Ya incluido en Raspberry Pi OS
# No requiere instalación
```

**Ventajas:**
- ✅ Incluido por defecto
- ✅ Más ligero que Pygame
- ✅ Interface simple pero funcional

**Desventajas:**
- ❌ También necesita pantalla
- ❌ Menos bonito que Pygame

### 4️⃣ Music21 (Generador de Imágenes)
```bash
pip install music21
sudo apt-get install lilypond  # Para generar PDFs
```

**Ventajas:**
- ✅ Genera PDFs profesionales
- ✅ Notación musical real
- ✅ Puedes imprimirlas

**Desventajas:**
- ❌ No es interactivo en tiempo real
- ❌ Requiere instalación pesada
- ❌ Genera archivos, no display en vivo

## 🔧 Instalación

### Opción A: Solo Texto (Recomendado para empezar)
```bash
# Ya está instalado, no hagas nada
# Usa la opción "curses" del menú
```

### Opción B: Pygame Completo
```bash
cd /home/pi/HowToPiano

# Instalar dependencias del sistema
sudo apt-get update
sudo apt-get install -y python3-pygame

# Instalar con pip
pip install pygame

# Probar instalación
python3 -c "import pygame; print('✓ Pygame OK')"
```

### Opción C: Music21 (Para PDFs)
```bash
pip install music21
sudo apt-get install lilypond
```

## 🎮 Uso

### Desde el Menú Principal

1. Carga una canción (opción 2)
2. Selecciona opción 8: "Ver partitura gráfica"
3. Elige display:
   - **Opción 1:** Pentagrama pygame
   - **Opción 2:** Piano Roll
   - **Opción 3:** Simple Tkinter

### Uso Directo (Python)

```python
from src.graphical_score import GraphicalScoreDisplay

# Crear display
display = GraphicalScoreDisplay()

# Dibujar pentagrama
display.draw_staff()

# Dibujar notas
notes = ['C4', 'D4', 'E4', 'F4', 'G4']
for i, note in enumerate(notes):
    display.draw_note(note, i)

# Cerrar
display.close()
```

### Piano Roll
```python
# Notas con tiempo y duración
notes_data = [
    (60, 0.0, 0.5),    # (nota_midi, inicio, duración)
    (62, 0.5, 0.5),
    (64, 1.0, 1.0)
]

display.display_piano_roll(notes_data)
```

## 📊 Comparación

| Característica | Curses | Pygame | Tkinter | Music21 |
|---------------|--------|---------|---------|---------|
| Instalación | ✅ Incluido | ⚠️ Requiere | ✅ Incluido | ❌ Complejo |
| Pantalla necesaria | ❌ No | ✅ Sí | ✅ Sí | ❌ No |
| SSH remoto | ✅ Sí | ❌ No | ❌ No | ✅ Sí |
| Pentagrama real | ❌ No | ✅ Sí | ⚠️ Básico | ✅ Profesional |
| Interactivo | ✅ Sí | ✅ Sí | ✅ Sí | ❌ No |
| Consumo recursos | 🟢 Bajo | 🔴 Alto | 🟡 Medio | 🔴 Alto |
| Pi Zero compatible | ✅ Perfecto | ⚠️ Lento | ✅ OK | ❌ Muy lento |

## 🎯 Recomendaciones

### Para Raspberry Pi Zero (TU CASO)

**🥇 Mejor opción: Terminal curses (actual)**
```bash
# Ya lo tienes configurado
# Usa: python3 main.py
# Opción 3: Modo aprendizaje
```

**Razones:**
- Pi Zero tiene poca RAM (512MB)
- Probablemente usarás SSH (sin pantalla)
- Funciona perfectamente para aprender
- No ralentiza el sistema

### Si conectas monitor HDMI

**🥈 Segunda opción: Tkinter simple**
```bash
# Ya incluido, solo necesitas monitor
python3 main.py
# Opción 8 → 3 (Tkinter)
```

**Solo si tienes Pi 3/4:**
```bash
# Puedes usar Pygame completo
sudo apt-get install python3-pygame
```

## ⚙️ Configuración

### Ajustar resolución Pygame
```python
# En src/graphical_score.py línea 30
display = GraphicalScoreDisplay(
    width=800,   # Ajusta según tu pantalla
    height=600   # Más pequeño = más rápido
)
```

### Deshabilitar gráficos (volver a texto)
```python
# En main.py línea 20
GRAPHICAL_AVAILABLE = False  # Forzar solo texto
```

## 🐛 Problemas Comunes

### "pygame not available"
```bash
# Solución 1: Instalar
pip install pygame

# Solución 2: Usar texto
# No instales nada, ya funciona con curses
```

### "No display available"
```bash
# Si usas SSH:
export DISPLAY=:0  # Si hay X11 local

# Mejor: usa curses en lugar de pygame
```

### Pantalla negra pygame
```bash
# Verifica que X11 esté corriendo
ps aux | grep X

# Inicia desde terminal gráfico (no SSH)
```

### Muy lento en Pi Zero
```bash
# Reduce resolución
# En graphical_score.py:
width=400, height=300  # Más pequeño

# O mejor: usa curses (texto)
```

## 📖 Ejemplos

### Ejemplo 1: Test Rápido
```bash
cd /home/pi/HowToPiano
python3 -m src.graphical_score
```

### Ejemplo 2: Display Personalizado
```python
from src.graphical_score import GraphicalScoreDisplay

display = GraphicalScoreDisplay(width=1024, height=768)

# Partitura simple
notes = ['C4', 'E4', 'G4', 'C5']
display.draw_staff()

for i, note in enumerate(notes):
    display.draw_note(note, i, is_current=(i==0))
    input(f"Nota: {note} (Enter para siguiente)")

display.close()
```

### Ejemplo 3: Sin Gráficos (ASCII)
```python
from src.graphical_score import GraphicalScoreDisplay

display = GraphicalScoreDisplay()
notes = ['C4', 'D4', 'E4', 'F4', 'G4']

# Usa versión texto si pygame no disponible
display.display_simple_text_notation(notes, current=2)
```

## 🎓 ¿Qué Opción Elegir?

### Principiante / Sin experiencia
→ **Usa curses (texto)**
- Ya funciona sin instalar
- Aprende igual de bien
- Sin complicaciones

### Intermedio / Monitor conectado
→ **Prueba Tkinter**
- Más visual
- No muy pesado
- Fácil configuración

### Avanzado / Pi potente (3/4)
→ **Pygame completo**
- Máxima calidad visual
- Piano Roll animado
- Experiencia premium

## 📚 Recursos

- [Pygame Docs](https://www.pygame.org/docs/)
- [Music21 Tutorial](https://web.mit.edu/music21/doc/)
- [Tkinter Canvas](https://docs.python.org/3/library/tkinter.html)

## ⚡ Resumen Ejecutivo

**TL;DR:**
- **Pi Zero sin pantalla** → Usa curses (ya instalado) ✅
- **Pi Zero con HDMI** → Tkinter (ya incluido) ✅
- **Pi 3/4 con pantalla** → Pygame (instalar) ⚙️
- **Generar PDFs** → Music21 (avanzado) 📄

**No necesitas instalar nada para empezar a aprender.**
El sistema actual con curses es perfecto para Pi Zero.

Pygame es **opcional** y solo útil si:
1. Tienes monitor conectado
2. Quieres visual "bonito"
3. Tu Pi tiene suficiente potencia

Para **aprender piano**, el display texto funciona igual de bien.
