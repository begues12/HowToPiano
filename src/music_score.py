#!/usr/bin/env python3
"""
Sistema de Partitura Musical con Scroll Automático Suave
Renderiza notación musical profesional usando fuentes musicales Unicode
Usa main_font.ttx para símbolos musicales de alta calidad
"""
import tkinter as tk
from typing import List, Tuple, Optional
import os


class MusicScore:
    """Sistema de partitura profesional con scroll suave"""
    
    def __init__(self, canvas: tk.Canvas):
        self.canvas = canvas
        self.notes = []  # Lista de (timestamp_ms, midi_note, duration_ms, velocity)
        self.current_time = 0
        self.target_time = 0  # Para interpolación suave
        
        # Detectar fuente musical disponible
        self.music_font = self._detect_music_font()
        
        # Configuración visual optimizada para claridad
        self.line_spacing = 12  # Espaciado óptimo para buena visibilidad
        self.playback_line_x = 200  # Línea vertical de "ahora"
        self.note_head_width = 7  # Cabeza de nota clara pero no muy grande
        self.note_head_height = 5  # Proporción elegante
        self.stem_length = 32  # Plica visible pero elegante
        self.stem_width = 1.8  # Plica clara
        
        # Ajustar espaciado según la fuente
        if self.music_font in ['Bravura', 'main_font', 'BravuraText']:
            # Fuentes musicales necesitan más espacio por ser símbolos más grandes
            self.pixels_per_ms = 0.35  # Mucho más espacio entre notas
        else:
            self.pixels_per_ms = 0.2  # Espacio normal para fuentes vectoriales
        
        # Colores profesionales con buen contraste
        self.color_staff = '#1a202c'  # Gris muy oscuro para líneas
        self.color_past = '#a0aec0'  # Gris medio para notas pasadas
        self.color_current = '#e53e3e'  # Rojo vibrante para nota actual
        self.color_future = '#2b6cb0'   # Azul oscuro para notas futuras
        
        # Animación suave
        self.animation_speed = 0.2  # Velocidad de interpolación (0-1)
        self.is_animating = False
        
        # Metadata para compases
        self.metadata = None
        
        # Duraciones de figuras musicales en ms (aproximadas para 120 BPM)
        self.figure_thresholds = {
            'whole': 2000,      # Redonda (4 beats)
            'half': 1000,       # Blanca (2 beats)
            'quarter': 500,     # Negra (1 beat)
            'eighth': 250,      # Corchea (1/2 beat)
            'sixteenth': 125,   # Semicorchea (1/4 beat)
        }
    
    def _detect_music_font(self):
        """Detecta la mejor fuente disponible para símbolos musicales"""
        from tkinter import font as tkfont
        
        # Obtener lista de fuentes instaladas en el sistema
        available_fonts = tkfont.families()
        
        # Priorizar Bravura (fuente profesional SMuFL)
        for font_name in ['Bravura', 'main_font', 'BravuraText']:
            if font_name in available_fonts:
                print(f"🎵 Usando fuente profesional: {font_name}")
                return font_name
        
        # Si no hay fuente musical, usar gráficos vectoriales
        print("⚠️ No se encontró fuente musical - usando gráficos vectoriales")
        return None  # None indica usar vectores
    
    def load_notes(self, note_events: List[Tuple[int, List[Tuple[int, int]]]], metadata: dict = None):
        """
        Carga eventos de notas en la partitura.
        
        Args:
            note_events: Lista de (timestamp_ms, [(note, velocity), ...])
            metadata: Diccionario con 'bpm', 'time_signature', etc.
        """
        self.notes.clear()
        self.metadata = metadata
        
        print(f"📝 Cargando {len(note_events)} eventos a partitura")
        if metadata:
            print(f"   Metadata: {metadata.get('bpm')} BPM, {metadata.get('time_signature')}")
        
        # Calcular duraciones reales entre notas
        for i, (timestamp, note_vel_pairs) in enumerate(note_events):
            # Calcular duración hasta la siguiente nota
            if i < len(note_events) - 1:
                next_timestamp = note_events[i + 1][0]
                duration = next_timestamp - timestamp
            else:
                duration = 500  # Última nota
            
            for midi_note, velocity in note_vel_pairs:
                self.notes.append((timestamp, midi_note, duration, velocity))
        
        print(f"✅ Partitura lista: {len(self.notes)} notas individuales")
        self.render()
    
    def render(self):
        """Renderiza la partitura completa"""
        self.canvas.delete('all')
        
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        
        if w < 2:
            return
        
        # Calcular posiciones del pentagrama (centrado ligeramente arriba)
        y_center = h // 2 - 10
        y_start = y_center - (2 * self.line_spacing)
        
        # Dibujar pentagrama (5 líneas horizontales claras)
        for i in range(5):
            y = y_start + (i * self.line_spacing)
            self.canvas.create_line(
                0, y, w, y,
                fill=self.color_staff,
                width=1.8,  # Grosor óptimo para visibilidad
                tags='staff_line'
            )
        
        # Dibujar clave de Sol con Bravura (SMuFL)
        # Bravura usa códigos SMuFL específicos
        if self.music_font == 'Bravura':
            # SMuFL: U+E050 = Clave de Sol (gClef)
            clef_symbol = '\uE050'
            clef_size = 55  # Reducido de 70 a 55 para ser más compacta
            y_offset = 0  # Sin offset adicional
        else:
            # Unicode estándar para otras fuentes
            clef_symbol = '𝄞'
            clef_size = 58
            y_offset = 0
        
        try:
            # Sombra sutil para efecto 3D
            self.canvas.create_text(
                26, y_center + y_offset + 1.5,
                text=clef_symbol,
                font=(self.music_font, clef_size),
                fill='#e2e8f0',
                tags='clef_shadow'
            )
            # Clave principal clara
            self.canvas.create_text(
                25, y_center + y_offset,
                text=clef_symbol,
                font=(self.music_font, clef_size),
                fill=self.color_staff,
                tags='clef'
            )

        except Exception as e:
            # Fallback
            print(f"⚠️ Error con {self.music_font}, usando fallback: {e}")
            self.canvas.create_text(
                26, y_center + 1.5,
                text='𝄞',
                font=('Arial', 54),
                fill='#e2e8f0',
                tags='clef_shadow'
            )
            self.canvas.create_text(
                25, y_center,
                text='𝄞',
                font=('Arial', 54),
                fill=self.color_staff,
                tags='clef'
            )
        
        # Si no hay notas, mostrar mensaje
        if not self.notes:
            self.canvas.create_text(
                w // 2, y_center,
                text='Carga una canción para ver la partitura',
                font=('Segoe UI', 11, 'italic'),
                fill='#a0aec0',
                tags='placeholder'
            )
            return
        
        # Dibujar barras de compás
        self._draw_bar_lines(y_start, w, h)
        
        # Dibujar línea de reproducción actual
        self.canvas.create_line(
            self.playback_line_x, 0,
            self.playback_line_x, h,
            fill=self.color_current,
            width=3,
            tags='playback_line'
        )
        
        # Dibujar todas las notas
        for timestamp, midi_note, duration, velocity in self.notes:
            # Calcular posición X basada en timestamp y tiempo actual
            x = self.playback_line_x + ((timestamp - self.current_time) * self.pixels_per_ms)
            
            # Solo dibujar si está visible
            if -50 < x < w + 50:
                y = self._midi_to_y(midi_note, y_start)
                color = self._get_note_color(x)
                
                # Determinar figura musical según duración
                figure_type = self._get_figure_type(duration)
                
                self._draw_note_with_figure(x, y, y_start, color, timestamp, figure_type, midi_note)
    
    def _midi_to_y(self, midi_note: int, y_start: int) -> int:
        """Convierte nota MIDI a posición Y en el pentagrama con mejor espaciado"""
        # Pentagrama en clave de Sol
        # Do4 (MIDI 60) = línea adicional debajo del pentagrama
        # Mi4 (MIDI 64) = línea inferior del pentagrama
        # Sol5 (MIDI 79) = línea superior del pentagrama
        
        # Usar Do4 como referencia central (más común en piano)
        reference_midi = 60  # Do central (C4)
        
        # Calcular diferencia de altura PRIMERO
        note_diff = midi_note - reference_midi
        
        # Calcular altura del canvas para centrar mejor
        canvas_height = self.canvas.winfo_height()
        if canvas_height < 2:
            canvas_height = 230  # Usar altura por defecto
        
        reference_y = canvas_height // 2 + 20  # Un poco abajo del centro
        
        # Cada semitono = espacio óptimo (ajustado para claridad)
        # Usar factor de 2.4 para mejor distribución vertical
        y_offset = -note_diff * (self.line_spacing / 2.4)
        
        return int(reference_y + y_offset)
    
    def _get_note_color(self, x: float) -> str:
        """Determina el color de una nota según su posición"""
        threshold = 20
        
        if x < self.playback_line_x - threshold:
            return self.color_past  # Pasada
        elif self.playback_line_x - threshold <= x <= self.playback_line_x + threshold:
            return self.color_current  # Tocando ahora
        else:
            return self.color_future  # Futura
    
    def _get_figure_type(self, duration_ms: int) -> str:
        """Determina el tipo de figura musical según la duración"""
        # Ajustar umbrales según BPM si hay metadata
        bpm = self.metadata.get('bpm', 120) if self.metadata else 120
        tempo_factor = 120 / bpm  # Factor de ajuste
        
        adjusted_duration = duration_ms / tempo_factor
        
        if adjusted_duration >= 1800:
            return 'whole'      # Redonda 𝅝
        elif adjusted_duration >= 900:
            return 'half'       # Blanca 𝅗𝅥
        elif adjusted_duration >= 450:
            return 'quarter'    # Negra 𝅘𝅥
        elif adjusted_duration >= 200:
            return 'eighth'     # Corchea 𝅘𝅥𝅮
        else:
            return 'sixteenth'  # Semicorchea 𝅘𝅥𝅯
    
    def _draw_note_with_figure(self, x: float, y: int, y_start: int, color: str, 
                               tag_suffix: int, figure_type: str, midi_note: int):
        """Dibuja una nota musical profesional con gráficos vectoriales"""
        
        # Determinar dirección de la plica (stem)
        # Notas agudas (arriba del pentagrama) -> plica hacia abajo
        # Notas graves (abajo del pentagrama) -> plica hacia arriba
        stem_up = y > y_start + (2 * self.line_spacing)
        
        # Dibujar alteración (sostenido/bemol) si es nota negra
        self._draw_accidental(x, y, midi_note, color, tag_suffix)
        
        # Usar siempre gráficos vectoriales para mejor calidad
        self._draw_note_professional(x, y, y_start, color, tag_suffix, figure_type, stem_up)
        
        # Líneas adicionales (ledger lines) si la nota está fuera del pentagrama
        self._draw_ledger_lines(x, y, y_start, color)
    
    def _draw_accidental(self, x: float, y: int, midi_note: int, color: str, tag_suffix: int):
        """Dibuja alteraciones (sostenidos ♯) claras y visibles"""
        # Determinar si es nota negra (alteración)
        note_in_octave = midi_note % 12
        black_keys = [1, 3, 6, 8, 10]  # C#, D#, F#, G#, A#
        
        if note_in_octave in black_keys:
            # Es una nota con sostenido
            if self.music_font in ['Bravura', 'main_font', 'BravuraText']:
                # SMuFL: U+E262 = Sostenido (accidentalSharp)
                sharp_symbol = '\uE262'
                accidental_size = 14
                try:
                    self.canvas.create_text(
                        x - 16, y,
                        text=sharp_symbol,
                        font=(self.music_font, accidental_size),
                        fill=color,
                        tags=f'accidental_{tag_suffix}'
                    )
                    return
                except:
                    pass
            
            # Fallback: usar # visible
            self.canvas.create_text(
                x - 16, y,
                text='#',
                font=('Segoe UI', 15, 'bold'),
                fill=color,
                tags=f'accidental_{tag_suffix}'
            )
    
    def _draw_note_professional(self, x: float, y: int, y_start: int, color: str,
                           tag_suffix: int, figure_type: str, stem_up: bool):
        """Dibuja nota con símbolos SMuFL profesionales si hay fuente musical"""
        
        # Si tenemos fuente musical, usar símbolos SMuFL
        if self.music_font in ['Bravura', 'main_font', 'BravuraText']:
            self._draw_note_smufl(x, y, color, tag_suffix, figure_type, stem_up)
        else:
            # Fallback: usar gráficos vectoriales (siempre funciona)
            self._draw_note_vector(x, y, color, tag_suffix, figure_type, stem_up)
    
    def _draw_note_smufl(self, x: float, y: int, color: str, tag_suffix: int, 
                         figure_type: str, stem_up: bool):
        """Dibuja nota usando símbolos SMuFL de Bravura"""
        
        # Símbolos SMuFL para cabezas de nota (tamaños más pequeños y compactos)
        if figure_type == 'whole':
            # U+E0A2 = noteheadWhole
            notehead = '\uE0A2'
            size = 18  # Reducido de 28 a 18
        elif figure_type == 'half':
            # U+E0A3 = noteheadHalf
            notehead = '\uE0A3'
            size = 18  # Reducido de 28 a 18
        else:
            # U+E0A4 = noteheadBlack (para negra, corchea, semicorchea)
            notehead = '\uE0A4'
            size = 18  # Reducido de 28 a 18
        
        # Dibujar cabeza de nota
        self.canvas.create_text(
            x, y,
            text=notehead,
            font=(self.music_font, size),
            fill=color,
            tags=f'note_{tag_suffix}'
        )
        
        # Agregar plica para blancas, negras, corcheas, semicorcheas
        if figure_type != 'whole':
            self._draw_stem(x, y, stem_up, color, tag_suffix)
            
            # Agregar corchetes para corcheas y semicorcheas
            if figure_type == 'eighth':
                self._draw_flag_smufl(x, y, stem_up, color, tag_suffix, 1)
            elif figure_type == 'sixteenth':
                self._draw_flag_smufl(x, y, stem_up, color, tag_suffix, 2)
    
    def _draw_note_vector(self, x: float, y: int, color: str, tag_suffix: int,
                          figure_type: str, stem_up: bool):
        """Dibuja nota con gráficos vectoriales (fallback)"""
        head_width = self.note_head_width
        head_height = self.note_head_height
        
        if figure_type == 'whole':
            # Redonda: óvalo vacío
            self.canvas.create_oval(
                x - head_width, y - head_height, 
                x + head_width, y + head_height,
                fill='white',
                outline=color,
                width=2.0,
                tags=f'note_{tag_suffix}'
            )
        elif figure_type == 'half':
            # Blanca: óvalo vacío + plica
            self.canvas.create_oval(
                x - head_width, y - head_height, 
                x + head_width, y + head_height,
                fill='white',
                outline=color,
                width=2.0,
                tags=f'note_{tag_suffix}'
            )
            self._draw_stem(x, y, stem_up, color, tag_suffix)
        else:
            # Negra/Corchea/Semicorchea: óvalo relleno + plica
            self.canvas.create_oval(
                x - head_width, y - head_height, 
                x + head_width, y + head_height,
                fill=color,
                outline=color,
                width=0,
                tags=f'note_{tag_suffix}'
            )
            self._draw_stem(x, y, stem_up, color, tag_suffix)
            
            # Agregar corchetes para corcheas y semicorcheas
            if figure_type == 'eighth':
                self._draw_flag_professional(x, y, stem_up, color, tag_suffix, 1)
            elif figure_type == 'sixteenth':
                self._draw_flag_professional(x, y, stem_up, color, tag_suffix, 2)
    
    def _draw_stem(self, x: float, y: int, stem_up: bool, color: str, tag_suffix: int):
        """Dibuja la plica de una nota delgada y elegante"""
        stem_length = self.stem_length
        
        if stem_up:
            # Plica hacia arriba (desde el lado derecho de la nota)
            self.canvas.create_line(
                x + self.note_head_width, y, 
                x + self.note_head_width, y - stem_length,
                fill=color,
                width=self.stem_width,
                tags=f'stem_{tag_suffix}'
            )
        else:
            # Plica hacia abajo (desde el lado izquierdo de la nota)
            self.canvas.create_line(
                x - self.note_head_width, y, 
                x - self.note_head_width, y + stem_length,
                fill=color,
                width=self.stem_width,
                tags=f'stem_{tag_suffix}'
            )
    
    def _draw_flag_smufl(self, x: float, y: int, stem_up: bool, color: str, 
                         tag_suffix: int, num_flags: int):
        """Dibuja corchetes usando símbolos SMuFL de Bravura"""
        stem_length = self.stem_length
        
        if stem_up:
            stem_x = x + self.note_head_width
            flag_y = y - stem_length
            # U+E240 = flag8thUp, U+E242 = flag16thUp
            flag_symbol = '\uE240' if num_flags == 1 else '\uE242'
        else:
            stem_x = x - self.note_head_width
            flag_y = y + stem_length
            # U+E241 = flag8thDown, U+E243 = flag16thDown
            flag_symbol = '\uE241' if num_flags == 1 else '\uE243'
        
        self.canvas.create_text(
            stem_x, flag_y,
            text=flag_symbol,
            font=(self.music_font, 16),  # Reducido de 24 a 16
            fill=color,
            anchor='w' if stem_up else 'w',
            tags=f'flag_{tag_suffix}'
        )
    
    def _draw_flag_professional(self, x: float, y: int, stem_up: bool, color: str, tag_suffix: int, num_flags: int):
        """Dibuja banderas pequeñas y elegantes para corcheas y semicorcheas (fallback)"""
        stem_length = self.stem_length
        flag_spacing = 4  # Más compactas
        flag_width = 8  # Más pequeñas
        
        if stem_up:
            stem_x = x + self.note_head_width
            stem_end_y = y - stem_length
            
            # Dibujar banderas curvadas más pequeñas
            for i in range(num_flags):
                flag_y = stem_end_y + (i * flag_spacing)
                
                # Crear polígono curvo compacto
                points = [
                    stem_x, flag_y,
                    stem_x + flag_width, flag_y + 3,
                    stem_x + flag_width + 1, flag_y + 5,
                    stem_x + flag_width - 2, flag_y + 6,
                    stem_x + 2, flag_y + 4,
                    stem_x, flag_y + 1.5
                ]
                
                self.canvas.create_polygon(
                    points,
                    fill=color,
                    outline='',
                    smooth=True,
                    tags=f'flag_{tag_suffix}'
                )
        else:
            stem_x = x - self.note_head_width
            stem_end_y = y + stem_length
            
            # Dibujar banderas curvadas más pequeñas
            for i in range(num_flags):
                flag_y = stem_end_y - (i * flag_spacing)
                
                # Crear polígono curvo compacto
                points = [
                    stem_x, flag_y,
                    stem_x + flag_width, flag_y - 3,
                    stem_x + flag_width + 1, flag_y - 5,
                    stem_x + flag_width - 2, flag_y - 6,
                    stem_x + 2, flag_y - 4,
                    stem_x, flag_y - 1.5
                ]
                
                self.canvas.create_polygon(
                    points,
                    fill=color,
                    outline='',
                    smooth=True,
                    tags=f'flag_{tag_suffix}'
                )
    
    def _draw_clef_graphic(self, x: int, y: int):
        """Dibuja clave de sol con gráficos vectoriales (fallback robusto)"""
        # Curva principal de la clave de sol
        points = [
            # Espiral inferior
            x, y + 30,
            x - 5, y + 25,
            x - 8, y + 15,
            x - 5, y + 5,
            x, y,
            x + 5, y - 5,
            x + 8, y - 15,
            x + 5, y - 25,
            x, y - 30,
            x - 5, y - 35,
            # Bucle superior
            x - 8, y - 40,
            x - 5, y - 45,
            x + 2, y - 48,
            x + 8, y - 45,
            x + 10, y - 38,
            x + 8, y - 30,
            x + 3, y - 25,
        ]
        
        # Dibujar línea curva suave
        self.canvas.create_line(
            points,
            fill=self.color_staff,
            width=3,
            smooth=True,
            tags='clef'
        )
        
        # Punto inferior característico
        self.canvas.create_oval(
            x - 4, y + 12,
            x + 4, y + 20,
            fill=self.color_staff,
            outline=self.color_staff,
            tags='clef'
        )
    
    def _draw_clef_graphic(self, x: int, y: int):
        """Dibuja clave de sol con gráficos vectoriales (fallback robusto)"""
        # Curva principal de la clave de sol
        points = [
            # Espiral inferior
            x, y + 30,
            x - 5, y + 25,
            x - 8, y + 15,
            x - 5, y + 5,
            x, y,
            x + 5, y - 5,
            x + 8, y - 15,
            x + 5, y - 25,
            x, y - 30,
            x - 5, y - 35,
            # Bucle superior
            x - 8, y - 40,
            x - 5, y - 45,
            x + 2, y - 48,
            x + 8, y - 45,
            x + 10, y - 38,
            x + 8, y - 30,
            x + 3, y - 25,
        ]
        
        # Dibujar línea curva suave
        self.canvas.create_line(
            points,
            fill=self.color_staff,
            width=3,
            smooth=True,
            tags='clef'
        )
        
        # Punto inferior característico
        self.canvas.create_oval(
            x - 4, y + 12,
            x + 4, y + 20,
            fill=self.color_staff,
            outline=self.color_staff,
            tags='clef'
        )
    
    def _draw_ledger_lines(self, x: float, y: int, y_start: int, color: str):
        """Dibuja líneas adicionales claras para notas fuera del pentagrama"""
        staff_top = y_start
        staff_bottom = y_start + (4 * self.line_spacing)
        
        # Líneas superiores (notas agudas) - claras y visibles
        if y < staff_top:
            line_y = staff_top - self.line_spacing
            while line_y >= y - 2:
                self.canvas.create_line(
                    x - 10, line_y, x + 10, line_y,
                    fill=color,
                    width=1.5,
                    tags='ledger'
                )
                line_y -= self.line_spacing
        
        # Líneas inferiores (notas graves) - claras y visibles
        elif y > staff_bottom:
            line_y = staff_bottom + self.line_spacing
            while line_y <= y + 2:
                self.canvas.create_line(
                    x - 10, line_y, x + 10, line_y,
                    fill=color,
                    width=1.5,
                    tags='ledger'
                )
                line_y += self.line_spacing
    
    def update_time(self, current_time_ms: int):
        """
        Actualiza el tiempo actual con animación suave (interpolación).
        
        Args:
            current_time_ms: Tiempo actual de reproducción en milisegundos
        """
        self.target_time = current_time_ms
        
        # Iniciar animación suave si no está activa
        if not self.is_animating:
            self.is_animating = True
            self._animate_scroll()
    
    def _animate_scroll(self):
        """Anima el scroll suavemente usando interpolación lineal"""
        if not self.is_animating:
            return
        
        # Interpolación lineal (lerp) para movimiento suave
        diff = self.target_time - self.current_time
        
        if abs(diff) > 1:  # Si hay diferencia significativa
            # Mover gradualmente hacia el objetivo
            self.current_time += diff * self.animation_speed
            self.render()
            
            # Continuar animación
            self.canvas.after(16, self._animate_scroll)  # ~60 FPS
        else:
            # Llegamos al objetivo
            self.current_time = self.target_time
            self.render()
            self.is_animating = False
    
    def _draw_bar_lines(self, y_start: int, canvas_width: int, canvas_height: int):
        """Dibuja las líneas de compás (barras verticales) usando metadata"""
        if not self.metadata:
            return
        
        bpm = self.metadata.get('bpm', 120)
        time_sig = self.metadata.get('time_signature', '4/4')
        
        # Parsear el time signature (ej: "4/4" -> 4 beats por compás)
        try:
            beats_per_measure = int(time_sig.split('/')[0])
        except:
            beats_per_measure = 4  # Default
        
        # Calcular duración de un compás en milisegundos
        ms_per_beat = 60000 / bpm  # Un beat en ms
        ms_per_measure = ms_per_beat * beats_per_measure
        
        # Calcular altura del pentagrama
        staff_top = y_start
        staff_bottom = y_start + (4 * self.line_spacing)
        
        # Dibujar barras desde el primer compás visible hasta el último
        # Empezar desde el compás que contiene current_time
        first_measure = int(self.current_time / ms_per_measure)
        
        # Calcular total de compases
        if self.notes:
            max_timestamp = max(note[0] for note in self.notes)
            total_measures = int(max_timestamp / ms_per_measure) + 1
        else:
            total_measures = 10
        
        # Dibujar compases visibles
        for measure_num in range(first_measure - 2, first_measure + 15):  # Ventana de compases
            measure_time_ms = measure_num * ms_per_measure
            
            # Calcular posición X basada en timestamp
            x = self.playback_line_x + ((measure_time_ms - self.current_time) * self.pixels_per_ms)
            
            # Solo dibujar si está visible
            if 50 < x < canvas_width:
                # Determinar si es el último compás (doble barra)
                is_final = measure_num == total_measures - 1
                
                if is_final:
                    # Barra final doble (más gruesa)
                    self.canvas.create_line(
                        x - 3, staff_top, x - 3, staff_bottom,
                        fill=self.color_staff,
                        width=2,
                        tags='bar_line'
                    )
                    self.canvas.create_line(
                        x, staff_top, x, staff_bottom,
                        fill=self.color_staff,
                        width=4,
                        tags='bar_line_final'
                    )
                else:
                    # Línea de compás normal
                    self.canvas.create_line(
                        x, staff_top, x, staff_bottom,
                        fill=self.color_staff,
                        width=2,
                        tags='bar_line'
                    )
                
                # Número de compás encima del pentagrama con fondo
                if measure_num >= 0:  # No dibujar números negativos
                    # Fondo semitransparente para el número
                    bbox_width = 20
                    bbox_height = 14
                    self.canvas.create_rectangle(
                        x - bbox_width/2, staff_top - 20,
                        x + bbox_width/2, staff_top - 6,
                        fill='#f7fafc',
                        outline='#e2e8f0',
                        width=1,
                        tags='measure_bg'
                    )
                    self.canvas.create_text(
                        x, staff_top - 13,
                        text=str(measure_num + 1),  # +1 porque los compases empiezan en 1
                        font=('Segoe UI', 9, 'bold'),
                        fill=self.color_staff,
                        tags='measure_number'
                    )
    
    def reset(self):
        """Resetea la partitura al inicio"""
        self.current_time = 0
        self.target_time = 0
        self.is_animating = False
        self.render()
    
    def set_colors(self, past: str = None, current: str = None, future: str = None):
        """Personaliza los colores de las notas"""
        if past:
            self.color_past = past
        if current:
            self.color_current = current
        if future:
            self.color_future = future
        
        self.render()
    
    def set_scroll_speed(self, pixels_per_ms: float):
        """Ajusta la velocidad de scroll"""
        self.pixels_per_ms = pixels_per_ms
        self.render()


if __name__ == "__main__":
    # Test del sistema de partitura
    print("🎼 Test de MusicScore")
    
    root = tk.Tk()
    root.title("Test MusicScore")
    root.geometry("800x200")
    
    canvas = tk.Canvas(root, bg='white', highlightthickness=0)
    canvas.pack(fill=tk.BOTH, expand=True)
    
    # Crear partitura
    score = MusicScore(canvas)
    
    # Datos de ejemplo con velocity
    test_events = [
        (0, [(60, 80)]),      # Do
        (500, [(62, 80)]),    # Re
        (1000, [(64, 80)]),   # Mi
        (1500, [(65, 80)]),   # Fa
        (2000, [(67, 80)]),   # Sol
        (2500, [(69, 80)]),   # La
        (3000, [(71, 80)]),   # Si
        (3500, [(72, 80)]),   # Do
    ]
    
    score.load_notes(test_events)
    
    # Simular scroll
    def animate():
        current = getattr(animate, 'time', 0)
        score.update_time(current)
        animate.time = current + 100
        
        if current < 4000:
            root.after(100, animate)
    
    root.after(1000, animate)  # Empezar después de 1s
    
    root.mainloop()
