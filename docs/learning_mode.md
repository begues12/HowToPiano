# 🎓 Guía del Modo Aprendizaje

El **Modo Aprendizaje** es la característica principal de HowToPiano que te permite aprender a tocar canciones paso a paso.

---

## 🌟 ¿Qué es el Modo Aprendizaje?

Es un sistema interactivo que:

✅ **Muestra la partitura** nota por nota  
✅ **Ilumina la tecla correcta** con el LED  
✅ **Te guía paso a paso** indicando qué tocar  
✅ **Detecta cuando tocas** (con teclado MIDI)  
✅ **Marca tu progreso** mostrando cuántas notas llevas  

---

## 🎹 Modos Disponibles

### 1️⃣ Práctica Guiada (Consola Simple)

**Mejor para:** Principiantes absolutos

```bash
sudo python3 main.py
# Selecciona opción 3 → Modo 1
```

**Funcionamiento:**
- Muestra la nota actual en pantalla
- Ilumina el LED correspondiente
- Esperas a presionar Enter después de tocar
- Avanza a la siguiente nota

**Pantalla típica:**
```
════════════════════════════════════════════════════════════
🎼 PARTITURA - Modo Práctica
════════════════════════════════════════════════════════════

🎯 NOTA ACTUAL: C4 (MIDI 60)
   Duración: 0.50s
   LED: 39
   Tecla: ⬜ Blanca

📋 Próximas notas:
   1. D4
   2. E4
   3. F4
   4. G4

📊 Progreso: [████████████░░░░░░░░░░░░░░░░] 30.0%
   Notas: 15/50
════════════════════════════════════════════════════════════
```

---

### 2️⃣ Práctica con Interfaz Visual (Terminal)

**Mejor para:** Usuarios que quieren una interfaz más bonita

```bash
sudo python3 main.py
# Selecciona opción 3 → Modo 2
```

**Funcionamiento:**
- Interfaz completa con `curses`
- Actualización en tiempo real
- Barra de progreso animada
- Presiona ESPACIO para avanzar

**Controles:**
- `ESPACIO` - Siguiente nota
- `Q` - Salir

---

### 3️⃣ Práctica con Detección MIDI (Automático)

**Mejor para:** Cuando tienes un teclado MIDI conectado

```bash
sudo python3 main.py
# Selecciona opción 3 → Modo 3
```

**Funcionamiento:**
- Detecta automáticamente cuando tocas
- Verifica que toques la nota correcta
- Solo avanza si es la nota esperada
- Da feedback inmediato (✓ Correcto / ✗ Incorrecto)

**Requiere:**
- Teclado MIDI conectado por USB
- Librería `mido` con soporte de puertos

---

## 🚀 Inicio Rápido

### Método 1: Desde el menú

```bash
sudo python3 main.py
```

1. Selecciona opción **1** (Listar archivos MIDI)
2. Selecciona opción **3** (Modo Aprendizaje)
3. Elige la canción
4. Selecciona modo de práctica (1, 2 o 3)

### Método 2: Directo con archivo

```bash
# Modo aprendizaje directo
sudo python3 main.py --learn /media/pi/USB/cancion.mid
```

### Método 3: Práctica con último archivo

```bash
sudo python3 main.py --practice
```

---

## 🎼 Qué Muestra en Pantalla

### Información de la Nota Actual:

```
🎯 TOCA AHORA:
     C4     ← Nombre de la nota (grande y claro)

MIDI: 60           ← Número MIDI
Duración: 0.50s    ← Cuánto dura
LED: 39            ← Qué LED se ilumina
Tecla: ⬜ Blanca   ← Tipo de tecla
```

### Próximas Notas:

```
📋 Próximas notas:
   1. D4
   2. E4
   3. F4
   4. G4
   5. A4
```

Te permite anticipar lo que sigue.

### Barra de Progreso:

```
📊 Progreso: [███████████████░░░░░░░░░░░░░] 60.0%
   Notas: 30/50
```

Sabes exactamente cuánto te falta.

---

## 🔌 Conectar Teclado MIDI

### 1. Conectar físicamente

```
Teclado MIDI USB → Cable USB → Adaptador OTG → Raspberry Pi
```

### 2. Verificar conexión

```bash
# Ver si se detecta el USB
lsusb

# Listar puertos MIDI
python3 -c "import mido; print(mido.get_input_names())"
```

Deberías ver algo como:
```
['USB MIDI Device', 'Keyboard', ...]
```

### 3. Usar en modo aprendizaje

El sistema detectará automáticamente el teclado y te pedirá seleccionar el puerto.

---

## 🎮 Flujo Típico de Aprendizaje

### Sesión Completa:

```
1. Conectar pendrive con MIDIs
2. Ejecutar: sudo python3 main.py
3. Seleccionar canción (opción 1 → luego opción 3)
4. Elegir modo de práctica
5. Comenzar:
   
   → 🎯 Nota mostrada en pantalla
   → 💡 LED se ilumina
   → 🎹 Tocas la tecla
   → ✓ Feedback correcto/incorrecto
   → 📈 Avanzas a la siguiente
   
6. Repetir hasta completar
7. 🎉 ¡Felicidades!
```

---

## 📱 Interfaz Visual Completa (Modo 2)

Cuando usas `curses` (Modo 2), ves una pantalla como esta:

