from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtGui import QPixmap, QPainter, QImage
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QByteArray
import tempfile
import os

import json
import hashlib

try:
    import verovio
except ImportError:
    verovio = None

try:
    import music21
except ImportError:
    music21 = None

class SongLibrary:
    """Manages cached songs and their rendered scores"""
    def __init__(self, library_path="library"):
        self.library_path = library_path
        self.songs_dir = os.path.join(library_path, "songs")
        self.cache_dir = os.path.join(library_path, "cache")
        self.metadata_file = os.path.join(library_path, "songs.json")
        
        # Create directories
        os.makedirs(self.songs_dir, exist_ok=True)
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Load or create metadata
        self.songs = self.load_metadata()
    
    def load_metadata(self):
        if os.path.exists(self.metadata_file):
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    def save_metadata(self):
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self.songs, f, indent=2, ensure_ascii=False)
    
    def get_song_id(self, filepath):
        """Generate unique ID based on file content"""
        with open(filepath, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    
    def add_song(self, midi_path):
        """Add a song to the library"""
        song_id = self.get_song_id(midi_path)
        song_name = os.path.splitext(os.path.basename(midi_path))[0]
        
        # Check if already exists
        for song in self.songs:
            if song['id'] == song_id:
                return song_id
        
        # Copy MIDI file
        dest_path = os.path.join(self.songs_dir, f"{song_id}.mid")
        import shutil
        shutil.copy2(midi_path, dest_path)
        
        # Add to metadata
        song_entry = {
            'id': song_id,
            'name': song_name,
            'path': dest_path,
            'svg_cached': False
        }
        self.songs.append(song_entry)
        self.save_metadata()
        
        return song_id
    
    def get_svg_cache_path(self, song_id):
        return os.path.join(self.cache_dir, f"{song_id}.svg")
    
    def cache_svg(self, song_id, svg_data):
        """Cache the rendered SVG"""
        cache_path = self.get_svg_cache_path(song_id)
        with open(cache_path, 'w', encoding='utf-8') as f:
            f.write(svg_data)
        
        # Update metadata
        for song in self.songs:
            if song['id'] == song_id:
                song['svg_cached'] = True
        self.save_metadata()
    
    def load_cached_svg(self, song_id):
        """Load cached SVG if exists"""
        cache_path = self.get_svg_cache_path(song_id)
        if os.path.exists(cache_path):
            with open(cache_path, 'r', encoding='utf-8') as f:
                return f.read()
        return None
    
    def get_song_by_id(self, song_id):
        for song in self.songs:
            if song['id'] == song_id:
                return song
        return None

class ScoreLoader(QThread):
    finished = pyqtSignal(str, str) # Returns (SVG data, song_id)
    error = pyqtSignal(str)

    def __init__(self, midi_path, toolkit, library):
        super().__init__()
        self.midi_path = midi_path
        self.tk = toolkit
        self.library = library

    def run(self):
        print("ScoreLoader: Starting...")
        if not music21 or not self.tk:
            self.error.emit("Libraries missing")
            return

        try:
            # Add to library
            song_id = self.library.add_song(self.midi_path)
            
            # Check cache
            cached_svg = self.library.load_cached_svg(song_id)
            if cached_svg:
                print(f"ScoreLoader: Using cached SVG for {song_id}")
                self.finished.emit(cached_svg, song_id)
                return
            
            # 1. Parse MIDI with music21
            print(f"ScoreLoader: Parsing MIDI {self.midi_path}...")
            score = music21.converter.parse(self.midi_path)
            
            # 1.2 Filter out Percussion/Drum tracks (they cause notation errors)
            parts_to_remove = []
            for part in score.parts:
                # Check name
                if "Percussion" in part.partName or "Drum" in part.partName:
                    parts_to_remove.append(part)
                    continue
                
                # Check instrument
                try:
                    instrument = part.getInstrument()
                    if instrument and (instrument.midiChannel == 9 or "Percussion" in str(instrument) or "Drum" in str(instrument)):
                        parts_to_remove.append(part)
                except:
                    pass

            for part in parts_to_remove:
                print(f"ScoreLoader: Removing part '{part.partName}' to prevent errors.")
                score.remove(part)

            # 1.5 Quantize to fix "inexpressible durations"
            # This forces notes to snap to a grid (e.g. 32nd notes), fixing issues with raw MIDI timing
            print("ScoreLoader: Quantizing score to fix durations...")
            try:
                score.quantize([4, 8, 16, 32], processOffsets=True, processDurations=True, inPlace=True)
            except Exception as qe:
                print(f"ScoreLoader: Quantization warning: {qe}")

            # 2. Export to MusicXML for Verovio
            print("ScoreLoader: Converting to MusicXML...")
            from music21.musicxml import m21ToXml
            gex = m21ToXml.GeneralObjectExporter(score)
            xml_bytes = gex.parse()
            
            if isinstance(xml_bytes, bytes):
                xml_str = xml_bytes.decode('utf-8')
            else:
                xml_str = xml_bytes

            print(f"ScoreLoader: XML Generated ({len(xml_str)} bytes). Loading into Verovio...")

            # 3. Load into Verovio
            self.tk.loadData(xml_str)
            
            # 4. Render to SVG
            print("ScoreLoader: Rendering SVG...")
            self.tk.setOptions({
                "pageHeight": 6000,
                "pageWidth": 2100,
                "scale": 40,
                "adjustPageHeight": True,
                "breaks": "encoded",
                "header": "none",
                "footer": "none",
                "svgViewBox": True
            })
            svg_data = self.tk.renderToSVG(1)
            print(f"ScoreLoader: SVG Rendered ({len(svg_data)} bytes).")
            
            # Cache the SVG
            self.library.cache_svg(song_id, svg_data)
            
            self.finished.emit(svg_data, song_id)

        except Exception as e:
            print(f"ScoreLoader Error: {e}")
            import traceback
            traceback.print_exc()
            self.error.emit(str(e))

class ScoreView(QScrollArea):
    def __init__(self, library):
        super().__init__()
        self.setWidgetResizable(True)
        self.setMinimumHeight(400)  # Ensure the score view has minimum height
        self.tk = verovio.toolkit() if verovio else None
        self.library = library
        self.current_svg_data = ""
        self.current_song_id = None
        
        if not verovio or not music21:
            lbl = QLabel("Verovio or Music21 not installed.\nCannot render score.")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.setWidget(lbl)
        else:
            self.show_placeholder("No Score Loaded")

    def show_placeholder(self, text):
        lbl = QLabel(text)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("font-size: 24px; color: #888;")
        self.setWidget(lbl)

    def load_midi(self, midi_path):
        if not self.tk: return
        
        self.show_placeholder("Loading Score...\n(This may take a moment)")
        
        self.loader = ScoreLoader(midi_path, self.tk, self.library)
        self.loader.finished.connect(self.on_loaded)
        self.loader.error.connect(self.on_error)
        self.loader.start()

    def on_loaded(self, svg_data, song_id):
        print(f"ScoreView: SVG received ({len(svg_data)} bytes) for song {song_id}")
        self.current_svg_data = svg_data
        self.current_song_id = song_id
        self.update_widget(svg_data)

    def update_widget(self, svg_data):
        # Try to use QSvgWidget directly instead of rendering to pixmap
        print("ScoreView: Loading SVG into widget...")
        
        # Create SVG widget
        from PyQt6.QtSvgWidgets import QSvgWidget
        widget = QSvgWidget()
        
        # Load SVG data
        svg_bytes = svg_data.encode('utf-8') if isinstance(svg_data, str) else svg_data
        widget.load(QByteArray(svg_bytes))
        
        # Check if loaded
        if widget.renderer() and widget.renderer().isValid():
            default_size = widget.renderer().defaultSize()
            print(f"ScoreView: SVG loaded successfully. Size: {default_size.width()}x{default_size.height()}")
            
            # Set size
            viewport_width = self.viewport().width()
            if viewport_width < 100:
                viewport_width = 1000
            
            if default_size.width() > 0:
                scale_factor = viewport_width / default_size.width()
                scaled_height = int(default_size.height() * scale_factor)
                widget.setFixedSize(viewport_width, scaled_height)
                print(f"ScoreView: Widget sized to {viewport_width}x{scaled_height}")
            else:
                widget.setFixedSize(viewport_width, 2000)
                print("ScoreView: Using fallback size")
            
            widget.setStyleSheet("background-color: white;")
            self.setWidget(widget)
            self.setStyleSheet("background-color: #f0f0f0;")
            print("ScoreView: Widget set successfully")
        else:
            print("ScoreView: ERROR - Failed to load SVG")
            self.show_placeholder("Error: Failed to load SVG")
        
    def on_error(self, msg):
        print(f"Score load error: {msg}")
        self.show_placeholder(f"Error loading score:\n{msg}")

    def highlight_at_time(self, time_sec):
        if not self.tk: return
        
        # Convert to milliseconds
        time_ms = int(time_sec * 1000)
        
        # Get elements at this time
        # Verovio expects time in ms for MIDI-loaded files
        try:
            elements = self.tk.getElementsAtTime(time_ms)
            
            # elements is a generic object, we need to check if it has ids
            # In Python binding, it might return a JSON string if configured?
            # Or a list of objects.
            # Let's try to assume it returns a list of objects with 'id' attribute
            # or just use the time to select?
            
            # Actually, let's try to use the JSON interface for selection if possible.
            # But for now, let's just try to re-render with the time?
            # No, renderToSVG doesn't take time.
            
            # Let's try to just print for now to verify connection
            # print(f"Highlighting at {time_ms}ms")
            pass
        except:
            pass

