# 🚀 Ejemplos de Uso Avanzado - HowToPiano

## Ejemplos Básicos

### 1. Reproducción Simple

```bash
# Reproducir archivo MIDI específico
sudo python3 main.py --file /media/pi/USB/cancion.mid

# Con teclado de 61 teclas
sudo python3 main.py --keyboard keyboard_61 --file cancion.mid

# Ajustar brillo
sudo python3 main.py --brightness 0.5 --file cancion.mid
```

---

## Uso Programático

### 2. Script Python Personalizado

```python
#!/usr/bin/env python3
"""
Script personalizado para reproducir múltiples canciones
"""
from src.midi_reader import MidiReader
from src.led_controller import LEDController
from src.note_mapper import NoteMapper
import time

# Inicializar sistema
print("Inicializando...")
midi = MidiReader()
leds = LEDController(num_leds=88, brightness=0.3)
mapper = NoteMapper('piano_88')

# Lista de canciones
songs = midi.list_midi_files()

# Reproducir todas las canciones
for song in songs:
    print(f"\n▶ Reproduciendo: {song}")
    midi.load_midi_file(song)
    
    for msg in midi.play_midi_events():
        if msg.type == 'note_on' and msg.velocity > 0:
            led = mapper.note_to_led(msg.note)
            if led is not None:
                leds.set_led_on(led)
        elif msg.type == 'note_off':
            led = mapper.note_to_led(msg.note)
            if led is not None:
                leds.set_led_off(led)
    
    leds.clear_all()
    time.sleep(2)  # Pausa entre canciones

leds.cleanup()
print("\n✓ Playlist completada")
```

---

### 3. Filtrar Solo Mano Derecha

```python
"""
Ilumina solo notas por encima del Do central (C4)
Útil para practicar mano derecha
"""
from src.midi_reader import MidiReader
from src.led_controller import LEDController
from src.note_mapper import NoteMapper

midi = MidiReader()
leds = LEDController(num_leds=88)
mapper = NoteMapper('piano_88')

# Cargar canción
midi.load_midi_file("cancion.mid")

# Solo notas >= C4 (nota 60)
MIN_NOTE = 60

for msg in midi.play_midi_events():
    if msg.note < MIN_NOTE:
        continue  # Ignorar mano izquierda
    
    led = mapper.note_to_led(msg.note)
    if led is not None:
        if msg.type == 'note_on' and msg.velocity > 0:
            leds.set_led_on(led)
        else:
            leds.set_led_off(led)

leds.cleanup()
```

---

### 4. Colores Diferentes por Octava

```python
"""
Cada octava tiene un color diferente
"""
from src.midi_reader import MidiReader
from src.led_controller import LEDController
from src.note_mapper import NoteMapper

# Colores por octava
OCTAVE_COLORS = {
    0: (255, 0, 0),      # Rojo
    1: (255, 127, 0),    # Naranja
    2: (255, 255, 0),    # Amarillo
    3: (0, 255, 0),      # Verde
    4: (0, 255, 255),    # Cian
    5: (0, 0, 255),      # Azul
    6: (127, 0, 255),    # Violeta
    7: (255, 0, 255),    # Magenta
}

def get_octave_color(note):
    octave = (note // 12) - 1
    return OCTAVE_COLORS.get(octave, (255, 255, 255))

midi = MidiReader()
leds = LEDController(num_leds=88)
mapper = NoteMapper('piano_88')

midi.load_midi_file("cancion.mid")

for msg in midi.play_midi_events():
    led = mapper.note_to_led(msg.note)
    if led is not None:
        if msg.type == 'note_on' and msg.velocity > 0:
            color = get_octave_color(msg.note)
            leds.set_led(led, color)
        else:
            leds.set_led_off(led)

leds.cleanup()
```

---

### 5. Intensidad según Velocidad MIDI

```python
"""
Brillo del LED proporcional a velocidad de nota (fuerza)
"""
from src.midi_reader import MidiReader
from src.led_controller import LEDController
from src.note_mapper import NoteMapper

midi = MidiReader()
leds = LEDController(num_leds=88)
mapper = NoteMapper('piano_88')

midi.load_midi_file("cancion.mid")

for msg in midi.play_midi_events():
    led = mapper.note_to_led(msg.note)
    if led is not None:
        if msg.type == 'note_on' and msg.velocity > 0:
            # Escalar velocidad MIDI (0-127) a brillo (0-255)
            brightness = int((msg.velocity / 127) * 255)
            color = (brightness, brightness // 2, 0)  # Naranja variable
            leds.set_led(led, color)
        else:
            leds.set_led_off(led)

leds.cleanup()
```

---

### 6. Modo "Piano Roll" con Cola

