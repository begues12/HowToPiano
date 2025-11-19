from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QListWidget, QLabel, 
                             QListWidgetItem, QLineEdit, QComboBox, QHBoxLayout)
from PyQt6.QtCore import pyqtSignal, Qt, QPropertyAnimation, QRect
from PyQt6.QtGui import QFont
import json
import os

class SongListWidget(QWidget):
    song_selected = pyqtSignal(str, str)  # (song_id, path)
    
    def __init__(self, library, parent=None):
        super().__init__(parent)
        self.library = library
        self.all_songs = []
        self.recent_songs = []  # Track recently played songs
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Title
        title = QLabel("Song Library")
        title.setStyleSheet("font-weight: bold; font-size: 13px; color: #2c3e50;")
        layout.addWidget(title)
        
        # Search box
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("🔍 Search songs...")
        self.search_box.textChanged.connect(self.filter_songs)
        self.search_box.setStyleSheet("""
            QLineEdit {
                padding: 6px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background: white;
            }
            QLineEdit:focus {
                border: 1px solid #3498db;
            }
        """)
        layout.addWidget(self.search_box)
        
        # Filter combo
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["All Songs", "Recent", "Favorites"])
        self.filter_combo.currentTextChanged.connect(self.apply_filter)
        self.filter_combo.setStyleSheet("""
            QComboBox {
                padding: 4px 8px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background: white;
            }
        """)
        layout.addWidget(self.filter_combo)
        
        # List widget with custom styling
        self.list_widget = QListWidget()
        self.list_widget.itemClicked.connect(self.on_item_clicked)
        self.list_widget.setStyleSheet("""
            QListWidget {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background: white;
                outline: none;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #ecf0f1;
            }
            QListWidget::item:hover {
                background: #e8f4f8;
                padding-left: 12px;
            }
            QListWidget::item:selected {
                background: #3498db;
                color: white;
            }
        """)
        layout.addWidget(self.list_widget)
        
        self.refresh()
    
    def refresh(self):
        """Reload the song list"""
        self.library.songs = self.library.load_metadata()
        self.all_songs = self.library.songs.copy()
        self.load_recent_songs()
        self.apply_filter(self.filter_combo.currentText())
    
    def load_recent_songs(self):
        """Load recent songs from file"""
        recent_file = os.path.join("library", "recent.json")
        if os.path.exists(recent_file):
            try:
                with open(recent_file, 'r', encoding='utf-8') as f:
                    self.recent_songs = json.load(f)
            except:
                self.recent_songs = []
        else:
            self.recent_songs = []
    
    def save_recent_song(self, song_id):
        """Save a song to recent list"""
        # Remove if already exists
        self.recent_songs = [s for s in self.recent_songs if s != song_id]
        # Add to front
        self.recent_songs.insert(0, song_id)
        # Keep only last 10
        self.recent_songs = self.recent_songs[:10]
        
        # Save to file
        recent_file = os.path.join("library", "recent.json")
        os.makedirs("library", exist_ok=True)
        with open(recent_file, 'w', encoding='utf-8') as f:
            json.dump(self.recent_songs, f)
    
    def apply_filter(self, filter_type):
        """Apply selected filter"""
        self.list_widget.clear()
        
        if filter_type == "Recent":
            # Show only recent songs
            songs_to_show = [s for s in self.all_songs if s['id'] in self.recent_songs]
            # Sort by recent order
            songs_to_show.sort(key=lambda s: self.recent_songs.index(s['id']) if s['id'] in self.recent_songs else 999)
        elif filter_type == "Favorites":
            # Placeholder for favorites (would need implementation)
            songs_to_show = [s for s in self.all_songs if s.get('favorite', False)]
        else:  # "All Songs"
            songs_to_show = self.all_songs
        
        self.display_songs(songs_to_show)
    
    def filter_songs(self, search_text):
        """Filter songs based on search text"""
        if not search_text:
            self.apply_filter(self.filter_combo.currentText())
            return
        
        # Get base filter
        filter_type = self.filter_combo.currentText()
        if filter_type == "Recent":
            base_songs = [s for s in self.all_songs if s['id'] in self.recent_songs]
        elif filter_type == "Favorites":
            base_songs = [s for s in self.all_songs if s.get('favorite', False)]
        else:
            base_songs = self.all_songs
        
        # Apply search filter
        search_lower = search_text.lower()
        filtered = [s for s in base_songs if search_lower in s['name'].lower()]
        self.display_songs(filtered)
    
    def display_songs(self, songs):
        """Display list of songs"""
        self.list_widget.clear()
        
        for song in songs:
            item = QListWidgetItem(song['name'])
            item.setData(Qt.ItemDataRole.UserRole, song['id'])  # Store song_id
            item.setData(Qt.ItemDataRole.UserRole + 1, song['path'])  # Store path
            
            # Set tooltip with full name
            item.setToolTip(song['name'])
            
            self.list_widget.addItem(item)
    
    def on_item_clicked(self, item):
        song_id = item.data(Qt.ItemDataRole.UserRole)
        path = item.data(Qt.ItemDataRole.UserRole + 1)
        
        if song_id and path:
            # Save to recent
            self.save_recent_song(song_id)
            self.song_selected.emit(song_id, path)
        else:
            print("SongList: ERROR - Missing song_id or path in item data")
