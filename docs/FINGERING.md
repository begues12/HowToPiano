# ✋ Sistema de Digitación - Guía Completa

## ¿Qué es la Digitación?

La **digitación** es la técnica de asignar cada nota musical a un dedo específico de la mano. En piano:
- **Mano Izquierda**: Dedos 5-4-3-2-1 (meñique → pulgar)
- **Mano Derecha**: Dedos 1-2-3-4-5 (pulgar → meñique)

### Numeración Estándar

```
        Mano Izquierda              Mano Derecha
        
    5  4  3  2  1              1  2  3  4  5
    │  │  │  │  │              │  │  │  │  │
    ▼  ▼  ▼  ▼  ▼              ▼  ▼  ▼  ▼  ▼
   ┌─┬─┬─┬─┬─┐              ┌─┬─┬─┬─┬─┐
   │▓│░│▓│░│▓│              │▓│░│▓│░│▓│
   └─┴─┴─┴─┴─┘              └─┴─┴─┴─┴─┘
   
   5 = Meñique                1 = Pulgar
   4 = Anular                 2 = Índice
   3 = Medio                  3 = Medio
   2 = Índice                 4 = Anular
   1 = Pulgar                 5 = Meñique
```

## 🎨 Implementación con Colores

### Paleta de Colores HowToPiano

```python
# Mano Izquierda (tonos cálidos)
FINGER_COLORS_LEFT = {
    1: '#FF0066',  # Pulgar    - Rosa fucsia
    2: '#FF6600',  # Índice    - Naranja
    3: '#FFCC00',  # Medio     - Amarillo dorado
    4: '#66FF00',  # Anular    - Verde lima
    5: '#00FF66'   # Meñique   - Verde esmeralda
}

# Mano Derecha (tonos fríos)
FINGER_COLORS_RIGHT = {
    1: '#00FFFF',  # Pulgar    - Cyan
    2: '#0099FF',  # Índice    - Azul cielo
    3: '#0033FF',  # Medio     - Azul marino
    4: '#6600FF',  # Anular    - Violeta
    5: '#FF00FF'   # Meñique   - Magenta
}
```

### Visualización

```
Mano Izquierda:
┌─────────┬─────────┬─────────┬─────────┬─────────┐
│ 5       │ 4       │ 3       │ 2       │ 1       │
│ 🟢      │ 🟡      │ 🟠      │ 🔴      │ 💖      │
│ Verde   │ Lima    │ Amarillo│ Naranja │ Rosa    │
│ Meñique │ Anular  │ Medio   │ Índice  │ Pulgar  │
└─────────┴─────────┴─────────┴─────────┴─────────┘

Mano Derecha:
┌─────────┬─────────┬─────────┬─────────┬─────────┐
│ 1       │ 2       │ 3       │ 4       │ 5       │
│ 💙      │ 🔵      │ 🌊      │ 💜      │ 💗      │
│ Cyan    │ Azul    │ Marino  │ Violeta │ Magenta │
│ Pulgar  │ Índice  │ Medio   │ Anular  │ Meñique │
└─────────┴─────────┴─────────┴─────────┴─────────┘
```

## 🧠 Algoritmos de Asignación

### 1. Reglas Básicas de Digitación

```python
def get_basic_fingering(note: int, hand: str = 'right') -> int:
    """
    Asigna dedo basado en posición de la nota
    
    Args:
        note: Número MIDI (21-108)
        hand: 'left' o 'right'
    
    Returns:
        Número de dedo (1-5)
    """
    # Convertir a posición en octava
    note_in_octave = note % 12
    
    # Patrones comunes
    white_keys = [0, 2, 4, 5, 7, 9, 11]  # C D E F G A B
    black_keys = [1, 3, 6, 8, 10]        # C# D# F# G# A#
    
    if hand == 'right':
        # Mano derecha (ascendente)
        if note_in_octave in [0, 5]:      # C, F
            return 1  # Pulgar en C y F
        elif note_in_octave in [2, 7]:    # D, G
            return 2  # Índice
        elif note_in_octave in [4, 9]:    # E, A
            return 3  # Medio
        elif note_in_octave in [11]:      # B
            return 4  # Anular
        elif note_in_octave in black_keys:
            return 2 if note_in_octave in [1, 6] else 3
    else:
        # Mano izquierda (descendente)
        if note_in_octave in [0, 5]:      # C, F
            return 1  # Pulgar en C y F
        elif note_in_octave in [2, 7]:    # D, G
            return 2  # Índice
        elif note_in_octave in [4, 9]:    # E, A
            return 3  # Medio
        elif note_in_octave in [11]:      # B
            return 4  # Anular
        elif note_in_octave in black_keys:
            return 2 if note_in_octave in [1, 6] else 3
    
    return 3  # Por defecto, medio
```

