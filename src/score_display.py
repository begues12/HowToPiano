"""
Score Display - Muestra partituras en pantalla y guía al usuario
Sistema de aprendizaje interactivo paso a paso
"""
import time
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from mido import MidiFile, Message

# curses no está disponible en Windows
try:
    import curses
    CURSES_AVAILABLE = True
except ImportError:
    CURSES_AVAILABLE = False


@dataclass
class NoteEvent:
    """Evento de nota con timing"""
    note: int
    velocity: int
    start_time: float
    duration: float
    note_name: str
    is_on: bool = True


class ScoreDisplay:
    """Muestra partituras y guía el aprendizaje paso a paso"""
    
    def __init__(self, midi_file: MidiFile, note_mapper):
        """
        Inicializa el display de partituras
        
        Args:
            midi_file: Archivo MIDI cargado
            note_mapper: Mapeador de notas a LEDs
        """
        self.midi_file = midi_file
        self.note_mapper = note_mapper
        self.note_events: List[NoteEvent] = []
        self.current_index = 0
        self._parse_notes()
        
    def _parse_notes(self):
        """Parsea el archivo MIDI y extrae todos los eventos de nota"""
        current_time = 0.0
        active_notes = {}  # {note: start_time}
        
        for msg in self.midi_file:
            current_time += msg.time
            
            if msg.type == 'note_on' and msg.velocity > 0:
                # Nota comienza
                active_notes[msg.note] = current_time
                
            elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                # Nota termina
                if msg.note in active_notes:
                    start_time = active_notes[msg.note]
                    duration = current_time - start_time
                    
                    note_event = NoteEvent(
                        note=msg.note,
                        velocity=msg.velocity,
                        start_time=start_time,
                        duration=duration,
                        note_name=self.note_mapper.get_note_name(msg.note)
                    )
                    self.note_events.append(note_event)
                    del active_notes[msg.note]
        
        # Ordenar por tiempo
        self.note_events.sort(key=lambda x: x.start_time)
        print(f"✓ {len(self.note_events)} notas parseadas")
    
    def get_upcoming_notes(self, count: int = 5) -> List[NoteEvent]:
        """
        Obtiene las próximas notas a tocar
        
        Args:
            count: Número de notas a mostrar
            
        Returns:
            Lista de próximos eventos
        """
        end_idx = min(self.current_index + count, len(self.note_events))
        return self.note_events[self.current_index:end_idx]
    
    def get_current_note(self) -> Optional[NoteEvent]:
        """Obtiene la nota actual a tocar"""
        if self.current_index < len(self.note_events):
            return self.note_events[self.current_index]
        return None
    
    def advance_note(self):
        """Avanza a la siguiente nota"""
        if self.current_index < len(self.note_events):
            self.current_index += 1
    
    def reset(self):
        """Reinicia el progreso"""
        self.current_index = 0
    
    def get_progress(self) -> Tuple[int, int, float]:
        """
        Obtiene el progreso actual
        
        Returns:
            Tupla (notas_tocadas, total_notas, porcentaje)
        """
        total = len(self.note_events)
        progress_pct = (self.current_index / total * 100) if total > 0 else 0
        return (self.current_index, total, progress_pct)
    
    def print_console_display(self):
        """Muestra información en consola (modo simple)"""
        print("\n" + "=" * 60)
        print("🎼 PARTITURA - Modo Práctica")
        print("=" * 60)
        
        current = self.get_current_note()
        if current:
            print(f"\n🎯 NOTA ACTUAL: {current.note_name} (MIDI {current.note})")
            print(f"   Duración: {current.duration:.2f}s")
            
            # Representación visual de la tecla
            led_idx = self.note_mapper.note_to_led(current.note)
            if led_idx is not None:
                print(f"   LED: {led_idx}")
                is_white = self.note_mapper._is_white_key(current.note)
                key_type = "⬜ Blanca" if is_white else "⬛ Negra"
                print(f"   Tecla: {key_type}")
        else:
            print("\n✓ ¡Partitura completada!")
        
        # Mostrar próximas notas
        upcoming = self.get_upcoming_notes(5)
        if len(upcoming) > 1:
            print(f"\n📋 Próximas notas:")
            for i, note in enumerate(upcoming[1:], 1):
                print(f"   {i}. {note.note_name}")
        
        # Barra de progreso
        played, total, pct = self.get_progress()
        bar_length = 40
        filled = int(bar_length * pct / 100)
        bar = "█" * filled + "░" * (bar_length - filled)
        print(f"\n📊 Progreso: [{bar}] {pct:.1f}%")
        print(f"   Notas: {played}/{total}")
        print("=" * 60)
    
    def display_terminal_ui(self, stdscr):
        """
        Interfaz de terminal con curses (más visual)
        
        Args:
            stdscr: Pantalla de curses
        """
        curses.curs_set(0)  # Ocultar cursor
        stdscr.nodelay(1)   # No bloquear en getch()
        
        # Colores
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_RED, curses.COLOR_BLACK)
        
        while self.current_index < len(self.note_events):
            stdscr.clear()
            height, width = stdscr.getmaxyx()
            
            # Título
            title = "🎹 HowToPiano - Modo Aprendizaje"
            stdscr.addstr(0, (width - len(title)) // 2, title, 
                         curses.color_pair(1) | curses.A_BOLD)
            
            # Nota actual
            current = self.get_current_note()
            if current:
                stdscr.addstr(3, 2, "🎯 TOCA AHORA:", curses.color_pair(2) | curses.A_BOLD)
                
                # Nota grande
                note_display = f"  {current.note_name}  "
                stdscr.addstr(5, (width - len(note_display)) // 2, note_display,
                            curses.color_pair(2) | curses.A_BOLD | curses.A_REVERSE)
                
                # Detalles
                stdscr.addstr(7, 2, f"MIDI: {current.note}")
                stdscr.addstr(8, 2, f"Duración: {current.duration:.2f}s")
                
                led_idx = self.note_mapper.note_to_led(current.note)
                if led_idx is not None:
                    stdscr.addstr(9, 2, f"LED: {led_idx}")
                
                is_white = self.note_mapper._is_white_key(current.note)
                key_type = "⬜ Blanca" if is_white else "⬛ Negra"
                stdscr.addstr(10, 2, f"Tecla: {key_type}")
            
            # Próximas notas
            upcoming = self.get_upcoming_notes(6)
            if len(upcoming) > 1:
                stdscr.addstr(12, 2, "📋 Próximas notas:", curses.color_pair(3))
                for i, note in enumerate(upcoming[1:6], 1):
                    stdscr.addstr(13 + i, 4, f"{i}. {note.note_name}")
            
            # Barra de progreso
            played, total, pct = self.get_progress()
            progress_y = height - 5
            stdscr.addstr(progress_y, 2, "Progreso:", curses.color_pair(3))
            
            bar_width = width - 4
            filled = int(bar_width * pct / 100)
            bar = "█" * filled + "░" * (bar_width - filled)
            stdscr.addstr(progress_y + 1, 2, bar, curses.color_pair(1))
            stdscr.addstr(progress_y + 2, 2, f"{played}/{total} notas ({pct:.1f}%)")
            
            # Instrucciones
            stdscr.addstr(height - 2, 2, "Presiona ESPACIO para siguiente nota | Q para salir")
            
            stdscr.refresh()
            
            # Esperar input
            key = stdscr.getch()
            if key == ord('q') or key == ord('Q'):
                break
            elif key == ord(' '):
                self.advance_note()
            
            time.sleep(0.05)
    
    def create_piano_roll_ascii(self, window_size: int = 20) -> str:
        """
        Crea representación ASCII tipo piano roll
        
        Args:
            window_size: Número de notas a mostrar
            
        Returns:
            String con piano roll ASCII
        """
        upcoming = self.get_upcoming_notes(window_size)
        if not upcoming:
            return "No hay más notas"
        
        # Encontrar rango de notas
        notes_set = {n.note for n in upcoming}
        min_note = min(notes_set)
        max_note = max(notes_set)
        
        # Crear grid
        lines = []
        lines.append("Piano Roll:")
        lines.append("-" * 50)
        
        for note_num in range(max_note, min_note - 1, -1):
            note_name = self.note_mapper.get_note_name(note_num)
            line = f"{note_name:>4} |"
            
            # Marcar si la nota está en las próximas
            for i, event in enumerate(upcoming):
                if event.note == note_num:
                    if i == 0:
                        line += " ▶"  # Nota actual
                    else:
                        line += " ●"  # Próxima nota
                else:
                    line += " ·"
            
            lines.append(line)
        
        lines.append("-" * 50)
        return "\n".join(lines)


