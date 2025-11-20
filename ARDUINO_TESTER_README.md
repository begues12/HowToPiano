# Arduino Connection Tester

Herramienta de diagnóstico para probar la conexión con Arduino.

## 🚀 Uso Rápido

```bash
python test_arduino.py
```

## 📋 Características

### 1. **Gestión de Conexión**
- 🔍 Detección automática de puertos COM
- ⚙️ Configuración de baudrate (9600, 19200, 38400, 57600, 115200)
- ✅ Conexión/desconexión con un clic
- 📊 Estado de conexión en tiempo real

### 2. **Pruebas Rápidas**
- **🎹 Test Note C4**: Envía una nota simple (MIDI 60) para verificar conectividad básica
- **🎵 Test C Scale**: Toca la escala de Do mayor (8 notas)
- **🎼 Test C Chord**: Toca el acorde de Do mayor (3 notas simultáneas)

### 3. **Comandos Manuales**
Envía comandos personalizados siguiendo el protocolo:
- `ON:note:velocity` - Activar nota
- `OFF:note` - Desactivar nota

Ejemplos:
```
ON:60:100    → Note On C4 con velocidad 100
OFF:60       → Note Off C4
ON:72:80     → Note On C5 con velocidad 80
```

### 4. **Prueba de Nota Personalizada**
- Selector de nota MIDI (21-108, rango de piano completo)
- Selector de velocity (0-127)
- Botón para enviar nota individual

### 5. **Consola de Log**
- Registro timestamped de todos los eventos
- Muestra comandos enviados y recibidos
- Botón para limpiar log

## 📝 Protocolo Arduino

El Arduino debe estar programado para responder a estos comandos:

### Formato de Entrada (PC → Arduino)
```
ON:note:velocity\n
OFF:note\n
```

### Formato de Salida (Arduino → PC)
```
ON:note:velocity\n
OFF:note\n
```

## 🔧 Configuración

La herramienta carga automáticamente la configuración desde `settings.json`:
```json
{
  "port": "COM3",
  "baud_rate": 9600
}
```

## 🎹 Notas MIDI de Referencia

| Nota | MIDI | Octava |
|------|------|--------|
| C4   | 60   | Middle C |
| C3   | 48   | Una octava abajo |
| C5   | 72   | Una octava arriba |
| A0   | 21   | Primera tecla del piano |
| C8   | 108  | Última tecla del piano |

## 🐛 Troubleshooting

### Arduino no aparece en la lista
1. Verifica que el cable USB esté conectado
2. Instala los drivers CH340/CP2102 si es necesario
3. Presiona "🔄 Refresh" para actualizar la lista

### No se conecta
1. Cierra otros programas que usen el puerto (IDE Arduino, Putty, etc.)
2. Verifica el baudrate correcto (debe coincidir con tu código Arduino)
3. Prueba con otro cable USB

### Se conecta pero no responde
1. Espera 2 segundos después de conectar (Arduino se resetea)
2. Verifica que tu sketch Arduino implemente el protocolo correctamente
3. Abre el Serial Monitor del IDE Arduino para verificar que el sketch funciona

## 💡 Tips

- **Antes de cargar un nuevo sketch:** Desconecta la herramienta
- **Para debug:** Usa el Serial Monitor del IDE Arduino en paralelo
- **Velocidad recomendada:** 9600 baud es la más estable
- **Notas simultáneas:** El Arduino puede manejar múltiples notas ON antes de OFF

## 🔗 Uso con el Programa Principal

Una vez verificada la conexión aquí:
1. Cierra esta herramienta
2. Ejecuta `python main.py`
3. El programa principal usará la misma configuración

## 📦 Dependencias

```bash
pip install pyserial PyQt6
```

Ya incluidas en `requirements.txt` del proyecto principal.