### 2. Digitación por Contexto (Avanzado)

```python
def get_contextual_fingering(notes: List[int], hand: str) -> List[int]:
    """
    Asigna dedos considerando secuencia completa
    Evita cambios innecesarios y optimiza para velocidad
    
    Args:
        notes: Secuencia de notas MIDI
        hand: 'left' o 'right'
    
    Returns:
        Lista de dedos para cada nota
    """
    fingering = []
    last_finger = None
    last_note = None
    
    for note in notes:
        # Calcular distancia con nota anterior
        if last_note is not None:
            interval = abs(note - last_note)
            
            # Si es paso (1-2 semitonos), mantener dedos adyacentes
            if interval <= 2 and last_finger:
                if hand == 'right':
                    finger = min(5, last_finger + 1)
                else:
                    finger = max(1, last_finger - 1)
            
            # Si es salto grande (>5 semitonos), resetear a posición base
            elif interval > 5:
                finger = get_basic_fingering(note, hand)
            
            # Intervalos medios (3-5 semitonos)
            else:
                finger = get_basic_fingering(note, hand)
        else:
            # Primera nota
            finger = get_basic_fingering(note, hand)
        
        fingering.append(finger)
        last_finger = finger
        last_note = note
    
    return fingering
```

### 3. Detección de Mano por Rango

```python
def detect_hand(note: int) -> str:
    """
    Detecta qué mano debería tocar una nota
    
    Args:
        note: Número MIDI (21-108)
    
    Returns:
        'left' o 'right'
    """
    # Do central (Middle C) = MIDI 60
    MIDDLE_C = 60
    
    if note < MIDDLE_C:
        return 'left'   # Notas graves
    elif note > MIDDLE_C:
        return 'right'  # Notas agudas
    else:
        return 'both'   # Do central - ambas manos
```

### 4. Digitación de Escalas

```python
def get_scale_fingering(scale_notes: List[int], hand: str) -> List[int]:
    """
    Digitación optimizada para escalas
    
    Patrones estándar:
    - Escala Do Mayor (mano derecha): 1-2-3-1-2-3-4-5
    - Escala Do Mayor (mano izquierda): 5-4-3-2-1-3-2-1
    """
    if hand == 'right':
        # Patrón derecha: 1-2-3, cruce con 1, continúa
        pattern = [1, 2, 3, 1, 2, 3, 4, 5]
    else:
        # Patrón izquierda: 5-4-3-2-1, cruce con 3
        pattern = [5, 4, 3, 2, 1, 3, 2, 1]
    
    # Repetir patrón si escala es más larga
    fingering = []
    for i in range(len(scale_notes)):
        fingering.append(pattern[i % len(pattern)])
    
    return fingering
```

### 5. Digitación de Acordes

```python
def get_chord_fingering(chord_notes: List[int], hand: str) -> List[int]:
    """
    Asigna dedos para acordes (notas simultáneas)
    
    Reglas:
    - Tríadas (3 notas): 1-3-5 o 5-3-1
    - Séptimas (4 notas): 1-2-3-5 o 5-3-2-1
    - Evitar usar mismo dedo en teclas adyacentes
    """
    num_notes = len(chord_notes)
    
    if hand == 'right':
        if num_notes == 2:
            return [1, 3]  # Pulgar y medio
        elif num_notes == 3:
            return [1, 3, 5]  # Pulgar, medio, meñique
        elif num_notes == 4:
            return [1, 2, 3, 5]  # Todos excepto anular
        else:
            return [1, 2, 3, 4, 5]  # Todos los dedos
    else:
        if num_notes == 2:
            return [5, 3]  # Meñique y medio
        elif num_notes == 3:
            return [5, 3, 1]  # Meñique, medio, pulgar
        elif num_notes == 4:
            return [5, 4, 2, 1]  # Todos excepto medio
        else:
            return [5, 4, 3, 2, 1]  # Todos los dedos
```

## 🔧 Integración en HowToPiano

### Módulo de Digitación

