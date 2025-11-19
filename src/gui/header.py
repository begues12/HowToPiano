"""
Componente Header - Barra superior con controles principales
"""
import tkinter as tk
from tkinter import ttk
from ..modern_theme import ModernTheme


class HeaderComponent:
    """Componente de cabecera con controles principales"""
    
    def __init__(self, parent, callbacks):
        """
        Args:
            parent: Widget padre (tk.Tk o tk.Frame)
            callbacks: Dict con funciones callback:
                - on_open: Abrir archivo
                - on_stop: Detener reproducción
                - on_play: Iniciar reproducción
                - on_practice: Modo práctica
                - on_settings: Abrir configuración
                - on_speed_change: Cambio de velocidad
                - on_sound_change: Cambio de sonido
        """
        self.parent = parent
        self.callbacks = callbacks
        
        # Crear frame principal
        self.frame = tk.Frame(parent, bg=ModernTheme.PRIMARY, height=45)
        self.frame.pack(fill=tk.X)
        self.frame.pack_propagate(False)
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Crea todos los widgets del header"""
        # Logo/Título
        tk.Label(
            self.frame,
            text="🎹 HowToPiano",
            font=('Segoe UI', 16, 'bold'),
            bg=ModernTheme.PRIMARY,
            fg=ModernTheme.TEXT_PRIMARY
        ).pack(side=tk.LEFT, padx=15)
        
        # Info de canción
        self._create_song_info()
        
        # Selectores de sonido y velocidad
        self._create_audio_controls()
        
        # Botones de acción
        self._create_action_buttons()
    
    def _create_song_info(self):
        """Crea el panel de información de la canción"""
        song_info_frame = tk.Frame(self.frame, bg=ModernTheme.PRIMARY)
        song_info_frame.pack(side=tk.LEFT, padx=20)
        
        self.song_label = tk.Label(
            song_info_frame,
            text="Sin canción",
            font=('Segoe UI', 10, 'bold'),
            bg=ModernTheme.PRIMARY,
            fg=ModernTheme.TEXT_PRIMARY
        )
        self.song_label.pack(anchor=tk.W)
        
        self.metadata_label = tk.Label(
            song_info_frame,
            text="",
            font=('Segoe UI', 8),
            bg=ModernTheme.PRIMARY,
            fg=ModernTheme.TEXT_SECONDARY
        )
        self.metadata_label.pack(anchor=tk.W)
    
    def _create_audio_controls(self):
        """Crea los controles de audio (sonido y velocidad)"""
        # Selector de sonido
        sound_frame = tk.Frame(self.frame, bg=ModernTheme.PRIMARY)
        sound_frame.pack(side=tk.LEFT, padx=20)
        
        tk.Label(
            sound_frame,
            text="Sonido:",
            font=('Segoe UI', 9),
            bg=ModernTheme.PRIMARY,
            fg=ModernTheme.TEXT_SECONDARY
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        style = ttk.Style()
        style.configure('Piano.TCombobox', background=ModernTheme.BG_CARD)
        
        sound_options = [
            '🎹 Acoustic Grand Piano',
            '🎹 Piano de Cola',
            '✨ Piano Brillante', 
            '🌙 Piano Suave',
            '⚡ Piano Eléctrico'
        ]
        
        self.sound_selector = ttk.Combobox(
            sound_frame,
            values=sound_options,
            state='readonly',
            width=22,
            font=('Segoe UI', 9),
            style='Piano.TCombobox'
        )
        self.sound_selector.set('🎹 Acoustic Grand Piano')
        self.sound_selector.bind('<<ComboboxSelected>>', 
                                 lambda e: self.callbacks['on_sound_change'](self.sound_selector.get()))
        self.sound_selector.pack(side=tk.LEFT)
        
        # Selector de velocidad
        speed_frame = tk.Frame(self.frame, bg=ModernTheme.PRIMARY)
        speed_frame.pack(side=tk.LEFT, padx=20)
        
        tk.Label(
            speed_frame,
            text="Velocidad:",
            font=('Segoe UI', 9),
            bg=ModernTheme.PRIMARY,
            fg=ModernTheme.TEXT_SECONDARY
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        speed_options = ['0.5x', '0.75x', '1.0x', '1.25x', '1.5x', '2.0x']
        self.speed_selector = ttk.Combobox(
            speed_frame,
            values=speed_options,
            state='readonly',
            width=7,
            font=('Segoe UI', 9),
            style='Piano.TCombobox'
        )
        self.speed_selector.set('1.0x')
        self.speed_selector.bind('<<ComboboxSelected>>', 
                                 lambda e: self.callbacks['on_speed_change'](self.speed_selector.get()))
        self.speed_selector.pack(side=tk.LEFT)
    
    def _create_action_buttons(self):
        """Crea los botones de acción (abrir, detener, reproducir, etc.)"""
        btn_frame = tk.Frame(self.frame, bg=ModernTheme.PRIMARY)
        btn_frame.pack(side=tk.RIGHT, padx=10)
        
        # Botón configuración
        tk.Button(
            btn_frame,
            text="⚙️",
            command=self.callbacks['on_settings'],
            bg=ModernTheme.BG_CARD,
            fg=ModernTheme.TEXT_PRIMARY,
            font=('Segoe UI', 14),
            relief=tk.FLAT,
            padx=8,
            pady=2,
            cursor='hand2'
        ).pack(side=tk.LEFT, padx=3)
        
        # Botón abrir
        tk.Button(
            btn_frame,
            text="📂 Abrir",
            command=self.callbacks['on_open'],
            bg=ModernTheme.BTN_PRIMARY_BG,
            fg=ModernTheme.TEXT_PRIMARY,
            font=('Segoe UI', 9, 'bold'),
            relief=tk.FLAT,
            padx=15,
            pady=5,
            cursor='hand2'
        ).pack(side=tk.LEFT, padx=3)
        
        # Botón detener
        self.stop_btn = tk.Button(
            btn_frame,
            text="⏹ Detener",
            command=self.callbacks['on_stop'],
            bg=ModernTheme.BTN_DANGER_BG,
            fg=ModernTheme.TEXT_PRIMARY,
            font=('Segoe UI', 9, 'bold'),
            relief=tk.FLAT,
            padx=15,
            pady=5,
            cursor='hand2',
            state=tk.DISABLED
        )
        self.stop_btn.pack(side=tk.LEFT, padx=3)
        
        # Botón reproducir
        self.play_btn = tk.Button(
            btn_frame,
            text="▶️ Reproducir",
            command=self.callbacks['on_play'],
            bg='#10b981',
            fg=ModernTheme.TEXT_PRIMARY,
            font=('Segoe UI', 9, 'bold'),
            relief=tk.FLAT,
            padx=15,
            pady=5,
            cursor='hand2'
        )
        self.play_btn.pack(side=tk.LEFT, padx=3)
        
        # Botón practicar
        self.practice_btn = tk.Button(
            btn_frame,
            text="🎹 Practicar",
            command=self.callbacks['on_practice'],
            bg='#3b82f6',
            fg=ModernTheme.TEXT_PRIMARY,
            font=('Segoe UI', 9, 'bold'),
            relief=tk.FLAT,
            padx=15,
            pady=5,
            cursor='hand2'
        )
        self.practice_btn.pack(side=tk.LEFT, padx=3)
    
    # === Métodos públicos para actualizar UI ===
    
    def update_song_info(self, song_name):
        """Actualiza el nombre de la canción"""
        display_name = f"🎵 {song_name[:30]}..." if len(song_name) > 30 else f"🎵 {song_name}"
        self.song_label.config(text=display_name)
    
    def update_metadata(self, bpm, time_signature, key_signature=""):
        """Actualiza la metadata (tempo, compás, tonalidad)"""
        bpm_str = f"{int(bpm)} BPM" if isinstance(bpm, (int, float)) else str(bpm)
        
        if isinstance(time_signature, tuple) and len(time_signature) >= 2:
            time_sig_str = f"{time_signature[0]}/{time_signature[1]}"
        else:
            time_sig_str = str(time_signature)
        
        key_str = f" | {key_signature}" if key_signature and key_signature != 'C' else ""
        
        self.metadata_label.config(text=f"🎵 {bpm_str} | 🎼 {time_sig_str}{key_str}")
    
    def set_playing_state(self, is_playing):
        """Actualiza el estado de los botones según si está reproduciendo"""
        if is_playing:
            self.stop_btn.config(state=tk.NORMAL)
            self.play_btn.config(state=tk.DISABLED)
            self.practice_btn.config(state=tk.DISABLED)
        else:
            self.stop_btn.config(state=tk.DISABLED)
            self.play_btn.config(state=tk.NORMAL)
            self.practice_btn.config(state=tk.NORMAL)
    
    def show_temporary_message(self, message, duration=2000):
        """Muestra un mensaje temporal en el label de metadata"""
        original = self.metadata_label.cget('text')
        self.metadata_label.config(text=message)
        self.parent.after(duration, lambda: self.metadata_label.config(text=original))
    
    def get_speed_value(self):
        """Retorna el valor numérico de velocidad seleccionada"""
        return float(self.speed_selector.get().replace('x', ''))
    
    def get_sound_profile(self):
        """Retorna el perfil de sonido mapeado"""
        profile_map = {
            '🎹 Acoustic Grand Piano': 'acoustic',
            '🎹 Piano de Cola': 'grand',
            '✨ Piano Brillante': 'bright',
            '🌙 Piano Suave': 'mellow',
            '⚡ Piano Eléctrico': 'electric'
        }
        return profile_map.get(self.sound_selector.get(), 'acoustic')