class InteractiveLearning:
    """Sistema de aprendizaje interactivo con detección de input"""
    
    def __init__(self, score_display, led_controller, midi_input=None):
        """
        Inicializa sistema de aprendizaje
        
        Args:
            score_display: Display de partituras
            led_controller: Controlador de LEDs
            midi_input: Puerto MIDI de entrada (opcional)
        """
        self.score_display = score_display
        self.led_controller = led_controller
        self.midi_input = midi_input
        self.waiting_for_note = False
        self.start_time = None
    
    def practice_mode_console(self):
        """Modo práctica en consola (sin detección MIDI)"""
        print("\n🎓 Modo Práctica - Consola")
        print("Presiona Enter después de tocar cada nota\n")
        
        while True:
            # Mostrar partitura
            self.score_display.print_console_display()
            
            current = self.score_display.get_current_note()
            if not current:
                print("\n🎉 ¡Felicidades! Completaste la partitura")
                break
            
            # Iluminar LED correspondiente
            led_idx = self.score_display.note_mapper.note_to_led(current.note)
            if led_idx is not None:
                self.led_controller.set_led_on(led_idx)
            
            # Esperar input
            try:
                input("👆 Toca la nota y presiona Enter... (o 'q' para salir) ")
                self.score_display.advance_note()
                
                # Apagar LED
                if led_idx is not None:
                    self.led_controller.set_led_off(led_idx)
                    
            except KeyboardInterrupt:
                print("\n\n⏸ Práctica interrumpida")
                break
        
        self.led_controller.clear_all()
    
    def practice_mode_terminal_ui(self):
        """Modo práctica con interfaz curses"""
        if not CURSES_AVAILABLE:
            print("⚠ curses no disponible - usando modo consola simple")
            return
        curses.wrapper(self.score_display.display_terminal_ui)


if __name__ == "__main__":
    # Test básico
    print("Test del sistema de partituras...")
    
    from src.midi_reader import MidiReader
    from src.note_mapper import NoteMapper
    from src.led_controller import LEDController
    
    # Crear archivo MIDI de prueba
    from mido import MidiFile, MidiTrack, Message
    
    mid = MidiFile()
    track = MidiTrack()
    mid.tracks.append(track)
    
    # Escala simple
    for note in [60, 62, 64, 65, 67]:
        track.append(Message('note_on', note=note, velocity=64, time=0))
        track.append(Message('note_off', note=note, velocity=64, time=480))
    
    mapper = NoteMapper('piano_88')
    score = ScoreDisplay(mid, mapper)
    
    print(f"✓ Notas en partitura: {len(score.note_events)}")
    print("\nPróximas notas:")
    for note in score.get_upcoming_notes(5):
        print(f"  - {note.note_name} ({note.duration:.2f}s)")