```python
# src/fingering.py

class FingeringEngine:
    """Motor de asignación de digitación"""
    
    def __init__(self, mode: str = 'basic'):
        """
        Args:
            mode: 'basic', 'contextual', 'scale', 'chord'
        """
        self.mode = mode
        
        # Colores por dedo
        self.colors_left = {
            1: '#FF0066', 2: '#FF6600', 3: '#FFCC00',
            4: '#66FF00', 5: '#00FF66'
        }
        self.colors_right = {
            1: '#00FFFF', 2: '#0099FF', 3: '#0033FF',
            4: '#6600FF', 5: '#FF00FF'
        }
    
    def assign_fingering(self, notes: List[int]) -> List[tuple]:
        """
        Asigna digitación a secuencia de notas
        
        Returns:
            Lista de tuplas (note, hand, finger, color)
        """
        result = []
        
        for note in notes:
            hand = self.detect_hand(note)
            
            if self.mode == 'basic':
                finger = self.get_basic_fingering(note, hand)
            elif self.mode == 'contextual':
                # Implementar contexto
                finger = self.get_contextual_fingering([note], hand)[0]
            
            # Obtener color
            if hand == 'left':
                color = self.colors_left[finger]
            else:
                color = self.colors_right[finger]
            
            result.append((note, hand, finger, color))
        
        return result
    
    def get_color_for_finger(self, finger: int, hand: str) -> str:
        """Retorna color para dedo específico"""
        if hand == 'left':
            return self.colors_left.get(finger, '#FFFFFF')
        else:
            return self.colors_right.get(finger, '#FFFFFF')
```

### Uso en GUI

```python
# En gui_app.py

from src.fingering import FingeringEngine

class HowToPianoGUI:
    
    def __init__(self):
        # ... código existente ...
        
        # Inicializar motor de digitación
        self.fingering_engine = FingeringEngine(mode='basic')
        self.show_fingering = False  # Configurable
    
    def highlight_key_with_finger(self, note: int, hand: str, finger: int):
        """Ilumina tecla con color de dedo"""
        
        # Obtener color según dedo
        color = self.fingering_engine.get_color_for_finger(finger, hand)
        
        # Iluminar LED físico
        if self.led_controller:
            self.led_controller.set_note(note, color)
        
        # Iluminar teclado virtual
        self.highlight_key(note, color)
        
        # Mostrar etiqueta de dedo (opcional)
        if self.show_fingering:
            self.display_finger_label(note, finger, hand)
    
    def display_finger_label(self, note: int, finger: int, hand: str):
        """Muestra número de dedo sobre la tecla"""
        
        # Calcular posición en canvas
        key_x, key_y = self.get_key_position(note)
        
        # Crear texto
        label = f"{finger}"
        if hand == 'left':
            label += "L"
        else:
            label += "R"
        
        # Dibujar en canvas
        self.keyboard_canvas.create_text(
            key_x + 10, key_y + 10,
            text=label,
            font=('Arial', 12, 'bold'),
            fill='white',
            tags=f'finger_label_{note}'
        )
```

### Configuración de Usuario

```python
# En ventana de configuración

def create_fingering_settings(self, parent):
    """Crea panel de configuración de digitación"""
    
    frame = tk.LabelFrame(parent, text="✋ Digitación")
    frame.pack(fill=tk.X, pady=10)
    
    # Activar/desactivar
    self.fingering_enabled = tk.BooleanVar(value=False)
    tk.Checkbutton(
        frame,
        text="Mostrar sugerencias de dedos",
        variable=self.fingering_enabled,
        command=self.toggle_fingering
    ).pack()
    
    # Modo de digitación
    tk.Label(frame, text="Modo:").pack()
    
    self.fingering_mode = tk.StringVar(value='basic')
    modes = [
        ('Básico (por posición)', 'basic'),
        ('Contextual (secuencia)', 'contextual'),
        ('Escalas optimizadas', 'scale')
    ]
    
    for text, value in modes:
        tk.Radiobutton(
            frame,
            text=text,
            variable=self.fingering_mode,
            value=value
        ).pack()
    
    # Vista previa de colores
    preview_frame = tk.Frame(frame)
    preview_frame.pack(pady=10)
    
    tk.Label(preview_frame, text="Colores:").pack()
    
    # Mano izquierda
    for finger in range(1, 6):
        color = self.fingering_engine.colors_left[finger]
        tk.Label(
            preview_frame,
            text=f"L{finger}",
            bg=color,
            width=3,
            relief=tk.RAISED
        ).pack(side=tk.LEFT, padx=2)
    
    # Mano derecha
    for finger in range(1, 6):
        color = self.fingering_engine.colors_right[finger]
        tk.Label(
            preview_frame,
            text=f"R{finger}",
            bg=color,
            width=3,
            relief=tk.RAISED
        ).pack(side=tk.LEFT, padx=2)
```

