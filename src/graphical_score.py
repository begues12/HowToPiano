"""
Graphical Score Display - Muestra partituras gráficas (OPCIONAL)
Requiere: pygame o music21
"""
import os
from typing import Optional, List

# Intentar importar librerías gráficas
try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    print("⚠ pygame no disponible - instala con: pip install pygame")

try:
    from music21 import converter, stream
    MUSIC21_AVAILABLE = True
except ImportError:
    MUSIC21_AVAILABLE = False
    print("⚠ music21 no disponible - instala con: pip install music21")


class GraphicalScoreDisplay:
    """
    Muestra partituras de forma gráfica
    
    Opciones:
    1. Pygame - Ventana con pentagrama y notas
    2. Music21 - Genera imágenes de partituras
    3. Piano Roll visual
    """
    
    def __init__(self, width: int = 800, height: int = 600):
        """
        Inicializa display gráfico
        
        Args:
            width: Ancho de ventana
            height: Alto de ventana
        """
        self.width = width
        self.height = height
        self.screen = None
        
        if PYGAME_AVAILABLE:
            self._init_pygame()
    
    def _init_pygame(self):
        """Inicializa pygame"""
        try:
            pygame.init()
            self.screen = pygame.display.set_mode((self.width, self.height))
            pygame.display.set_caption("HowToPiano - Partitura")
            print("✓ Pygame inicializado")
        except Exception as e:
            print(f"✗ Error inicializando pygame: {e}")
    
    def draw_staff(self):
        """Dibuja pentagrama musical"""
        if not PYGAME_AVAILABLE or not self.screen:
            return
        
        BLACK = (0, 0, 0)
        WHITE = (255, 255, 255)
        
        self.screen.fill(WHITE)
        
        # Pentagrama (5 líneas)
        staff_y_start = 200
        line_spacing = 20
        
        for i in range(5):
            y = staff_y_start + (i * line_spacing)
            pygame.draw.line(self.screen, BLACK, (50, y), (self.width - 50, y), 2)
        
        pygame.display.flip()
    
    def draw_note(self, note_name: str, position: int, is_current: bool = False):
        """
        Dibuja una nota en el pentagrama
        
        Args:
            note_name: Nombre de la nota (C4, D#5, etc.)
            position: Posición horizontal
            is_current: Si es la nota actual (resaltada)
        """
        if not PYGAME_AVAILABLE or not self.screen:
            return
        
        BLACK = (0, 0, 0)
        RED = (255, 0, 0)
        
        # Mapeo simple de notas a posición vertical
        note_positions = {
            'C4': 280, 'D4': 270, 'E4': 260, 'F4': 250, 'G4': 240,
            'A4': 230, 'B4': 220, 'C5': 210
        }
        
        y = note_positions.get(note_name, 240)
        x = 100 + (position * 80)
        
        color = RED if is_current else BLACK
        
        # Dibujar nota (círculo simple)
        pygame.draw.circle(self.screen, color, (x, y), 10)
        
        # Plica (línea vertical)
        pygame.draw.line(self.screen, color, (x + 10, y), (x + 10, y - 50), 2)
        
        pygame.display.flip()
    
    def display_pygame_score(self, notes: List[str], current_index: int = 0):
        """
        Muestra partitura completa con pygame
        
        Args:
            notes: Lista de nombres de notas
            current_index: Índice de la nota actual
        """
        if not PYGAME_AVAILABLE:
            print("✗ Pygame no disponible")
            return
        
        self.draw_staff()
        
        # Dibujar notas
        visible_notes = notes[max(0, current_index - 2):current_index + 5]
        
        for i, note in enumerate(visible_notes):
            is_current = (i == min(2, current_index))
            self.draw_note(note, i, is_current)
        
        # Procesar eventos
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return False
        
        return True
    
    def display_piano_roll(self, notes: List[tuple], width: int = 800, height: int = 400):
        """
        Dibuja piano roll tipo Synthesia
        
        Args:
            notes: Lista de tuplas (note, start_time, duration)
            width: Ancho del roll
            height: Alto del roll
        """
        if not PYGAME_AVAILABLE:
            print("✗ Pygame no disponible")
            return
        
        screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("HowToPiano - Piano Roll")
        
        WHITE = (255, 255, 255)
        BLUE = (50, 150, 255)
        BLACK = (0, 0, 0)
        
        screen.fill(BLACK)
        
        # Dibujar teclado en la parte inferior
        key_width = width // 88
        key_height = 80
        
        for i in range(88):
            x = i * key_width
            y = height - key_height
            color = WHITE if i % 2 == 0 else (200, 200, 200)
            pygame.draw.rect(screen, color, (x, y, key_width, key_height), 1)
        
        # Dibujar notas cayendo
        for note, start_time, duration in notes:
            x = (note - 21) * key_width  # Ajustar según nota
            y = height - key_height - (start_time * 50)  # Escala temporal
            h = duration * 50
            
            pygame.draw.rect(screen, BLUE, (x, y, key_width, h))
        
        pygame.display.flip()
        
        # Esperar cierre
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
        
        pygame.quit()
    
    def generate_music21_score(self, midi_file: str, output_file: str = "partitura.png"):
        """
        Genera imagen de partitura con music21
        
        Args:
            midi_file: Ruta al archivo MIDI
            output_file: Nombre del archivo de salida
        """
        if not MUSIC21_AVAILABLE:
            print("✗ music21 no disponible")
            return None
        
        try:
            # Cargar MIDI
            score = converter.parse(midi_file)
            
            # Generar imagen
            score.write('lily.png', fp=output_file)
            print(f"✓ Partitura guardada en: {output_file}")
            return output_file
            
        except Exception as e:
            print(f"✗ Error generando partitura: {e}")
            return None
    
    def display_simple_text_notation(self, notes: List[str], current: int):
        """
        Versión simplificada ASCII (sin librerías gráficas)
        
        Args:
            notes: Lista de nombres de notas
            current: Índice actual
        """
        print("\n" + "=" * 60)
        print("🎼 PARTITURA (Notación Simple)")
        print("=" * 60)
        
        # Mostrar próximas notas en línea
        window = notes[max(0, current - 2):current + 8]
        
        notation = ""
        for i, note in enumerate(window):
            if i == min(2, current):
                notation += f" [{note:^4}] "  # Nota actual resaltada
            else:
                notation += f"  {note:^4}  "
        
        print("\n" + notation)
        print("    " + "   ▲" + " " * (len(window) * 7 - 4))
        print("    Actual\n")
        print("=" * 60)
    
    def close(self):
        """Cierra ventana gráfica"""
        if PYGAME_AVAILABLE and self.screen:
            pygame.quit()


