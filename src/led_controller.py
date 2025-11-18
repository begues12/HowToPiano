"""
LED Controller - Controla tiras LED WS2812B/WS2813 desde Raspberry Pi
"""
import time
from typing import Tuple, Optional
try:
    import board
    import neopixel
except ImportError:
    print("⚠ Librería neopixel no disponible. Modo simulación activado.")
    board = None
    neopixel = None


class LEDController:
    """Controlador para tiras LED WS2812B/WS2813"""
    
    # Colores predefinidos (R, G, B)
    COLOR_OFF = (0, 0, 0)
    COLOR_NOTE_ON = (255, 50, 0)      # Naranja brillante
    COLOR_NOTE_ACTIVE = (0, 255, 100) # Verde-azul
    COLOR_STANDBY = (10, 10, 30)      # Azul tenue
    
    def __init__(self, num_leds: int = 88, pin: int = 18, brightness: float = 0.3, 
                 auto_write: bool = True, simulate: bool = False):
        """
        Inicializa el controlador LED
        
        Args:
            num_leds: Número de LEDs en la tira (88 para piano completo)
            pin: Pin GPIO (por defecto GPIO 18 / Pin 12)
            brightness: Brillo de 0.0 a 1.0
            auto_write: Si True, actualiza LEDs inmediatamente
            simulate: Modo simulación para testing sin hardware
        """
        self.num_leds = num_leds
        self.brightness = brightness
        self.simulate = simulate or (neopixel is None)
        
        if not self.simulate:
            try:
                # Configurar la tira LED
                pin_obj = getattr(board, f'D{pin}')
                self.pixels = neopixel.NeoPixel(
                    pin_obj, 
                    num_leds, 
                    brightness=brightness,
                    auto_write=auto_write,
                    pixel_order=neopixel.GRB
                )
                print(f"✓ Tira LED inicializada: {num_leds} LEDs en GPIO{pin}")
            except Exception as e:
                print(f"✗ Error inicializando LEDs, modo simulación: {e}")
                self.simulate = True
        else:
            print(f"⚠ Modo simulación: {num_leds} LEDs virtuales")
            # Array para simular estado de LEDs
            self.pixels = [(0, 0, 0) for _ in range(num_leds)]
    
    def set_led(self, index: int, color: Tuple[int, int, int]):
        """
        Enciende un LED específico con un color
        
        Args:
            index: Índice del LED (0 a num_leds-1)
            color: Tupla RGB (r, g, b) con valores 0-255
        """
        if 0 <= index < self.num_leds:
            if self.simulate:
                self.pixels[index] = color
            else:
                self.pixels[index] = color
        else:
            print(f"⚠ LED {index} fuera de rango (0-{self.num_leds-1})")
    
    def set_led_on(self, index: int, color: Optional[Tuple[int, int, int]] = None):
        """
        Enciende un LED (nota activa)
        
        Args:
            index: Índice del LED
            color: Color personalizado (opcional)
        """
        color = color or self.COLOR_NOTE_ON
        self.set_led(index, color)
    
    def set_led_off(self, index: int):
        """
        Apaga un LED (nota desactivada)
        
        Args:
            index: Índice del LED
        """
        self.set_led(index, self.COLOR_OFF)
    
    def set_all(self, color: Tuple[int, int, int]):
        """
        Establece todos los LEDs al mismo color
        
        Args:
            color: Tupla RGB
        """
        if self.simulate:
            self.pixels = [color] * self.num_leds
        else:
            self.pixels.fill(color)
    
    def clear_all(self):
        """Apaga todos los LEDs"""
        self.set_all(self.COLOR_OFF)
    
    def set_brightness(self, brightness: float):
        """
        Ajusta el brillo global
        
        Args:
            brightness: Valor de 0.0 a 1.0
        """
        self.brightness = max(0.0, min(1.0, brightness))
        if not self.simulate:
            self.pixels.brightness = self.brightness
        print(f"✓ Brillo ajustado: {self.brightness * 100:.0f}%")
    
    def test_sequence(self, delay: float = 0.05):
        """
        Secuencia de prueba: recorre todos los LEDs
        
        Args:
            delay: Tiempo entre LEDs en segundos
        """
        print("▶ Iniciando secuencia de prueba...")
        
        # Encender uno por uno
        for i in range(self.num_leds):
            self.set_led_on(i)
            time.sleep(delay)
            self.set_led_off(i)
        
        # Flash completo
        for _ in range(3):
            self.set_all(self.COLOR_NOTE_ON)
            time.sleep(0.2)
            self.clear_all()
            time.sleep(0.2)
        
        print("✓ Secuencia de prueba completada")
    
    def rainbow_effect(self, duration: float = 5.0):
        """
        Efecto arcoíris en toda la tira
        
        Args:
            duration: Duración del efecto en segundos
        """
        print("▶ Efecto arcoíris...")
        steps = 256
        delay = duration / steps
        
        for j in range(steps):
            for i in range(self.num_leds):
                pixel_index = (i * 256 // self.num_leds) + j
                color = self._wheel(pixel_index & 255)
                self.set_led(i, color)
            time.sleep(delay)
        
        self.clear_all()
    
    def _wheel(self, pos: int) -> Tuple[int, int, int]:
        """
        Genera color de rueda arcoíris (0-255)
        
        Args:
            pos: Posición en la rueda (0-255)
            
        Returns:
            Color RGB
        """
        if pos < 85:
            return (pos * 3, 255 - pos * 3, 0)
        elif pos < 170:
            pos -= 85
            return (255 - pos * 3, 0, pos * 3)
        else:
            pos -= 170
            return (0, pos * 3, 255 - pos * 3)
    
    def set_range(self, start: int, end: int, color: Tuple[int, int, int]):
        """
        Establece un rango de LEDs al mismo color
        
        Args:
            start: LED inicial
            end: LED final (inclusivo)
            color: Color RGB
        """
        for i in range(start, min(end + 1, self.num_leds)):
            self.set_led(i, color)
    
    def fade_out(self, duration: float = 1.0, steps: int = 20):
        """
        Desvanece todos los LEDs gradualmente
        
        Args:
            duration: Duración total del fade
            steps: Número de pasos del fade
        """
        if self.simulate:
            self.clear_all()
            return
        
        delay = duration / steps
        for step in range(steps, 0, -1):
            factor = step / steps
            self.pixels.brightness = self.brightness * factor
            time.sleep(delay)
        
        self.clear_all()
        self.pixels.brightness = self.brightness
    
    def cleanup(self):
        """Limpia y apaga todos los LEDs"""
        print("🔌 Apagando LEDs...")
        self.clear_all()


if __name__ == "__main__":
    # Ejemplo de uso
    print("=== Test del controlador LED ===\n")
    
    # Crear controlador (modo simulación para testing)
    controller = LEDController(num_leds=88, simulate=True)
    
    # Prueba básica
    print("\n1. Encendiendo LED 0...")
    controller.set_led_on(0)
    time.sleep(0.5)
    controller.set_led_off(0)
    
    print("\n2. Encendiendo rango (20-30)...")
    controller.set_range(20, 30, LEDController.COLOR_NOTE_ACTIVE)
    time.sleep(1)
    controller.clear_all()
    
    print("\n3. Ajustando brillo...")
    controller.set_brightness(0.5)
    
    print("\n4. Test completo...")
    controller.test_sequence(delay=0.01)
    
    print("\n✓ Test completado")
