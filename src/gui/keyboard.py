"""
Componente Keyboard - Teclado virtual interactivo
"""
import tkinter as tk
from ..modern_theme import ModernTheme


class KeyboardComponent:
    """Componente de teclado virtual con soporte para digitación"""
    
    def __init__(self, parent, callbacks, num_keys=61, show_fingering=False):
        """
        Args:
            parent: Widget padre
            callbacks: Dict con funciones callback:
                - on_key_click: Cuando se hace click en una tecla
            num_keys: Número de teclas (25, 37, 49, 61, 76, 88)
            show_fingering: Si mostrar números de dedos
        """
        self.parent = parent
        self.callbacks = callbacks
        self.num_keys = num_keys
        self.show_fingering = show_fingering
        self.key_rectangles = {}  # {note: (x1, y1, x2, y2, is_black, rect_id)}
        
        # Colores de digitación (mano derecha)
        self.finger_colors = {
            1: '#00FFFF',  # Cyan - Pulgar
            2: '#0099FF',  # Azul cielo - Índice
            3: '#0033FF',  # Azul marino - Medio
            4: '#6600FF',  # Violeta - Anular
            5: '#FF00FF'   # Magenta - Meñique
        }
        
        # Crear frame principal
        self.frame = tk.Frame(parent, bg=ModernTheme.BG_CARD, height=150)
        self.frame.pack(fill=tk.X, pady=(0, 10))
        self.frame.pack_propagate(False)
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Crea el canvas del teclado"""
        # Título
        tk.Label(
            self.frame,
            text="🎹 Teclado Virtual",
            font=('Segoe UI', 10, 'bold'),
            bg=ModernTheme.BG_CARD,
            fg=ModernTheme.TEXT_PRIMARY
        ).pack(pady=(8, 5), padx=10, anchor=tk.W)
        
        # Canvas
        self.canvas = tk.Canvas(
            self.frame,
            bg=ModernTheme.BG_LIGHT,
            highlightthickness=0,
            height=110
        )
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        self.canvas.bind('<Button-1>', self._on_click)
        self.canvas.bind('<Configure>', lambda e: self.draw())
    
    def draw(self):
        """Dibuja el teclado completo"""
        self.canvas.delete('all')
        self.key_rectangles.clear()
        
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        
        if w < 2:
            return
        
        # Calcular dimensiones
        keys_to_white = {25: 15, 37: 22, 49: 29, 61: 36, 76: 45, 88: 52}
        num_white = keys_to_white.get(self.num_keys, 36)
        
        white_width = w / num_white
        black_width = white_width * 0.6
        black_height = h * 0.6
        
        # Nota inicial según número de teclas
        start_notes = {25: 48, 37: 48, 49: 36, 61: 36, 76: 28, 88: 21}
        start_note = start_notes.get(self.num_keys, 36)
        
        # Dibujar teclas blancas primero
        white_positions = self._draw_white_keys(num_white, white_width, h, start_note)
        
        # Dibujar teclas negras encima
        self._draw_black_keys(white_positions, black_width, black_height)
    
    def _draw_white_keys(self, num_white, white_width, height, start_note):
        """Dibuja todas las teclas blancas"""
        white_positions = []
        
        for i in range(num_white):
            x1 = i * white_width
            x2 = x1 + white_width
            
            # Calcular nota MIDI
            octave = i // 7
            note_in_octave = i % 7
            white_notes = [0, 2, 4, 5, 7, 9, 11]  # C D E F G A B
            midi_note = start_note + (octave * 12) + white_notes[note_in_octave]
            
            # Color de la tecla
            if self.show_fingering:
                finger = self._get_finger_for_note(midi_note)
                if finger:
                    key_color = self._lighten_color(self.finger_colors[finger], 0.7)
                else:
                    key_color = 'white'
            else:
                key_color = 'white'
            
            # Dibujar tecla
            rect_id = self.canvas.create_rectangle(
                x1, 0, x2, height,
                fill=key_color,
                outline='#cbd5e0',
                width=1,
                tags=(f'key_{midi_note}', 'white_key')
            )
            
            self.key_rectangles[midi_note] = (x1, 0, x2, height, False, rect_id)
            white_positions.append((i, x1, x2, midi_note))
            
            # Mostrar número de dedo si está activo
            if self.show_fingering:
                finger = self._get_finger_for_note(midi_note)
                if finger:
                    self.canvas.create_text(
                        (x1 + x2) / 2, height - 15,
                        text=str(finger),
                        font=('Arial', 10, 'bold'),
                        fill=self.finger_colors[finger]
                    )
        
        return white_positions
    
    def _draw_black_keys(self, white_positions, black_width, black_height):
        """Dibuja todas las teclas negras"""
        # Patrón de teclas negras: C# D# _ F# G# A# _
        black_pattern = [True, True, False, True, True, True, False]
        
        for i, x1, x2, white_midi in white_positions:
            if i >= len(white_positions) - 1:
                continue
            
            note_in_octave = i % 7
            if black_pattern[note_in_octave]:
                # Posición centrada entre dos teclas blancas
                black_x1 = x2 - (black_width / 2)
                black_x2 = black_x1 + black_width
                
                # Nota MIDI para tecla negra (un semitono arriba)
                black_midi = white_midi + 1
                
                # Color
                if self.show_fingering:
                    finger = self._get_finger_for_note(black_midi)
                    if finger:
                        key_color = self._lighten_color(self.finger_colors[finger], 0.3)
                    else:
                        key_color = '#2d3748'
                else:
                    key_color = '#2d3748'
                
                # Dibujar tecla negra
                rect_id = self.canvas.create_rectangle(
                    black_x1, 0, black_x2, black_height,
                    fill=key_color,
                    outline='#1a202c',
                    width=1,
                    tags=(f'key_{black_midi}', 'black_key')
                )
                
                self.key_rectangles[black_midi] = (black_x1, 0, black_x2, black_height, True, rect_id)
                
                # Número de dedo
                if self.show_fingering:
                    finger = self._get_finger_for_note(black_midi)
                    if finger:
                        self.canvas.create_text(
                            (black_x1 + black_x2) / 2, black_height - 15,
                            text=str(finger),
                            font=('Arial', 9, 'bold'),
                            fill='white'
                        )
    
    def _on_click(self, event):
        """Maneja el click en el teclado"""
        x, y = event.x, event.y
        
        # Buscar primero en teclas negras (tienen prioridad)
        clicked = None
        for note, data in self.key_rectangles.items():
            x1, y1, x2, y2, is_black, rect_id = data
            if is_black and x1 <= x <= x2 and y1 <= y <= y2:
                clicked = note
                break
        
        # Si no, buscar en teclas blancas
        if not clicked:
            for note, data in self.key_rectangles.items():
                x1, y1, x2, y2, is_black, rect_id = data
                if not is_black and x1 <= x <= x2 and y1 <= y <= y2:
                    clicked = note
                    break
        
        # Notificar callback
        if clicked and 'on_key_click' in self.callbacks:
            self.callbacks['on_key_click'](clicked)
    
    # === Métodos públicos ===
    
    def highlight_key(self, note, color=None):
        """Ilumina una tecla con un color específico"""
        if note not in self.key_rectangles:
            return
        
        if color is None:
            is_black = self.key_rectangles[note][4]
            color = '#ffd700' if not is_black else '#ffaa00'
        
        rect_id = self.key_rectangles[note][5]
        self.canvas.itemconfig(rect_id, fill=color)
    
    def restore_key(self, note):
        """Restaura el color original de una tecla"""
        if note not in self.key_rectangles:
            return
        
        is_black = self.key_rectangles[note][4]
        rect_id = self.key_rectangles[note][5]
        
        # Color según digitación o default
        if self.show_fingering:
            finger = self._get_finger_for_note(note)
            if finger:
                factor = 0.3 if is_black else 0.7
                color = self._lighten_color(self.finger_colors[finger], factor)
            else:
                color = '#2d3748' if is_black else 'white'
        else:
            color = '#2d3748' if is_black else 'white'
        
        self.canvas.itemconfig(rect_id, fill=color)
    
    def set_num_keys(self, num_keys):
        """Cambia el número de teclas y redibuja"""
        self.num_keys = num_keys
        self.draw()
    
    def set_fingering(self, show):
        """Activa/desactiva la visualización de digitación"""
        self.show_fingering = show
        self.draw()
    
    # === Métodos privados auxiliares ===
    
    def _get_finger_for_note(self, note):
        """Devuelve el dedo sugerido para una nota (1-5)"""
        note_in_octave = note % 12
        pattern = {
            0: 1, 2: 2, 4: 3, 5: 1, 7: 2, 9: 3, 11: 4,  # Blancas
            1: 2, 3: 3, 6: 2, 8: 3, 10: 4  # Negras
        }
        return pattern.get(note_in_octave, None)
    
    def _lighten_color(self, hex_color, factor=0.5):
        """Aclara un color hex"""
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        
        r = int(r + (255 - r) * factor)
        g = int(g + (255 - g) * factor)
        b = int(b + (255 - b) * factor)
        
        return f'#{r:02x}{g:02x}{b:02x}'