# ============================================
# Versión Minimalista con Tkinter (incluido)
# ============================================

try:
    import tkinter as tk
    from tkinter import Canvas
    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False


class TkinterScoreDisplay:
    """Display simple con Tkinter (no requiere instalación extra)"""
    
    def __init__(self):
        if not TKINTER_AVAILABLE:
            print("✗ Tkinter no disponible")
            return
        
        self.root = tk.Tk()
        self.root.title("HowToPiano - Partitura")
        self.root.geometry("800x400")
        
        self.canvas = Canvas(self.root, width=800, height=400, bg='white')
        self.canvas.pack()
        
        # Label para nota actual
        self.note_label = tk.Label(
            self.root, 
            text="", 
            font=("Arial", 48, "bold"),
            fg="red"
        )
        self.note_label.pack()
        
        # Label para próximas
        self.upcoming_label = tk.Label(
            self.root,
            text="",
            font=("Arial", 16)
        )
        self.upcoming_label.pack()
    
    def update_display(self, current_note: str, upcoming: List[str]):
        """Actualiza display"""
        if not TKINTER_AVAILABLE:
            return
        
        self.note_label.config(text=f"🎯 {current_note}")
        self.upcoming_label.config(text="Próximas: " + " → ".join(upcoming[:5]))
        
        self.root.update()
    
    def run(self):
        """Inicia bucle de Tkinter"""
        if TKINTER_AVAILABLE:
            self.root.mainloop()


# ============================================
# Ejemplo de Uso
# ============================================

if __name__ == "__main__":
    print("=== Test de Displays Gráficos ===\n")
    
    # Verificar disponibilidad
    print("Librerías disponibles:")
    print(f"  Pygame: {'✓' if PYGAME_AVAILABLE else '✗'}")
    print(f"  Music21: {'✓' if MUSIC21_AVAILABLE else '✗'}")
    print(f"  Tkinter: {'✓' if TKINTER_AVAILABLE else '✗'}")
    
    # Test con notas de ejemplo
    notes = ['C4', 'D4', 'E4', 'F4', 'G4', 'A4', 'B4', 'C5']
    
    # Opción 1: Pygame
    if PYGAME_AVAILABLE:
        print("\nTest Pygame:")
        display = GraphicalScoreDisplay()
        display.draw_staff()
        
        import time
        for i, note in enumerate(notes):
            display.draw_note(note, i, i == 2)
            time.sleep(0.5)
        
        time.sleep(2)
        display.close()
    
    # Opción 2: Tkinter
    elif TKINTER_AVAILABLE:
        print("\nUsando Tkinter (simple):")
        tk_display = TkinterScoreDisplay()
        tk_display.update_display('C4', ['D4', 'E4', 'F4'])
        # tk_display.run()  # Descomentar para ver ventana
    
    # Opción 3: Texto simple (siempre funciona)
    else:
        print("\nUsando notación ASCII:")
        display = GraphicalScoreDisplay()
        display.display_simple_text_notation(notes, 2)
