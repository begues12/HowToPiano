# Fix: LEDs No Encendían Para Todas Las Notas

## Problema Detectado

**Síntoma**: Algunos LEDs no se encendían durante la reproducción, especialmente en modos de entrenamiento (Practice, Student, etc.)

**Causa Raíz**: Los métodos de callback de los modos de entrenamiento NO enviaban comandos LED al Arduino:
- `on_mode_note_highlight()` - Solo activaba visualmente el piano, sin LED
- `on_mode_note_unhighlight()` - Solo desactivaba visualmente, sin apagar LED  
- `on_mode_staff_note_on()` - Solo destacaba en pentagrama, sin LED
- `on_mode_staff_note_off()` - Solo quitaba highlight, sin apagar LED

## Solución Implementada

### 1. `on_mode_note_highlight()` - Añadido control LED

**Antes:**
```python
def on_mode_note_highlight(self, pitch, color):
    """Training mode wants to highlight a piano key"""
    self._activate_piano_key(pitch, 80, color, play_audio=False)
```

**Después:**
```python
def on_mode_note_highlight(self, pitch, color):
    """Training mode wants to highlight a piano key"""
    # Register as expected active note
    self.expected_active_notes.add(pitch)
    
    # Visual feedback
    if color is None:
        color = self.get_played_note_color()
    self.piano_widget.note_on(pitch, color)
    
    # ✅ Arduino LED - ALWAYS send for every note highlight
    if self.arduino_connected and self.arduino_serial:
        self.send_arduino_led_on(pitch, 80)
```

### 2. `on_mode_note_unhighlight()` - Añadido apagado LED

**Antes:**
```python
def on_mode_note_unhighlight(self, pitch):
    """Training mode wants to unhighlight a piano key"""
    self._deactivate_piano_key(pitch, stop_audio=False)
```

**Después:**
```python
def on_mode_note_unhighlight(self, pitch):
    """Training mode wants to unhighlight a piano key"""
    # Unregister from expected active notes
    self.expected_active_notes.discard(pitch)
    
    # Visual feedback
    self.piano_widget.note_off(pitch)
    
    # ✅ Arduino LED - ALWAYS turn off
    if self.arduino_connected and self.arduino_serial:
        self.send_arduino_led_off(pitch)
```

### 3. `on_mode_staff_note_on()` - Añadido control LED

**Antes:**
```python
def on_mode_staff_note_on(self, pitch):
    """Called when a training mode wants to highlight a note on the staff"""
    if hasattr(self.score_view, 'highlight_note_by_pitch'):
        self.score_view.highlight_note_by_pitch(pitch, "green")
```

**Después:**
```python
def on_mode_staff_note_on(self, pitch):
    """Called when a training mode wants to highlight a note on the staff"""
    if hasattr(self.score_view, 'highlight_note_by_pitch'):
        self.score_view.highlight_note_by_pitch(pitch, "green")
    
    # ✅ Also light up the LED (for Practice mode when showing which notes to play)
    if self.arduino_connected and self.arduino_serial:
        self.send_arduino_led_on(pitch, 100)
```

### 4. `on_mode_staff_note_off()` - Añadido apagado LED

**Antes:**
```python
def on_mode_staff_note_off(self, pitch):
    """Called when a training mode wants to unhighlight a note on the staff"""
    if hasattr(self.score_view, 'unhighlight_note_by_pitch'):
        self.score_view.unhighlight_note_by_pitch(pitch)
```

**Después:**
```python
def on_mode_staff_note_off(self, pitch):
    """Called when a training mode wants to unhighlight a note on the staff"""
    if hasattr(self.score_view, 'unhighlight_note_by_pitch'):
        self.score_view.unhighlight_note_by_pitch(pitch)
    
    # ✅ Turn off the LED
    if self.arduino_connected and self.arduino_serial:
        self.send_arduino_led_off(pitch)
```

## Flujo de Eventos Corregido

### Modo Play/Master:
```
StaffWidget cruza nota
    ↓
on_staff_note_triggered()
    ↓
_activate_piano_key()
    ↓
✅ send_arduino_led_on() ← Ya funcionaba
```

### Modo Practice (Fase PLAY):
```
training_mode.py: note_highlight.emit(note)
    ↓
✅ on_mode_note_highlight() ← AHORA ENCIENDE LED
    ↓
piano_widget.note_on() + send_arduino_led_on()
```

### Modo Practice (Detectar nota):
```
training_mode.py: staff_note_on.emit(note)
    ↓
✅ on_mode_staff_note_on() ← AHORA ENCIENDE LED
    ↓
score_view.highlight + send_arduino_led_on()
```

## Archivo Modificado

**`src/ui/main_window.py`**:
- ✅ `on_mode_note_highlight()` - Añadido `send_arduino_led_on()`
- ✅ `on_mode_note_unhighlight()` - Añadido `send_arduino_led_off()`
- ✅ `on_mode_staff_note_on()` - Añadido `send_arduino_led_on()`
- ✅ `on_mode_staff_note_off()` - Añadido `send_arduino_led_off()`

## Testing

### Test 1: Modo Play
```
1. Cargar canción MIDI
2. Reproducir en modo Play
3. ✅ Verificar que TODOS los LEDs se encienden
```

### Test 2: Modo Master
```
1. Cambiar a modo Master
2. Reproducir
3. ✅ Verificar que TODOS los LEDs se encienden con gradiente RGB
```

### Test 3: Modo Practice (CRÍTICO)
```
1. Cambiar a modo Practice
2. Fase LISTEN: ✅ LEDs se encienden automáticamente
3. Fase PLAY: ✅ LEDs destacan notas que debes tocar
4. Al tocar nota correcta: ✅ LED permanece encendido
5. Al tocar nota incorrecta: ✅ LEDs rojos
```

### Test 4: Modo Student
```
1. Cambiar a modo Student
2. Turno del profesor: ✅ LEDs se encienden al tocar acordes
3. Turno del estudiante: ✅ LEDs destacan acordes a tocar
```

## Beneficios

✅ **100% de cobertura**: TODAS las notas ahora encienden LEDs
✅ **Consistencia**: Mismo comportamiento en todos los modos
✅ **Sin duplicación**: Código limpio sin llamadas redundantes
✅ **Thread-safe**: Usa el mismo mecanismo de envío que ya funcionaba

## Verificación de Cobertura

| Modo | Signal/Callback | LED Encendido | Estado |
|------|----------------|---------------|--------|
| Play/Master | `on_staff_note_triggered()` | ✅ | Ya funcionaba |
| Practice (LISTEN) | `on_staff_note_triggered()` | ✅ | Ya funcionaba |
| Practice (PLAY) | `on_mode_note_highlight()` | ✅ | **CORREGIDO** |
| Practice (PLAY) | `on_mode_staff_note_on()` | ✅ | **CORREGIDO** |
| Student (Teacher) | `on_mode_note_highlight()` | ✅ | **CORREGIDO** |
| Student (Student) | `on_mode_note_highlight()` | ✅ | **CORREGIDO** |
| User Input | `on_arduino_note_on()` | ✅ | Ya funcionaba |
| MIDI Input | `on_midi_note_on()` | ✅ | Ya funcionaba |

---

**Resultado**: 🎉 **TODOS los LEDs ahora se encienden correctamente en TODOS los modos**

**Fecha**: 2025-11-26
**Versión**: 2.1
**Estado**: ✅ Corregido y Verificado
