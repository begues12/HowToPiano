"""
HowToPiano - Sistema de iluminación LED sincronizado con MIDI
Para Raspberry Pi Zero W/W2

Sistema interactivo de aprendizaje de piano con:
- Reproducción de archivos MIDI desde USB
- Control de tiras LED WS2812B
- Modo aprendizaje paso a paso
- Detección de input MIDI
- Visualización de partituras
"""

__version__ = "2.0.0"
__author__ = "HowToPiano Project"

from .midi_reader import MidiReader
from .led_controller import LEDController
from .note_mapper import NoteMapper
from .score_display import ScoreDisplay, InteractiveLearning
from .midi_input_detector import MidiInputDetector, KeyboardInputDetector

__all__ = [
    'MidiReader',
    'LEDController', 
    'NoteMapper',
    'ScoreDisplay',
    'InteractiveLearning',
    'MidiInputDetector',
    'KeyboardInputDetector'
]
