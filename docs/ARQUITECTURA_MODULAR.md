# Arquitectura Modular de HowToPiano

## 📁 Estructura de Archivos

```
HowToPiano/
├── gui_compact.py          # GUI original (monolítica)
├── gui_modular.py          # GUI refactorizada (modular)
└── src/
    ├── gui/                # 🆕 Componentes UI modulares
    │   ├── __init__.py
    │   ├── header.py       # Barra superior
    │   ├── library.py      # Biblioteca de canciones
    │   ├── score.py        # Partitura musical
    │   ├── keyboard.py     # Teclado virtual
    │   └── stats.py        # Estadísticas
    ├── modern_theme.py     # Tema visual
    ├── piano_sound.py      # Generación de sonido
    ├── midi_parser.py      # Parser de archivos MIDI
    └── music_score.py      # Renderizado de partitura
```

## 🏗️ Arquitectura en Capas

### Capa 1: Componentes UI (`src/gui/`)
Cada componente es **independiente** y **reutilizable**:

#### `HeaderComponent`
- **Responsabilidad**: Barra superior con controles principales
- **Widgets**: Logo, info de canción, selectores de sonido/velocidad, botones
- **API Pública**:
  - `update_song_info(name)` - Actualiza nombre de canción
  - `update_metadata(bpm, time_sig, key)` - Actualiza tempo/compás
  - `set_playing_state(is_playing)` - Habilita/deshabilita botones
  - `show_temporary_message(msg)` - Muestra mensaje temporal
  - `get_speed_value()` - Obtiene velocidad seleccionada
  - `get_sound_profile()` - Obtiene perfil de sonido

#### `LibraryComponent`
- **Responsabilidad**: Panel de biblioteca con lista de canciones
- **Widgets**: Lista scrollable, botones buscar/cargar, label de preescucha
- **API Pública**:
  - `set_songs(songs)` - Establece lista completa
  - `add_song(path)` - Añade una canción
  - `refresh()` - Refresca visualización
  - `get_selected_song()` - Obtiene canción seleccionada

#### `ScoreComponent`
- **Responsabilidad**: Visualización de partitura con progreso
- **Widgets**: Canvas de partitura, barra de progreso clickeable
- **API Pública**:
  - `load_notes(events, metadata)` - Carga notas MIDI
  - `update_time(ms)` - Actualiza scroll de partitura
  - `update_progress(percent)` - Actualiza barra de progreso
  - `reset()` - Resetea al inicio

#### `KeyboardComponent`
- **Responsabilidad**: Teclado virtual interactivo
- **Widgets**: Canvas con teclas blancas y negras clickeables
- **API Pública**:
  - `draw()` - Redibuja teclado completo
  - `highlight_key(note, color)` - Ilumina una tecla
  - `restore_key(note)` - Restaura color original
  - `set_num_keys(num)` - Cambia tamaño del teclado
  - `set_fingering(show)` - Activa/desactiva digitación

#### `StatsComponent`
- **Responsabilidad**: Panel de estadísticas de práctica
- **Widgets**: 4 tarjetas (Score, Precisión, Combo, Notas)
- **API Pública**:
  - `reset(total_notes)` - Resetea estadísticas
  - `add_score(points)` - Suma puntos (nota correcta)
  - `break_combo()` - Rompe combo (nota incorrecta)
  - `increment_notes_played()` - Incrementa contador
  - `get_stats()` - Obtiene todas las estadísticas

### Capa 2: Controlador Principal (`gui_modular.py`)
Orquesta todos los componentes y maneja la lógica de negocio:

```python
class ModularHowToPianoGUI:
    def __init__(self):
        # 1. Crear componentes UI
        self.header = HeaderComponent(...)
        self.library = LibraryComponent(...)
        self.score = ScoreComponent(...)
        self.keyboard = KeyboardComponent(...)
        self.stats = StatsComponent(...)
        
        # 2. Conectar callbacks
        # UI → Lógica de negocio
    
    # Handlers (UI → Core)
    def _handle_open_file(self): ...
    def _handle_play(self): ...
    def _handle_stop(self): ...
    
    # Lógica de negocio (Core)
    def _load_song(self, path): ...
    def _auto_play_thread(self): ...
    def _practice_thread(self): ...
```

### Capa 3: Servicios de Negocio (`src/`)
Lógica pura sin UI:

- **`MidiParser`**: Parsea archivos MIDI → eventos con timing
- **`PianoSound`**: Genera sonido sintético de piano
- **`MusicScore`**: Renderiza notación musical en canvas
- **`ModernTheme`**: Constantes de colores/estilos

## 🔄 Flujo de Comunicación

### Patrón: **Callbacks (Inyección de dependencias)**

```
[Usuario]
   ↓ (click)
[Componente UI]
   ↓ (callback)
[Controlador Principal]
   ↓ (usa servicios)
[Servicios de Negocio]
   ↓ (actualiza)
[Componente UI]
```

#### Ejemplo: Usuario hace click en "Reproducir"

