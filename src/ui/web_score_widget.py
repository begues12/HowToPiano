import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEnginePage
from PyQt6.QtCore import QUrl, pyqtSlot, QObject, pyqtSignal
from PyQt6.QtWebChannel import QWebChannel
import json
import mido

class ConsoleWebPage(QWebEnginePage):
    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        print(f"js: {message}")

class WebScoreWidget(QWidget):
    """
    Widget que renderiza la partitura usando VexFlow en un WebView.
    Reemplaza al antiguo StaffWidget.
    """
    
    # Signals expected by MainWindow
    note_triggered = pyqtSignal(int, int)  # pitch, velocity
    note_ended = pyqtSignal(int)           # pitch
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.webview = QWebEngineView()
        self.webview.setPage(ConsoleWebPage(self.webview))
        self.layout.addWidget(self.webview)
        
        # Cargar el archivo HTML local
        current_dir = os.path.dirname(os.path.abspath(__file__))
        html_path = os.path.join(current_dir, "web", "index.html")
        self.webview.setUrl(QUrl.fromLocalFile(html_path))
        
        # Configurar canal de comunicación (opcional si solo usamos runJavaScript)
        # self.channel = QWebChannel()
        # self.webview.page().setWebChannel(self.channel)
        
        # Properties for compatibility
        self.tempo_bpm = 120
        self.base_pixels_per_second = 100
        self.pixels_per_second = 100
        self._visual_zoom_scale = 1.0
        self.notes = [] # Dummy list to prevent crashes
        
        # More compatibility properties
        self.base_staff_spacing = 100 # Dummy value
        self.staff_spacing = 100      # Dummy value
        self.base_left_margin = 50    # Dummy value
        self.left_margin = 50         # Dummy value
        self.preparation_time = 3.0   # Time before song starts
        
        # Playback tracking
        self.triggered_notes = set()
        self.currently_playing_notes = set()
        self.last_time = -10.0
        
        print("WebScoreWidget initialized with VexFlow")

    def load_notes(self, notes_data, tempo=120):
        """
        Envía las notas a VexFlow para renderizar.
        notes_data: Lista de diccionarios con formato VexFlow
        Ejemplo: [{'keys': ['c/4'], 'duration': 'q'}, ...]
        """
        # Convertir a JSON
        json_data = json.dumps(notes_data)
        js_command = f"renderNotes({json_data}, {tempo});"
        self.webview.page().runJavaScript(js_command)

    def highlight_note(self, index, color="red"):
        """Cambia el color de una nota específica"""
        js_command = f"highlightNote({index}, '{color}');"
        self.webview.page().runJavaScript(js_command)

    def highlight_note_by_pitch(self, pitch, color="red"):
        """Highlights a note by pitch near the current cursor time"""
        # Find note with this pitch closest to current time
        closest_note = None
        min_diff = float('inf')
        
        # Use last_time as current time
        current_time = self.last_time
        
        for note in self.notes:
            if note['pitch'] == pitch:
                diff = abs(note['start_time'] - current_time)
                if diff < min_diff:
                    min_diff = diff
                    closest_note = note
        
        if closest_note and min_diff < 1.0: # Only if within 1 second
            self.highlight_note(closest_note['id'], color)

    def unhighlight_note_by_pitch(self, pitch):
        """Restores original color for note"""
        # We need to know the original color. 
        # For now, let's just recalculate it based on pitch (Boomwhackers)
        color = self.get_note_color(pitch)
        self.highlight_note_by_pitch(pitch, color)

    def move_cursor(self, x_pos):
        """Mueve el cursor de reproducción"""
        js_command = f"moveCursor({x_pos});"
        self.webview.page().runJavaScript(js_command)

    def midi_pitch_to_vexflow(self, pitch):
        """Converts MIDI pitch (60) to VexFlow key ('c/4')"""
        notes = ['c', 'c#', 'd', 'd#', 'e', 'f', 'f#', 'g', 'g#', 'a', 'a#', 'b']
        octave = (pitch // 12) - 1
        note_index = pitch % 12
        note_name = notes[note_index]
        return f"{note_name}/{octave}"

    def duration_to_vexflow(self, duration_beats):
        """Converts duration in beats to VexFlow duration code"""
        # Simple quantization
        if duration_beats >= 3.5: return "w"
        if duration_beats >= 1.75: return "h"
        if duration_beats >= 0.85: return "q"
        if duration_beats >= 0.4: return "8"
        if duration_beats >= 0.2: return "16"
        return "32"

    def load_midi_notes(self, file_path):
        """Alias for load_midi_file for compatibility"""
        return self.load_midi_file(file_path)

    # Métodos de compatibilidad con el antiguo StaffWidget
    def get_note_color(self, pitch):
        """Returns the color for a given pitch (Boomwhackers style)"""
        colors = [
            "#FF0000", # C - Red
            "#FF0000", # C#
            "#FF7F00", # D - Orange
            "#FF7F00", # D#
            "#FFFF00", # E - Yellow
            "#00FF00", # F - Green
            "#00FF00", # F#
            "#0000FF", # G - Blue
            "#0000FF", # G#
            "#4B0082", # A - Indigo/Dark Blue
            "#4B0082", # A#
            "#8B00FF"  # B - Violet/Purple
        ]
        return colors[pitch % 12]

    def load_midi_file(self, file_path):
        print(f"Loading MIDI: {file_path}")
        
        # Reset playback tracking
        self.triggered_notes.clear()
        self.currently_playing_notes.clear()
        self.last_time = -10.0
        
        try:
            # 1. Parse for Visuals (Ticks)
            mid = mido.MidiFile(file_path)
            ticks_per_beat = mid.ticks_per_beat
            
            events = []
            for track in mid.tracks:
                current_time = 0
                for msg in track:
                    current_time += msg.time
                    if msg.type == 'note_on' and msg.velocity > 0:
                        events.append({'time': current_time, 'type': 'note_on', 'note': msg.note, 'velocity': msg.velocity})
                    elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                        events.append({'time': current_time, 'type': 'note_off', 'note': msg.note})
            
            events.sort(key=lambda x: x['time'])
            
            active_notes = {}
            final_notes = []
            
            for event in events:
                if event['type'] == 'note_on':
                    active_notes[event['note']] = event['time']
                elif event['type'] == 'note_off':
                    if event['note'] in active_notes:
                        start_ticks = active_notes[event['note']]
                        duration_ticks = event['time'] - start_ticks
                        duration_beats = duration_ticks / ticks_per_beat
                        
                        final_notes.append({
                            'pitch': event['note'],
                            'start_ticks': start_ticks,
                            'duration_beats': duration_beats
                        })
                        del active_notes[event['note']]
            
            # Sort by start time AND pitch for deterministic order
            final_notes.sort(key=lambda x: (x['start_ticks'], x['pitch']))
            
            # 2. Parse for Timing (Seconds) - Replicating MidiEngine logic
            mid_timing = mido.MidiFile(file_path) # Re-open to iterate
            timing_events = []
            current_time = 0
            
            # Extract initial tempo
            initial_bpm = 120
            tempo_found = False
            
            for msg in mid_timing:
                current_time += msg.time
                if msg.type == 'set_tempo' and not tempo_found:
                    initial_bpm = mido.tempo2bpm(msg.tempo)
                    tempo_found = True
                if msg.type in ['note_on', 'note_off']:
                    timing_events.append({'time': current_time, 'msg': msg})
            
            # Remove silence
            first_note_time = 0
            for event in timing_events:
                if event['msg'].type == 'note_on' and event['msg'].velocity > 0:
                    first_note_time = event['time']
                    break
            
            if first_note_time > 0:
                for event in timing_events:
                    event['time'] -= first_note_time
            
            # Build timing notes
            timing_notes = []
            active_timing_notes = {}
            for event in timing_events:
                msg = event['msg']
                time = event['time']
                if msg.type == 'note_on' and msg.velocity > 0:
                    if msg.note not in active_timing_notes:
                         active_timing_notes[msg.note] = time
                elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                    if msg.note in active_timing_notes:
                        start = active_timing_notes[msg.note]
                        duration = time - start
                        timing_notes.append({
                            'pitch': msg.note,
                            'start_time': start,
                            'duration': duration
                        })
                        del active_timing_notes[msg.note]
            
            timing_notes.sort(key=lambda x: (x['start_time'], x['pitch']))
            
            # 3. Merge
            vexflow_notes = []
            self.notes = []
            
            use_timing_notes = len(final_notes) == len(timing_notes)
            if not use_timing_notes:
                print(f"Warning: Note count mismatch! Visual: {len(final_notes)}, Timing: {len(timing_notes)}. Using approximate timing.")
            
            for i, note in enumerate(final_notes):
                key = self.midi_pitch_to_vexflow(note['pitch'])
                duration = self.duration_to_vexflow(note['duration_beats'])
                
                if use_timing_notes:
                    start_time_sec = timing_notes[i]['start_time']
                    duration_sec = timing_notes[i]['duration']
                else:
                    # Fallback
                    bpm = self.tempo_bpm if self.tempo_bpm > 0 else 120
                    seconds_per_beat = 60.0 / bpm
                    start_time_sec = (note['start_ticks'] / ticks_per_beat) * seconds_per_beat
                    duration_sec = note['duration_beats'] * seconds_per_beat
                
                vexflow_notes.append({
                    'keys': [key],
                    'duration': duration,
                    'color': 'black', # Start black, highlight when played
                    'pitch': note['pitch'],
                    'start_time': start_time_sec,
                    'duration_sec': duration_sec,
                    'id': i
                })
                
                self.notes.append({
                    'pitch': note['pitch'],
                    'id': i,
                    'start_time': start_time_sec,
                    'duration': duration_sec,
                    'x': 0,
                    'y': 0
                })
            
            # Limit for performance if too many notes
            # if len(vexflow_notes) > 500:
            #     print("Truncating notes for VexFlow performance")
            #     vexflow_notes = vexflow_notes[:500]
                
            self.load_notes(vexflow_notes, initial_bpm)
            return True
            
        except Exception as e:
            print(f"Error loading MIDI: {e}")
            import traceback
            traceback.print_exc()
            return False

    def set_tempo(self, bpm):
        self.tempo_bpm = bpm

    def play(self):
        """Start JS playback loop"""
        self.webview.page().runJavaScript("play();")

    def stop(self):
        """Stop JS playback loop"""
        self.webview.page().runJavaScript("pause();")
        
    def note_on(self, pitch):
        pass
        
    def note_off(self, pitch):
        pass
        
    def reset_triggers(self):
        pass
        
    def update_cursor(self, time_sec):
        """Called by MainWindow to update cursor position"""
        js_command = f"updateCursor({time_sec});"
        self.webview.page().runJavaScript(js_command)
        
    def set_playback_time(self, time_sec):
        self.update_cursor(time_sec)
        self.check_notes(time_sec)

    def check_notes(self, current_time):
        """Check for notes that should start or end at current_time"""
        # Reset if we jumped back significantly (seek)
        if current_time < self.last_time - 1.0:
            self.triggered_notes.clear()
            # Stop all currently playing notes
            for note_id in list(self.currently_playing_notes):
                # Find pitch for this note_id
                for note in self.notes:
                    if note['id'] == note_id:
                        self.note_ended.emit(note['pitch'])
                        break
            self.currently_playing_notes.clear()
            
        self.last_time = current_time
        
        # Tolerance for triggering (50ms)
        tolerance = 0.05 

        # Check for notes to start or end
        for note in self.notes:
            start = note['start_time']
            duration = note['duration']
            end = start + duration
            pitch = note['pitch']
            note_id = note['id']
            
            # Optimization: Stop checking if we are far past current time
            # self.notes is sorted by start_time
            if start > current_time + tolerance:
                # If note starts in future, we only need to check if it's currently playing (unlikely if sorted)
                # But we must continue checking other notes if they are playing
                if not self.currently_playing_notes:
                    break # No more notes to start, and none playing
                if note_id not in self.currently_playing_notes:
                    continue # Skip this future note

            # Note Start
            # We use a window [start, start + tolerance] to trigger
            if start <= current_time <= start + tolerance:
                if note_id not in self.triggered_notes:
                    print(f"[WebScoreWidget] Note triggered: pitch={pitch} at time={current_time:.2f}")
                    self.note_triggered.emit(pitch, 80) # Velocity 80
                    self.triggered_notes.add(note_id)
                    self.currently_playing_notes.add(note_id)
            
            # Note End
            if current_time >= end:
                if note_id in self.currently_playing_notes:
                    self.note_ended.emit(pitch)
                    self.currently_playing_notes.remove(note_id)
        
    def go_to_start(self):
        self.update_cursor(0)
        
    @property
    def visual_zoom_scale(self):
        return self._visual_zoom_scale
        
    @visual_zoom_scale.setter
    def visual_zoom_scale(self, value):
        self._visual_zoom_scale = value
        # Update zoom in JS
        js_command = f"setZoom({value});"
        self.webview.page().runJavaScript(js_command)

    def pitch_to_y(self, pitch):
        return 0 # Dummy
        
    def get_finger_for_note(self, note_id):
        return 1 # Dummy

    def reset_score(self):
        """Resets the score state (colors and scroll)"""
        self.webview.page().runJavaScript("resetNotes();")

    def set_active_color(self, color):
        """Sets the color for active notes"""
        self.webview.page().runJavaScript(f"setActiveNoteColor('{color}');")
        
    def set_view_mode(self, mode):
        """Sets the view mode: 'scrolling' or 'paging'"""
        self.webview.page().runJavaScript(f"setViewMode('{mode}');")
    
    def start_countdown(self, callback):
        """Starts a visual countdown and then calls the callback"""
        from PyQt6.QtCore import QTimer
        
        # Use the preparation_time property
        duration = getattr(self, 'preparation_time', 3.0)
        
        # Trigger JS visual
        self.webview.page().runJavaScript(f"if(typeof startCountdown === 'function') startCountdown({duration});")
        
        # Create a timer to trigger the callback after the duration
        self._countdown_timer = QTimer(self)
        self._countdown_timer.setSingleShot(True)
        self._countdown_timer.timeout.connect(callback)
        self._countdown_timer.start(int(duration * 1000))
