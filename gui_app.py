#!/usr/bin/env python3
"""
HowToPiano - Aplicación GUI Principal
Interfaz gráfica completa con tkinter
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import os
from pathlib import Path
from typing import Optional, List, Dict
import threading
import time

# Importar módulos del proyecto
try:
    from src.midi_reader import MidiReader
    from src.led_controller import LEDController
    from src.note_mapper import NoteMapper
    HAS_HARDWARE = True
except ImportError:
    HAS_HARDWARE = False
    print("⚠ Módulos hardware no disponibles - Modo simulación")


class HowToPianoGUI:
    """Aplicación GUI principal"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🎹 HowToPiano - Sistema de Aprendizaje Musical")
        self.root.geometry("1000x700")
        self.root.configure(bg='#1e1e1e')
        
        # Variables
        self.current_song = None
        self.midi_reader = None
        self.led_controller = None
        self.note_mapper = None
        self.playing = False
        self.practice_thread = None
        
        # Configuración
        self.config = self.load_config()
        self.recent_songs = self.load_recent_songs()
        
        # Crear interfaz
        self.create_widgets()
        
        # Inicializar hardware
        if HAS_HARDWARE:
            self.init_hardware()
    
    def load_config(self) -> dict:
        """Carga configuración"""
        try:
            with open('config/config.json', 'r') as f:
                return json.load(f)
        except:
            return {
                'keyboard_type': 'piano_88',
                'num_leds': 88,
                'num_keys': 88,
                'brightness': 0.3,
                'led_mode': 'full',
                'usb_path': '/media/pi/'
            }
    
    def save_config(self):
        """Guarda configuración"""
        try:
            os.makedirs('config', exist_ok=True)
            with open('config/config.json', 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Error guardando config: {e}")
    
    def load_recent_songs(self) -> list:
        """Carga canciones recientes"""
        try:
            with open('config/recent.json', 'r') as f:
                return json.load(f)
        except:
            return []
    
    def save_recent_song(self, filepath: str):
        """Guarda canción en recientes"""
        if filepath not in self.recent_songs:
            self.recent_songs.insert(0, filepath)
            self.recent_songs = self.recent_songs[:10]  # Max 10
            
            os.makedirs('config', exist_ok=True)
            with open('config/recent.json', 'w') as f:
                json.dump(self.recent_songs, f)
    
    def create_widgets(self):
        """Crea todos los widgets de la interfaz"""
        
        # ============ BARRA SUPERIOR ============
        top_frame = tk.Frame(self.root, bg='#2d2d2d', height=60)
        top_frame.pack(fill=tk.X, padx=0, pady=0)
        top_frame.pack_propagate(False)
        
        # Título
        title = tk.Label(
            top_frame, 
            text="🎹 HowToPiano",
            font=('Arial', 20, 'bold'),
            bg='#2d2d2d',
            fg='#00ff88'
        )
        title.pack(side=tk.LEFT, padx=20, pady=10)
        
        # Estado
        self.status_label = tk.Label(
            top_frame,
            text="Sin partitura cargada",
            font=('Arial', 10),
            bg='#2d2d2d',
            fg='#888888'
        )
        self.status_label.pack(side=tk.LEFT, padx=20)
        
        # Botón configuración
        config_btn = tk.Button(
            top_frame,
            text="⚙ Configuración",
            command=self.show_config_window,
            bg='#444444',
            fg='white',
            font=('Arial', 10),
            relief=tk.FLAT,
            padx=15,
            pady=5,
            cursor='hand2'
        )
        config_btn.pack(side=tk.RIGHT, padx=10)
        
        # ============ CONTENEDOR PRINCIPAL ============
        main_container = tk.Frame(self.root, bg='#1e1e1e')
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # ============ PANEL IZQUIERDO - PARTITURAS ============
        left_panel = tk.Frame(main_container, bg='#2d2d2d', width=300)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 10))
        left_panel.pack_propagate(False)
        
        # Título sección
        tk.Label(
            left_panel,
            text="📁 Partituras",
            font=('Arial', 14, 'bold'),
            bg='#2d2d2d',
            fg='white'
        ).pack(pady=(10, 5), padx=10, anchor=tk.W)
        
        # Botones de búsqueda
        btn_frame = tk.Frame(left_panel, bg='#2d2d2d')
        btn_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Button(
            btn_frame,
            text="🔍 Buscar MIDI",
            command=self.browse_midi_files,
            bg='#0066cc',
            fg='white',
            font=('Arial', 9),
            relief=tk.FLAT,
            cursor='hand2'
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        tk.Button(
            btn_frame,
            text="📂 USB",
            command=self.scan_usb_files,
            bg='#0066cc',
            fg='white',
            font=('Arial', 9),
            relief=tk.FLAT,
            cursor='hand2'
        ).pack(side=tk.LEFT)
        
        # Lista recientes
        tk.Label(
            left_panel,
            text="⏱ Recientes",
            font=('Arial', 10, 'bold'),
            bg='#2d2d2d',
            fg='#aaaaaa'
        ).pack(pady=(15, 5), padx=10, anchor=tk.W)
        
        # Listbox recientes
        recent_frame = tk.Frame(left_panel, bg='#2d2d2d')
        recent_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        scrollbar = tk.Scrollbar(recent_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.recent_listbox = tk.Listbox(
            recent_frame,
            bg='#1a1a1a',
            fg='white',
            font=('Arial', 9),
            selectbackground='#0066cc',
            yscrollcommand=scrollbar.set,
            relief=tk.FLAT
        )
        self.recent_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.recent_listbox.yview)
        
        self.recent_listbox.bind('<Double-Button-1>', self.load_from_recent)
        
        self.update_recent_list()
        
        # ============ PANEL DERECHO - CONTROL Y VISUALIZACIÓN ============
        right_panel = tk.Frame(main_container, bg='#2d2d2d')
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Información canción actual
        info_frame = tk.Frame(right_panel, bg='#3a3a3a', height=100)
        info_frame.pack(fill=tk.X, padx=15, pady=15)
        info_frame.pack_propagate(False)
        
        self.song_title_label = tk.Label(
            info_frame,
            text="Sin partitura cargada",
            font=('Arial', 16, 'bold'),
            bg='#3a3a3a',
            fg='white'
        )
        self.song_title_label.pack(pady=(10, 5))
        
        self.song_info_label = tk.Label(
            info_frame,
            text="Carga un archivo MIDI para comenzar",
            font=('Arial', 10),
            bg='#3a3a3a',
            fg='#888888'
        )
        self.song_info_label.pack()
        
        # ============ MODOS DE PRÁCTICA ============
        modes_frame = tk.LabelFrame(
            right_panel,
            text="🎓 Modos de Aprendizaje",
            font=('Arial', 12, 'bold'),
            bg='#2d2d2d',
            fg='white',
            relief=tk.FLAT
        )
        modes_frame.pack(fill=tk.X, padx=15, pady=10)
        
        # Descripción de cada modo
        modes_info = [
            ("👨‍🎓 Modo Alumno", "Espera cada X acordes para que practiques", self.start_student_mode),
            ("🎹 Modo Práctica", "Ilumina las teclas pero no espera", self.start_practice_mode),
            ("🎼 Modo Maestro", "Ilumina solo las teclas que presionas", self.start_teacher_mode)
        ]
        
        for title, desc, command in modes_info:
            mode_btn_frame = tk.Frame(modes_frame, bg='#2d2d2d')
            mode_btn_frame.pack(fill=tk.X, padx=10, pady=5)
            
            btn = tk.Button(
                mode_btn_frame,
                text=title,
                command=command,
                bg='#0066cc',
                fg='white',
                font=('Arial', 11, 'bold'),
                relief=tk.FLAT,
                cursor='hand2',
                width=20
            )
            btn.pack(side=tk.LEFT, padx=(0, 10))
            
            tk.Label(
                mode_btn_frame,
                text=desc,
                bg='#2d2d2d',
                fg='#aaaaaa',
                font=('Arial', 9)
            ).pack(side=tk.LEFT)
        
        # Configuración de práctica
        practice_config = tk.Frame(modes_frame, bg='#2d2d2d')
        practice_config.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(
            practice_config,
            text="Esperar cada:",
            bg='#2d2d2d',
            fg='white',
            font=('Arial', 9)
        ).pack(side=tk.LEFT)
        
        self.wait_chords_var = tk.IntVar(value=4)
        wait_spinner = tk.Spinbox(
            practice_config,
            from_=1,
            to=16,
            textvariable=self.wait_chords_var,
            width=5,
            font=('Arial', 9),
            bg='#1a1a1a',
            fg='white',
            relief=tk.FLAT
        )
        wait_spinner.pack(side=tk.LEFT, padx=5)
        
        tk.Label(
            practice_config,
            text="acordes (Modo Alumno)",
            bg='#2d2d2d',
            fg='white',
            font=('Arial', 9)
        ).pack(side=tk.LEFT)
        
        # ============ PARTITURA VISUAL ============
        score_frame = tk.LabelFrame(
            right_panel,
            text="🎼 Partitura",
            font=('Arial', 10, 'bold'),
            bg='#2d2d2d',
            fg='white',
            relief=tk.FLAT
        )
        score_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(10, 5))
        
        # Canvas para partitura (más grande)
        self.score_canvas = tk.Canvas(
            score_frame,
            bg='#ffffff',
            height=180,
            highlightthickness=0
        )
        self.score_canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Bind para redibujar al cambiar tamaño
        self.score_canvas.bind('<Configure>', lambda e: self.draw_staff())
        
        self.draw_staff()
        
        # Mostrar notas de ejemplo al iniciar
        self.root.after(500, lambda: self.update_score_display(
            [60],  # Do central actual
            [62, 64, 65, 67, 69, 71, 72]  # Próximas notas
        ))
        
        # ============ VISUALIZACIÓN TECLADO ============
        keyboard_frame = tk.LabelFrame(
            right_panel,
            text="🎹 Teclado Virtual (Clickeable)",
            font=('Arial', 12, 'bold'),
            bg='#2d2d2d',
            fg='white',
            relief=tk.FLAT,
            height=120
        )
        keyboard_frame.pack(fill=tk.X, padx=15, pady=(5, 10))
        keyboard_frame.pack_propagate(False)
        
        # Canvas para dibujar teclado
        self.keyboard_canvas = tk.Canvas(
            keyboard_frame,
            bg='#1a1a1a',
            highlightthickness=0
        )
        self.keyboard_canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Hacer teclado clickeable
        self.keyboard_canvas.bind('<Button-1>', self.on_keyboard_click)
        
        # Diccionario para mapear teclas
        self.key_rectangles = {}  # {note: (x1, y1, x2, y2, is_black)}
        
        self.draw_keyboard()
        
        # ============ CONTROLES DE REPRODUCCIÓN ============
        controls_frame = tk.Frame(right_panel, bg='#2d2d2d')
        controls_frame.pack(fill=tk.X, padx=15, pady=10)
        
        # Botón STOP grande
        self.stop_btn = tk.Button(
            controls_frame,
            text="⏹ DETENER",
            command=self.stop_playing,
            bg='#cc0000',
            fg='white',
            font=('Arial', 12, 'bold'),
            relief=tk.FLAT,
            cursor='hand2',
            state=tk.DISABLED,
            height=2
        )
        self.stop_btn.pack(fill=tk.X)
        
        # Barra de progreso
        progress_frame = tk.Frame(right_panel, bg='#2d2d2d')
        progress_frame.pack(fill=tk.X, padx=15, pady=5)
        
        tk.Label(
            progress_frame,
            text="Progreso:",
            bg='#2d2d2d',
            fg='white',
            font=('Arial', 9)
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            mode='determinate',
            length=300
        )
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.progress_label = tk.Label(
            progress_frame,
            text="0%",
            bg='#2d2d2d',
            fg='white',
            font=('Arial', 9)
        )
        self.progress_label.pack(side=tk.LEFT, padx=(10, 0))
    
    def draw_keyboard(self):
        """Dibuja el teclado virtual"""
        self.keyboard_canvas.delete('all')
        self.key_rectangles.clear()
        
        canvas_width = self.keyboard_canvas.winfo_width()
        canvas_height = self.keyboard_canvas.winfo_height()
        
        if canvas_width < 10:  # No inicializado
            canvas_width = 700
            canvas_height = 150
        
        num_white_keys = 52  # 88 teclas = 52 blancas
        white_key_width = canvas_width / num_white_keys
        white_key_height = canvas_height * 0.9
        black_key_width = white_key_width * 0.6
        black_key_height = white_key_height * 0.6
        
        # Mapeo de teclas blancas a notas MIDI (empezando en A0 = 21)
        white_note_offsets = [0, 2, 3, 5, 7, 8, 10]  # A B C D E F G
        
        # Dibujar teclas blancas
        for i in range(num_white_keys):
            octave = i // 7
            note_in_octave = white_note_offsets[i % 7]
            midi_note = 21 + (octave * 12) + note_in_octave
            
            x = i * white_key_width
            x2 = x + white_key_width
            
            self.keyboard_canvas.create_rectangle(
                x, 0, x2, white_key_height,
                fill='white',
                outline='#333333',
                tags=f'key_{midi_note}'
            )
            
            # Guardar coordenadas
            self.key_rectangles[midi_note] = (x, 0, x2, white_key_height, False)
        
        # Dibujar teclas negras (patrón repetitivo)
        black_key_pattern = [1, 1, 0, 1, 1, 1, 0]  # En cada octava (después de A B - C# D# - F G A)
        black_note_offsets = [1, 4, 6, 9, 11]  # A# C# D# F# G# en octava
        black_idx_in_octave = 0
        
        for i in range(num_white_keys - 1):
            if black_key_pattern[i % 7]:
                octave = i // 7
                
                # Calcular nota MIDI de la tecla negra
                if i % 7 < 2:  # A# o C#
                    black_offset = black_note_offsets[i % 7]
                elif i % 7 == 3:  # D#
                    black_offset = black_note_offsets[2]
                elif i % 7 == 4:  # F#
                    black_offset = black_note_offsets[3]
                else:  # G#
                    black_offset = black_note_offsets[4]
                
                midi_note = 21 + (octave * 12) + black_offset
                
                x = (i + 0.7) * white_key_width
                x2 = x + black_key_width
                
                self.keyboard_canvas.create_rectangle(
                    x, 0, x2, black_key_height,
                    fill='black',
                    outline='#111111',
                    tags=f'key_{midi_note}'
                )
                
                # Guardar coordenadas
                self.key_rectangles[midi_note] = (x, 0, x2, black_key_height, True)
                black_idx_in_octave += 1
    
    def highlight_key(self, note: int, color: str = '#00ff88'):
        """Ilumina una tecla en el teclado virtual"""
        try:
            self.keyboard_canvas.itemconfig(f'key_{note}', fill=color)
            
            # También iluminar LED físico si está disponible
            if self.led_controller and HAS_HARDWARE:
                led_idx = self.note_mapper.note_to_led(note)
                if led_idx is not None:
                    # Convertir color hex a RGB
                    r = int(color[1:3], 16)
                    g = int(color[3:5], 16)
                    b = int(color[5:7], 16)
                    self.led_controller.set_led(led_idx, (r, g, b))
        except Exception as e:
            print(f"Error iluminando tecla {note}: {e}")
    
    def clear_keyboard_highlights(self):
        """Limpia todas las iluminaciones"""
        # Restaurar colores originales
        for note, (x1, y1, x2, y2, is_black) in self.key_rectangles.items():
            color = 'black' if is_black else 'white'
            self.keyboard_canvas.itemconfig(f'key_{note}', fill=color)
        
        # Apagar LEDs físicos
        if self.led_controller and HAS_HARDWARE:
            self.led_controller.clear_all()
    
    def browse_midi_files(self):
        """Abre diálogo para buscar archivos MIDI"""
        filepath = filedialog.askopenfilename(
            title="Seleccionar archivo MIDI",
            filetypes=[
                ("Archivos MIDI", "*.mid *.midi"),
                ("Todos los archivos", "*.*")
            ]
        )
        
        if filepath:
            self.load_song(filepath)
    
    def scan_usb_files(self):
        """Escanea USB en busca de archivos MIDI"""
        usb_path = self.config.get('usb_path', '/media/pi/')
        
        if not os.path.exists(usb_path):
            messagebox.showwarning(
                "USB no encontrado",
                f"No se encontró el directorio USB: {usb_path}\n\n"
                "Configura la ruta correcta en Configuración."
            )
            return
        
        # Buscar archivos .mid recursivamente
        midi_files = []
        for root, dirs, files in os.walk(usb_path):
            for file in files:
                if file.lower().endswith(('.mid', '.midi')):
                    midi_files.append(os.path.join(root, file))
        
        if not midi_files:
            messagebox.showinfo(
                "Sin archivos",
                "No se encontraron archivos MIDI en el USB"
            )
            return
        
        # Mostrar popup de selección
        self.show_midi_selection_popup(midi_files)
    
    def show_midi_selection_popup(self, files: List[str]):
        """Muestra popup con lista de archivos MIDI"""
        popup = tk.Toplevel(self.root)
        popup.title("Archivos MIDI en USB")
        popup.geometry("500x400")
        popup.configure(bg='#2d2d2d')
        
        tk.Label(
            popup,
            text="📁 Selecciona un archivo",
            font=('Arial', 12, 'bold'),
            bg='#2d2d2d',
            fg='white'
        ).pack(pady=10)
        
        # Listbox con scrollbar
        list_frame = tk.Frame(popup, bg='#2d2d2d')
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        listbox = tk.Listbox(
            list_frame,
            bg='#1a1a1a',
            fg='white',
            font=('Arial', 10),
            selectbackground='#0066cc',
            yscrollcommand=scrollbar.set
        )
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=listbox.yview)
        
        # Llenar listbox
        for f in files:
            listbox.insert(tk.END, os.path.basename(f))
        
        def on_select():
            selection = listbox.curselection()
            if selection:
                selected_file = files[selection[0]]
                popup.destroy()
                self.load_song(selected_file)
        
        # Botón cargar
        tk.Button(
            popup,
            text="✓ Cargar Seleccionado",
            command=on_select,
            bg='#0066cc',
            fg='white',
            font=('Arial', 10, 'bold'),
            cursor='hand2'
        ).pack(pady=10)
        
        listbox.bind('<Double-Button-1>', lambda e: on_select())
    
    def load_from_recent(self, event=None):
        """Carga canción desde lista de recientes"""
        selection = self.recent_listbox.curselection()
        if selection:
            filepath = self.recent_songs[selection[0]]
            if os.path.exists(filepath):
                self.load_song(filepath)
            else:
                messagebox.showerror(
                    "Archivo no encontrado",
                    f"El archivo ya no existe:\n{filepath}"
                )
                self.recent_songs.remove(filepath)
                self.update_recent_list()
    
    def load_song(self, filepath: str):
        """Carga un archivo MIDI"""
        try:
            self.current_song = filepath
            self.midi_reader = MidiReader(filepath) if HAS_HARDWARE else None
            
            # Actualizar UI
            filename = os.path.basename(filepath)
            self.song_title_label.config(text=filename)
            self.song_info_label.config(text=f"📍 {filepath}")
            self.status_label.config(
                text=f"✓ Cargado: {filename}",
                fg='#00ff88'
            )
            
            # Guardar en recientes
            self.save_recent_song(filepath)
            self.update_recent_list()
            
            messagebox.showinfo(
                "¡Listo!",
                f"Partitura cargada:\n{filename}\n\n"
                "Selecciona un modo de aprendizaje para comenzar."
            )
            
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"No se pudo cargar el archivo:\n{str(e)}"
            )
    
    def update_recent_list(self):
        """Actualiza lista de recientes en UI"""
        self.recent_listbox.delete(0, tk.END)
        for song in self.recent_songs:
            self.recent_listbox.insert(tk.END, os.path.basename(song))
    
    def start_student_mode(self):
        """Modo Alumno - Espera cada X acordes"""
        if not self.current_song:
            messagebox.showwarning("Sin partitura", "Carga un archivo MIDI primero")
            return
        
        self.playing = True
        self.stop_btn.config(state=tk.NORMAL)
        self.status_label.config(text="▶ Modo Alumno activo", fg='#00ff88')
        
        wait_chords = self.wait_chords_var.get()
        
        # Ejecutar en thread separado
        self.practice_thread = threading.Thread(
            target=self._student_mode_thread,
            args=(wait_chords,),
            daemon=True
        )
        self.practice_thread.start()
    
    def _student_mode_thread(self, wait_chords: int):
        """Thread del modo alumno - Espera que toques cada X acordes"""
        if not self.current_song:
            self.root.after(0, lambda: messagebox.showwarning("Error", "No hay canción cargada"))
            self.playing = False
            return
        
        try:
            # Extraer notas de la canción
            notes = self._extract_notes_from_song()
            if not notes:
                self.root.after(0, lambda: messagebox.showwarning("Error", "No se encontraron notas en la canción"))
                self.playing = False
                return
            
            # Agrupar en bloques
            total_notes = len(notes)
            chord_index = 0
            notes_shown = 0
            
            self.root.after(0, lambda: self.update_status("▶ Modo Alumno - Toca las notas iluminadas", '#00ff88'))
            
            while self.playing and notes_shown < total_notes:
                # Obtener siguiente bloque de notas
                end_index = min(notes_shown + wait_chords, total_notes)
                current_block = notes[notes_shown:end_index]
                
                # Actualizar partitura visual
                upcoming = notes[end_index:end_index+10] if end_index < total_notes else []
                self.root.after(0, lambda cb=current_block, up=upcoming: self.update_score_display(cb, up))
                
                # Iluminar teclas del bloque
                for note in current_block:
                    self.root.after(0, lambda n=note: self.highlight_key(n, '#00ff88'))
                
                # Actualizar progreso
                progress = int((notes_shown / total_notes) * 100)
                self.root.after(0, lambda p=progress: self.update_progress(p))
                
                # Esperar que el usuario toque las notas (simulado con tiempo)
                # En implementación real, esperarías input MIDI
                time.sleep(2.0 * wait_chords)  # 2 segundos por nota
                
                # Limpiar teclas
                self.root.after(0, self.clear_keyboard_highlights)
                
                # Avanzar
                notes_shown = end_index
                chord_index += 1
                
                # Pequeña pausa entre bloques
                time.sleep(0.5)
            
            # Finalizado
            self.root.after(0, lambda: messagebox.showinfo(
                "¡Completado!",
                f"Has completado la canción en Modo Alumno\n\n"
                f"Total de notas: {total_notes}\n"
                f"Bloques completados: {chord_index}"
            ))
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Error en modo alumno: {e}"))
        finally:
            self.playing = False
            self.root.after(0, lambda: self.stop_btn.config(state=tk.DISABLED))
            self.root.after(0, self.clear_keyboard_highlights)
            self.root.after(0, lambda: self.update_status("⏸ Detenido", '#888888'))
    
    def start_practice_mode(self):
        """Modo Práctica - Ilumina sin esperar"""
        if not self.current_song:
            messagebox.showwarning("Sin partitura", "Carga un archivo MIDI primero")
            return
        
        self.playing = True
        self.stop_btn.config(state=tk.NORMAL)
        self.status_label.config(text="▶ Modo Práctica activo", fg='#ffaa00')
        
        self.practice_thread = threading.Thread(
            target=self._practice_mode_thread,
            daemon=True
        )
        self.practice_thread.start()
    
    def _practice_mode_thread(self):
        """Thread del modo práctica - Ilumina sin esperar"""
        if not self.current_song:
            self.root.after(0, lambda: messagebox.showwarning("Error", "No hay canción cargada"))
            self.playing = False
            return
        
        try:
            # Extraer notas con timing
            notes_with_timing = self._extract_notes_with_timing()
            if not notes_with_timing:
                self.root.after(0, lambda: messagebox.showwarning("Error", "No se encontraron notas en la canción"))
                self.playing = False
                return
            
            total_notes = len(notes_with_timing)
            self.root.after(0, lambda: self.update_status("▶ Modo Práctica - Sigue el ritmo", '#ffaa00'))
            
            for i, (note, duration) in enumerate(notes_with_timing):
                if not self.playing:
                    break
                
                # Actualizar partitura
                current = [note]
                upcoming = [n for n, d in notes_with_timing[i+1:i+11]]
                self.root.after(0, lambda c=current, u=upcoming: self.update_score_display(c, u))
                
                # Iluminar tecla
                self.root.after(0, lambda n=note: self.highlight_key(n, '#ffaa00'))
                
                # Actualizar progreso
                progress = int((i / total_notes) * 100)
                self.root.after(0, lambda p=progress: self.update_progress(p))
                
                # Mantener iluminada según duración
                time.sleep(duration)
                
                # Apagar tecla
                if i < total_notes - 1:  # No apagar la última inmediatamente
                    self.root.after(0, lambda n=note: self.restore_key_color(n))
            
            # Finalizado
            self.root.after(0, lambda: messagebox.showinfo(
                "¡Completado!",
                f"Has completado la canción en Modo Práctica\n\n"
                f"Total de notas: {total_notes}"
            ))
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Error en modo práctica: {e}"))
        finally:
            self.playing = False
            self.root.after(0, lambda: self.stop_btn.config(state=tk.DISABLED))
            self.root.after(0, self.clear_keyboard_highlights)
            self.root.after(0, lambda: self.update_status("⏸ Detenido", '#888888'))
    
    def start_teacher_mode(self):
        """Modo Maestro - Ilumina teclas presionadas"""
        if not self.current_song:
            messagebox.showwarning("Sin partitura", "Carga un archivo MIDI primero")
            return
        
        self.playing = True
        self.stop_btn.config(state=tk.NORMAL)
        self.status_label.config(text="▶ Modo Maestro activo", fg='#ff00ff')
        
        self.practice_thread = threading.Thread(
            target=self._teacher_mode_thread,
            daemon=True
        )
        self.practice_thread.start()
    
    def stop_playing(self):
        """Detiene la reproducción"""
        self.playing = False
        self.stop_btn.config(state=tk.DISABLED)
        self.status_label.config(text="⏸ Detenido", fg='#888888')
        self.clear_keyboard_highlights()
    
    def show_config_window(self):
        """Muestra ventana de configuración"""
        config_win = tk.Toplevel(self.root)
        config_win.title("⚙ Configuración")
        config_win.geometry("600x500")
        config_win.configure(bg='#2d2d2d')
        
        # Título
        tk.Label(
            config_win,
            text="⚙ Configuración del Sistema",
            font=('Arial', 14, 'bold'),
            bg='#2d2d2d',
            fg='white'
        ).pack(pady=20)
        
        # Frame principal
        main_frame = tk.Frame(config_win, bg='#2d2d2d')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20)
        
        # ===== CONFIGURACIÓN DE TECLADO =====
        keyboard_frame = tk.LabelFrame(
            main_frame,
            text="🎹 Configuración del Teclado",
            font=('Arial', 11, 'bold'),
            bg='#2d2d2d',
            fg='white'
        )
        keyboard_frame.pack(fill=tk.X, pady=10)
        
        # Número de teclas
        keys_frame = tk.Frame(keyboard_frame, bg='#2d2d2d')
        keys_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(
            keys_frame,
            text="Número de teclas:",
            bg='#2d2d2d',
            fg='white',
            font=('Arial', 10)
        ).pack(side=tk.LEFT)
        
        num_keys_var = tk.IntVar(value=self.config.get('num_keys', 88))
        tk.Spinbox(
            keys_frame,
            from_=25,
            to=88,
            textvariable=num_keys_var,
            width=10,
            font=('Arial', 10),
            bg='#1a1a1a',
            fg='white'
        ).pack(side=tk.LEFT, padx=10)
        
        tk.Label(
            keys_frame,
            text="(25, 49, 61, 88 teclas)",
            bg='#2d2d2d',
            fg='#888888',
            font=('Arial', 9)
        ).pack(side=tk.LEFT)
        
        # Número de LEDs
        leds_frame = tk.Frame(keyboard_frame, bg='#2d2d2d')
        leds_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(
            leds_frame,
            text="Número de LEDs:",
            bg='#2d2d2d',
            fg='white',
            font=('Arial', 10)
        ).pack(side=tk.LEFT)
        
        num_leds_var = tk.IntVar(value=self.config.get('num_leds', 88))
        led_spinbox = tk.Spinbox(
            leds_frame,
            from_=25,
            to=150,
            textvariable=num_leds_var,
            width=10,
            font=('Arial', 10),
            bg='#1a1a1a',
            fg='white',
            command=lambda: self.test_last_led(num_leds_var.get())
        )
        led_spinbox.pack(side=tk.LEFT, padx=10)
        
        tk.Label(
            leds_frame,
            text="LEDs disponibles en tu tira",
            bg='#2d2d2d',
            fg='#888888',
            font=('Arial', 9)
        ).pack(side=tk.LEFT)
        
        # Botón para probar último LED
        tk.Button(
            leds_frame,
            text="💡 Test",
            command=lambda: self.test_last_led(num_leds_var.get()),
            bg='#0066cc',
            fg='white',
            font=('Arial', 9),
            cursor='hand2'
        ).pack(side=tk.LEFT, padx=5)
        
        # Modo LED
        led_mode_frame = tk.Frame(keyboard_frame, bg='#2d2d2d')
        led_mode_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(
            led_mode_frame,
            text="Modo LED:",
            bg='#2d2d2d',
            fg='white',
            font=('Arial', 10)
        ).pack(side=tk.LEFT)
        
        led_mode_var = tk.StringVar(value=self.config.get('led_mode', 'full'))
        
        modes = [
            ("Completo", "full"),
            ("Compacto", "compact"),
            ("Custom", "custom")
        ]
        
        for text, value in modes:
            tk.Radiobutton(
                led_mode_frame,
                text=text,
                variable=led_mode_var,
                value=value,
                bg='#2d2d2d',
                fg='white',
                selectcolor='#0066cc',
                font=('Arial', 9)
            ).pack(side=tk.LEFT, padx=5)
        
        # Explicación
        tk.Label(
            keyboard_frame,
            text="💡 El sistema ajustará automáticamente el mapeo LED→Tecla",
            bg='#2d2d2d',
            fg='#00ff88',
            font=('Arial', 9),
            wraplength=500
        ).pack(padx=10, pady=5)
        
        # ===== BRILLO =====
        brightness_frame = tk.LabelFrame(
            main_frame,
            text="💡 Brillo de LEDs",
            font=('Arial', 11, 'bold'),
            bg='#2d2d2d',
            fg='white'
        )
        brightness_frame.pack(fill=tk.X, pady=10)
        
        brightness_var = tk.DoubleVar(value=self.config.get('brightness', 0.3))
        
        tk.Scale(
            brightness_frame,
            from_=0.1,
            to=1.0,
            resolution=0.1,
            orient=tk.HORIZONTAL,
            variable=brightness_var,
            bg='#2d2d2d',
            fg='white',
            highlightthickness=0
        ).pack(fill=tk.X, padx=10, pady=5)
        
        # ===== DIGITACIÓN (OPCIONAL) =====
        finger_frame = tk.LabelFrame(
            main_frame,
            text="✋ Sugerencia de Digitación",
            font=('Arial', 11, 'bold'),
            bg='#2d2d2d',
            fg='white'
        )
        finger_frame.pack(fill=tk.X, pady=10)
        
        show_fingers_var = tk.BooleanVar(value=self.config.get('show_fingering', False))
        
        tk.Checkbutton(
            finger_frame,
            text="Mostrar sugerencia de dedos (experimental)",
            variable=show_fingers_var,
            bg='#2d2d2d',
            fg='white',
            selectcolor='#0066cc',
            font=('Arial', 10)
        ).pack(padx=10, pady=5)
        
        tk.Label(
            finger_frame,
            text="Usa colores diferentes para sugerir qué dedo usar",
            bg='#2d2d2d',
            fg='#888888',
            font=('Arial', 9)
        ).pack(padx=10)
        
        # Botones
        btn_frame = tk.Frame(config_win, bg='#2d2d2d')
        btn_frame.pack(pady=20)
        
        def save_and_close():
            self.config['num_keys'] = num_keys_var.get()
            self.config['num_leds'] = num_leds_var.get()
            self.config['led_mode'] = led_mode_var.get()
            self.config['brightness'] = brightness_var.get()
            self.config['show_fingering'] = show_fingers_var.get()
            
            self.save_config()
            
            # Recalcular mapeo
            if HAS_HARDWARE and self.note_mapper:
                self.init_hardware()
            
            messagebox.showinfo("Guardado", "Configuración guardada correctamente")
            config_win.destroy()
        
        tk.Button(
            btn_frame,
            text="✓ Guardar",
            command=save_and_close,
            bg='#00cc00',
            fg='white',
            font=('Arial', 11, 'bold'),
            width=15,
            cursor='hand2'
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            btn_frame,
            text="✗ Cancelar",
            command=config_win.destroy,
            bg='#cc0000',
            fg='white',
            font=('Arial', 11, 'bold'),
            width=15,
            cursor='hand2'
        ).pack(side=tk.LEFT, padx=5)
    
    def init_hardware(self):
        """Inicializa hardware (LEDs, mapper)"""
        if not HAS_HARDWARE:
            return
        
        try:
            num_leds = self.config.get('num_leds', 88)
            brightness = self.config.get('brightness', 0.3)
            
            self.led_controller = LEDController(
                num_leds=num_leds,
                brightness=brightness,
                simulate=True  # Cambiar a False en Raspberry Pi
            )
            
            self.note_mapper = NoteMapper(
                keyboard_type=f"piano_{self.config.get('num_keys', 88)}"
            )
            
            print("✓ Hardware inicializado")
            
        except Exception as e:
            print(f"✗ Error inicializando hardware: {e}")
    
    def on_keyboard_click(self, event):
        """Maneja clicks en el teclado virtual"""
        x, y = event.x, event.y
        
        # Buscar qué tecla se clickeó (teclas negras primero)
        clicked_note = None
        
        # Primero revisar teclas negras (están encima)
        for note, (x1, y1, x2, y2, is_black) in self.key_rectangles.items():
            if is_black and x1 <= x <= x2 and y1 <= y <= y2:
                clicked_note = note
                break
        
        # Si no es negra, revisar blancas
        if clicked_note is None:
            for note, (x1, y1, x2, y2, is_black) in self.key_rectangles.items():
                if not is_black and x1 <= x <= x2 and y1 <= y <= y2:
                    clicked_note = note
                    break
        
        if clicked_note is not None:
            # Iluminar tecla temporalmente
            self.highlight_key(clicked_note, '#ffff00')  # Amarillo
            
            # Reproducir sonido (opcional - requiere pygame.mixer)
            # self.play_note_sound(clicked_note)
            
            # Restaurar después de 300ms
            self.root.after(300, lambda: self.restore_key_color(clicked_note))
    
    def restore_key_color(self, note: int):
        """Restaura el color original de una tecla"""
        if note in self.key_rectangles:
            is_black = self.key_rectangles[note][4]
            color = 'black' if is_black else 'white'
            self.keyboard_canvas.itemconfig(f'key_{note}', fill=color)
            
            # Apagar LED
            if self.led_controller and HAS_HARDWARE:
                led_idx = self.note_mapper.note_to_led(note)
                if led_idx is not None:
                    self.led_controller.set_led(led_idx, (0, 0, 0))
    
    def test_last_led(self, num_leds: int):
        """Enciende el último LED para verificar el tamaño"""
        if self.led_controller and HAS_HARDWARE:
            # Apagar todos
            self.led_controller.clear_all()
            
            # Encender último
            last_led_idx = num_leds - 1
            self.led_controller.set_led(last_led_idx, (255, 0, 0))  # Rojo
            
            messagebox.showinfo(
                "Test LED",
                f"LED #{num_leds} (último) debería estar encendido en ROJO.\n\n"
                f"Si no lo ves, ajusta el número de LEDs.\n"
                f"Si ves un LED diferente, verifica las conexiones."
            )
            
            # Apagar después de 3 segundos
            self.root.after(3000, lambda: self.led_controller.clear_all())
        else:
            messagebox.showinfo(
                "Modo Simulación",
                f"En Raspberry Pi, el LED #{num_leds} se encendería en ROJO.\n\n"
                f"Usa esto para verificar que tienes el número correcto de LEDs."
            )
    
    def draw_staff(self):
        """Dibuja el pentagrama musical"""
        self.score_canvas.delete('all')
        
        width = self.score_canvas.winfo_width()
        height = self.score_canvas.winfo_height()
        
        if width < 10:
            width = 700
        if height < 50:
            height = 180
        
        # Dibujar 5 líneas del pentagrama (centrado verticalmente)
        line_spacing = 16  # Más espaciado
        start_y = (height - (4 * line_spacing)) // 2
        
        for i in range(5):
            y = start_y + (i * line_spacing)
            self.score_canvas.create_line(
                40, y, width - 40, y,
                fill='#000000',
                width=2,
                tags='staff_line'
            )
        
        # Clave de Sol (simplificada - texto)
        self.score_canvas.create_text(
            60, start_y + (2 * line_spacing),
            text='𝄞',
            font=('Arial', 48),
            fill='#000000',
            tags='clef'
        )
    
    def draw_note_on_staff(self, note: int, x: int, highlight: bool = False):
        """
        Dibuja una nota en el pentagrama
        
        Args:
            note: Número MIDI (60 = Do central)
            x: Posición horizontal
            highlight: Si debe estar iluminada
        """
        # Obtener dimensiones actuales
        height = self.score_canvas.winfo_height()
        if height < 50:
            height = 180
        
        # Mapear nota MIDI a posición vertical en pentagrama
        middle_c = 60
        line_spacing = 16
        staff_start_y = (height - (4 * line_spacing)) // 2
        note_spacing = line_spacing // 2  # 8 pixels por paso
        
        # Calcular posición Y (más alto = Y menor)
        note_offset = note - middle_c
        y = staff_start_y + (4 * line_spacing) - (note_offset * note_spacing)
        
        # Color según si está iluminada
        if highlight:
            note_color = '#ff0000'  # Rojo para nota actual
            note_size = 12
        else:
            note_color = '#000000'  # Negro para próximas
            note_size = 9
        
        # Dibujar cabeza de nota (círculo relleno sólido)
        self.score_canvas.create_oval(
            x - note_size, y - note_size,
            x + note_size, y + note_size,
            fill=note_color,
            outline=note_color,
            width=2,
            tags=f'note_{note}_{x}'
        )
        
        # Plica (línea vertical)
        stem_length = 40
        if note >= 60:  # Notas altas - plica hacia abajo
            self.score_canvas.create_line(
                x - note_size, y,
                x - note_size, y + stem_length,
                fill=note_color,
                width=2,
                tags=f'stem_{note}_{x}'
            )
        else:  # Notas bajas - plica hacia arriba
            self.score_canvas.create_line(
                x + note_size, y,
                x + note_size, y - stem_length,
                fill=note_color,
                width=2,
                tags=f'stem_{note}_{x}'
            )
        
        # Líneas adicionales si están fuera del pentagrama
        if y < staff_start_y - 8:  # Por encima
            temp_y = staff_start_y - line_spacing
            while temp_y > y:
                self.score_canvas.create_line(
                    x - 12, temp_y,
                    x + 12, temp_y,
                    fill='#000000',
                    width=2,
                    tags=f'ledger_{note}_{x}'
                )
                temp_y -= line_spacing
        elif y > staff_start_y + (4 * line_spacing) + 8:  # Por debajo
            temp_y = staff_start_y + (5 * line_spacing)
            while temp_y < y:
                self.score_canvas.create_line(
                    x - 12, temp_y,
                    x + 12, temp_y,
                    fill='#000000',
                    width=2,
                    tags=f'ledger_{note}_{x}'
                )
                temp_y += line_spacing
    
    def update_score_display(self, current_notes: list, upcoming_notes: list):
        """
        Actualiza la partitura visual
        
        Args:
            current_notes: Lista de notas actuales (iluminadas)
            upcoming_notes: Lista de próximas notas (sin iluminar)
        """
        # Limpiar notas anteriores (mantener pentagrama)
        for item in self.score_canvas.find_all():
            tags = self.score_canvas.gettags(item)
            if tags and tags[0].startswith(('note_', 'stem_', 'ledger_')):
                self.score_canvas.delete(item)
        
        # Posiciones X para las notas (más espaciado)
        start_x = 120
        spacing = 50
        
        # Dibujar notas actuales (iluminadas)
        for i, note in enumerate(current_notes[:3]):  # Máximo 3 simultáneas
            x = start_x + (i * 25)
            self.draw_note_on_staff(note, x, highlight=True)
        
        # Dibujar próximas notas
        x_offset = start_x + 100
        for i, note in enumerate(upcoming_notes[:8]):  # Mostrar próximas 8
            x = x_offset + (i * spacing)
            self.draw_note_on_staff(note, x, highlight=False)
    
    def update_status(self, text: str, color: str):
        """Actualiza el label de estado"""
        self.status_label.config(text=text, fg=color)
    
    def update_progress(self, percentage: int):
        """Actualiza la barra de progreso"""
        self.progress_bar['value'] = percentage
        self.progress_label.config(text=f"{percentage}%")
    
    def _extract_notes_from_song(self):
        """Extrae notas MIDI de la canción actual (solo números)"""
        if not self.current_song:
            return []
        
        # Simulación para testing
        if not HAS_HARDWARE:
            # Generar escala de ejemplo: C D E F G A B C (60-72)
            return [60, 62, 64, 65, 67, 69, 71, 72, 64, 65, 67, 69, 71, 72, 60]
        
        try:
            from mido import MidiFile
            mid = MidiFile(self.current_song)
            
            notes = []
            for track in mid.tracks:
                for msg in track:
                    if msg.type == 'note_on' and msg.velocity > 0:
                        notes.append(msg.note)
                        if len(notes) >= 100:  # Límite
                            break
                if notes:
                    break
            
            return notes if notes else [60, 62, 64, 65, 67]
        except Exception as e:
            print(f"Error extrayendo notas: {e}")
            return [60, 62, 64, 65, 67]  # Escala por defecto
    
    def _extract_notes_with_timing(self):
        """Extrae notas con duración para modo práctica"""
        if not self.current_song:
            return []
        
        if not HAS_HARDWARE:
            # Simulación sin hardware - usar extracción simple
            notes = self._extract_notes_from_song()
            # Asignar duración fija de 0.5s a cada nota
            return [(note, 0.5) for note in notes]
        
        try:
            from mido import MidiFile
            mid = MidiFile(self.current_song)
            
            notes_with_timing = []
            
            for track in mid.tracks:
                time_per_tick = 0.0005  # 500 microsegundos por tick (ajustable)
                
                for msg in track:
                    if msg.type == 'note_on' and msg.velocity > 0:
                        # Convertir tiempo MIDI a segundos
                        duration = msg.time * time_per_tick
                        if duration < 0.1:  # Mínimo 0.1s
                            duration = 0.3
                        
                        # Nota MIDI directa
                        notes_with_timing.append((msg.note, duration))
                        
                        if len(notes_with_timing) >= 100:  # Límite
                            break
                
                if notes_with_timing:
                    break  # Usar solo primera pista con notas
            
            return notes_with_timing if notes_with_timing else [(60, 0.5)]
            
        except Exception as e:
            print(f"Error extrayendo timing: {e}")
            # Fallback: notas sin timing
            notes = self._extract_notes_from_song()
            return [(note, 0.5) for note in notes]
    
    def update_status(self, text: str, color: str):
        """Actualiza el label de estado"""
        self.status_label.config(text=text, fg=color)
    
    def update_progress(self, percentage: int):
        """Actualiza la barra de progreso"""
        self.progress_bar['value'] = percentage
        self.progress_label.config(text=f"{percentage}%")
    
    def run(self):
        """Ejecuta la aplicación"""
        # Bind para redibujar teclado al redimensionar
        self.keyboard_canvas.bind('<Configure>', lambda e: self.draw_keyboard())
        
        self.root.mainloop()


# ============================================
# PUNTO DE ENTRADA
# ============================================

if __name__ == "__main__":
    app = HowToPianoGUI()
    app.run()
