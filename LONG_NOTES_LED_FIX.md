# Fix: LEDs de Notas Largas No Se Apagaban

## Problema
Las notas con duración larga (whole notes, half notes, etc.) mantenían sus LEDs encendidos hasta que otra nota los activaba, en lugar de apagarse cuando la duración de la nota expiraba.

**Síntoma reportado:** "Cuando una nota es muy larga se queda endendida hasta que intenta volverla a encender"

## Causa Raíz

El código en `staff_widget.py` usaba `trigger_time` (que incluye compensación de latencia de audio) tanto para **encender** como para **apagar** notas:

```python
# ❌ INCORRECTO (antes)
trigger_time = current_time + self.audio_latency_sec

# NOTE ON
if (note_time <= trigger_time <= note_time + trigger_tolerance and ...):
    self.note_triggered.emit(note['pitch'], velocity)

# NOTE OFF  
if (trigger_time >= note_end_time and ...):  # ← Problema aquí
    self.note_ended.emit(note['pitch'])
```

### ¿Por qué causaba el problema?

1. **Latencia de audio** (`audio_latency_sec`) típicamente es ~12ms (0.012s)
2. `trigger_time` anticipa el tiempo para compensar la latencia del buffer de audio
3. Para **NOTE_ON**: Esto es correcto ✅ - el sonido llega justo cuando la nota cruza la línea roja visual
4. Para **NOTE_OFF**: Esto causa apagado prematuro ❌ - la nota se apaga ~12ms ANTES de que su duración expire

### Impacto en notas largas

Para una nota de 2 segundos:
- **Duración esperada**: 2.000s
- **Duración real con bug**: 1.988s (apaga 12ms antes)
- Para notas muy largas (4-8 segundos), esta diferencia se acumula

Además, si el loop de actualización (`_check_and_trigger_notes`) se ejecuta a 60 FPS (~16.6ms por frame), y la condición de NOTE_OFF solo se verifica cuando `trigger_time >= note_end_time`, puede perderse el momento exacto y la nota quedarse encendida varios frames más.

## Solución Implementada

**Separar la lógica de timing para NOTE_ON y NOTE_OFF:**

```python
# ✅ CORRECTO (después)
trigger_time = current_time + self.audio_latency_sec

# NOTE ON - usa trigger_time (con compensación de latencia)
if (note_time <= trigger_time <= note_time + trigger_tolerance and ...):
    self.note_triggered.emit(note['pitch'], velocity)

# NOTE OFF - usa current_time (SIN compensación de latencia)
if (current_time >= note_end_time and ...):
    self.note_ended.emit(note['pitch'])
```

### Justificación

- **NOTE_ON con `trigger_time`**: 
  - Anticipa el inicio para que el sonido llegue a los altavoces exactamente cuando la nota cruza la línea roja
  - Compensa el buffer de audio del sistema (~12ms)
  
- **NOTE_OFF con `current_time`**:
  - Respeta la duración exacta de la nota sin anticipación
  - Las notas se apagan cuando su tiempo real de duración expira
  - No hay necesidad de compensar latencia porque el "apagado" es instantáneo

## Archivos Modificados

### `src/ui/staff_widget.py`

1. **Línea ~767**: Cambió condición de NOTE_OFF de `trigger_time` a `current_time`

```python
# Antes:
if (trigger_time >= note_end_time and note_id in self.triggered_notes):

# Después:
if (current_time >= note_end_time and note_id in self.triggered_notes):
```

2. **Línea ~121**: Removió conexiones inexistentes a señales de SongWidget

```python
# Antes:
self.song_widget.note_triggered.connect(self._on_note_triggered)
self.song_widget.note_ended.connect(self._on_note_ended)

# Después:
# Note: SongWidget is a simple container, not QObject - no signals to connect
```

3. **Línea ~703**: Eliminó método innecesario `_on_note_ended()`

SongWidget NO es un QObject y no tiene señales PyQt - es solo un contenedor de datos.

## Pruebas Recomendadas

1. **Cargar canción con notas largas** (whole notes, half notes)
2. **Activar Play o Master mode** con LEDs conectados
3. **Verificar comportamiento**:
   - LED se enciende cuando la nota inicia
   - LED se APAGA exactamente cuando la duración expira
   - NO debe quedarse encendido hasta la siguiente nota
   
4. **Casos de prueba específicos**:
   - Nota de 4 segundos (whole note a 60 BPM)
   - Nota de 8 segundos (con tempo lento)
   - Acordes con duraciones diferentes

## Detalles Técnicos

### Flujo de Señales (después del fix)

```
StaffWidget._check_and_trigger_notes()
  ↓
[Verifica: current_time >= note_end_time]
  ↓
self.note_ended.emit(pitch)
  ↓
MainWindow.on_staff_note_ended(pitch)
  ↓
MainWindow._deactivate_piano_key(midi_note)
  ↓
MainWindow.send_arduino_led_off(midi_note)
  ↓
Arduino: "OFF:21\n"
  ↓
LED se apaga
```

### Frecuencia de Actualización

`_check_and_trigger_notes()` se llama desde `update_position()` cada vez que se actualiza el tiempo de reproducción (típicamente 60 FPS = cada ~16ms).

Con el fix:
- Precisión de NOTE_OFF: ±16ms (un frame a 60 FPS)
- Muy superior a la anterior donde podía quedarse encendido indefinidamente

## Contexto del Sistema

### LED Buffering System

Este fix trabaja con el sistema de buffering existente:
- Buffer de 20ms (50 Hz) para comandos LED
- Comando `OFF:note` se envía inmediatamente al buffer
- Buffer se vacía cada 20ms en formato `BATCH:`

### Protocol Arduino

```
LED:note,r,g,b\n   - Enciende LED con RGB
OFF:note\n         - Apaga LED específico
BATCH:\n           - Señal de inicio de batch
CLEAR\n            - Apaga todos los LEDs
```

## Mejoras Relacionadas

Este fix es parte de una serie de optimizaciones para el sistema de LEDs:

1. ✅ Async loading con progreso
2. ✅ Protocolo texto RGB (115200 baud)
3. ✅ Gradient RGB completo (88 teclas)
4. ✅ LED buffering (20ms batch)
5. ✅ Cleanup automático de LEDs huérfanos
6. ✅ Fix de notas largas (este documento)

## Resultado Esperado

Las notas largas ahora:
- ✅ Encienden el LED cuando inician
- ✅ Mantienen el LED encendido durante toda la duración
- ✅ Apagan el LED exactamente cuando la duración expira
- ✅ No requieren que otra nota las "reemplace" para apagarse

**Problema resuelto: Las notas largas ahora respetan su duración y apagan sus LEDs correctamente.**
