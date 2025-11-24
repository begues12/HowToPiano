# Sistema de Coordenadas Correcto

## Problema Actual
- La tolerancia de 8ms es demasiado estricta y se saltan notas
- El sistema de coordenadas no respeta preparation_time correctamente
- El scroll no está bien sincronizado con el tiempo

## Sistema Correcto

### Coordenadas
```
Línea Roja = T₀ (tiempo 0)
Posición X de nota = left_margin + red_line_offset + (note_time * pixels_per_second)
Scroll = current_time * pixels_per_second

Cuando T = 0:
- La nota en tiempo 0 está en la línea roja
- Las notas en T = -3s están 3 segundos a la izquierda (fuera de pantalla si preparation < 3)
- Las notas en T = +5s están 5 segundos a la derecha

Red Line Position: left_margin + red_line_offset
Note Visual Position: red_line_pos + (note_time - current_time) * pixels_per_second
```

### Triggering
```
Una nota se activa cuando:
current_time >= note.start_time - tolerance

Tolerance debería ser al menos 1-2 frames (16-32ms) para no perder notas
```

### Zoom
```
pixels_per_second = base_pixels_per_second * (zoom / 100) * (tempo / 120)
```

### Preparation Time
```
Al inicio: current_time = -preparation_time
Esto hace que las notas aparezcan preparadas antes de T₀
```
