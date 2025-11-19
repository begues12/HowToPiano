"""
Módulo GUI - Componentes de interfaz separados por funcionalidad
"""

from .header import HeaderComponent
from .library import LibraryComponent
from .score import ScoreComponent
from .keyboard import KeyboardComponent
from .stats import StatsComponent
from .settings import SettingsDialog

__all__ = [
    'HeaderComponent',
    'LibraryComponent',
    'ScoreComponent',
    'KeyboardComponent',
    'StatsComponent',
    'SettingsDialog'
]
