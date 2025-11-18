"""
MIDI Input Detector - Detecta cuando el usuario toca las teclas correctas
Compatible con teclados MIDI conectados por USB
"""
import time
from typing import Optional, Callable, Set
try:
    import mido
    from mido import Message
    MIDO_AVAILABLE = True
except ImportError:
    MIDO_AVAILABLE = False
    print("⚠ mido no disponible - detección MIDI deshabilitada")


class MidiInputDetector:
    """Detecta input MIDI del teclado del usuario"""
    
    def __init__(self, port_name: Optional[str] = None):
        """
        Inicializa detector de input MIDI
        
        Args:
            port_name: Nombre del puerto MIDI (None = autodetectar)
        """
        self.port = None
        self.active_notes: Set[int] = set()
        self.note_callback: Optional[Callable] = None
        
        if MIDO_AVAILABLE:
            self._connect(port_name)
        else:
            print("⚠ Modo sin detección MIDI - usa Enter manual")
    
    def _connect(self, port_name: Optional[str] = None):
        """Conecta al puerto MIDI"""
        try:
            available_ports = mido.get_input_names()
            
            if not available_ports:
                print("⚠ No se encontraron puertos MIDI de entrada")
                return
            
            print(f"📌 Puertos MIDI disponibles:")
            for i, port in enumerate(available_ports, 1):
                print(f"  {i}. {port}")
            
            # Seleccionar puerto
            if port_name:
                target_port = port_name
            elif len(available_ports) == 1:
                target_port = available_ports[0]
                print(f"✓ Usando puerto: {target_port}")
            else:
                print("\nSelecciona puerto (0 para ninguno):")
                choice = input("> ").strip()
                if choice == '0' or not choice:
                    return
                idx = int(choice) - 1
                if 0 <= idx < len(available_ports):
                    target_port = available_ports[idx]
                else:
                    print("✗ Selección inválida")
                    return
            
            self.port = mido.open_input(target_port)
            print(f"✓ Conectado a: {target_port}")
            
        except Exception as e:
            print(f"✗ Error conectando MIDI: {e}")
    
    def listen(self, timeout: float = 0.01) -> Optional[Message]:
        """
        Escucha mensajes MIDI (no bloqueante)
        
        Args:
            timeout: Tiempo máximo de espera
            
        Returns:
            Mensaje MIDI o None
        """
        if not self.port:
            return None
        
        try:
            for msg in self.port.iter_pending():
                if msg.type in ['note_on', 'note_off']:
                    self._process_message(msg)
                    return msg
        except Exception as e:
            print(f"⚠ Error leyendo MIDI: {e}")
        
        return None
    
    def _process_message(self, msg: Message):
        """Procesa mensaje MIDI y actualiza estado"""
        if msg.type == 'note_on' and msg.velocity > 0:
            self.active_notes.add(msg.note)
            if self.note_callback:
                self.note_callback(msg.note, True)
        elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
            self.active_notes.discard(msg.note)
            if self.note_callback:
                self.note_callback(msg.note, False)
    
    def wait_for_note(self, expected_note: int, timeout: float = 30.0) -> bool:
        """
        Espera a que se toque una nota específica
        
        Args:
            expected_note: Nota MIDI esperada
            timeout: Tiempo máximo de espera
            
        Returns:
            True si se tocó la nota correcta
        """
        if not self.port:
            # Modo manual sin MIDI
            return True
        
        start_time = time.time()
        
        while (time.time() - start_time) < timeout:
            msg = self.listen()
            
            if msg and msg.type == 'note_on' and msg.velocity > 0:
                if msg.note == expected_note:
                    return True
                else:
                    # Nota incorrecta
                    return False
            
            time.sleep(0.01)
        
        return False  # Timeout
    
    def is_note_active(self, note: int) -> bool:
        """Verifica si una nota está actualmente presionada"""
        return note in self.active_notes
    
    def get_active_notes(self) -> Set[int]:
        """Obtiene todas las notas actualmente presionadas"""
        return self.active_notes.copy()
    
    def set_note_callback(self, callback: Callable):
        """
        Configura callback para eventos de nota
        
        Args:
            callback: Función(note: int, is_on: bool)
        """
        self.note_callback = callback
    
    def close(self):
        """Cierra conexión MIDI"""
        if self.port:
            self.port.close()
            print("🔌 Puerto MIDI cerrado")
    
    @staticmethod
    def list_ports():
        """Lista puertos MIDI disponibles"""
        if not MIDO_AVAILABLE:
            print("⚠ mido no disponible")
            return []
        
        print("\n📌 Puertos MIDI de entrada:")
        ports = mido.get_input_names()
        for i, port in enumerate(ports, 1):
            print(f"  {i}. {port}")
        
        return ports


class KeyboardInputDetector:
    """Detector alternativo usando teclado de computadora (para testing)"""
    
    NOTE_MAP = {
        'a': 60,  # C4
        's': 62,  # D4
        'd': 64,  # E4
        'f': 65,  # F4
        'g': 67,  # G4
        'h': 69,  # A4
        'j': 71,  # B4
        'k': 72,  # C5
    }
    
    def __init__(self):
        """Inicializa detector de teclado"""
        print("\n⌨️  Modo teclado de computadora:")
        print("   a=C, s=D, d=E, f=F, g=G, h=A, j=B, k=C")
    
    def wait_for_note(self, expected_note: int) -> bool:
        """Espera input de teclado"""
        from src.note_mapper import NoteMapper
        mapper = NoteMapper('piano_88')
        expected_name = mapper.get_note_name(expected_note)
        
        print(f"\n👆 Toca {expected_name} (nota {expected_note})")
        print("   o presiona la tecla correspondiente:")
        
        # Buscar tecla correspondiente
        for key, note in self.NOTE_MAP.items():
            if note == expected_note:
                print(f"   → Presiona '{key}'")
                break
        
        try:
            key = input("> ").strip().lower()
            
            if key in self.NOTE_MAP:
                pressed_note = self.NOTE_MAP[key]
                return pressed_note == expected_note
            
            return False
            
        except KeyboardInterrupt:
            return False


if __name__ == "__main__":
    print("=== Test del detector MIDI ===\n")
    
    # Listar puertos
    MidiInputDetector.list_ports()
    
    # Test básico
    print("\nCreando detector...")
    detector = MidiInputDetector()
    
    if detector.port:
        print("\n🎹 Toca algunas teclas (10 segundos)...")
        start = time.time()
        
        while time.time() - start < 10:
            msg = detector.listen()
            if msg:
                print(f"  {msg.type}: nota {msg.note}")
            time.sleep(0.01)
        
        detector.close()
    else:
        print("\n⚠ No hay puerto MIDI conectado")
        print("Usa KeyboardInputDetector para testing")