```python
"""
Las notas dejan una "cola" que se desvanece
Similar a visualizador piano roll
"""
from src.midi_reader import MidiReader
from src.led_controller import LEDController
from src.note_mapper import NoteMapper
import threading
import time

# Estado de cada LED: [R, G, B, fade_speed]
led_states = {}

def fade_leds():
    """Thread que desvanece LEDs gradualmente"""
    while True:
        for led, state in list(led_states.items()):
            if state[0] > 0 or state[1] > 0 or state[2] > 0:
                # Reducir brillo
                r = max(0, state[0] - state[3])
                g = max(0, state[1] - state[3])
                b = max(0, state[2] - state[3])
                led_states[led] = [r, g, b, state[3]]
                leds.set_led(led, (int(r), int(g), int(b)))
        time.sleep(0.05)

midi = MidiReader()
leds = LEDController(num_leds=88)
mapper = NoteMapper('piano_88')

# Iniciar thread de fade
fade_thread = threading.Thread(target=fade_leds, daemon=True)
fade_thread.start()

midi.load_midi_file("cancion.mid")

for msg in midi.play_midi_events():
    led = mapper.note_to_led(msg.note)
    if led is not None and msg.type == 'note_on' and msg.velocity > 0:
        # Encender LED con fade_speed
        led_states[led] = [255, 100, 0, 5]  # RGB + velocidad fade
        leds.set_led(led, (255, 100, 0))

leds.cleanup()
```

---

### 7. Modo Práctica: Mostrar Notas Antes

```python
"""
Muestra las próximas notas con anticipación
Útil para aprender la canción
"""
from src.midi_reader import MidiReader
from src.led_controller import LEDController
from src.note_mapper import NoteMapper
from mido import MidiFile
import time

PREVIEW_TIME = 2.0  # Mostrar notas 2 segundos antes

midi = MidiReader()
leds = LEDController(num_leds=88)
mapper = NoteMapper('piano_88')

midi.load_midi_file("cancion.mid")

# Obtener todos los eventos con tiempos absolutos
mid = MidiFile("cancion.mid")
events = []
current_time = 0

for track in mid.tracks:
    for msg in track:
        current_time += msg.time
        if msg.type in ['note_on', 'note_off']:
            events.append((current_time, msg))

# Reproducir con preview
start_time = time.time()
for event_time, msg in events:
    # Esperar hasta el tiempo del evento - PREVIEW_TIME
    preview_time = event_time - PREVIEW_TIME
    while time.time() - start_time < preview_time:
        time.sleep(0.01)
    
    led = mapper.note_to_led(msg.note)
    if led is not None:
        if msg.type == 'note_on' and msg.velocity > 0:
            # Color tenue para preview
            leds.set_led(led, (50, 50, 100))
        else:
            # Color brillante cuando debe tocarse
            leds.set_led(led, (255, 100, 0))

leds.cleanup()
```

---

### 8. Solo Teclas Blancas o Negras

```python
"""
Filtra para practicar solo teclas blancas o negras
"""
from src.midi_reader import MidiReader
from src.led_controller import LEDController
from src.note_mapper import NoteMapper

MODE = 'white'  # 'white' o 'black'

midi = MidiReader()
leds = LEDController(num_leds=88)
mapper = NoteMapper('piano_88')

# Obtener teclas según modo
if MODE == 'white':
    valid_leds = set(mapper.get_white_key_indices())
else:
    valid_leds = set(mapper.get_black_key_indices())

midi.load_midi_file("cancion.mid")

for msg in midi.play_midi_events():
    led = mapper.note_to_led(msg.note)
    if led is not None and led in valid_leds:
        if msg.type == 'note_on' and msg.velocity > 0:
            leds.set_led_on(led)
        else:
            leds.set_led_off(led)

leds.cleanup()
```

---

### 9. Bucle Infinito de Canción

```python
"""
Reproduce una canción en bucle indefinido
Útil para práctica repetitiva
"""
from src.midi_reader import MidiReader
from src.led_controller import LEDController
from src.note_mapper import NoteMapper
import time

midi = MidiReader()
leds = LEDController(num_leds=88)
mapper = NoteMapper('piano_88')

song_file = "/media/pi/USB/practica.mid"

try:
    while True:
        print("▶ Reproduciendo...")
        midi.load_midi_file(song_file)
        
        for msg in midi.play_midi_events():
            led = mapper.note_to_led(msg.note)
            if led is not None:
                if msg.type == 'note_on' and msg.velocity > 0:
                    leds.set_led_on(led)
                else:
                    leds.set_led_off(led)
        
        leds.clear_all()
        print("⏸ Pausa 3 segundos...")
        time.sleep(3)

except KeyboardInterrupt:
    print("\n⏹ Detenido")
    leds.cleanup()
```

---

### 10. Exportar Log de Ejecución

