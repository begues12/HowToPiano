"""
Asynchronous song loading worker
Handles MIDI loading, processing, and UI updates in background thread
"""
from PyQt6.QtCore import QThread, pyqtSignal
import os
import traceback


class SongLoaderWorker(QThread):
    """Worker thread for loading songs asynchronously"""
    
    # Signals
    progress_update = pyqtSignal(str, int)  # (status_message, progress_percent)
    load_complete = pyqtSignal(dict)  # (song_data)
    load_failed = pyqtSignal(str)  # (error_message)
    
    def __init__(self, midi_engine, song_library, song_id, path):
        super().__init__()
        self.midi_engine = midi_engine
        self.song_library = song_library
        self.song_id = song_id
        self.path = path
        self._cancelled = False
    
    def cancel(self):
        """Request cancellation of loading operation"""
        self._cancelled = True
    
    def run(self):
        """Load song in background thread"""
        try:
            if self._cancelled:
                return
            
            # Step 1: Validate file exists
            self.progress_update.emit("Checking file...", 10)
            if not os.path.exists(self.path):
                self.load_failed.emit(f"Song file not found: {self.path}")
                return
            
            if self._cancelled:
                return
            
            # Step 2: Get song metadata
            self.progress_update.emit("Loading metadata...", 20)
            song = self.song_library.get_song_by_id(self.song_id)
            if not song:
                self.load_failed.emit(f"Song not found in library: {self.song_id}")
                return
            
            if self._cancelled:
                return
            
            # Step 3: Load MIDI file
            self.progress_update.emit(f"Loading MIDI: {song['name']}...", 40)
            if not self.midi_engine.load_midi(self.path):
                self.load_failed.emit("Failed to parse MIDI file")
                return
            
            if self._cancelled:
                return
            
            # Step 4: Calculate total time
            self.progress_update.emit("Processing events...", 70)
            total_time = 0
            if self.midi_engine.events:
                total_time = max(evt['time'] for evt in self.midi_engine.events)
            
            if self._cancelled:
                return
            
            # Step 5: Prepare song data
            self.progress_update.emit("Finalizing...", 90)
            song_data = {
                'song': song,
                'path': self.path,
                'total_time': total_time,
                'events': self.midi_engine.events,
            }
            
            if self._cancelled:
                return
            
            # Complete
            self.progress_update.emit("Done!", 100)
            self.load_complete.emit(song_data)
            
        except Exception as e:
            error_msg = f"Error loading song: {str(e)}\n{traceback.format_exc()}"
            print(error_msg)
            self.load_failed.emit(str(e))


class LibraryRefreshWorker(QThread):
    """Worker thread for refreshing song library"""
    
    # Signals
    progress_update = pyqtSignal(str, int)  # (status_message, progress_percent)
    refresh_complete = pyqtSignal(list)  # (songs_list)
    refresh_failed = pyqtSignal(str)  # (error_message)
    
    def __init__(self, song_library):
        super().__init__()
        self.song_library = song_library
        self._cancelled = False
    
    def cancel(self):
        """Request cancellation"""
        self._cancelled = True
    
    def run(self):
        """Refresh library in background"""
        try:
            self.progress_update.emit("Scanning library...", 30)
            
            if self._cancelled:
                return
            
            # Reload metadata
            songs = self.song_library.load_metadata()
            
            if self._cancelled:
                return
            
            self.progress_update.emit("Complete!", 100)
            self.refresh_complete.emit(songs)
            
        except Exception as e:
            error_msg = f"Error refreshing library: {str(e)}"
            print(error_msg)
            self.refresh_failed.emit(str(e))
