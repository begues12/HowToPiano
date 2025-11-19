# Custom Instruments

Esta carpeta es para tus perfiles personalizados.

## 📝 Cómo añadir un perfil personalizado

1. **Crear subcarpeta:**
   ```
   custom/mi_piano/
   ```

2. **Añadir archivos WAV (88 notas):**
   ```
   custom/mi_piano/
   ├── note_21.wav   # A0
   ├── note_22.wav   # A#0
   ...
   └── note_108.wav  # C8
   ```

3. **Opcional: Añadir config.json:**
   ```json
   {
     "name": "Mi Piano",
     "description": "Piano personalizado con samples reales",
     "type": "sampled"
   }
   ```

4. Reiniciar la aplicación

## 🎹 Ejemplo de estructura completa

```
custom/
├── steinway_d/
│   ├── config.json
│   ├── note_21.wav
│   ├── note_22.wav
│   ...
│   └── note_108.wav
└── yamaha_c7/
    ├── config.json
    └── samples/
        ├── note_21.wav
        ...
```

## 💾 Donde conseguir samples

- **Freesound.org**: Samples gratuitos
- **Philharmonia Orchestra**: Instrumentos profesionales
- **Salamander Grand Piano**: Piano de cola completo y gratuito

Los perfiles personalizados aparecerán automáticamente en el selector de sonido.
