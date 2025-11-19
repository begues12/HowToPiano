#!/usr/bin/env python3
"""
HowToPiano GUI - Versión COMPACTA e INTELIGENTE
Diseño optimizado para mostrar todo lo esencial sin scroll
Refactorizado con separación de responsabilidades
"""
import tkinter as tk
from tkinter import filedialog, messagebox
import json
import os
import threading
import time
from pathlib import Path

# Tema moderno
from src.modern_theme import ModernTheme, ModernWidgets

# Nuevos módulos refactorizados
from src.piano_sound import PianoSound
from src.midi_parser import MidiParser
from src.music_score import MusicScore

# Importar módulos de hardware (con fallback)
try:
    from src.midi_reader import MidiReader
    from src.led_controller import LEDController
    from src.note_mapper import NoteMapper
    HAS_HARDWARE = True
except ImportError:
    HAS_HARDWARE = False
    print("⚠️ Módulos de hardware no disponibles - modo simulación")


class CompactHowToPianoGUI:
    """GUI Compacta e Inteligente"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🎹 HowToPiano")
        self.root.geometry("1400x850")
        self.root.configure(bg=ModernTheme.BG_DARK)
        
        # Cargar configuración
        self.config = self.load_config()
        
        # Variables
        self.current_song = None
        self.current_song_path = None
        self.playing = False
        self.piano_sound = PianoSound(0.5, profile='acoustic')
        self.recent_songs = self.load_recent()
        self.key_rectangles = {}
        self.active_mode = None
        self.show_fingering = self.config.get('show_fingering', False)
        self.use_virtual_keyboard = False  # Para clases sin MIDI
        self.num_keys = self.config.get('num_keys', 61)
        
        # Caché
        self._notes_cache = {}
        self._metadata_cache = {}
        
        # Sistema de partitura con scroll
        self.staff_notes = []  # Lista de (x, y, note_value, timestamp)
        self.staff_scroll_offset = 0
        self.staff_pixels_per_ms = 0.1  # Píxeles por milisegundo
        self.current_playback_time = 0
        
        # Colores de digitación
        self.finger_colors_right = {
            1: '#00FFFF',  # Cyan - Pulgar
            2: '#0099FF',  # Azul cielo - Índice
            3: '#0033FF',  # Azul marino - Medio
            4: '#6600FF',  # Violeta - Anular
            5: '#FF00FF'   # Magenta - Meñique
        }
        
        self.create_compact_ui()
    
    def load_config(self):
        """Carga configuración desde archivo"""
        try:
            with open('config/config.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {'num_keys': 61, 'show_fingering': False, 'brightness': 0.4}
    
    def save_config(self):
        """Guarda configuración en archivo"""
        try:
            os.makedirs('config', exist_ok=True)
            with open('config/config.json', 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error guardando config: {e}")
    
    def load_recent(self):
        try:
            with open('config/recent.json', 'r') as f:
                return json.load(f)
        except:
            return []
    
    def save_recent(self, path):
        if path not in self.recent_songs:
            self.recent_songs.insert(0, path)
            self.recent_songs = self.recent_songs[:10]
            os.makedirs('config', exist_ok=True)
            with open('config/recent.json', 'w') as f:
                json.dump(self.recent_songs, f)
    
    def create_compact_ui(self):
        """Crea UI compacta y eficiente"""
        
        # ============ HEADER COMPACTO ============
        header = tk.Frame(self.root, bg=ModernTheme.PRIMARY, height=45)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        tk.Label(
            header,
            text="🎹 HowToPiano",
            font=('Segoe UI', 16, 'bold'),
            bg=ModernTheme.PRIMARY,
            fg=ModernTheme.TEXT_PRIMARY
        ).pack(side=tk.LEFT, padx=15)
        
        # Info compacta de canción cargada CON METADATA
        song_info_frame = tk.Frame(header, bg=ModernTheme.PRIMARY)
        song_info_frame.pack(side=tk.LEFT, padx=20)
        
        self.song_label = tk.Label(
            song_info_frame,
            text="Sin canción",
            font=('Segoe UI', 10, 'bold'),
            bg=ModernTheme.PRIMARY,
            fg=ModernTheme.TEXT_PRIMARY
        )
        self.song_label.pack(anchor=tk.W)
        
        # Metadata: Tempo y compás
        self.metadata_label = tk.Label(
            song_info_frame,
            text="",
            font=('Segoe UI', 8),
            bg=ModernTheme.PRIMARY,
            fg=ModernTheme.TEXT_SECONDARY
        )
        self.metadata_label.pack(anchor=tk.W)
        
        # Selector de sonido de piano
        sound_frame = tk.Frame(header, bg=ModernTheme.PRIMARY)
        sound_frame.pack(side=tk.LEFT, padx=20)
        
        tk.Label(
            sound_frame,
            text="Sonido:",
            font=('Segoe UI', 9),
            bg=ModernTheme.PRIMARY,
            fg=ModernTheme.TEXT_SECONDARY
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        # Combobox para seleccionar perfil
        from tkinter import ttk
        style = ttk.Style()
        style.configure('Piano.TCombobox', background=ModernTheme.BG_CARD)
        
        sound_options = [
            '� Acoustic Grand Piano',
            '�🎹 Piano de Cola',
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
        self.sound_selector.set('� Acoustic Grand Piano')
        self.sound_selector.bind('<<ComboboxSelected>>', self.on_sound_change)
        self.sound_selector.pack(side=tk.LEFT)
        
        # Control de velocidad de reproducción
        speed_frame = tk.Frame(header, bg=ModernTheme.PRIMARY)
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
        self.speed_selector.bind('<<ComboboxSelected>>', self.on_speed_change)
        self.speed_selector.pack(side=tk.LEFT)
        
        # Variable para velocidad de reproducción
        self.playback_speed = 1.0
        
        # Botones rápidos
        btn_frame = tk.Frame(header, bg=ModernTheme.PRIMARY)
        btn_frame.pack(side=tk.RIGHT, padx=10)
        
        tk.Button(
            btn_frame,
            text="⚙️",
            command=self.show_settings,
            bg=ModernTheme.BG_CARD,
            fg=ModernTheme.TEXT_PRIMARY,
            font=('Segoe UI', 14),
            relief=tk.FLAT,
            padx=8,
            pady=2,
            cursor='hand2'
        ).pack(side=tk.LEFT, padx=3)
        
        tk.Button(
            btn_frame,
            text="📂 Abrir",
            command=self.quick_load,
            bg=ModernTheme.BTN_PRIMARY_BG,
            fg=ModernTheme.TEXT_PRIMARY,
            font=('Segoe UI', 9, 'bold'),
            relief=tk.FLAT,
            padx=15,
            pady=5,
            cursor='hand2'
        ).pack(side=tk.LEFT, padx=3)
        
        self.stop_btn = tk.Button(
            btn_frame,
            text="⏹ Detener",
            command=self.stop_playing,
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
        
        # Botón de Reproducir (auto-play)
        self.play_btn = tk.Button(
            btn_frame,
            text="▶️ Reproducir",
            command=self.start_auto_play,
            bg='#10b981',
            fg=ModernTheme.TEXT_PRIMARY,
            font=('Segoe UI', 9, 'bold'),
            relief=tk.FLAT,
            padx=15,
            pady=5,
            cursor='hand2'
        )
        self.play_btn.pack(side=tk.LEFT, padx=3)
        
        # Botón de Practicar
        self.practice_btn = tk.Button(
            btn_frame,
            text="🎹 Practicar",
            command=self.start_practice_mode,
            bg='#3b82f6',
            fg=ModernTheme.TEXT_PRIMARY,
            font=('Segoe UI', 9, 'bold'),
            relief=tk.FLAT,
            padx=15,
            pady=5,
            cursor='hand2'
        )
        self.practice_btn.pack(side=tk.LEFT, padx=3)
        
        # ============ CONTENEDOR PRINCIPAL ============
        main = tk.Frame(self.root, bg=ModernTheme.BG_DARK)
        main.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # ============ COLUMNA IZQUIERDA - BIBLIOTECA ============
        left = tk.Frame(main, bg=ModernTheme.BG_CARD, width=280)
        left.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 10))
        left.pack_propagate(False)
        
        # Título
        tk.Label(
            left,
            text="📚 Biblioteca",
            font=('Segoe UI', 11, 'bold'),
            bg=ModernTheme.BG_CARD,
            fg=ModernTheme.TEXT_PRIMARY
        ).pack(pady=8, padx=10, anchor=tk.W)
        
        # Lista con preescucha
        list_frame = tk.Frame(left, bg=ModernTheme.BG_CARD)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.song_listbox = tk.Listbox(
            list_frame,
            bg=ModernTheme.BG_LIGHT,
            fg=ModernTheme.TEXT_PRIMARY,
            font=('Segoe UI', 9),
            selectbackground=ModernTheme.PRIMARY,
            relief=tk.FLAT,
            bd=0,
            highlightthickness=0,
            yscrollcommand=scrollbar.set
        )
        self.song_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.song_listbox.yview)
        
        # Bind para selección
        self.song_listbox.bind('<<ListboxSelect>>', self.on_song_select)
        self.song_listbox.bind('<Double-Button-1>', self.load_selected_song)
        
        # Botones de acción
        action_frame = tk.Frame(left, bg=ModernTheme.BG_CARD)
        action_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Button(
            action_frame,
            text="🔍 Buscar",
            command=self.browse_files,
            bg=ModernTheme.PRIMARY,
            fg=ModernTheme.TEXT_PRIMARY,
            font=('Segoe UI', 9, 'bold'),
            relief=tk.FLAT,
            cursor='hand2',
            width=12
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        tk.Button(
            action_frame,
            text="▶ Cargar",
            command=self.load_selected_song,
            bg=ModernTheme.SECONDARY,
            fg=ModernTheme.TEXT_PRIMARY,
            font=('Segoe UI', 9, 'bold'),
            relief=tk.FLAT,
            cursor='hand2',
            width=12
        ).pack(side=tk.LEFT)
        
        # Info de preescucha
        self.preview_label = tk.Label(
            left,
            text="Selecciona para preescuchar",
            font=('Segoe UI', 8),
            bg=ModernTheme.BG_CARD,
            fg=ModernTheme.TEXT_MUTED,
            wraplength=260,
            justify=tk.LEFT
        )
        self.preview_label.pack(pady=(0, 10), padx=10, anchor=tk.W)
        
        # Cargar recientes
        self.refresh_song_list()
        
        # ============ COLUMNA DERECHA - CONTENIDO PRINCIPAL ============
        right = tk.Frame(main, bg=ModernTheme.BG_DARK)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # ============ PARTITURA (MÁS GRANDE Y PROMINENTE) ============
        staff_card = tk.Frame(right, bg=ModernTheme.BG_CARD, height=380)
        staff_card.pack(fill=tk.X, pady=(0, 10))
        staff_card.pack_propagate(False)
        
        tk.Label(
            staff_card,
            text="🎼 Partitura Musical",
            font=('Segoe UI', 11, 'bold'),
            bg=ModernTheme.BG_CARD,
            fg=ModernTheme.TEXT_PRIMARY
        ).pack(pady=(8, 5), padx=10, anchor=tk.W)
        
        # Barra de progreso con seek
        progress_frame = tk.Frame(staff_card, bg=ModernTheme.BG_CARD)
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
        self.progress_canvas.bind('<Button-1>', self.on_progress_click)
        
        # Label de porcentaje
        self.progress_text_label = tk.Label(
            progress_frame,
            text="0%",
            font=('Segoe UI', 8, 'bold'),
            bg=ModernTheme.BG_CARD,
            fg=ModernTheme.TEXT_PRIMARY
        )
        self.progress_text_label.place(in_=self.progress_canvas, relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        self.staff_canvas = tk.Canvas(
            staff_card,
            bg='white',
            highlightthickness=0,
            height=300
        )
        self.staff_canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Inicializar MusicScore
        self.music_score = MusicScore(self.staff_canvas)
        self.staff_canvas.bind('<Configure>', lambda e: self.music_score.render())
        
        # ============ PANEL DE ESTADÍSTICAS ============
        stats_card = tk.Frame(right, bg=ModernTheme.BG_CARD, height=80)
        stats_card.pack(fill=tk.X, pady=(0, 10))
        stats_card.pack_propagate(False)
        
        tk.Label(
            stats_card,
            text="📊 Estadísticas de Práctica",
            font=('Segoe UI', 10, 'bold'),
            bg=ModernTheme.BG_CARD,
            fg=ModernTheme.TEXT_PRIMARY
        ).pack(pady=(8, 5), padx=10, anchor=tk.W)
        
        stats_row = tk.Frame(stats_card, bg=ModernTheme.BG_CARD)
        stats_row.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Score
        score_frame = tk.Frame(stats_row, bg=ModernTheme.BG_LIGHT, relief=tk.FLAT, bd=1)
        score_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10), ipadx=15, ipady=8)
        tk.Label(score_frame, text="Score", font=('Segoe UI', 9), bg=ModernTheme.BG_LIGHT, fg=ModernTheme.TEXT_MUTED, anchor=tk.CENTER).pack(fill=tk.X, pady=(2, 0))
        self.score_label = tk.Label(score_frame, text="0", font=('Segoe UI', 18, 'bold'), bg=ModernTheme.BG_LIGHT, fg='#10b981', anchor=tk.CENTER)
        self.score_label.pack(fill=tk.X, pady=(0, 2))
        
        # Precisión
        accuracy_frame = tk.Frame(stats_row, bg=ModernTheme.BG_LIGHT, relief=tk.FLAT, bd=1)
        accuracy_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10), ipadx=15, ipady=8)
        tk.Label(accuracy_frame, text="Precisión", font=('Segoe UI', 9), bg=ModernTheme.BG_LIGHT, fg=ModernTheme.TEXT_MUTED, anchor=tk.CENTER).pack(fill=tk.X, pady=(2, 0))
        self.accuracy_label = tk.Label(accuracy_frame, text="100%", font=('Segoe UI', 18, 'bold'), bg=ModernTheme.BG_LIGHT, fg='#3b82f6', anchor=tk.CENTER)
        self.accuracy_label.pack(fill=tk.X, pady=(0, 2))
        
        # Combo
        combo_frame = tk.Frame(stats_row, bg=ModernTheme.BG_LIGHT, relief=tk.FLAT, bd=1)
        combo_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10), ipadx=15, ipady=8)
        tk.Label(combo_frame, text="Combo", font=('Segoe UI', 9), bg=ModernTheme.BG_LIGHT, fg=ModernTheme.TEXT_MUTED, anchor=tk.CENTER).pack(fill=tk.X, pady=(2, 0))
        self.combo_label = tk.Label(combo_frame, text="0x", font=('Segoe UI', 18, 'bold'), bg=ModernTheme.BG_LIGHT, fg='#f59e0b', anchor=tk.CENTER)
        self.combo_label.pack(fill=tk.X, pady=(0, 2))
        
        # Notas tocadas
        notes_frame = tk.Frame(stats_row, bg=ModernTheme.BG_LIGHT, relief=tk.FLAT, bd=1)
        notes_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, ipadx=15, ipady=8)
        tk.Label(notes_frame, text="Notas", font=('Segoe UI', 9), bg=ModernTheme.BG_LIGHT, fg=ModernTheme.TEXT_MUTED, anchor=tk.CENTER).pack(fill=tk.X, pady=(2, 0))
        self.notes_played_label = tk.Label(notes_frame, text="0/0", font=('Segoe UI', 18, 'bold'), bg=ModernTheme.BG_LIGHT, fg='#8b5cf6', anchor=tk.CENTER)
        self.notes_played_label.pack(fill=tk.X, pady=(0, 2))
        
        # Variables de estadísticas
        self.score = 0
        self.accuracy = 100.0  # Empieza en 100%
        self.combo = 0
        self.max_combo = 0
        self.notes_played = 0
        self.notes_correct = 0
        self.notes_missed = 0
        self.total_notes = 0
        
        # ============ TECLADO VIRTUAL (MÁS ALTO) ============
        keyboard_card = tk.Frame(right, bg=ModernTheme.BG_CARD, height=150)
        keyboard_card.pack(fill=tk.X, pady=(0, 10))
        keyboard_card.pack_propagate(False)
        
        tk.Label(
            keyboard_card,
            text="🎹 Teclado Virtual",
            font=('Segoe UI', 10, 'bold'),
            bg=ModernTheme.BG_CARD,
            fg=ModernTheme.TEXT_PRIMARY
        ).pack(pady=(8, 5), padx=10, anchor=tk.W)
        
        self.keyboard_canvas = tk.Canvas(
            keyboard_card,
            bg=ModernTheme.BG_LIGHT,
            highlightthickness=0,
            height=110
        )
        self.keyboard_canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        self.keyboard_canvas.bind('<Button-1>', self.on_key_click)
        self.keyboard_canvas.bind('<Configure>', lambda e: self.draw_keyboard())
        
        # ============ MODOS DE PRÁCTICA (SOLO SI HAY CANCIÓN) ============
        self.modes_card = tk.Frame(right, bg=ModernTheme.BG_CARD)
        # NO se empaqueta aquí - solo cuando se carga una canción
        
        tk.Label(
            self.modes_card,
            text="🎓 Modos de Práctica",
            font=('Segoe UI', 10, 'bold'),
            bg=ModernTheme.BG_CARD,
            fg=ModernTheme.TEXT_PRIMARY
        ).pack(pady=(8, 10), padx=10, anchor=tk.W)
        
        # Modos en fila
        modes_row = tk.Frame(self.modes_card, bg=ModernTheme.BG_CARD)
        modes_row.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        modes = [
            ("👨‍🎓 Alumno", self.start_student_mode, ModernTheme.INFO),
            ("🎹 Práctica", self.start_practice_mode, ModernTheme.SECONDARY),
            ("🎼 Maestro", self.start_teacher_mode, ModernTheme.ACCENT)
        ]
        
        for text, cmd, color in modes:
            tk.Button(
                modes_row,
                text=text,
                command=cmd,
                bg=color,
                fg=ModernTheme.TEXT_PRIMARY,
                font=('Segoe UI', 9, 'bold'),
                relief=tk.FLAT,
                padx=20,
                pady=8,
                cursor='hand2'
            ).pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        
        # Progreso
        self.progress_frame = tk.Frame(self.modes_card, bg=ModernTheme.BG_CARD)
        self.progress_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.progress_bar = tk.Canvas(
            self.progress_frame,
            bg=ModernTheme.BG_LIGHT,
            height=8,
            highlightthickness=0
        )
        self.progress_bar.pack(fill=tk.X)
        
        # Dibujar inicial
        self.root.after(100, lambda: self.music_score.render())
        self.root.after(100, self.draw_keyboard)
    

    
    def load_notes_to_staff(self):
        """Carga todas las notas del MIDI a MusicScore"""
        if not self.current_song_path:
            return
        
        note_events = self._notes_cache.get(self.current_song_path, [])
        metadata = self._metadata_cache.get(self.current_song_path, {})
        
        print(f"📝 Cargando {len(note_events)} eventos a MusicScore")
        
        # MusicScore espera el mismo formato: [(timestamp_ms, [notes])] + metadata
        self.music_score.load_notes(note_events, metadata)
        self.music_score.render()
        
        print(f"✅ Partitura cargada y renderizada")
    
    def update_staff_scroll(self, current_time_ms):
        """Actualiza el scroll de la partitura durante la reproducción usando MusicScore"""
        self.current_playback_time = current_time_ms
        self.music_score.update_time(current_time_ms)
        self.music_score.render()
    
    def draw_keyboard(self):
        """Dibuja teclado virtual compacto con digitación opcional"""
        self.keyboard_canvas.delete('all')
        self.key_rectangles.clear()
        
        w = self.keyboard_canvas.winfo_width()
        h = self.keyboard_canvas.winfo_height()
        
        if w < 2:
            return
        
        # Calcular número de teclas blancas según el total de teclas
        # Teclas: 25=15 blancas, 37=22, 49=29, 61=36, 76=45, 88=52
        keys_to_white = {25: 15, 37: 22, 49: 29, 61: 36, 76: 45, 88: 52}
        num_white = keys_to_white.get(self.num_keys, 36)  # Default 61 teclas
        
        white_width = w / num_white
        black_width = white_width * 0.6
        black_height = h * 0.6
        
        # Nota inicial según número de teclas (centrado en C4 = MIDI 60)
        if self.num_keys == 25:
            start_note = 48  # C3
        elif self.num_keys == 37:
            start_note = 48  # C3
        elif self.num_keys == 49:
            start_note = 36  # C2
        elif self.num_keys == 61:
            start_note = 36  # C2 (estándar)
        elif self.num_keys == 76:
            start_note = 28  # E1
        else:  # 88
            start_note = 21  # A0
        
        # PRIMERO: Dibujar TODAS las teclas blancas
        white_key_positions = []
        for i in range(num_white):
            x1 = i * white_width
            x2 = x1 + white_width
            # Calcular nota MIDI correcta para cada tecla blanca
            octave = i // 7
            note_in_octave = i % 7
            white_notes = [0, 2, 4, 5, 7, 9, 11]  # C D E F G A B
            midi_note = start_note + (octave * 12) + white_notes[note_in_octave]
            
            # Color de la tecla: si show_fingering está activo, usar color de dedo (suave)
            if self.show_fingering:
                finger = self.get_finger_for_note(midi_note)
                if finger:
                    base_color = self.finger_colors_right.get(finger, '#FFFFFF')
                    key_color = self.lighten_color(base_color, 0.7)  # Muy claro para teclas blancas
                else:
                    key_color = 'white'
            else:
                key_color = 'white'
            
            rect_id = self.keyboard_canvas.create_rectangle(
                x1, 0, x2, h,
                fill=key_color,
                outline='#cbd5e0',
                width=1,
                tags=(f'key_{midi_note}', 'white_key')
            )
            self.key_rectangles[midi_note] = (x1, 0, x2, h, False, rect_id)
            white_key_positions.append((i, x1, x2, midi_note))
            
            # Mostrar número de dedo si está activo
            if self.show_fingering:
                finger = self.get_finger_for_note(midi_note)
                if finger:
                    color = self.finger_colors_right.get(finger, '#666666')
                    self.keyboard_canvas.create_text(
                        (x1 + x2) / 2, h - 15,
                        text=str(finger),
                        font=('Segoe UI', 10, 'bold'),
                        fill=color,
                        tags=f'finger_{midi_note}'
                    )
        
        # SEGUNDO: Dibujar teclas negras ENCIMA de las blancas
        # Patrón de teclas negras: sí, sí, no, sí, sí, sí, no (C# D# _ F# G# A# _)
        black_pattern = [True, True, False, True, True, True, False]  # para C D E F G A B
        
        for i, x1, x2, white_midi in white_key_positions:
            if i >= num_white - 1:  # No dibujar después de la última blanca
                break
            
            # Determinar si después de esta tecla blanca hay una negra
            note_in_octave = i % 7
            if black_pattern[note_in_octave]:
                # Calcular posición centrada entre esta blanca y la siguiente
                next_x1 = (i + 1) * white_width
                black_x = x2 - (black_width / 2)
                
                # Calcular la nota MIDI de la tecla negra directamente desde la blanca
                # Si la blanca es C(0), D(2), F(5), G(7), A(9) -> negra es +1
                white_notes = [0, 2, 4, 5, 7, 9, 11]  # C D E F G A B
                white_note_value = white_notes[note_in_octave]
                black_midi = white_midi + 1  # La negra siempre está 1 semitono arriba
                
                # Color de la tecla negra: si show_fingering está activo, usar color de dedo (oscuro)
                if self.show_fingering:
                    finger = self.get_finger_for_note(black_midi)
                    if finger:
                        base_color = self.finger_colors_right.get(finger, '#000000')
                        key_color = self.lighten_color(base_color, 0.3)  # Oscuro para teclas negras
                    else:
                        key_color = 'black'
                else:
                    key_color = 'black'
                
                rect_id = self.keyboard_canvas.create_rectangle(
                    black_x, 0, black_x + black_width, black_height,
                    fill=key_color,
                    outline='#2d3748',
                    width=1,
                    tags=(f'key_{black_midi}', 'black_key')
                )
                self.key_rectangles[black_midi] = (black_x, 0, black_x + black_width, black_height, True, rect_id)
                
                # Mostrar número de dedo si está activo
                if self.show_fingering:
                    finger = self.get_finger_for_note(black_midi)
                    if finger:
                        color = self.finger_colors_right.get(finger, '#CCCCCC')
                        self.keyboard_canvas.create_text(
                            black_x + black_width/2, black_height - 10,
                            text=str(finger),
                            font=('Segoe UI', 8, 'bold'),
                            fill=color,
                            tags=f'finger_{black_midi}'
                        )
    
    def get_finger_for_note(self, note):
        """Devuelve el dedo sugerido para una nota (1-5)"""
        # Simplificado: patrón básico basado en octava
        note_in_octave = note % 12
        # C=1, D=2, E=3, F=1, G=2, A=3, B=4
        pattern = {0: 1, 2: 2, 4: 3, 5: 1, 7: 2, 9: 3, 11: 4,
                   1: 2, 3: 3, 6: 2, 8: 3, 10: 4}  # Negras
        return pattern.get(note_in_octave, None)
    
    def on_key_click(self, event):
        """Click en tecla - prioriza teclas negras"""
        x, y = event.x, event.y
        
        # PRIMERO buscar si click en tecla negra (tienen prioridad por estar encima)
        clicked = None
        for note, data in self.key_rectangles.items():
            x1, y1, x2, y2, is_black, rect_id = data
            if is_black and x1 <= x <= x2 and y1 <= y <= y2:
                clicked = note
                break
        
        # Si no es tecla negra, buscar en blancas
        if not clicked:
            for note, data in self.key_rectangles.items():
                x1, y1, x2, y2, is_black, rect_id = data
                if not is_black and x1 <= x <= x2 and y1 <= y <= y2:
                    clicked = note
                    break
        
        if clicked:
            self.piano_sound.play_note(clicked)
            self.highlight_key(clicked)
            self.root.after(300, lambda n=clicked: self.restore_key(n))
    
    def highlight_key(self, note, color=None):
        """Ilumina tecla con color específico"""
        if note not in self.key_rectangles:
            return
        
        try:
            if color is None:
                # Usar color de digitación brillante si está activo
                if self.show_fingering:
                    finger = self.get_finger_for_note(note)
                    if finger:
                        # Usar el color del dedo pero más brillante (saturado)
                        color = self.finger_colors_right.get(finger, ModernTheme.ACCENT)
                    else:
                        color = ModernTheme.ACCENT
                else:
                    color = ModernTheme.ACCENT
            
            # Obtener el rect_id directamente
            rect_id = self.key_rectangles[note][5]
            self.keyboard_canvas.itemconfig(rect_id, fill=color)
            
            # También actualizar por tag como backup
            items = self.keyboard_canvas.find_withtag(f'key_{note}')
            for item in items:
                self.keyboard_canvas.itemconfig(item, fill=color)
        except Exception as e:
            print(f"❌ Error highlighting key {note}: {e}")
    
    def restore_key(self, note):
        """Restaura color original de tecla o color de digitación"""
        if note not in self.key_rectangles:
            return
        
        try:
            is_black = self.key_rectangles[note][4]
            rect_id = self.key_rectangles[note][5]
            
            # Si show_fingering está activo, usar color de dedo (más suave)
            if self.show_fingering:
                finger = self.get_finger_for_note(note)
                if finger:
                    base_color = self.finger_colors_right.get(finger, '#FFFFFF')
                    # Hacer el color más suave (más claro) para el fondo
                    color = self.lighten_color(base_color, 0.7) if not is_black else self.lighten_color(base_color, 0.3)
                else:
                    color = 'black' if is_black else 'white'
            else:
                color = 'black' if is_black else 'white'
            
            # Restaurar usando rect_id directo
            self.keyboard_canvas.itemconfig(rect_id, fill=color)
            
            # También por tag como backup
            items = self.keyboard_canvas.find_withtag(f'key_{note}')
            for item in items:
                self.keyboard_canvas.itemconfig(item, fill=color)
        except Exception as e:
            print(f"❌ Error restoring key {note}: {e}")
    
    def lighten_color(self, hex_color, factor=0.5):
        """Aclara un color hex para usarlo como fondo"""
        # Convertir hex a RGB
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        
        # Mezclar con blanco según el factor (0=color original, 1=blanco)
        r = int(r + (255 - r) * factor)
        g = int(g + (255 - g) * factor)
        b = int(b + (255 - b) * factor)
        
        return f'#{r:02x}{g:02x}{b:02x}'
    
    def refresh_song_list(self):
        """Actualiza lista de canciones"""
        self.song_listbox.delete(0, tk.END)
        for song in self.recent_songs:
            name = os.path.basename(song)
            self.song_listbox.insert(tk.END, f"🎵 {name}")
    
    def browse_files(self):
        """Buscar archivos"""
        files = filedialog.askopenfilenames(
            title="Seleccionar archivos MIDI",
            filetypes=[("MIDI files", "*.mid *.midi"), ("All files", "*.*")]
        )
        if files:
            for f in files:
                self.save_recent(f)
            self.refresh_song_list()
    
    def on_song_select(self, event):
        """Cuando se selecciona una canción - mostrar preescucha usando MidiParser"""
        selection = self.song_listbox.curselection()
        if not selection:
            return
        
        idx = selection[0]
        if idx >= len(self.recent_songs):
            return
        
        path = self.recent_songs[idx]
        
        # Preescucha - mostrar info básica sin parsear todo
        try:
            # Mostrar solo el nombre del archivo para preview rápido
            filename = os.path.basename(path)
            self.preview_label.config(
                text=f"📄 {filename}\n"
                     f"Doble-click para cargar"
            )
        except Exception as e:
            self.preview_label.config(
                text=f"📄 {os.path.basename(path)}\nDoble-click para cargar"
            )
    
    def load_selected_song(self, event=None):
        """Cargar canción seleccionada"""
        selection = self.song_listbox.curselection()
        if not selection:
            messagebox.showwarning("Aviso", "Selecciona una canción primero")
            return
        
        idx = selection[0]
        if idx >= len(self.recent_songs):
            return
        
        path = self.recent_songs[idx]
        self.load_song(path)
    
    def quick_load(self):
        """Carga rápida desde diálogo"""
        file = filedialog.askopenfilename(
            title="Abrir archivo MIDI",
            filetypes=[("MIDI files", "*.mid *.midi"), ("All files", "*.*")]
        )
        if file:
            self.save_recent(file)
            self.refresh_song_list()
            self.load_song(file)
    
    def load_song(self, path):
        """Carga una canción y muestra popup de selección de modo"""
        # DETENER reproducción anterior si está activa
        if self.playing:
            response = messagebox.askyesno(
                "Canción en reproducción",
                "Hay una canción reproduciéndose. ¿Deseas detenerla y cargar la nueva?"
            )
            if response:
                self.stop_playing()
                time.sleep(0.2)  # Dar tiempo para que se detenga
            else:
                return  # No cargar nueva canción
        
        # Copiar archivo a carpeta midi/ y crear archivo de scores
        copied_path = self._copy_midi_to_library(path)
        if copied_path:
            path = copied_path  # Usar la copia local
        
        self.current_song_path = path
        name = os.path.basename(path)
        
        # Actualizar header con nombre
        self.song_label.config(text=f"🎵 {name[:30]}..." if len(name) > 30 else f"🎵 {name}")
        
        # Limpiar metadata mientras carga
        self.metadata_label.config(text="Cargando...")
        
        # Resetear tiempo de reproducción
        self.current_playback_time = 0
        
        # Cargar notas en background
        threading.Thread(target=self._load_notes_and_staff_bg, args=(path,), daemon=True).start()
        
        # NO mostrar popup automático - usar botones en el header
        # self.show_mode_selection_dialog()
    
    def _copy_midi_to_library(self, source_path):
        """Copia archivo MIDI a carpeta midi/ y crea archivo de scores paralelo"""
        try:
            import shutil
            import json
            from datetime import datetime
            
            # Crear carpeta midi/ si no existe
            midi_dir = os.path.join(os.path.dirname(__file__), 'midi')
            os.makedirs(midi_dir, exist_ok=True)
            
            # Nombre base del archivo
            filename = os.path.basename(source_path)
            basename = os.path.splitext(filename)[0]
            
            # Ruta destino
            dest_path = os.path.join(midi_dir, filename)
            
            # Solo copiar si no existe o es diferente
            if not os.path.exists(dest_path) or os.path.abspath(source_path) != os.path.abspath(dest_path):
                shutil.copy2(source_path, dest_path)
                print(f"📂 Archivo copiado a: {dest_path}")
            
            # Crear archivo de scores paralelo (JSON)
            scores_path = os.path.join(midi_dir, f"{basename}_scores.json")
            
            # Cargar scores existentes o crear nuevo
            if os.path.exists(scores_path):
                with open(scores_path, 'r', encoding='utf-8') as f:
                    scores_data = json.load(f)
            else:
                scores_data = {
                    "filename": filename,
                    "created": datetime.now().isoformat(),
                    "sessions": [],
                    "best_score": 0,
                    "total_plays": 0,
                    "notes_learned": []
                }
            
            # Actualizar última carga
            scores_data["last_loaded"] = datetime.now().isoformat()
            scores_data["total_plays"] = scores_data.get("total_plays", 0) + 1
            
            # Guardar archivo de scores
            with open(scores_path, 'w', encoding='utf-8') as f:
                json.dump(scores_data, f, indent=2, ensure_ascii=False)
            
            print(f"📊 Archivo de scores: {scores_path}")
            return dest_path
            
        except Exception as e:
            print(f"⚠️ Error copiando archivo: {e}")
            return None
    
    def _load_notes_and_staff_bg(self, path):
        """Carga notas MIDI y genera partitura"""
        # Primero cargar las notas
        self._load_notes_bg(path)
        
        # Luego generar la partitura
        self.root.after(100, self.load_notes_to_staff)
        
        # Resetear estadísticas
        self.root.after(150, self.reset_stats)
    
    def _load_notes_bg(self, path):
        """Carga notas usando MidiParser"""
        try:
            # Usar MidiParser para parsear el archivo
            parser = MidiParser()
            note_events, metadata = parser.parse_file(path)
            
            print(f"🎵 Cargando MIDI: {os.path.basename(path)}")
            print(f"   Tempo: {metadata.get('bpm', metadata.get('tempo', 'N/A'))} BPM")
            print(f"   Firma de tiempo: {metadata.get('time_signature', 'N/A')}")
            print(f"   Key: {metadata.get('key_signature', 'N/A')}")
            
            # Convertir formato de MidiParser a formato esperado por GUI
            # MidiParser devuelve: [(timestamp_ms, [notes])]
            # GUI espera: [(timestamp_ms, [notes])]
            # ¡Ya es el mismo formato!
            
            # Limitar eventos pero mantener diversidad
            if len(note_events) > 500:
                step = len(note_events) // 500
                note_events = [note_events[i] for i in range(0, len(note_events), step)][:500]
            
            # Guardar en caché
            self._notes_cache[path] = note_events
            self._metadata_cache = metadata
            
            # Actualizar metadata en el header
            self.root.after(0, lambda: self.update_metadata_display(metadata))
            
            print(f"✅ Cargados {len(note_events)} eventos")
            if note_events:
                print(f"   Primera nota: {note_events[0]}")
                print(f"   Última nota: {note_events[-1]}")
                # Contar notas únicas (ahora son tuplas (note, velocity))
                unique_notes = set()
                for _, note_vel_pairs in note_events:
                    for note, vel in note_vel_pairs:
                        unique_notes.add(note)
                print(f"   Notas únicas: {len(unique_notes)} (rango: {min(unique_notes)}-{max(unique_notes)})")
        except Exception as e:
            print(f"❌ Error cargando MIDI con MidiParser: {e}")
            import traceback
            traceback.print_exc()
            # Fallback: usar datos de prueba
            parser = MidiParser()
            fallback_data = parser.parse_file("")  # Devuelve datos de prueba
            self._notes_cache[path] = fallback_data[0]
            self._metadata_cache = fallback_data[1]
    
    def update_metadata_display(self, metadata):
        """Actualiza el display de metadata (tempo y compás)"""
        try:
            # Obtener BPM
            bpm = metadata.get('bpm', metadata.get('tempo', 'N/A'))
            if isinstance(bpm, (int, float)):
                bpm = int(bpm)
            
            # Obtener compás
            time_sig = metadata.get('time_signature', (4, 4))
            if isinstance(time_sig, tuple) and len(time_sig) >= 2:
                time_sig_str = f"{time_sig[0]}/{time_sig[1]}"
            else:
                time_sig_str = "4/4"
            
            # Obtener tonalidad si existe
            key = metadata.get('key_signature', '')
            key_str = f" | {key}" if key and key != 'C' else ""
            
            # Actualizar label
            self.metadata_label.config(
                text=f"🎵 {bpm} BPM | 🎼 {time_sig_str}{key_str}"
            )
        except Exception as e:
            print(f"⚠️ Error actualizando metadata: {e}")
            self.metadata_label.config(text="")
    
    def start_student_mode(self):
        """Modo alumno - aprende nota por nota"""
        if not self.current_song_path:
            messagebox.showwarning("Aviso", "Carga una canción primero")
            return
        
        mode_msg = "🎓 Modo Aprendiz Iniciado\n\n"
        if self.use_virtual_keyboard:
            mode_msg += "Usando teclado virtual en pantalla\n"
            mode_msg += "Click en las teclas iluminadas para avanzar"
        else:
            mode_msg += "Toca las teclas iluminadas en tu MIDI\n"
            mode_msg += "El sistema espera cada nota correcta"
        
        messagebox.showinfo("Modo Aprendiz", mode_msg)
        self.playing = True
        self.stop_btn.config(state=tk.NORMAL)
        threading.Thread(target=self._student_mode_thread, daemon=True).start()
    def start_auto_play(self):
        """Modo reproducción automática - reproduce el MIDI sin esperar input del usuario"""
        if not self.current_song_path:
            messagebox.showwarning("Aviso", "Carga una canción primero")
            return
        
        if self.playing:
            messagebox.showwarning("Aviso", "Ya hay una reproducción en curso")
            return
        
        self.playing = True
        self.stop_btn.config(state=tk.NORMAL)
        self.play_btn.config(state=tk.DISABLED)
        self.practice_btn.config(state=tk.DISABLED)
        threading.Thread(target=self._auto_play_thread, daemon=True).start()
    
    def start_practice_mode(self):
        """Modo práctica"""
        if not self.current_song_path:
            messagebox.showwarning("Aviso", "Carga una canción primero")
            return
        
        if self.playing:
            messagebox.showwarning("Aviso", "Ya hay una reproducción en curso")
            return
        
        self.playing = True
        self.stop_btn.config(state=tk.NORMAL)
        self.play_btn.config(state=tk.DISABLED)
        self.practice_btn.config(state=tk.DISABLED)
        threading.Thread(target=self._practice_thread, daemon=True).start()
    
    def _student_mode_thread(self):
        """Thread de modo alumno - espera que presionen la tecla correcta"""
        note_events = self._notes_cache.get(self.current_song_path, [(0, [60]), (1, [62]), (2, [64])])
        
        for i, (timestamp, note_list) in enumerate(note_events):
            if not self.playing:
                break
            
            # ACTUALIZAR SCROLL DE LA PARTITURA
            self.root.after(0, lambda t=timestamp: self.update_staff_scroll(t))
            
            # Iluminar TODAS las notas del acorde/evento
            for note, vel in note_list:
                self.root.after(0, lambda n=note: self.highlight_key(n))
            
            # Progreso
            progress = int((i / len(note_events)) * 100)
            self.root.after(0, lambda p=progress: self.update_progress(p))
            
            # Esperar 2 segundos (simulando que toca)
            # TODO: Implementar detección real de MIDI input
            time.sleep(2.0)
            
            # Reproducir TODAS las notas del acorde CON VELOCIDAD SIMULTÁNEAMENTE
            sound_threads = []
            for note, vel in note_list:
                def play_concurrent(n, v):
                    self.piano_sound.play_note(n, v)
                thread = threading.Thread(target=play_concurrent, args=(note, vel), daemon=True)
                thread.start()
                sound_threads.append(thread)
            time.sleep(0.3)
            
            # Restaurar TODAS las notas
            for note, vel in note_list:
                self.root.after(0, lambda n=note: self.restore_key(n))
        
        self.playing = False
        self.root.after(0, lambda: self.stop_btn.config(state=tk.DISABLED))
        self.root.after(0, lambda: messagebox.showinfo("¡Completado!", "¡Bien hecho! Has terminado la lección"))
        # Resetear partitura
        self.root.after(0, lambda: self.update_staff_scroll(0))
    
    def _practice_thread(self):
        """Thread de práctica - reproduce automáticamente con timing real"""
        note_events = self._notes_cache.get(self.current_song_path, [(0, [60]), (500, [62]), (1000, [64])])
        
        print(f"\n🎹 Iniciando reproducción: {len(note_events)} eventos")
        
        start_time = time.time()
        last_timestamp = 0
        
        for i, (timestamp, note_list) in enumerate(note_events):
            if not self.playing:
                print("⏹ Reproducción detenida por usuario")
                break
            
            # Calcular cuánto tiempo esperar
            if i == 0:
                # Primera nota: empezar inmediatamente
                delay = 0
            else:
                # Calcular delay real entre eventos
                time_diff_ms = timestamp - last_timestamp
                delay = time_diff_ms / 1000.0  # Convertir ms a segundos
                
                # Aplicar velocidad de reproducción (dividir para hacer más rápido)
                delay = delay / self.playback_speed
                
                # Solo limitar delays extremadamente largos (silencios)
                if delay > 5.0:
                    delay = 5.0  # Máximo 5 segundos para silencios largos
                
                # Permitir delays muy cortos (acordes rápidos)
                # No hay mínimo - respetar el timing del MIDI
            
            # ACTUALIZAR SCROLL DE LA PARTITURA ANTES DE ESPERAR
            self.root.after(0, lambda t=timestamp: self.update_staff_scroll(t))
            
            if delay > 0:
                time.sleep(delay)
            
            last_timestamp = timestamp
            
            # Iluminar y tocar TODAS las notas del acorde CON VELOCIDAD
            note_names = [f"{n}(v{v})" for n, v in note_list]
            time_diff_ms = timestamp - last_timestamp if i > 0 else 0
            print(f"  ♪ t={timestamp}ms: Tocando {note_names} (Δt={time_diff_ms}ms, delay={delay:.3f}s)")
            
            # Tocar todas las notas SIMULTÁNEAMENTE usando threads
            sound_threads = []
            for note, vel in note_list:
                # Iluminar tecla
                self.root.after(0, lambda n=note: self.highlight_key(n))
                
                # Reproducir sonido en thread separado para simultaneidad
                def play_concurrent(n, v):
                    self.piano_sound.play_note(n, v)
                
                thread = threading.Thread(target=play_concurrent, args=(note, vel), daemon=True)
                thread.start()
                sound_threads.append(thread)
            
            # Actualizar progreso
            progress = int((i / len(note_events)) * 100)
            self.root.after(0, lambda p=progress: self.update_progress(p))
            
            # Restaurar notas después de 200ms (no bloqueante)
            for note, vel in note_list:
                self.root.after(200, lambda n=note: self.restore_key(n))
        
        elapsed = time.time() - start_time
        print(f"✅ Reproducción completada en {elapsed:.1f}s")
        
        self.playing = False
        self.root.after(0, lambda: self.stop_btn.config(state=tk.DISABLED))
        self.root.after(0, lambda: self.play_btn.config(state=tk.NORMAL))
        self.root.after(0, lambda: self.practice_btn.config(state=tk.NORMAL))
        self.root.after(0, lambda: self.update_progress(0))
        # Resetear partitura al inicio
        self.root.after(0, lambda: self.update_staff_scroll(0))
    
    def _auto_play_thread(self):
        """Thread de reproducción automática - reproduce el MIDI sin esperar input"""
        note_events = self._notes_cache.get(self.current_song_path, [(0, [60]), (500, [62]), (1000, [64])])
        
        print(f"\n▶️ Reproducción automática: {len(note_events)} eventos")
        
        start_time = time.time()
        last_timestamp = 0
        
        for i, (timestamp, note_list) in enumerate(note_events):
            if not self.playing:
                print("⏹ Reproducción detenida por usuario")
                break
            
            # Calcular delay entre eventos
            if i == 0:
                delay = 0
            else:
                time_diff_ms = timestamp - last_timestamp
                delay = time_diff_ms / 1000.0
                delay = delay / self.playback_speed
                
                # Limitar delays extremadamente largos
                if delay > 5.0:
                    delay = 5.0
            
            # Actualizar scroll ANTES de tocar
            self.root.after(0, lambda t=timestamp: self.update_staff_scroll(t))
            
            if delay > 0:
                time.sleep(delay)
            
            last_timestamp = timestamp
            
            # Log
            note_names = [f"{n}(v{v})" for n, v in note_list]
            print(f"  ♪ t={timestamp}ms: {note_names}")
            
            # Tocar todas las notas SIMULTÁNEAMENTE
            for note, vel in note_list:
                # Iluminar tecla
                self.root.after(0, lambda n=note: self.highlight_key(n))
                
                # Reproducir sonido en thread separado
                def play_concurrent(n, v):
                    self.piano_sound.play_note(n, v)
                
                thread = threading.Thread(target=play_concurrent, args=(note, vel), daemon=True)
                thread.start()
            
            # Actualizar progreso y estadísticas
            progress = int((i / len(note_events)) * 100)
            self.root.after(0, lambda p=progress: self.update_progress(p))
            
            # Actualizar stats: +10 puntos por nota, +5 por combo
            base_points = 10 * len(note_list)
            combo_bonus = min(self.combo * 5, 100)  # Máximo 100 de bonus
            self.root.after(0, lambda: self.add_score(base_points + combo_bonus))
            self.root.after(0, lambda: self.increment_notes_played())
            
            # Restaurar notas después de 200ms (no bloqueante)
            for note, vel in note_list:
                self.root.after(200, lambda n=note: self.restore_key(n))
        
        elapsed = time.time() - start_time
        print(f"✅ Reproducción automática completada en {elapsed:.1f}s")
        
        self.playing = False
        self.root.after(0, lambda: self.stop_btn.config(state=tk.DISABLED))
        self.root.after(0, lambda: self.play_btn.config(state=tk.NORMAL))
        self.root.after(0, lambda: self.practice_btn.config(state=tk.NORMAL))
        self.root.after(0, lambda: self.update_progress(0))
        self.root.after(0, lambda: self.update_staff_scroll(0))
    
    def start_teacher_mode(self):
        """Modo maestro - ilumina lo que tocas"""
        if not self.current_song_path:
            messagebox.showwarning("Aviso", "Carga una canción primero")
            return
        
        mode_msg = "🎼 Modo Maestro Iniciado\n\n"
        if self.use_virtual_keyboard:
            mode_msg += "Usando teclado virtual en pantalla\n"
            mode_msg += "Las teclas se iluminan al tocarlas\n"
            mode_msg += "Click para tocar libremente"
        else:
            mode_msg += "Toca tu teclado MIDI libremente\n"
            mode_msg += "Las teclas se iluminan automáticamente\n"
            mode_msg += "Perfecto para enseñar a otros"
        
        messagebox.showinfo("Modo Maestro", mode_msg)
        # En modo maestro no hay reproducción automática
        print("🎼 Modo Maestro: Toca libremente, las teclas se iluminarán")
    
    def update_progress(self, percent):
        """Actualiza barra de progreso (legacy)"""
        self.progress_bar.delete('all')
        w = self.progress_bar.winfo_width()
        if w > 2:
            fill_width = int(w * percent / 100)
            self.progress_bar.create_rectangle(
                0, 0, fill_width, 8,
                fill=ModernTheme.SECONDARY,
                outline=''
            )
        
        # Actualizar también la nueva barra de progreso con seek
        self.update_progress_bar(percent)
    
    def update_progress_bar(self, percent):
        """Actualiza la barra de progreso principal con porcentaje"""
        self.progress_canvas.delete('all')
        w = self.progress_canvas.winfo_width()
        h = self.progress_canvas.winfo_height()
        
        if w > 2:
            # Fondo
            self.progress_canvas.create_rectangle(
                0, 0, w, h,
                fill=ModernTheme.BG_LIGHT,
                outline=''
            )
            
            # Barra de progreso
            fill_width = int(w * percent / 100)
            if fill_width > 0:
                self.progress_canvas.create_rectangle(
                    0, 0, fill_width, h,
                    fill='#3b82f6',
                    outline=''
                )
            
            # Actualizar texto de porcentaje
            self.progress_text_label.config(text=f"{int(percent)}%")
    
    def on_progress_click(self, event):
        """Maneja el click en la barra de progreso para saltar a una posición"""
        if not self.current_song_path or not self._notes_cache.get(self.current_song_path):
            return
        
        w = self.progress_canvas.winfo_width()
        if w <= 0:
            return
        
        # Calcular porcentaje basado en la posición del click
        click_percent = (event.x / w) * 100
        
        # Obtener duración total de la canción
        note_events = self._notes_cache.get(self.current_song_path, [])
        if not note_events:
            return
        
        last_timestamp = note_events[-1][0]
        
        # Calcular timestamp objetivo
        target_time = int((click_percent / 100) * last_timestamp)
        
        # Actualizar scroll de la partitura
        self.update_staff_scroll(target_time)
        
        print(f"🎯 Salto a {int(click_percent)}% (t={target_time}ms)")
    
    def stop_playing(self):
        """Detiene reproducción y limpia estado"""
        self.playing = False
        self.stop_btn.config(state=tk.DISABLED)
        self.play_btn.config(state=tk.NORMAL)
        self.practice_btn.config(state=tk.NORMAL)
        
        # Detener todos los sonidos de pygame
        try:
            import pygame
            pygame.mixer.stop()  # Detiene todos los canales
        except:
            pass
        
        # Resetear progreso
        self.update_progress(0)
        
        # Restaurar todas las teclas
        for note in range(21, 109):
            self.restore_key(note)
    
    def reset_stats(self):
        """Resetea las estadísticas de práctica"""
        self.score = 0
        self.accuracy = 100.0  # Empieza en 100%
        self.combo = 0
        self.max_combo = 0
        self.notes_played = 0
        self.notes_correct = 0  # Notas tocadas correctamente
        self.notes_missed = 0   # Notas falladas
        self.total_notes = len(self._notes_cache.get(self.current_song_path, []))
        
        self.update_stats_display()
    
    def update_stats_display(self):
        """Actualiza la visualización de estadísticas"""
        self.score_label.config(text=str(self.score))
        self.accuracy_label.config(text=f"{int(self.accuracy)}%")
        self.combo_label.config(text=f"{self.combo}x")
        self.notes_played_label.config(text=f"{self.notes_played}/{self.total_notes}")
    
    def add_score(self, points):
        """Agrega puntos al score (nota correcta)"""
        self.score += points
        self.combo += 1
        self.notes_correct += 1
        if self.combo > self.max_combo:
            self.max_combo = self.combo
        
        # Recalcular precisión: notas correctas / notas procesadas
        self.update_accuracy()
        self.update_stats_display()
    
    def break_combo(self):
        """Rompe el combo actual (nota incorrecta)"""
        self.combo = 0
        self.notes_missed += 1
        
        # Recalcular precisión
        self.update_accuracy()
        self.update_stats_display()
    
    def update_accuracy(self):
        """Actualiza el porcentaje de precisión"""
        notes_attempted = self.notes_correct + self.notes_missed
        if notes_attempted > 0:
            self.accuracy = (self.notes_correct / notes_attempted) * 100
        else:
            self.accuracy = 100.0  # Si no se ha intentado nada, mantener 100%
    
    def increment_notes_played(self):
        """Incrementa el contador de notas tocadas (solo contador visual)"""
        self.notes_played += 1
        self.update_stats_display()
    
    def show_mode_selection_dialog(self):
        """Muestra diálogo elegante para seleccionar modo de práctica"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Selecciona Modo de Práctica")
        dialog.geometry("600x400")
        dialog.configure(bg=ModernTheme.BG_DARK)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Centrar en pantalla
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (600 // 2)
        y = (dialog.winfo_screenheight() // 2) - (400 // 2)
        dialog.geometry(f"600x400+{x}+{y}")
        
        # Título
        tk.Label(
            dialog,
            text="🎓 ¿Cómo quieres practicar?",
            font=('Segoe UI', 18, 'bold'),
            bg=ModernTheme.BG_DARK,
            fg=ModernTheme.TEXT_PRIMARY
        ).pack(pady=30)
        
        # Contenedor de botones
        btn_container = tk.Frame(dialog, bg=ModernTheme.BG_DARK)
        btn_container.pack(expand=True, fill=tk.BOTH, padx=40, pady=20)
        
        # Definir modos con iconos grandes
        modes = [
            {
                'name': '👨‍🎓 Aprendiz',
                'icon': '👨‍🎓',
                'desc': 'Aprende nota por nota\nEl sistema espera a que toques\ncada tecla correcta',
                'color': ModernTheme.INFO,
                'command': lambda: self.select_mode(dialog, 'student')
            },
            {
                'name': '🎹 Práctica',
                'icon': '🎹',
                'desc': 'Reproduce la canción\nIlumina las teclas mientras\nsuena el piano',
                'color': ModernTheme.SECONDARY,
                'command': lambda: self.select_mode(dialog, 'practice')
            },
            {
                'name': '🎼 Maestro',
                'icon': '🎼',
                'desc': 'Tú tocas, el sistema ilumina\nPerfecto para enseñar a otros\no practicar libremente',
                'color': ModernTheme.ACCENT,
                'command': lambda: self.select_mode(dialog, 'teacher')
            }
        ]
        
        # Crear columnas
        for i, mode in enumerate(modes):
            col = tk.Frame(btn_container, bg=ModernTheme.BG_DARK)
            col.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=10)
            
            # Card del modo
            card = tk.Frame(col, bg=mode['color'], cursor='hand2')
            card.pack(fill=tk.BOTH, expand=True)
            
            # Icono grande
            icon_label = tk.Label(
                card,
                text=mode['icon'],
                font=('Segoe UI', 60),
                bg=mode['color'],
                fg=ModernTheme.TEXT_PRIMARY
            )
            icon_label.pack(pady=(20, 10))
            
            # Nombre
            name_label = tk.Label(
                card,
                text=mode['name'],
                font=('Segoe UI', 14, 'bold'),
                bg=mode['color'],
                fg=ModernTheme.TEXT_PRIMARY
            )
            name_label.pack(pady=5)
            
            # Descripción
            desc_label = tk.Label(
                card,
                text=mode['desc'],
                font=('Segoe UI', 9),
                bg=mode['color'],
                fg=ModernTheme.TEXT_SECONDARY,
                justify=tk.CENTER,
                wraplength=150
            )
            desc_label.pack(pady=(5, 20))
            
            # Hacer clickeable toda la card
            for widget in [card, icon_label, name_label, desc_label]:
                widget.bind('<Button-1>', lambda e, cmd=mode['command']: cmd())
                widget.bind('<Enter>', lambda e, c=card: c.config(relief=tk.RAISED, bd=3))
                widget.bind('<Leave>', lambda e, c=card: c.config(relief=tk.FLAT, bd=0))
    
    def select_mode(self, dialog, mode):
        """Selecciona un modo y cierra el diálogo"""
        dialog.destroy()
        self.active_mode = mode
        
        # Ejecutar el modo correspondiente
        if mode == 'student':
            self.start_student_mode()
        elif mode == 'practice':
            self.start_practice_mode()
        elif mode == 'teacher':
            self.start_teacher_mode()
    
    def on_speed_change(self, event=None):
        """Maneja el cambio de velocidad de reproducción"""
        selection = self.speed_selector.get()
        # Extraer valor numérico (ej: "1.5x" -> 1.5)
        self.playback_speed = float(selection.replace('x', ''))
        
        # Mostrar feedback visual
        current_text = self.metadata_label.cget('text')
        self.metadata_label.config(text=f"⚡ Velocidad: {selection}")
        self.root.after(2000, lambda: self.metadata_label.config(text=current_text))
    
    def on_sound_change(self, event=None):
        """Maneja el cambio de perfil de sonido de piano"""
        selection = self.sound_selector.get()
        
        # Mapear selección a perfil
        profile_map = {
            '� Acoustic Grand Piano': 'acoustic',
            '�🎹 Piano de Cola': 'grand',
            '✨ Piano Brillante': 'bright',
            '🌙 Piano Suave': 'mellow',
            '⚡ Piano Eléctrico': 'electric'
        }
        
        profile = profile_map.get(selection, 'acoustic')
        self.piano_sound.set_profile(profile)
        
        # Mostrar feedback visual en el label de metadata
        current_text = self.metadata_label.cget('text')
        self.metadata_label.config(text=f"✅ Sonido: {selection}")
        # Restaurar texto original después de 2 segundos
        self.root.after(2000, lambda: self.metadata_label.config(text=current_text))
    
    def show_settings(self):
        """Muestra panel de configuración"""
        settings = tk.Toplevel(self.root)
        settings.title("⚙️ Configuración")
        settings.geometry("600x700")
        settings.configure(bg=ModernTheme.BG_DARK)
        settings.transient(self.root)
        
        # Centrar
        settings.update_idletasks()
        x = (settings.winfo_screenwidth() // 2) - (300)
        y = (settings.winfo_screenheight() // 2) - (350)
        settings.geometry(f"600x700+{x}+{y}")
        
        # Título
        tk.Label(
            settings,
            text="⚙️ Configuración",
            font=('Segoe UI', 16, 'bold'),
            bg=ModernTheme.BG_DARK,
            fg=ModernTheme.TEXT_PRIMARY
        ).pack(pady=20)
        
        # Contenedor scrollable
        canvas = tk.Canvas(settings, bg=ModernTheme.BG_DARK, highlightthickness=0)
        scrollbar = tk.Scrollbar(settings, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=ModernTheme.BG_DARK)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True, padx=20)
        scrollbar.pack(side="right", fill="y")
        
        # ========== SECCIÓN: AUDIO ==========
        audio_section = tk.Frame(scrollable_frame, bg=ModernTheme.BG_CARD)
        audio_section.pack(fill=tk.X, pady=10, padx=10, ipady=10)
        
        tk.Label(
            audio_section,
            text="🔊 Audio",
            font=('Segoe UI', 12, 'bold'),
            bg=ModernTheme.BG_CARD,
            fg=ModernTheme.TEXT_PRIMARY
        ).pack(anchor=tk.W, padx=10, pady=(5, 10))
        
        # Volumen
        vol_frame = tk.Frame(audio_section, bg=ModernTheme.BG_CARD)
        vol_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(
            vol_frame,
            text="Volumen:",
            font=('Segoe UI', 10),
            bg=ModernTheme.BG_CARD,
            fg=ModernTheme.TEXT_PRIMARY
        ).pack(side=tk.LEFT)
        
        volume_slider = tk.Scale(
            vol_frame,
            from_=0,
            to=100,
            orient=tk.HORIZONTAL,
            bg=ModernTheme.BG_CARD,
            fg=ModernTheme.TEXT_PRIMARY,
            highlightthickness=0,
            command=lambda v: setattr(self.piano_sound, 'volume', float(v)/100)
        )
        volume_slider.set(50)
        volume_slider.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=10)
        
        # ========== SECCIÓN: DIGITACIÓN ==========
        finger_section = tk.Frame(scrollable_frame, bg=ModernTheme.BG_CARD)
        finger_section.pack(fill=tk.X, pady=10, padx=10, ipady=10)
        
        tk.Label(
            finger_section,
            text="✋ Digitación",
            font=('Segoe UI', 12, 'bold'),
            bg=ModernTheme.BG_CARD,
            fg=ModernTheme.TEXT_PRIMARY
        ).pack(anchor=tk.W, padx=10, pady=(5, 10))
        
        fingering_var = tk.BooleanVar(value=self.show_fingering)
        
        def toggle_fingering():
            self.show_fingering = fingering_var.get()
            self.config['show_fingering'] = self.show_fingering
            self.draw_keyboard()
        
        tk.Checkbutton(
            finger_section,
            text="Mostrar números de dedos en teclas",
            variable=fingering_var,
            command=toggle_fingering,
            bg=ModernTheme.BG_CARD,
            fg=ModernTheme.TEXT_PRIMARY,
            selectcolor=ModernTheme.BG_LIGHT,
            font=('Segoe UI', 10)
        ).pack(anchor=tk.W, padx=10, pady=5)
        
        # Info de colores
        tk.Label(
            finger_section,
            text="Colores: 1=Cyan, 2=Azul, 3=Marino, 4=Violeta, 5=Magenta",
            font=('Segoe UI', 8),
            bg=ModernTheme.BG_CARD,
            fg=ModernTheme.TEXT_MUTED
        ).pack(anchor=tk.W, padx=10, pady=5)
        
        # ========== SECCIÓN: PIANO ==========
        piano_section = tk.Frame(scrollable_frame, bg=ModernTheme.BG_CARD)
        piano_section.pack(fill=tk.X, pady=10, padx=10, ipady=10)
        
        tk.Label(
            piano_section,
            text="🎹 Piano",
            font=('Segoe UI', 12, 'bold'),
            bg=ModernTheme.BG_CARD,
            fg=ModernTheme.TEXT_PRIMARY
        ).pack(anchor=tk.W, padx=10, pady=(5, 10))
        
        # Número de teclas
        keys_frame = tk.Frame(piano_section, bg=ModernTheme.BG_CARD)
        keys_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(
            keys_frame,
            text="Número de teclas:",
            font=('Segoe UI', 10),
            bg=ModernTheme.BG_CARD,
            fg=ModernTheme.TEXT_PRIMARY
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        keys_var = tk.IntVar(value=self.config.get('num_keys', 61))
        
        keys_options = [25, 37, 49, 61, 76, 88]
        for num_keys in keys_options:
            rb = tk.Radiobutton(
                keys_frame,
                text=str(num_keys),
                variable=keys_var,
                value=num_keys,
                bg=ModernTheme.BG_CARD,
                fg=ModernTheme.TEXT_PRIMARY,
                selectcolor=ModernTheme.BG_LIGHT,
                font=('Segoe UI', 9),
                command=lambda k=num_keys: self.update_num_keys(k)
            )
            rb.pack(side=tk.LEFT, padx=5)
        
        tk.Label(
            piano_section,
            text="Cambia el tamaño del piano virtual en pantalla",
            font=('Segoe UI', 8),
            bg=ModernTheme.BG_CARD,
            fg=ModernTheme.TEXT_MUTED
        ).pack(anchor=tk.W, padx=10, pady=5)
        
        # ========== SECCIÓN: TECLADO MIDI ==========
        midi_section = tk.Frame(scrollable_frame, bg=ModernTheme.BG_CARD)
        midi_section.pack(fill=tk.X, pady=10, padx=10, ipady=10)
        
        tk.Label(
            midi_section,
            text="�️ Teclado MIDI",
            font=('Segoe UI', 12, 'bold'),
            bg=ModernTheme.BG_CARD,
            fg=ModernTheme.TEXT_PRIMARY
        ).pack(anchor=tk.W, padx=10, pady=(5, 10))
        
        virtual_var = tk.BooleanVar(value=self.use_virtual_keyboard)
        
        def toggle_virtual():
            self.use_virtual_keyboard = virtual_var.get()
            status = "VIRTUAL" if self.use_virtual_keyboard else "FÍSICO"
            messagebox.showinfo("Teclado", f"Usando teclado {status}")
        
        tk.Checkbutton(
            midi_section,
            text="Usar solo teclado virtual (sin MIDI físico)",
            variable=virtual_var,
            command=toggle_virtual,
            bg=ModernTheme.BG_CARD,
            fg=ModernTheme.TEXT_PRIMARY,
            selectcolor=ModernTheme.BG_LIGHT,
            font=('Segoe UI', 10)
        ).pack(anchor=tk.W, padx=10, pady=5)
        
        tk.Label(
            midi_section,
            text="Útil para dar clases sin teclado MIDI conectado",
            font=('Segoe UI', 8),
            bg=ModernTheme.BG_CARD,
            fg=ModernTheme.TEXT_MUTED
        ).pack(anchor=tk.W, padx=10, pady=5)
        
        # ========== SECCIÓN: LEDs ==========
        led_section = tk.Frame(scrollable_frame, bg=ModernTheme.BG_CARD)
        led_section.pack(fill=tk.X, pady=10, padx=10, ipady=10)
        
        tk.Label(
            led_section,
            text="💡 LEDs",
            font=('Segoe UI', 12, 'bold'),
            bg=ModernTheme.BG_CARD,
            fg=ModernTheme.TEXT_PRIMARY
        ).pack(anchor=tk.W, padx=10, pady=(5, 10))
        
        tk.Label(
            led_section,
            text="Brillo:",
            font=('Segoe UI', 10),
            bg=ModernTheme.BG_CARD,
            fg=ModernTheme.TEXT_PRIMARY
        ).pack(anchor=tk.W, padx=10, pady=5)
        
        brightness_slider = tk.Scale(
            led_section,
            from_=0,
            to=255,
            orient=tk.HORIZONTAL,
            bg=ModernTheme.BG_CARD,
            fg=ModernTheme.TEXT_PRIMARY,
            highlightthickness=0
        )
        brightness_slider.set(128)
        brightness_slider.pack(fill=tk.X, padx=10, pady=5)
        
        # Botón cerrar
        def save_and_close():
            self.save_config()
            settings.destroy()
        
        tk.Button(
            settings,
            text="✅ Guardar y Cerrar",
            command=save_and_close,
            bg=ModernTheme.SECONDARY,
            fg=ModernTheme.TEXT_PRIMARY,
            font=('Segoe UI', 11, 'bold'),
            relief=tk.FLAT,
            padx=20,
            pady=10,
            cursor='hand2'
        ).pack(pady=20)
    
    def update_num_keys(self, num_keys):
        """Actualiza el número de teclas del piano"""
        self.num_keys = num_keys
        self.config['num_keys'] = num_keys
        self.draw_keyboard()
        messagebox.showinfo("Piano", f"Piano configurado con {num_keys} teclas")
    
    def run(self):
        """Ejecuta la aplicación"""
        self.root.mainloop()


if __name__ == "__main__":
    print("=" * 60)
    print("🎹 HowToPiano - GUI COMPACTA E INTELIGENTE")
    print("=" * 60)
    print("\n✨ Características:")
    print("  • Layout compacto - todo visible")
    print("  • Preescucha de archivos MIDI")
    print("  • Modos solo cuando hay canción")
    print("  • Partitura y teclado grandes")
    print("  • Diseño eficiente\n")
    
    app = CompactHowToPianoGUI()
    app.run()