```python
# 1. Usuario hace click en botón
HeaderComponent: botón "▶️ Reproducir"
                 ↓
# 2. Componente llama callback
callbacks['on_play']()
                 ↓
# 3. Controlador maneja evento
ModularHowToPianoGUI._handle_play():
    - Valida estado
    - Actualiza UI: header.set_playing_state(True)
    - Inicia thread: _auto_play_thread()
                 ↓
# 4. Thread de reproducción
_auto_play_thread():
    - Usa servicios: midi_parser, piano_sound
    - Actualiza UI: score.update_time(), keyboard.highlight_key()
```

## ✅ Ventajas de la Arquitectura Modular

### 1. **Separación de Responsabilidades**
- Cada componente tiene **una sola responsabilidad**
- UI separada de lógica de negocio
- Fácil identificar dónde está cada funcionalidad

### 2. **Reusabilidad**
- Los componentes pueden usarse en **otras aplicaciones**
- Ejemplo: `KeyboardComponent` puede usarse en un afinador de guitarra

### 3. **Mantenibilidad**
- Cambios en un componente **no afectan** a otros
- Código más corto y legible (~200-300 líneas por archivo)
- Fácil encontrar bugs

### 4. **Testabilidad**
- Cada componente puede **testearse independientemente**
- Mocks fáciles con callbacks

### 5. **Escalabilidad**
- Fácil añadir nuevos componentes
- Fácil extender funcionalidad existente

## 🆚 Comparación: Monolítico vs Modular

### `gui_compact.py` (Monolítico)
```python
class CompactHowToPianoGUI:
    def __init__(self):
        # 1900 líneas en un solo archivo
        self.create_compact_ui()
        # Todo mezclado: UI + lógica + eventos
    
    def create_compact_ui(self):
        # Crea header inline
        header = tk.Frame(...)
        tk.Label(header, text="🎹 HowToPiano").pack(...)
        tk.Button(header, text="▶️", command=self.start_auto_play).pack(...)
        
        # Crea biblioteca inline
        library = tk.Frame(...)
        self.song_listbox = tk.Listbox(...)
        # ... 50 líneas más ...
        
        # Crea partitura inline
        # ... 100 líneas más ...
        
        # Crea teclado inline
        # ... 150 líneas más ...
```

**Problemas**:
- ❌ Difícil mantener (1900 líneas)
- ❌ Imposible reutilizar componentes
- ❌ Difícil testear
- ❌ UI y lógica mezcladas

### `gui_modular.py` (Modular)
```python
class ModularHowToPianoGUI:
    def __init__(self):
        # Solo 400 líneas - orquestación
        self._create_modular_ui()
    
    def _create_modular_ui(self):
        # Instanciar componentes (clean!)
        self.header = HeaderComponent(self.root, callbacks)
        self.library = LibraryComponent(main, callbacks)
        self.score = ScoreComponent(right, callbacks)
        self.keyboard = KeyboardComponent(right, callbacks)
        self.stats = StatsComponent(right)
    
    # Solo handlers y lógica de negocio
    def _handle_play(self): ...
    def _load_song(self, path): ...
```

**Ventajas**:
- ✅ Fácil mantener (archivos pequeños)
- ✅ Componentes reutilizables
- ✅ Fácil testear
- ✅ UI y lógica separadas

## 📊 Métricas de Código

| Métrica | Monolítico | Modular |
|---------|-----------|---------|
| Archivo principal | 1900 líneas | 400 líneas |
| Archivos totales | 1 | 7 |
| Líneas por archivo | 1900 | 200-300 |
| Funciones en main | 80+ | 20 |
| Reusabilidad | Baja | Alta |
| Testabilidad | Difícil | Fácil |

## 🎯 Cómo Usar

### Ejecutar versión modular:
```bash
python gui_modular.py
```

### Añadir nuevo componente:

1. **Crear archivo** en `src/gui/mi_componente.py`:
```python
class MiComponente:
    def __init__(self, parent, callbacks):
        self.parent = parent
        self.callbacks = callbacks
        self.frame = tk.Frame(parent)
        self._create_widgets()
    
    def _create_widgets(self):
        # Crear UI
        pass
    
    # API pública
    def do_something(self):
        pass
```

2. **Importar** en `gui_modular.py`:
```python
from src.gui.mi_componente import MiComponente

class ModularHowToPianoGUI:
    def _create_modular_ui(self):
        self.mi_comp = MiComponente(parent, callbacks)
```

3. **Usar** desde controlador:
```python
self.mi_comp.do_something()
```

## 🔮 Próximos Pasos

1. **Añadir `SettingsDialog`**: Diálogo modal de configuración
2. **Añadir `ModesPanel`**: Panel de modos de práctica
3. **Crear tests unitarios** para cada componente
4. **Migrar** `gui_compact.py` → `gui_modular.py` completamente
5. **Documentar** APIs públicas con docstrings

## 📚 Patrones de Diseño Usados

- **Component Pattern**: Cada widget es un componente independiente
- **Observer Pattern**: Callbacks para comunicación UI → Controlador
- **Facade Pattern**: Controlador simplifica acceso a servicios
- **Strategy Pattern**: Perfiles de sonido intercambiables
- **Factory Pattern**: Creación de componentes centralizada

---

**Autor**: Refactorización modular de HowToPiano  
**Fecha**: Noviembre 2025  
**Versión**: 2.0 (Modular)
