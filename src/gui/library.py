"""
Componente Library - Panel de biblioteca de canciones
"""
import tkinter as tk
from tkinter import filedialog, messagebox
import os
from ..modern_theme import ModernTheme


class LibraryComponent:
    """Componente de biblioteca de canciones con preescucha"""
    
    def __init__(self, parent, callbacks):
        """
        Args:
            parent: Widget padre
            callbacks: Dict con funciones callback:
                - on_select: Cuando se selecciona una canción
                - on_load: Cuando se carga una canción
                - on_browse: Cuando se buscan nuevos archivos
        """
        self.parent = parent
        self.callbacks = callbacks
        self.recent_songs = []
        
        # Crear frame principal
        self.frame = tk.Frame(parent, bg=ModernTheme.BG_CARD, width=280)
        self.frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 10))
        self.frame.pack_propagate(False)
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Crea todos los widgets de la biblioteca"""
        # Título
        tk.Label(
            self.frame,
            text="📚 Biblioteca",
            font=('Segoe UI', 11, 'bold'),
            bg=ModernTheme.BG_CARD,
            fg=ModernTheme.TEXT_PRIMARY
        ).pack(pady=8, padx=10, anchor=tk.W)
        
        # Lista de canciones
        self._create_song_list()
        
        # Botones de acción
        self._create_action_buttons()
        
        # Label de preescucha
        self.preview_label = tk.Label(
            self.frame,
            text="Selecciona para preescuchar",
            font=('Segoe UI', 8),
            bg=ModernTheme.BG_CARD,
            fg=ModernTheme.TEXT_MUTED,
            wraplength=260,
            justify=tk.LEFT
        )
        self.preview_label.pack(pady=(0, 10), padx=10, anchor=tk.W)
    
    def _create_song_list(self):
        """Crea la lista de canciones con scroll"""
        list_frame = tk.Frame(self.frame, bg=ModernTheme.BG_CARD)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.song_listbox = tk.Listbox(
            list_frame,
            bg=ModernTheme.BG_LIGHT,
            fg=ModernTheme.TEXT_PRIMARY,
            font=('Segoe UI', 9),
            selectbackground=ModernTheme.PRIMARY,
            relief=tk.FLAT,
            bd=0,
            highlightthickness=0,
            yscrollcommand=scrollbar.set
        )
        self.song_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.song_listbox.yview)
        
        # Bind eventos
        self.song_listbox.bind('<<ListboxSelect>>', self._on_select)
        self.song_listbox.bind('<Double-Button-1>', self._on_double_click)
    
    def _create_action_buttons(self):
        """Crea los botones de buscar y cargar"""
        action_frame = tk.Frame(self.frame, bg=ModernTheme.BG_CARD)
        action_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Button(
            action_frame,
            text="🔍 Buscar",
            command=self._on_browse,
            bg=ModernTheme.PRIMARY,
            fg=ModernTheme.TEXT_PRIMARY,
            font=('Segoe UI', 9, 'bold'),
            relief=tk.FLAT,
            cursor='hand2',
            width=12
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        tk.Button(
            action_frame,
            text="▶ Cargar",
            command=self._on_load_click,
            bg=ModernTheme.SECONDARY,
            fg=ModernTheme.TEXT_PRIMARY,
            font=('Segoe UI', 9, 'bold'),
            relief=tk.FLAT,
            cursor='hand2',
            width=12
        ).pack(side=tk.LEFT)
    
    # === Eventos internos ===
    
    def _on_select(self, event):
        """Maneja la selección de una canción"""
        selection = self.song_listbox.curselection()
        if not selection:
            return
        
        idx = selection[0]
        if idx >= len(self.recent_songs):
            return
        
        path = self.recent_songs[idx]
        filename = os.path.basename(path)
        
        self.preview_label.config(
            text=f"📄 {filename}\nDoble-click para cargar"
        )
        
        # Llamar callback externo
        if 'on_select' in self.callbacks:
            self.callbacks['on_select'](path)
    
    def _on_double_click(self, event):
        """Maneja el doble click (carga la canción)"""
        self._on_load_click()
    
    def _on_load_click(self):
        """Maneja el click en botón Cargar"""
        selection = self.song_listbox.curselection()
        if not selection:
            messagebox.showwarning("Aviso", "Selecciona una canción primero")
            return
        
        idx = selection[0]
        if idx >= len(self.recent_songs):
            return
        
        path = self.recent_songs[idx]
        
        # Llamar callback externo
        if 'on_load' in self.callbacks:
            self.callbacks['on_load'](path)
    
    def _on_browse(self):
        """Maneja el click en botón Buscar"""
        files = filedialog.askopenfilenames(
            title="Seleccionar archivos MIDI",
            filetypes=[("MIDI files", "*.mid *.midi"), ("All files", "*.*")]
        )
        
        if files and 'on_browse' in self.callbacks:
            self.callbacks['on_browse'](list(files))
    
    # === Métodos públicos ===
    
    def set_songs(self, songs):
        """Establece la lista de canciones"""
        self.recent_songs = songs
        self.refresh()
    
    def add_song(self, path):
        """Añade una canción a la lista"""
        if path not in self.recent_songs:
            self.recent_songs.insert(0, path)
            self.recent_songs = self.recent_songs[:10]  # Máximo 10
            self.refresh()
    
    def refresh(self):
        """Refresca la lista visual de canciones"""
        self.song_listbox.delete(0, tk.END)
        for song in self.recent_songs:
            name = os.path.basename(song)
            self.song_listbox.insert(tk.END, f"🎵 {name}")
    
    def get_selected_song(self):
        """Retorna la ruta de la canción seleccionada"""
        selection = self.song_listbox.curselection()
        if not selection:
            return None
        
        idx = selection[0]
        if idx >= len(self.recent_songs):
            return None
        
        return self.recent_songs[idx]
