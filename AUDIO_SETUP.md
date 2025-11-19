# Configuración de Audio (Piano Sounds)

⚠️ **IMPORTANTE**: El audio es completamente OPCIONAL. El programa funciona perfectamente sin sonido.

## Sin Audio (Configuración por Defecto)

El programa funcionará sin problemas mostrando:
```
FluidSynth not available - audio playback disabled
```

**Todo funciona normalmente**: pentagrama, piano interactivo, modos de entrenamiento, evaluación, etc.

---

## Para ACTIVAR Audio (Opcional - Avanzado)

Si quieres sonidos de piano reales, necesitas instalar FluidSynth en Windows:

### Paso 1: Instalar FluidSynth (Windows)

1. **Descargar FluidSynth para Windows:**
   - https://github.com/FluidSynth/fluidsynth/releases
   - Buscar el archivo: `fluidsynth-x.x.x-win10-x64.zip` (última versión)

2. **Extraer en una carpeta:**
   ```
   C:\tools\fluidsynth\
   ```
   Debe quedar: `C:\tools\fluidsynth\bin\fluidsynth.exe`

3. **Agregar al PATH de Windows:**
   - Buscar "Variables de entorno" en Windows
   - Editar "Path" del sistema
   - Agregar: `C:\tools\fluidsynth\bin`

### Paso 2: Descargar SoundFont

1. **Crear carpeta:**
   ```
   C:\soundfonts\
   ```

2. **Descargar SoundFont (elige uno):**
   
   **FluidR3_GM (Recomendado - 140 MB):**
   ```
   https://github.com/musescore/MuseScore/raw/2.3.2/share/sound/FluidR3_GM.sf2
   ```

   **MuseScore_General (Alternativa - 35 MB):**
   ```
   https://ftp.osuosl.org/pub/musescore/soundfont/MuseScore_General/MuseScore_General.sf2
   ```

3. **Guardar como:**
   ```
   C:\soundfonts\FluidR3_GM.sf2
   ```

### Paso 3: Verificar

Al iniciar el programa deberías ver:
```
FluidSynth module loaded successfully
Audio: Loaded soundfont C:\soundfonts\FluidR3_GM.sf2
```

---

## Alternativa: Sin FluidSynth (Más Simple)

Si no quieres instalar FluidSynth, simplemente desinstala pyfluidsynth:
```bash
pip uninstall pyfluidsynth
```

El programa detectará automáticamente que no está disponible y funcionará sin audio.
