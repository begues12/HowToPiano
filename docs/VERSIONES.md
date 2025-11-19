# 🎹 HowToPiano - Guía de Versiones

## 📦 Versiones Disponibles

### 1. **gui_compact.py** - Versión Compacta (Original)
- ✅ Funcional y completa
- ✅ Todo el código en un archivo
- ⚠️ 1900 líneas - difícil de mantener

**Ejecutar:**
```bash
python gui_compact.py
```

### 2. **gui_modular.py** - Versión Modular (Refactorizada)
- ✅ Código separado por componentes
- ✅ Fácil de mantener y extender
- ✅ Reutilizable y testeable
- 🆕 Arquitectura moderna

**Ejecutar:**
```bash
python gui_modular.py
```

## 🏗️ Estructura Modular

```
src/gui/
├── header.py      # Barra superior con controles
├── library.py     # Biblioteca de canciones
├── score.py       # Partitura musical con progreso
├── keyboard.py    # Teclado virtual interactivo
└── stats.py       # Panel de estadísticas
```

## 🎯 ¿Cuál usar?

### Usa `gui_compact.py` si:
- Solo quieres usar la app sin modificar código
- Prefieres un archivo único

### Usa `gui_modular.py` si:
- Vas a desarrollar nuevas funcionalidades
- Quieres entender mejor el código
- Necesitas reutilizar componentes
- Prefieres arquitectura limpia

## 📖 Documentación

- **[ARQUITECTURA_MODULAR.md](docs/ARQUITECTURA_MODULAR.md)** - Explicación detallada de la refactorización

## ✨ Funcionalidades (ambas versiones)

- 🎵 Carga archivos MIDI
- 🎹 Teclado virtual clickeable
- 📜 Partitura con scroll automático
- 🎼 Múltiples perfiles de sonido de piano
- ⚡ Control de velocidad de reproducción
- 📊 Estadísticas de práctica
- 🎨 Digitación con colores
- 💾 Biblioteca con canciones recientes
- 📈 Barra de progreso con seek

## 🔄 Migración

Si tienes código personalizado en `gui_compact.py`:

1. Identifica la funcionalidad que modificaste
2. Busca el componente correspondiente en `src/gui/`
3. Aplica el cambio en el componente modular
4. Actualiza el controlador si es necesario

**Ejemplo:**
```python
# Antes (gui_compact.py)
class CompactHowToPianoGUI:
    def draw_keyboard(self):
        # 150 líneas de código...

# Después (gui_modular.py + src/gui/keyboard.py)
# En KeyboardComponent.draw():
# Solo 80 líneas - más fácil de modificar
```

## 🐛 Reportar Problemas

Si encuentras bugs, especifica qué versión usas:
- `[compact]` para gui_compact.py
- `[modular]` para gui_modular.py
