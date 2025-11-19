# Fuentes Musicales Profesionales para HowToPiano

## Fuentes Recomendadas (Gratuitas)

### 1. **Bravura** (Recomendada) ⭐
- **Descripción**: Fuente musical profesional diseñada por Steinberg para notación musical
- **Formato**: OpenType (OTF)
- **Descarga**: https://github.com/steinbergmedia/bravura/releases
- **Instalación**: 
  1. Descargar `main_font.ttx`
  2. Click derecho → Instalar
  3. Reiniciar la aplicación
- **Ventajas**: 
  - Muy completa (símbolos SMuFL)
  - Diseño elegante y legible
  - Usado en software profesional

### 2. **Petaluma** (Estilo manuscrito)
- **Descripción**: Fuente con aspecto de escritura a mano elegante
- **Formato**: OpenType (OTF)
- **Descarga**: https://github.com/steinbergmedia/petaluma/releases
- **Ideal para**: Aspecto más informal pero profesional

### 3. **MuseScore's Leland** (Alternativa)
- **Descripción**: Fuente diseñada para MuseScore
- **Descarga**: https://github.com/MuseScoreFonts/Leland
- **Ventajas**: Optimizada para pantalla

### 4. **Emmentaler** (GNU LilyPond)
- **Descripción**: Fuente del software de notación LilyPond
- **Descarga**: Incluida con LilyPond
- **Ventajas**: Código abierto, muy completa

## Cómo Usar en Python/Tkinter

### Opción 1: Instalar la fuente en el sistema
```python
# En music_score.py, cambiar la fuente:
font=('Bravura', 16, 'normal')  # En lugar de 'Segoe UI Symbol'
```

### Opción 2: Usar PIL/Pillow para cargar fuentes personalizadas
```python
from PIL import Image, ImageDraw, ImageFont
import tkinter as tk
from PIL import ImageTk

# Cargar fuente personalizada
font = ImageFont.truetype("assets/main_font.ttx", 24)
```

### Opción 3: Usar librería especializada

#### **python-ly** (LilyPond)
```bash
pip install python-ly
```
Renderiza partituras usando LilyPond como backend.

#### **abjad** (Composición musical)
```bash
pip install abjad
```
Sistema completo de notación musical profesional.

#### **music21** (Análisis y notación)
```bash
pip install music21
```
Librería completa para análisis y renderizado de música.

## Símbolos Musicales Unicode (SMuFL)

Con fuentes musicales profesionales, puedes usar:

```python
# Notas
'𝅝'  # Whole note (redonda)
'𝅗𝅥' # Half note (blanca)
'𝅘𝅥' # Quarter note (negra)
'𝅘𝅥𝅮' # Eighth note (corchea)
'𝅘𝅥𝅯' # Sixteenth note (semicorchea)

# Alteraciones
'♯' # Sharp (sostenido)
'♭' # Flat (bemol)
'♮' # Natural

# Claves
'𝄞' # G clef (clave de sol)
'𝄢' # F clef (clave de fa)

# Dinámicas
'𝆏' # Piano
'𝆐' # Forte
'𝆑' # Mezzo
```

## Configuración Actual

Actualmente HowToPiano usa:
- **Fuente**: Segoe UI Symbol (incluida en Windows)
- **Fallback**: Arial
- **Ventaja**: No requiere instalación adicional
- **Desventaja**: Símbolos menos refinados

## Próximos Pasos

1. **Instalar main_font**: Descarga e instala main_font.ttx desde assets/
2. **Modificar código**: Cambiar 'Segoe UI Symbol' por 'Bravura'
3. **Probar**: Reiniciar la aplicación y ver la mejora

## Comparación Visual

| Fuente | Calidad | Instalación | Compatibilidad |
|--------|---------|-------------|----------------|
| Segoe UI Symbol | ⭐⭐⭐ | ✅ Incluida | Windows |
| Bravura | ⭐⭐⭐⭐⭐ | Manual | Todos |
| Petaluma | ⭐⭐⭐⭐ | Manual | Todos |
| Leland | ⭐⭐⭐⭐ | Manual | Todos |

## Recursos Adicionales

- **SMuFL Standard**: https://www.smufl.org/
- **Bravura Font**: https://www.smufl.org/fonts/
- **Music21 Documentation**: https://web.mit.edu/music21/
