"""
Componente Stats - Panel de estadísticas de práctica
"""
import tkinter as tk
from ..modern_theme import ModernTheme


class StatsComponent:
    """Componente de estadísticas de práctica"""
    
    def __init__(self, parent):
        """
        Args:
            parent: Widget padre
        """
        self.parent = parent
        
        # Variables de estadísticas
        self.score = 0
        self.accuracy = 100.0
        self.combo = 0
        self.max_combo = 0
        self.notes_played = 0
        self.notes_correct = 0
        self.notes_missed = 0
        self.total_notes = 0
        
        # Crear frame principal
        self.frame = tk.Frame(parent, bg=ModernTheme.BG_CARD, height=80)
        self.frame.pack(fill=tk.X, pady=(0, 10))
        self.frame.pack_propagate(False)
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Crea todos los widgets de estadísticas"""
        # Título
        tk.Label(
            self.frame,
            text="📊 Estadísticas de Práctica",
            font=('Segoe UI', 10, 'bold'),
            bg=ModernTheme.BG_CARD,
            fg=ModernTheme.TEXT_PRIMARY
        ).pack(pady=(8, 5), padx=10, anchor=tk.W)
        
        # Fila de stats
        stats_row = tk.Frame(self.frame, bg=ModernTheme.BG_CARD)
        stats_row.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Score
        self._create_stat_card(
            stats_row, 
            "Score", 
            "0", 
            '#10b981',
            'score_label'
        )
        
        # Precisión
        self._create_stat_card(
            stats_row, 
            "Precisión", 
            "100%", 
            '#3b82f6',
            'accuracy_label'
        )
        
        # Combo
        self._create_stat_card(
            stats_row, 
            "Combo", 
            "0x", 
            '#f59e0b',
            'combo_label'
        )
        
        # Notas tocadas
        self._create_stat_card(
            stats_row, 
            "Notas", 
            "0/0", 
            '#8b5cf6',
            'notes_label',
            is_last=True
        )
    
    def _create_stat_card(self, parent, title, value, color, attr_name, is_last=False):
        """Crea una tarjeta de estadística individual"""
        frame = tk.Frame(
            parent, 
            bg=ModernTheme.BG_LIGHT, 
            relief=tk.FLAT, 
            bd=1
        )
        
        padding = (0, 0) if is_last else (0, 10)
        frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=padding, ipadx=15, ipady=8)
        
        # Título
        tk.Label(
            frame, 
            text=title, 
            font=('Segoe UI', 9), 
            bg=ModernTheme.BG_LIGHT, 
            fg=ModernTheme.TEXT_MUTED, 
            anchor=tk.CENTER
        ).pack(fill=tk.X, pady=(2, 0))
        
        # Valor
        label = tk.Label(
            frame, 
            text=value, 
            font=('Segoe UI', 18, 'bold'), 
            bg=ModernTheme.BG_LIGHT, 
            fg=color, 
            anchor=tk.CENTER
        )
        label.pack(fill=tk.X, pady=(0, 2))
        
        # Guardar referencia
        setattr(self, attr_name, label)
    
    # === Métodos públicos ===
    
    def reset(self, total_notes=0):
        """Resetea todas las estadísticas"""
        self.score = 0
        self.accuracy = 100.0
        self.combo = 0
        self.max_combo = 0
        self.notes_played = 0
        self.notes_correct = 0
        self.notes_missed = 0
        self.total_notes = total_notes
        
        self.update_display()
    
    def add_score(self, points):
        """Añade puntos al score (nota correcta)"""
        self.score += points
        self.combo += 1
        self.notes_correct += 1
        
        if self.combo > self.max_combo:
            self.max_combo = self.combo
        
        self._update_accuracy()
        self.update_display()
    
    def break_combo(self):
        """Rompe el combo (nota incorrecta)"""
        self.combo = 0
        self.notes_missed += 1
        
        self._update_accuracy()
        self.update_display()
    
    def increment_notes_played(self):
        """Incrementa el contador de notas tocadas"""
        self.notes_played += 1
        self.update_display()
    
    def update_display(self):
        """Actualiza la visualización de todas las estadísticas"""
        self.score_label.config(text=str(self.score))
        self.accuracy_label.config(text=f"{int(self.accuracy)}%")
        self.combo_label.config(text=f"{self.combo}x")
        self.notes_label.config(text=f"{self.notes_played}/{self.total_notes}")
    
    def _update_accuracy(self):
        """Recalcula la precisión"""
        notes_attempted = self.notes_correct + self.notes_missed
        if notes_attempted > 0:
            self.accuracy = (self.notes_correct / notes_attempted) * 100
        else:
            self.accuracy = 100.0
    
    # === Getters ===
    
    def get_stats(self):
        """Retorna todas las estadísticas como diccionario"""
        return {
            'score': self.score,
            'accuracy': self.accuracy,
            'combo': self.combo,
            'max_combo': self.max_combo,
            'notes_played': self.notes_played,
            'notes_correct': self.notes_correct,
            'notes_missed': self.notes_missed,
            'total_notes': self.total_notes
        }
