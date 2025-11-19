"""
Componente Score - Visualización de partitura musical
"""
import tkinter as tk
from ..modern_theme import ModernTheme
from ..music_score import MusicScore


class ScoreComponent:
    """Componente de partitura musical con barra de progreso"""
    
    def __init__(self, parent, callbacks):
        """
        Args:
            parent: Widget padre
            callbacks: Dict con funciones callback:
                - on_progress_click: Cuando se hace click en la barra de progreso
        """
        self.parent = parent
        self.callbacks = callbacks
        
        # Crear frame principal
        self.frame = tk.Frame(parent, bg=ModernTheme.BG_CARD, height=380)
        self.frame.pack(fill=tk.X, pady=(0, 10))
        self.frame.pack_propagate(False)
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Crea todos los widgets de la partitura"""
        # Título
        tk.Label(
            self.frame,
            text="🎼 Partitura Musical",
            font=('Segoe UI', 11, 'bold'),
            bg=ModernTheme.BG_CARD,
            fg=ModernTheme.TEXT_PRIMARY
        ).pack(pady=(8, 5), padx=10, anchor=tk.W)
        
        # Barra de progreso con seek
        self._create_progress_bar()
        
        # Canvas de partitura
        self.canvas = tk.Canvas(
            self.frame,
            bg='white',
            highlightthickness=0,
            height=300
        )
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Inicializar MusicScore
        self.music_score = MusicScore(self.canvas)
        self.canvas.bind('<Configure>', lambda e: self.music_score.render())
    
    def _create_progress_bar(self):
        """Crea la barra de progreso clickeable"""
        progress_frame = tk.Frame(self.frame, bg=ModernTheme.BG_CARD)
        progress_frame.pack(fill=tk.X, padx=10, pady=(0, 5))
        
        self.progress_canvas = tk.Canvas(
            progress_frame,
            bg=ModernTheme.BG_LIGHT,
            highlightthickness=1,
            highlightbackground=ModernTheme.TEXT_MUTED,
            height=25,
            cursor='hand2'
        )
        self.progress_canvas.pack(fill=tk.X)
        self.progress_canvas.bind('<Button-1>', self._on_progress_click)
        
        # Label de porcentaje
        self.progress_text_label = tk.Label(
            progress_frame,
            text="0%",
            font=('Segoe UI', 8, 'bold'),
            bg=ModernTheme.BG_CARD,
            fg=ModernTheme.TEXT_PRIMARY
        )
        self.progress_text_label.place(
            in_=self.progress_canvas, 
            relx=0.5, 
            rely=0.5, 
            anchor=tk.CENTER
        )
    
    def _on_progress_click(self, event):
        """Maneja el click en la barra de progreso"""
        if 'on_progress_click' in self.callbacks:
            w = self.progress_canvas.winfo_width()
            if w > 0:
                percent = (event.x / w) * 100
                self.callbacks['on_progress_click'](percent)
    
    # === Métodos públicos ===
    
    def load_notes(self, note_events, metadata):
        """Carga las notas en la partitura"""
        self.music_score.load_notes(note_events, metadata)
        self.music_score.render()
    
    def update_time(self, current_time_ms):
        """Actualiza la posición de scroll de la partitura"""
        self.music_score.update_time(current_time_ms)
        self.music_score.render()
    
    def update_progress(self, percent):
        """Actualiza la barra de progreso visual"""
        self.progress_canvas.delete('all')
        w = self.progress_canvas.winfo_width()
        h = self.progress_canvas.winfo_height()
        
        if w > 2:
            # Barra de fondo
            self.progress_canvas.create_rectangle(
                0, 0, w, h,
                fill=ModernTheme.BG_LIGHT,
                outline=''
            )
            
            # Barra de progreso
            progress_w = (w * percent) / 100
            self.progress_canvas.create_rectangle(
                0, 0, progress_w, h,
                fill=ModernTheme.PRIMARY,
                outline=''
            )
        
        # Actualizar texto
        self.progress_text_label.config(text=f"{int(percent)}%")
    
    def reset(self):
        """Resetea la partitura al inicio"""
        self.update_time(0)
        self.update_progress(0)