```
┌────────────────────────────────────────────────────────────┐
│         🎹 HowToPiano - Modo Aprendizaje                  │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  🎯 TOCA AHORA:                                           │
│                                                            │
│            ╔═══════╗                                       │
│            ║   C4  ║                                       │
│            ╚═══════╝                                       │
│                                                            │
│  MIDI: 60                                                 │
│  Duración: 0.50s                                          │
│  LED: 39                                                  │
│  Tecla: ⬜ Blanca                                         │
│                                                            │
│  📋 Próximas notas:                                       │
│     1. D4                                                 │
│     2. E4                                                 │
│     3. F4                                                 │
│     4. G4                                                 │
│     5. A4                                                 │
│                                                            │
├────────────────────────────────────────────────────────────┤
│  Progreso:                                                │
│  ████████████████████░░░░░░░░░░░░░░░░░░░░                │
│  30/50 notas (60.0%)                                      │
├────────────────────────────────────────────────────────────┤
│  Presiona ESPACIO para siguiente nota | Q para salir     │
└────────────────────────────────────────────────────────────┘
```

---

## 🎯 Detección Automática (Modo 3)

### Con Teclado MIDI:

```python
# El sistema:
1. Muestra la nota esperada (ej: C4)
2. Ilumina el LED correspondiente
3. Espera tu input MIDI
4. Cuando tocas:
   - Si es CORRECTO → ✓ mensaje + siguiente nota
   - Si es INCORRECTO → ✗ mensaje + intenta de nuevo
```

### Sin Teclado MIDI (alternativo):

Si no tienes teclado MIDI, puedes usar el teclado de computadora:

```
Teclas del computador → Notas
────────────────────────────────
a → C4 (Do)
s → D4 (Re)
d → E4 (Mi)
f → F4 (Fa)
g → G4 (Sol)
h → A4 (La)
j → B4 (Si)
k → C5 (Do)
```

---

## 💡 Tips para Aprender Mejor

### 1. Empieza Despacio

Usa canciones simples como escalas o melodías básicas.

### 2. Modo Manual Primero (Modo 1)

Aprende la secuencia sin presión de tiempo.

### 3. Luego Detección (Modo 3)

Una vez que conozcas la secuencia, practica con detección para perfeccionar.

### 4. Divide la Canción

Si es muy larga, practica sección por sección.

### 5. Ajusta el Brillo

Si los LEDs distraen:
```bash
# Brillo bajo
sudo python3 main.py --brightness 0.1
```

---

## 🛠️ Comandos Útiles

```bash
# Aprendizaje con archivo específico
sudo python3 main.py --learn /ruta/cancion.mid

# Modo aprendizaje desde menú
sudo python3 main.py --practice

# Con teclado de 61 teclas
sudo python3 main.py --keyboard keyboard_61 --practice

# Brillo bajo para menos distracción
sudo python3 main.py --brightness 0.2 --practice
```

---

## 🐛 Solución de Problemas

### "No se detectó teclado MIDI"

1. Verifica conexión USB
2. Prueba: `lsusb` y busca tu teclado
3. Instala: `sudo apt install libasound2-dev`
4. Usa modo alternativo con teclado de computadora

### "Notas incorrectas detectadas"

El teclado puede estar transpuesto. Ajusta en la configuración del teclado MIDI.

### "Interfaz visual no funciona"

Si `curses` da problemas:
- Usa Modo 1 (consola simple)
- O actualiza: `pip3 install windows-curses` (en Windows)

### "Los LEDs no se iluminan"

- Ejecuta con `sudo`
- Verifica conexiones
- Prueba: `sudo python3 main.py --test`

---

## 📊 Estadísticas de Progreso

Durante la práctica, el sistema muestra:

```
📊 Progreso: [████████████░░░░░░░░] 60.0%
   Notas: 30/50
```

Al completar:

```
🎉 ¡Felicidades! Completaste la partitura
   Total de notas: 50
   Tiempo: 3:45 minutos
```

---

## 🎓 Modos de Uso Recomendados

### Para Principiantes:
1. **Modo 1** (Consola) - Sin presión, a tu ritmo
2. Canciones simples (escalas)
3. Brillo LED alto para guía clara

### Para Intermedios:
1. **Modo 2** (Visual) - Interfaz más bonita
2. Canciones completas
3. Práctica por secciones

### Para Avanzados:
1. **Modo 3** (Detección) - Feedback inmediato
2. Canciones complejas
3. LEDs como referencia sutil (brillo bajo)

---

## 🎵 Ejemplos Paso a Paso

### Ejemplo 1: Aprender "Twinkle Twinkle"

```bash
# 1. Cargar el archivo
sudo python3 main.py

# 2. Menú → 3 (Modo Aprendizaje)

# 3. Seleccionar twinkle_twinkle.mid

# 4. Modo 1 (Consola simple)

# 5. Seguir instrucciones en pantalla
```

### Ejemplo 2: Práctica con Detección

```bash
# Directo con detección MIDI
sudo python3 main.py --learn /media/pi/USB/escala_c.mid
# Seleccionar Modo 3
```

---

## 🔮 Funcionalidades Futuras

- [ ] Grabación de tus intentos
- [ ] Análisis de errores comunes
- [ ] Sistema de puntuación
- [ ] Modos de velocidad (lento → normal → rápido)
- [ ] Soporte para repetición de secciones
- [ ] Exportar estadísticas de progreso

---

**¡Disfruta aprendiendo piano! 🎹✨**

Para más ayuda: Ver `docs/troubleshooting.md`