## 📊 Ejemplo Visual Completo

### Escala Do Mayor (C Major)

```
Mano Derecha:
┌────────────────────────────────────────────────────┐
│ C    D    E    F    G    A    B    C'              │
│ 💖   🔵   🌊   💖   🔵   🌊   💜   💗             │
│ 1    2    3    1    2    3    4    5               │
└────────────────────────────────────────────────────┘

Mano Izquierda:
┌────────────────────────────────────────────────────┐
│ C    B    A    G    F    E    D    C'              │
│ 💖   🔴   🟠   🟡   💖   🟠   🟡   🟢             │
│ 1    2    3    4    1    3    4    5               │
└────────────────────────────────────────────────────┘
```

### Acorde Do Mayor (C-E-G)

```
Mano Derecha:
┌─────────────────┐
│  C    E    G    │
│  💖   🌊   💗   │
│  1    3    5    │
└─────────────────┘

Mano Izquierda:
┌─────────────────┐
│  G    E    C    │
│  🟢   🟠   💖   │
│  5    3    1    │
└─────────────────┘
```

## 🎯 Casos de Uso

### Caso 1: Principiante Absoluto
```python
config = {
    'fingering_enabled': True,
    'mode': 'basic',
    'show_labels': True,     # Mostrar números
    'color_intensity': 1.0   # Colores brillantes
}
```

### Caso 2: Estudiante Intermedio
```python
config = {
    'fingering_enabled': True,
    'mode': 'contextual',    # Considera secuencias
    'show_labels': False,    # Solo colores
    'color_intensity': 0.7
}
```

### Caso 3: Avanzado
```python
config = {
    'fingering_enabled': False,  # No necesita ayuda
    'mode': 'contextual',
    'show_labels': False
}
```

## 🔬 Algoritmos Avanzados (Futuro)

### Machine Learning para Digitación Personalizada

```python
class MLFingeringEngine:
    """
    Aprende tu estilo de digitación
    Ajusta sugerencias basándose en:
    - Tamaño de tu mano
    - Piezas que tocas frecuentemente
    - Errores comunes
    """
    
    def train_from_history(self, midi_input_history):
        """Entrena modelo con tu historial"""
        pass
    
    def predict_optimal_fingering(self, notes):
        """Predice mejor digitación para ti"""
        pass
```

### Detección de Anatomía de Mano

```python
def calibrate_hand_size():
    """
    Pide al usuario tocar:
    - Do con pulgar
    - Sol con meñique
    
    Calcula: extensión máxima cómoda
    Ajusta: digitación personalizada
    """
    pass
```

## 📚 Referencias

- [Piano Pedagogy](https://pianopedagogy.org/) - Técnicas de enseñanza
- [ABRSM Syllabus](https://www.abrsm.org/) - Escalas y digitación estándar
- [Hanon Exercises](https://imslp.org/) - Ejercicios clásicos
- [Music Theory](https://www.musictheory.net/) - Teoría musical

## 💡 Tips de Implementación

1. **Empieza simple**: Usa digitación básica primero
2. **Hazlo opcional**: No todos los usuarios la necesitan
3. **Feedback visual claro**: Colores + números
4. **Calibración**: Permite ajustar según nivel del usuario
5. **Aprende del usuario**: Guarda preferencias de digitación

## 🐛 Consideraciones

- **No hay digitación "perfecta"**: Varía según pieza, tempo, intérprete
- **Flexibilidad**: Permite al usuario cambiar sugerencias
- **Contexto importa**: Una nota puede usar dedos diferentes según vecinas
- **Comodidad primero**: Si una digitación es incómoda, cámbiala

## 🚀 Próximos Pasos

1. Implementar `src/fingering.py` con clase base
2. Integrar en `gui_app.py` con visualización
3. Añadir configuración en ventana de settings
4. Crear archivo de tests para validar algoritmos
5. Documentar patrones específicos por tipo de pieza

---

**¿Preguntas?** La digitación es más arte que ciencia - experimenta y encuentra lo que funciona para cada usuario.
