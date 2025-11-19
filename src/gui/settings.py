"""
Diálogo de Configuración - Panel completo de ajustes
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from ..modern_theme import ModernTheme


class SettingsDialog:
    """Diálogo modal de configuración completa"""
    
    def __init__(self, parent, current_config, callbacks):
        """
        Args:
            parent: Ventana padre
            current_config: Dict con configuración actual
            callbacks: Dict con funciones callback:
                - on_save: Cuando se guarda la configuración
                - on_test_led: Para probar último LED
        """
        self.parent = parent
        self.config = current_config.copy()
        self.callbacks = callbacks
        
        # Crear ventana modal
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("⚙️ Configuración")
        self.dialog.geometry("700x800")
        self.dialog.configure(bg=ModernTheme.BG_DARK)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Centrar
        self._center_window()
        
        # Crear contenido
        self._create_widgets()
    
    def _center_window(self):
        """Centra la ventana en la pantalla"""
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (350)
        y = (self.dialog.winfo_screenheight() // 2) - (400)
        self.dialog.geometry(f"700x800+{x}+{y}")
    
    def _create_widgets(self):
        """Crea todos los widgets del diálogo"""
        # Título
        tk.Label(
            self.dialog,
            text="⚙️ Configuración",
            font=('Segoe UI', 18, 'bold'),
            bg=ModernTheme.BG_DARK,
            fg=ModernTheme.TEXT_PRIMARY
        ).pack(pady=20)
        
        # Contenedor scrollable
        self._create_scrollable_content()
        
        # Botones inferiores
        self._create_bottom_buttons()
    
    def _create_scrollable_content(self):
        """Crea el contenedor scrollable con todas las opciones"""
        canvas = tk.Canvas(self.dialog, bg=ModernTheme.BG_DARK, highlightthickness=0)
        scrollbar = tk.Scrollbar(self.dialog, orient="vertical", command=canvas.yview)
        self.scrollable_frame = tk.Frame(canvas, bg=ModernTheme.BG_DARK)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True, padx=20)
        scrollbar.pack(side="right", fill="y")
        
        # Crear secciones
        self._create_audio_section()
        self._create_instrument_section()
        self._create_piano_section()
        self._create_fingering_section()
        self._create_midi_section()
        self._create_led_section()
        self._create_visual_section()
    
    def _create_section_frame(self, title, icon):
        """Crea un frame de sección con título"""
        section = tk.Frame(self.scrollable_frame, bg=ModernTheme.BG_CARD)
        section.pack(fill=tk.X, pady=10, padx=10, ipady=15)
        
        tk.Label(
            section,
            text=f"{icon} {title}",
            font=('Segoe UI', 12, 'bold'),
            bg=ModernTheme.BG_CARD,
            fg=ModernTheme.TEXT_PRIMARY
        ).pack(anchor=tk.W, padx=15, pady=(10, 15))
        
        return section
    
    def _create_audio_section(self):
        """Sección: Audio"""
        section = self._create_section_frame("Audio", "🔊")
        
        # Volumen general
        vol_frame = tk.Frame(section, bg=ModernTheme.BG_CARD)
        vol_frame.pack(fill=tk.X, padx=15, pady=5)
        
        tk.Label(
            vol_frame,
            text="Volumen General:",
            font=('Segoe UI', 10),
            bg=ModernTheme.BG_CARD,
            fg=ModernTheme.TEXT_PRIMARY
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        self.volume_var = tk.IntVar(value=int(self.config.get('volume', 50)))
        self.volume_label = tk.Label(
            vol_frame,
            text=f"{self.volume_var.get()}%",
            font=('Segoe UI', 10, 'bold'),
            bg=ModernTheme.BG_CARD,
            fg=ModernTheme.PRIMARY
        )
        self.volume_label.pack(side=tk.RIGHT)
        
        volume_slider = tk.Scale(
            vol_frame,
            from_=0,
            to=100,
            orient=tk.HORIZONTAL,
            bg=ModernTheme.BG_CARD,
            fg=ModernTheme.TEXT_PRIMARY,
            highlightthickness=0,
            variable=self.volume_var,
            command=lambda v: self.volume_label.config(text=f"{v}%")
        )
        volume_slider.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=10)
    
    def _create_instrument_section(self):
        """Sección: Instrumento/Perfil de Piano"""
        section = self._create_section_frame("Perfil de Instrumento", "🎹")
        
        # Cargar gestor de perfiles
        try:
            from src.instrument_profiles import get_profile_manager
            self.profile_manager = get_profile_manager()
        except ImportError:
            self.profile_manager = None
        
        # Selector de perfil
        profile_frame = tk.Frame(section, bg=ModernTheme.BG_CARD)
        profile_frame.pack(fill=tk.X, padx=15, pady=5)
        
        tk.Label(
            profile_frame,
            text="Perfil de Sonido:",
            font=('Segoe UI', 10),
            bg=ModernTheme.BG_CARD,
            fg=ModernTheme.TEXT_PRIMARY
        ).pack(anchor=tk.W, pady=(0, 5))
        
        self.profile_var = tk.StringVar(value=self.config.get('sound_profile', 'acoustic'))
        
        # Obtener perfiles disponibles del gestor
        if self.profile_manager:
            available_profiles = self.profile_manager.get_profile_list()
        else:
            # Fallback a perfiles por defecto
            available_profiles = [
                {'id': 'acoustic', 'name': 'Acoustic Grand Piano', 'type': 'synthetic', 'has_samples': False},
                {'id': 'grand', 'name': 'Piano de Cola', 'type': 'synthetic', 'has_samples': False},
                {'id': 'bright', 'name': 'Piano Brillante', 'type': 'synthetic', 'has_samples': False},
                {'id': 'mellow', 'name': 'Piano Suave', 'type': 'synthetic', 'has_samples': False},
                {'id': 'electric', 'name': 'Piano Eléctrico', 'type': 'synthetic', 'has_samples': False},
            ]
        
        # Crear radio buttons con información de samples
        for profile_info in available_profiles:
            profile_id = profile_info['id']
            profile_name = profile_info['name']
            has_samples = profile_info.get('has_samples', False)
            
            # Icono según tipo
            if has_samples:
                icon = "🎵"  # Tiene samples WAV
                suffix = " (WAV)"
            else:
                icon = "🎹"  # Síntesis
                suffix = ""
            
            display_name = f"{icon} {profile_name}{suffix}"
            
            rb = tk.Radiobutton(
                profile_frame,
                text=display_name,
                variable=self.profile_var,
                value=profile_id,
                bg=ModernTheme.BG_CARD,
                fg=ModernTheme.TEXT_PRIMARY,
                selectcolor=ModernTheme.BG_LIGHT,
                font=('Segoe UI', 9),
                activebackground=ModernTheme.BG_CARD,
                activeforeground=ModernTheme.PRIMARY
            )
            rb.pack(anchor=tk.W, padx=20, pady=2)
        
        # Info de perfiles
        info_frame = tk.Frame(section, bg=ModernTheme.BG_LIGHT)
        info_frame.pack(fill=tk.X, padx=15, pady=10)
        
        tk.Label(
            info_frame,
            text="💡 Añade archivos note_21.wav a note_108.wav\nen assets/instruments/custom/ para usar samples reales",
            font=('Segoe UI', 8),
            bg=ModernTheme.BG_LIGHT,
            fg=ModernTheme.TEXT_SECONDARY,
            justify=tk.LEFT
        ).pack(padx=10, pady=5)
        
        # Botón para gestionar perfiles personalizados
        tk.Button(
            section,
            text="📁 Gestionar Perfiles Personalizados",
            command=self._manage_custom_profiles,
            bg=ModernTheme.PRIMARY,
            fg=ModernTheme.TEXT_PRIMARY,
            font=('Segoe UI', 9, 'bold'),
            relief=tk.FLAT,
            padx=15,
            pady=8,
            cursor='hand2'
        ).pack(padx=15, pady=(10, 5))
        
        # Info sobre dónde están los perfiles
        tk.Label(
            section,
            text="📂 Perfiles: assets/instruments/",
            font=('Segoe UI', 8),
            bg=ModernTheme.BG_CARD,
            fg=ModernTheme.TEXT_MUTED
        ).pack(anchor=tk.W, padx=15, pady=(0, 10))
    
    def _create_piano_section(self):
        """Sección: Piano"""
        section = self._create_section_frame("Piano Virtual", "🎹")
        
        # Número de teclas
        keys_frame = tk.Frame(section, bg=ModernTheme.BG_CARD)
        keys_frame.pack(fill=tk.X, padx=15, pady=5)
        
        tk.Label(
            keys_frame,
            text="Número de teclas:",
            font=('Segoe UI', 10),
            bg=ModernTheme.BG_CARD,
            fg=ModernTheme.TEXT_PRIMARY
        ).pack(anchor=tk.W, pady=(0, 10))
        
        self.num_keys_var = tk.IntVar(value=self.config.get('num_keys', 61))
        
        keys_options = [
            (25, "25 teclas (2 octavas)"),
            (37, "37 teclas (3 octavas)"),
            (49, "49 teclas (4 octavas)"),
            (61, "61 teclas (5 octavas) - Estándar"),
            (76, "76 teclas (6 octavas)"),
            (88, "88 teclas (7 octavas) - Piano completo")
        ]
        
        for num_keys, label in keys_options:
            rb = tk.Radiobutton(
                keys_frame,
                text=label,
                variable=self.num_keys_var,
                value=num_keys,
                bg=ModernTheme.BG_CARD,
                fg=ModernTheme.TEXT_PRIMARY,
                selectcolor=ModernTheme.BG_LIGHT,
                font=('Segoe UI', 9),
                activebackground=ModernTheme.BG_CARD
            )
            rb.pack(anchor=tk.W, padx=20, pady=2)
    
    def _create_fingering_section(self):
        """Sección: Digitación"""
        section = self._create_section_frame("Digitación", "✋")
        
        # Checkbox mostrar digitación
        self.fingering_var = tk.BooleanVar(value=self.config.get('show_fingering', False))
        
        tk.Checkbutton(
            section,
            text="Mostrar números de dedos en teclas",
            variable=self.fingering_var,
            bg=ModernTheme.BG_CARD,
            fg=ModernTheme.TEXT_PRIMARY,
            selectcolor=ModernTheme.BG_LIGHT,
            font=('Segoe UI', 10),
            activebackground=ModernTheme.BG_CARD
        ).pack(anchor=tk.W, padx=15, pady=5)
        
        # Info de colores
        tk.Label(
            section,
            text="Colores: 1=Cyan (Pulgar), 2=Azul (Índice), 3=Marino (Medio),\n"
                 "4=Violeta (Anular), 5=Magenta (Meñique)",
            font=('Segoe UI', 8),
            bg=ModernTheme.BG_CARD,
            fg=ModernTheme.TEXT_MUTED,
            justify=tk.LEFT
        ).pack(anchor=tk.W, padx=15, pady=(0, 10))
    
    def _create_midi_section(self):
        """Sección: MIDI"""
        section = self._create_section_frame("Teclado MIDI", "🎹")
        
        # Checkbox usar solo virtual
        self.virtual_keyboard_var = tk.BooleanVar(
            value=self.config.get('use_virtual_keyboard', False)
        )
        
        tk.Checkbutton(
            section,
            text="Usar solo teclado virtual (sin MIDI físico)",
            variable=self.virtual_keyboard_var,
            bg=ModernTheme.BG_CARD,
            fg=ModernTheme.TEXT_PRIMARY,
            selectcolor=ModernTheme.BG_LIGHT,
            font=('Segoe UI', 10),
            activebackground=ModernTheme.BG_CARD
        ).pack(anchor=tk.W, padx=15, pady=5)
        
        tk.Label(
            section,
            text="Útil para dar clases sin teclado MIDI conectado",
            font=('Segoe UI', 8),
            bg=ModernTheme.BG_CARD,
            fg=ModernTheme.TEXT_MUTED
        ).pack(anchor=tk.W, padx=15, pady=(0, 10))
    
    def _create_led_section(self):
        """Sección: LEDs"""
        section = self._create_section_frame("Control de LEDs", "💡")
        
        # Número de LEDs
        leds_frame = tk.Frame(section, bg=ModernTheme.BG_CARD)
        leds_frame.pack(fill=tk.X, padx=15, pady=5)
        
        tk.Label(
            leds_frame,
            text="Número de LEDs:",
            font=('Segoe UI', 10),
            bg=ModernTheme.BG_CARD,
            fg=ModernTheme.TEXT_PRIMARY
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        self.num_leds_var = tk.IntVar(value=self.config.get('num_leds', 88))
        
        num_leds_entry = tk.Spinbox(
            leds_frame,
            from_=1,
            to=200,
            textvariable=self.num_leds_var,
            font=('Segoe UI', 10),
            width=8,
            bg=ModernTheme.BG_LIGHT,
            fg=ModernTheme.TEXT_PRIMARY
        )
        num_leds_entry.pack(side=tk.RIGHT)
        
        # Brillo
        brightness_frame = tk.Frame(section, bg=ModernTheme.BG_CARD)
        brightness_frame.pack(fill=tk.X, padx=15, pady=10)
        
        tk.Label(
            brightness_frame,
            text="Brillo:",
            font=('Segoe UI', 10),
            bg=ModernTheme.BG_CARD,
            fg=ModernTheme.TEXT_PRIMARY
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        self.brightness_var = tk.IntVar(value=self.config.get('brightness', 128))
        self.brightness_label = tk.Label(
            brightness_frame,
            text=f"{int((self.brightness_var.get()/255)*100)}%",
            font=('Segoe UI', 10, 'bold'),
            bg=ModernTheme.BG_CARD,
            fg=ModernTheme.PRIMARY
        )
        self.brightness_label.pack(side=tk.RIGHT)
        
        brightness_slider = tk.Scale(
            brightness_frame,
            from_=0,
            to=255,
            orient=tk.HORIZONTAL,
            bg=ModernTheme.BG_CARD,
            fg=ModernTheme.TEXT_PRIMARY,
            highlightthickness=0,
            variable=self.brightness_var,
            command=lambda v: self.brightness_label.config(
                text=f"{int((float(v)/255)*100)}%"
            )
        )
        brightness_slider.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=10)
        
        # Botón test LED
        tk.Button(
            section,
            text="💡 Probar Último LED",
            command=self._test_last_led,
            bg=ModernTheme.SECONDARY,
            fg=ModernTheme.TEXT_PRIMARY,
            font=('Segoe UI', 9, 'bold'),
            relief=tk.FLAT,
            padx=15,
            pady=8,
            cursor='hand2'
        ).pack(padx=15, pady=(5, 10))
    
    def _create_visual_section(self):
        """Sección: Visual"""
        section = self._create_section_frame("Interfaz Visual", "🎨")
        
        # Mostrar partitura
        self.show_score_var = tk.BooleanVar(
            value=self.config.get('show_score', True)
        )
        
        tk.Checkbutton(
            section,
            text="Mostrar partitura musical",
            variable=self.show_score_var,
            bg=ModernTheme.BG_CARD,
            fg=ModernTheme.TEXT_PRIMARY,
            selectcolor=ModernTheme.BG_LIGHT,
            font=('Segoe UI', 10),
            activebackground=ModernTheme.BG_CARD
        ).pack(anchor=tk.W, padx=15, pady=5)
        
        # Tema (futuro)
        tk.Label(
            section,
            text="Temas personalizados disponibles próximamente",
            font=('Segoe UI', 8),
            bg=ModernTheme.BG_CARD,
            fg=ModernTheme.TEXT_MUTED
        ).pack(anchor=tk.W, padx=15, pady=(0, 10))
    
    def _create_bottom_buttons(self):
        """Crea los botones inferiores (Guardar/Cancelar)"""
        btn_frame = tk.Frame(self.dialog, bg=ModernTheme.BG_DARK)
        btn_frame.pack(fill=tk.X, padx=20, pady=20)
        
        tk.Button(
            btn_frame,
            text="❌ Cancelar",
            command=self.dialog.destroy,
            bg=ModernTheme.BG_CARD,
            fg=ModernTheme.TEXT_PRIMARY,
            font=('Segoe UI', 11, 'bold'),
            relief=tk.FLAT,
            padx=30,
            pady=12,
            cursor='hand2'
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Button(
            btn_frame,
            text="✅ Guardar Cambios",
            command=self._save_settings,
            bg=ModernTheme.SECONDARY,
            fg=ModernTheme.TEXT_PRIMARY,
            font=('Segoe UI', 11, 'bold'),
            relief=tk.FLAT,
            padx=30,
            pady=12,
            cursor='hand2'
        ).pack(side=tk.RIGHT)
    
    # === Métodos de acción ===
    
    def _manage_custom_profiles(self):
        """Abre el gestor de perfiles personalizados con información real"""
        import os
        from pathlib import Path
        
        # Obtener info de perfiles
        if self.profile_manager:
            profiles = self.profile_manager.get_profile_list()
            custom_profiles = [p for p in profiles if 'custom' in p['id'].lower()]
        else:
            custom_profiles = []
        
        info_text = "📁 Gestión de Perfiles Personalizados\n\n"
        
        # Mostrar perfiles custom detectados
        if custom_profiles:
            info_text += "✅ Perfiles personalizados detectados:\n\n"
            for p in custom_profiles:
                samples_info = ""
                if self.profile_manager:
                    stats = self.profile_manager.get_profile_stats(p['id'])
                    if stats:
                        if stats['has_samples']:
                            coverage = stats.get('coverage', 0)
                            samples_info = f" - {stats['num_samples']}/88 notas ({coverage:.0f}%)"
                        else:
                            samples_info = " - Solo síntesis"
                
                info_text += f"  • {p['name']}{samples_info}\n"
            info_text += "\n"
        else:
            info_text += "⚠️ No hay perfiles personalizados detectados\n\n"
        
        # Instrucciones
        info_text += "Para añadir un perfil personalizado:\n\n"
        info_text += "1. Coloca archivos WAV en:\n"
        info_text += "   assets/instruments/custom/\n\n"
        info_text += "2. Nombra los archivos como:\n"
        info_text += "   note_21.wav, note_22.wav, ..., note_108.wav\n\n"
        info_text += "3. Opcional: Crea config.json con parámetros\n\n"
        info_text += "4. Haz clic en 'Recargar Perfiles' o reinicia\n\n"
        
        # Botón para abrir carpeta
        info_text += "💡 Ver README en assets/instruments/ para más info"
        
        # Crear diálogo con botones
        dialog = tk.Toplevel(self.dialog)
        dialog.title("Gestión de Perfiles")
        dialog.geometry("500x400")
        dialog.configure(bg=ModernTheme.BG_DARK)
        dialog.transient(self.dialog)
        dialog.grab_set()
        
        # Texto
        text_widget = tk.Text(
            dialog,
            wrap=tk.WORD,
            bg=ModernTheme.BG_CARD,
            fg=ModernTheme.TEXT_PRIMARY,
            font=('Segoe UI', 10),
            relief=tk.FLAT,
            padx=20,
            pady=20
        )
        text_widget.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        text_widget.insert('1.0', info_text)
        text_widget.config(state=tk.DISABLED)
        
        # Botones
        btn_frame = tk.Frame(dialog, bg=ModernTheme.BG_DARK)
        btn_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        tk.Button(
            btn_frame,
            text="📂 Abrir Carpeta",
            command=lambda: os.startfile(str(Path("assets/instruments"))),
            bg=ModernTheme.PRIMARY,
            fg=ModernTheme.TEXT_PRIMARY,
            font=('Segoe UI', 9, 'bold'),
            relief=tk.FLAT,
            padx=15,
            pady=8
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Button(
            btn_frame,
            text="🔄 Recargar Perfiles",
            command=lambda: self._reload_profiles(dialog),
            bg=ModernTheme.SECONDARY,
            fg=ModernTheme.TEXT_PRIMARY,
            font=('Segoe UI', 9, 'bold'),
            relief=tk.FLAT,
            padx=15,
            pady=8
        ).pack(side=tk.LEFT)
        
        tk.Button(
            btn_frame,
            text="Cerrar",
            command=dialog.destroy,
            bg=ModernTheme.BG_CARD,
            fg=ModernTheme.TEXT_PRIMARY,
            font=('Segoe UI', 9),
            relief=tk.FLAT,
            padx=15,
            pady=8
        ).pack(side=tk.RIGHT)
    
    def _reload_profiles(self, dialog):
        """Recarga los perfiles y actualiza la UI"""
        if self.profile_manager:
            self.profile_manager.reload_profiles()
            messagebox.showinfo("Recarga", "Perfiles recargados exitosamente", parent=dialog)
            dialog.destroy()
            # Recargar sección de instrumentos
            messagebox.showinfo("Información", "Cierra y vuelve a abrir Configuración para ver los cambios")
        else:
            messagebox.showwarning("Error", "Gestor de perfiles no disponible", parent=dialog)
    
    def _test_last_led(self):
        """Prueba el último LED"""
        if 'on_test_led' in self.callbacks:
            self.callbacks['on_test_led'](self.num_leds_var.get())
        else:
            messagebox.showinfo("Test LED", f"Probando LED #{self.num_leds_var.get()}")
    
    def _save_settings(self):
        """Guarda la configuración y cierra el diálogo"""
        # Actualizar config con valores del formulario
        self.config['volume'] = self.volume_var.get()
        self.config['sound_profile'] = self.profile_var.get()
        self.config['num_keys'] = self.num_keys_var.get()
        self.config['show_fingering'] = self.fingering_var.get()
        self.config['use_virtual_keyboard'] = self.virtual_keyboard_var.get()
        self.config['num_leds'] = self.num_leds_var.get()
        self.config['brightness'] = self.brightness_var.get()
        self.config['show_score'] = self.show_score_var.get()
        
        # Llamar callback
        if 'on_save' in self.callbacks:
            self.callbacks['on_save'](self.config)
        
        # Cerrar diálogo
        self.dialog.destroy()
    
    def show(self):
        """Muestra el diálogo modal"""
        self.dialog.wait_window()
