# Esquema de Colores - How To Piano

## Colores de Notas Activas (Cuando se Tocan)

### 🔵 Cian Brillante (0, 200, 255) - Reproducción Automática
**Cuándo aparece:** Cuando el programa reproduce la partitura automáticamente
- Modo Maestro: notas que el programa toca
- Modo Estudiante: acordes que el profesor (programa) muestra
- Cualquier reproducción automática de la canción

**Propósito:** Mostrar qué notas está tocando el programa

---

### 🟠 Naranja Brillante (255, 140, 0) - Input del Usuario
**Cuándo aparece:** Cuando TÚ tocas las teclas
- Click del mouse en el piano
- Teclas del controlador MIDI/Arduino
- Cualquier input manual del usuario

**Propósito:** Feedback visual de tus acciones

---

## Colores de Dedos (Guía de Digitación)

Colores pasteles suaves para la asignación de dedos:

### 🔴 Rojo Suave (255, 100, 100) - Dedo 1 (Pulgar)
### 🟢 Verde Suave (100, 200, 100) - Dedo 2 (Índice)
### 🔵 Azul Suave (100, 150, 255) - Dedo 3 (Medio)
### 🟡 Amarillo Suave (255, 200, 100) - Dedo 4 (Anular)
### 🟣 Púrpura Suave (200, 100, 255) - Dedo 5 (Meñique)

**Propósito:** Guiar qué dedo usar para cada tecla
**Opacidad:** Semi-transparente (alpha 80 teclas blancas, 120 teclas negras)

---

## Diferencias Visuales

### Colores de Notas Activas
- **Brillantes y saturados**
- **Opacos (sin transparencia)**
- **Se activan al tocar**
- **Desaparecen al soltar**

### Colores de Dedos
- **Pasteles suaves**
- **Semi-transparentes**
- **Siempre visibles (si está activado)**
- **No cambian al tocar**

---

## Configuración

Puedes activar/desactivar en **Settings → Piano**:

- ✅ **Show note names on keys** - Letras C, D, E, etc.
- ✅ **Show finger colors on keys** - Colores pasteles de dedos
- ✅ **Show finger numbers (1-5)** - Números de dedos
- ✅ **Show colors when notes are played** - Colores brillantes al tocar

---

## Ejemplo Visual

```
Tecla en reposo con dedo asignado:
┌─────────────┐
│   Fondo:    │
│   Pastel    │  ← Color suave de dedo (ej: verde pastel)
│   Verde     │
│      2      │  ← Número de dedo
│      D      │  ← Nombre de nota
└─────────────┘

Usuario toca la tecla:
┌─────────────┐
│   Fondo:    │
│   NARANJA   │  ← Color brillante de acción (naranja)
│  BRILLANTE  │
│      2      │  ← Número aún visible
│      D      │  ← Nombre aún visible
└─────────────┘

Programa toca la tecla:
┌─────────────┐
│   Fondo:    │
│    CIAN     │  ← Color brillante de reproducción (cian)
│  BRILLANTE  │
│      2      │
│      D      │
└─────────────┘
```

---

## Persistencia

La configuración visual se guarda automáticamente en `settings.json` y se restaura al iniciar el programa.
