# Mejoras de Sistema LED - Arduino

## Resumen de Mejoras Implementadas

Se han implementado dos mejoras críticas para el sistema de LEDs:

### 1. 🔄 Inversión de Índice LED

**Problema**: Si el Arduino/tira LED está montado en el lado derecho del piano, los LEDs se encienden al revés (nota grave ilumina tecla aguda).

**Solución**: Nueva opción en Settings → LedTeacher → **"Reverse LED index (strip on right side)"**

#### Funcionamiento:
```python
# Fórmula de inversión:
if led_index_reverse:
    actual_midi_note = 129 - midi_note  # Invierte A0 (21) ↔ C8 (108)
```

| Nota Original | MIDI Note | LED Normal | LED Invertido |
|---------------|-----------|------------|---------------|
| A0 (grave) | 21 | LED 0 (izq) | LED 87 (der) |
| C4 (medio) | 60 | LED 39 (medio) | LED 48 (medio) |
| C8 (agudo) | 108 | LED 87 (der) | LED 0 (izq) |

#### Uso:
1. **Hardware en lado izquierdo**: `led_index_reverse = false` (default)
2. **Hardware en lado derecho**: `led_index_reverse = true`

Se aplica automáticamente en:
- ✅ `send_arduino_led_on()` - Al encender LED
- ✅ `send_arduino_led_off()` - Al apagar LED
- ✅ Todos los modos de entrenamiento

---

### 2. 🧹 Limpieza Automática de LEDs

**Problema**: LEDs se quedaban encendidos después de pausar/detener reproducción.

**Solución**: Sistema de limpieza automática multi-nivel

#### Sistema de Detección (Cada 100ms)

```python
def _cleanup_orphaned_keys(self):
    """Detecta LEDs huérfanos que no deberían estar encendidos"""
    current_active = set(piano_widget.active_notes.keys())
    orphaned_notes = current_active - expected_active_notes
    
    for note in orphaned_notes:
        piano_widget.note_off(note)
        send_arduino_led_off(note)  # 🆕 Apaga LED en Arduino
        midi_engine.synth.note_off(note)
```

#### Comando CLEAR al Arduino

```python
def _clear_all_active_notes(self):
    """Limpia todos los LEDs al pausar/detener"""
    # 🆕 Envía comando CLEAR al Arduino
    if arduino_connected:
        arduino_serial.write("CLEAR\n".encode('utf-8'))
        arduino_serial.flush()
    
    # Limpia widgets locales
    score_view.active_note_ids.clear()
    piano_widget.active_notes.clear()
    expected_active_notes.clear()
```

#### Ventajas:
✅ **Detección automática**: Timer de 100ms encuentra LEDs huérfanos
✅ **Limpieza garantizada**: Comando CLEAR al Arduino en pause/stop
✅ **Sin intervención manual**: Todo automático
✅ **Thread-safe**: Usa mutex para evitar race conditions

---

## Configuración en `settings.json`

```json
{
  "led_gradient_reverse": true,     // Invierte colores RGB (agudos oscuros)
  "led_index_reverse": false,       // 🆕 Invierte índice LED (hardware derecha)
  "ledteacher_enabled": true,
  "ledteacher_port": "COM19",
  "ledteacher_baud": 115200
}
```

---

## Archivos Modificados

### 1. `settings.json`
- Añadido: `"led_index_reverse": false`

### 2. `src/ui/settings_dialog.py`
- Añadido checkbox: `"Reverse LED index (strip on right side)"`
- Guardado en `get_settings()`

### 3. `src/ui/main_window.py`

**Cambios en `send_arduino_led_on()`:**
```python
# Inversión de índice LED
if self.settings.get("led_index_reverse", False):
    actual_midi_note = 129 - midi_note

# Usa actual_midi_note en comando
command = f"LED:{actual_midi_note},{r},{g},{b}\n"
```

**Cambios en `send_arduino_led_off()`:**
```python
# Inversión de índice LED
if self.settings.get("led_index_reverse", False):
    actual_midi_note = 129 - midi_note

command = f"OFF:{actual_midi_note}\n"
```

**Cambios en `_clear_all_active_notes()`:**
```python
# 🆕 Envía comando CLEAR al Arduino
if self.arduino_connected and self.arduino_serial:
    command = "CLEAR\n"
    self.arduino_serial.write(command.encode('utf-8'))
    self.arduino_serial.flush()
```

**Cambios en `_cleanup_orphaned_keys()`:**
```python
# 🆕 Apaga LED en Arduino también
for note in orphaned_notes:
    self.piano_widget.note_off(note)
    self.send_arduino_led_off(note)  # Nuevo
    # ... stop audio ...
```

### 4. `README.md`
- Documentación de inversión de índice LED
- Documentación de limpieza automática

---

## Testing

### Test 1: Inversión de Índice LED

1. **Hardware en lado izquierdo** (normal):
   ```
   Settings → LedTeacher → Uncheck "Reverse LED index"
   Reproducir → Nota grave (A0) ilumina LED izquierdo ✅
   ```

2. **Hardware en lado derecho** (invertido):
   ```
   Settings → LedTeacher → Check "Reverse LED index"
   Reproducir → Nota grave (A0) ilumina LED derecho ✅
   ```

### Test 2: Limpieza Automática

1. **Durante reproducción**:
   ```
   Reproducir canción → LEDs se encienden ✅
   Pausar → TODOS los LEDs se apagan inmediatamente ✅
   ```

2. **LEDs huérfanos**:
   ```
   Si un LED queda encendido por error
   → Timer de 100ms lo detecta y apaga automáticamente ✅
   ```

3. **Comando CLEAR**:
   ```
   Abrir Arduino Console
   Pausar reproducción
   → Ver "CLEAR" en log del console ✅
   ```

---

## Compatibilidad

✅ Arduino Uno/Nano/Mega
✅ WS2812B/WS2813 LED strips
✅ Protocolo de texto a 115200 baud
✅ Compatible con firmware Arduino existente
✅ No requiere actualización de Arduino sketch

---

## Beneficios para el Usuario

### Inversión de Índice LED:
- 🎹 **Flexibilidad de montaje**: Arduino puede estar en cualquier lado
- 🔧 **Sin cambios de hardware**: Solo configuración software
- ✨ **Mapeo correcto**: LEDs siempre iluminan la tecla correcta

### Limpieza Automática:
- 🧹 **Sin LEDs fantasma**: Nunca quedan LEDs encendidos por error
- ⚡ **Respuesta instantánea**: Al pausar, LEDs se apagan inmediatamente
- 🛡️ **Robusto**: Sistema de 3 niveles (orphan detection, CLEAR, manual)
- 🎯 **Profesional**: Comportamiento predecible y confiable

---

**Fecha**: 2025-11-26
**Versión**: 2.0
**Estado**: ✅ Implementado y Probado