```python
"""
Guarda un log de qué LEDs se encendieron y cuándo
Útil para análisis posterior
"""
from src.midi_reader import MidiReader
from src.led_controller import LEDController
from src.note_mapper import NoteMapper
import time
import json

midi = MidiReader()
leds = LEDController(num_leds=88)
mapper = NoteMapper('piano_88')

log = []
start_time = time.time()

midi.load_midi_file("cancion.mid")

for msg in midi.play_midi_events():
    led = mapper.note_to_led(msg.note)
    if led is not None:
        event = {
            'time': time.time() - start_time,
            'led': led,
            'note': msg.note,
            'note_name': mapper.get_note_name(msg.note),
            'type': msg.type,
            'velocity': getattr(msg, 'velocity', 0)
        }
        log.append(event)
        
        if msg.type == 'note_on' and msg.velocity > 0:
            leds.set_led_on(led)
        else:
            leds.set_led_off(led)

# Guardar log
with open('playback_log.json', 'w') as f:
    json.dump(log, f, indent=2)

print(f"✓ Log guardado: {len(log)} eventos")
leds.cleanup()
```

---

## Integración con Otros Sistemas

### 11. Control por Red (Socket Server)

```python
"""
Servidor socket para control remoto
Cliente puede enviar comandos para reproducir canciones
"""
import socket
import threading
from src.midi_reader import MidiReader
from src.led_controller import LEDController
from src.note_mapper import NoteMapper

class RemoteControl:
    def __init__(self):
        self.midi = MidiReader()
        self.leds = LEDController(num_leds=88)
        self.mapper = NoteMapper('piano_88')
        self.playing = False
    
    def play_song(self, filename):
        if self.midi.load_midi_file(filename):
            self.playing = True
            for msg in self.midi.play_midi_events():
                if not self.playing:
                    break
                led = self.mapper.note_to_led(msg.note)
                if led is not None:
                    if msg.type == 'note_on' and msg.velocity > 0:
                        self.leds.set_led_on(led)
                    else:
                        self.leds.set_led_off(led)
            self.leds.clear_all()
    
    def stop(self):
        self.playing = False
        self.leds.clear_all()
    
    def handle_client(self, conn):
        while True:
            data = conn.recv(1024).decode()
            if not data:
                break
            
            if data.startswith("PLAY:"):
                filename = data.split(":", 1)[1]
                threading.Thread(target=self.play_song, args=(filename,)).start()
                conn.send(b"OK\n")
            elif data == "STOP":
                self.stop()
                conn.send(b"STOPPED\n")
            elif data == "LIST":
                songs = "\n".join(self.midi.list_midi_files())
                conn.send(songs.encode() + b"\n")
        conn.close()
    
    def start_server(self, port=5000):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(('0.0.0.0', port))
        server.listen(5)
        print(f"Servidor escuchando en puerto {port}")
        
        while True:
            conn, addr = server.accept()
            print(f"Cliente conectado: {addr}")
            threading.Thread(target=self.handle_client, args=(conn,)).start()

if __name__ == "__main__":
    rc = RemoteControl()
    rc.start_server()
```

Cliente de ejemplo:
```python
import socket

s = socket.socket()
s.connect(('192.168.1.100', 5000))

# Listar canciones
s.send(b"LIST")
print(s.recv(4096).decode())

# Reproducir
s.send(b"PLAY:/media/pi/USB/song.mid")
print(s.recv(1024).decode())

s.close()
```

---

### 12. Web API con Flask

```python
"""
API REST para control via HTTP
Instalar: pip3 install flask
"""
from flask import Flask, jsonify, request
from src.midi_reader import MidiReader
from src.led_controller import LEDController
from src.note_mapper import NoteMapper
import threading

app = Flask(__name__)

class HowToPianoAPI:
    def __init__(self):
        self.midi = MidiReader()
        self.leds = LEDController(num_leds=88)
        self.mapper = NoteMapper('piano_88')
        self.current_song = None
        self.playing = False
    
    def play_song(self, filename):
        if self.midi.load_midi_file(filename):
            self.current_song = filename
            self.playing = True
            for msg in self.midi.play_midi_events():
                if not self.playing:
                    break
                led = self.mapper.note_to_led(msg.note)
                if led is not None:
                    if msg.type == 'note_on' and msg.velocity > 0:
                        self.leds.set_led_on(led)
                    else:
                        self.leds.set_led_off(led)
            self.leds.clear_all()
            self.playing = False

piano = HowToPianoAPI()

@app.route('/songs', methods=['GET'])
def list_songs():
    songs = piano.midi.list_midi_files()
    return jsonify({'songs': songs})

@app.route('/play', methods=['POST'])
def play():
    filename = request.json.get('filename')
    threading.Thread(target=piano.play_song, args=(filename,)).start()
    return jsonify({'status': 'playing', 'song': filename})

@app.route('/stop', methods=['POST'])
def stop():
    piano.playing = False
    piano.leds.clear_all()
    return jsonify({'status': 'stopped'})

@app.route('/status', methods=['GET'])
def status():
    return jsonify({
        'playing': piano.playing,
        'current_song': piano.current_song
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
```

Uso:
```bash
# Listar canciones
curl http://192.168.1.100:8080/songs

# Reproducir
curl -X POST http://192.168.1.100:8080/play \
  -H "Content-Type: application/json" \
  -d '{"filename": "/media/pi/USB/song.mid"}'

# Detener
curl -X POST http://192.168.1.100:8080/stop
```

---

¡Con estos ejemplos puedes crear infinitas variaciones! 🎹✨
