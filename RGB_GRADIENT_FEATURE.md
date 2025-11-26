# RGB Gradient Feature - Play & Master Modes

## Overview
Sistema de gradiente RGB completo que se aplica automáticamente a los LEDs en modos **Play** y **Master**, creando una visualización espectacular del teclado completo.

## Comportamiento por Modo

### Modos Play y Master 🌈
- **Gradiente RGB completo** de 88 teclas
- Graves (A0) → Oscuro (azul/púrpura)
- Centro → Verde/amarillo
- Agudos (C8) → Brillante (naranja/rojo)
- Sensibilidad de velocidad: El brillo se ajusta según velocity (0-127)

### Otros Modos (Practice, Student, Corrector) 💚
- **Color verde tradicional** para claridad de aprendizaje
- Brightness basado en velocity
- Sin gradiente (enfocado en corrección, no en espectáculo)

## Cálculo del Gradiente

```python
# Posición en el teclado: 0.0 (graves) a 1.0 (agudos)
position = (midi_note - 21) / 87.0  # 88 teclas (21-108)

# Rangos de color:
# 0.0 - 0.2: Azul oscuro → Cian
# 0.2 - 0.4: Cian → Verde
# 0.4 - 0.6: Verde → Amarillo
# 0.6 - 0.8: Amarillo → Naranja
# 0.8 - 1.0: Naranja → Rojo
```

## Opción de Inversión

**Configuración**: `Settings → LedTeacher → "Reverse gradient (dark to bright)"`

- **Normal** (default): Graves oscuros → Agudos brillantes
- **Invertido**: Graves brillantes → Agudos oscuros

Almacenado en `settings.json`:
```json
{
  "led_gradient_reverse": false
}
```

## Ventajas

✅ **Visualización espectacular** del rango completo del piano
✅ **Orientación espacial** inmediata (graves vs agudos)
✅ **Experiencia profesional** similar a piano LED comerciales
✅ **Configurable** según preferencia del usuario
✅ **No interfiere** con modos de aprendizaje (Practice mantiene verde)

## Implementación

### Archivo modificado: `src/ui/main_window.py`

Método `send_arduino_led_on()`:
- Detecta modo actual via `training_manager.current_mode`
- Si modo = "Play" o "Master" → Aplica gradiente RGB
- Si modo = otros → Usa verde tradicional
- Lee configuración `led_gradient_reverse` desde settings

### Archivos modificados:

1. **`settings.json`**: Añadido `"led_gradient_reverse": false`
2. **`src/ui/settings_dialog.py`**: 
   - Añadido checkbox "Reverse gradient"
   - Guardado en get_settings()
3. **`src/ui/main_window.py`**: 
   - Lógica de gradiente RGB en `send_arduino_led_on()`
4. **`README.md`**: 
   - Documentación de la feature

## Testing

### Test Manual:
1. Abrir la aplicación: `python main.py`
2. Cargar una canción MIDI
3. **Modo Play**: Click "Play" → Verifica gradiente RGB en LEDs
4. **Modo Master**: Cambiar a modo "Master" → Verifica gradiente RGB
5. **Modo Practice**: Cambiar a "Practice" → Verifica LEDs verdes
6. **Settings**: 
   - Abrir Settings → LedTeacher
   - Marcar "Reverse gradient"
   - Reproducir → Verifica gradiente invertido

### Valores RGB Esperados:

| Nota | Position | RGB Normal | RGB Invertido |
|------|----------|------------|---------------|
| A0 (21) | 0.0 | (0, 0, 64) Azul oscuro | (255, 0, 0) Rojo |
| C4 (60) | 0.44 | (100, 255, 0) Verde-amarillo | (255, 200, 0) Naranja |
| C8 (108) | 1.0 | (255, 0, 0) Rojo | (0, 0, 64) Azul oscuro |

## Compatibilidad

- ✅ Arduino Uno/Nano/Mega
- ✅ WS2812B LED strips
- ✅ Protocolo de texto a 115200 baud
- ✅ Compatible con todas las versiones del firmware Arduino existente

## Notas Técnicas

- **Performance**: Sin impacto en rendimiento (cálculo simple en Python)
- **Latency**: Sin latencia adicional (cálculo instantáneo)
- **Thread-safe**: Usa el mismo mutex que el resto de comandos Arduino
- **Logging**: Se registra en consola Arduino con valores RGB exactos

---

**Autor**: Implementation based on user request
**Fecha**: 2025-11-26
**Versión**: 1.0
