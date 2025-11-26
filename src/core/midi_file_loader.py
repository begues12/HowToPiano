"""
Worker for loading MIDI files from file dialog
"""
from PyQt6.QtCore import QThread, pyqtSignal
import os
import traceback


class MidiFileLoaderWorker(QThread):
    """Worker thread for loading MIDI files asynchronously"""
    
    # Signals
    progress_update = pyqtSignal(str, int)  # (status_message, progress_percent)
    load_complete = pyqtSignal(dict)  # (midi_data)
    load_failed = pyqtSignal(str)  # (error_message)
    
    def __init__(self, midi_engine, song_library, file_path):
        super().__init__()
        self.midi_engine = midi_engine
        self.song_library = song_library
        self.file_path = file_path
        self._cancelled = False
    
    def cancel(self):
        """Request cancellation of loading operation"""
        self._cancelled = True
    
    def run(self):
        """Load MIDI file in background thread"""
        try:
            if self._cancelled:
                return
            
            file_name = os.path.basename(self.file_path)
            
            # Step 1: Load MIDI
            self.progress_update.emit(f"Loading {file_name}...", 30)
            if not self.midi_engine.load_midi(self.file_path):
                self.load_failed.emit("Failed to parse MIDI file")
                return
            
            if self._cancelled:
                return
            
            # Step 2: Add to library
            self.progress_update.emit("Adding to library...", 60)
            song_id = self.song_library.add_song(self.file_path)
            
            if self._cancelled:
                return
            
            # Step 3: Calculate duration
            self.progress_update.emit("Processing...", 80)
            total_time = 0
            if self.midi_engine.events:
                total_time = max(evt['time'] for evt in self.midi_engine.events)
            
            if self._cancelled:
                return
            
            # Complete
            self.progress_update.emit("Done!", 100)
            midi_data = {
                'path': self.file_path,
                'name': file_name,
                'song_id': song_id,
                'total_time': total_time,
                'events': self.midi_engine.events,
            }
            self.load_complete.emit(midi_data)
            
        except Exception as e:
            error_msg = f"Error loading MIDI: {str(e)}\n{traceback.format_exc()}"
            print(error_msg)
            self.load_failed.emit(str(e))
