#!/usr/bin/env python3
"""
HowToPiano GUI - Versión MODULAR Y REFACTORIZADA
Código separado en componentes reutilizables por funcionalidad
"""
import tkinter as tk
from tkinter import messagebox
import json
import os
import threading
import time

# Tema moderno
from src.modern_theme import ModernTheme

# Componentes UI modulares
from src.gui.header import HeaderComponent
from src.gui.library import LibraryComponent
from src.gui.score import ScoreComponent
from src.gui.keyboard import KeyboardComponent
from src.gui.stats import StatsComponent
from src.gui.settings import SettingsDialog

# Módulos de lógica de negocio
from src.piano_sound import PianoSound
from src.midi_parser import MidiParser

# Hardware (con fallback)
try:
    from src.midi_reader import MidiReader
    from src.led_controller import LEDController
    from src.note_mapper import NoteMapper
    HAS_HARDWARE = True
except ImportError:
    HAS_HARDWARE = False
    print("⚠️ Módulos de hardware no disponibles - modo simulación")


class ModularHowToPianoGUI:
    """GUI modular con componentes separados"""
    
    def __init__(self):
        # Ventana principal
        self.root = tk.Tk()
        self.root.title("🎹 HowToPiano - Modular")
        self.root.geometry("1400x850")
        self.root.configure(bg=ModernTheme.BG_DARK)
        
        # Estado de la aplicación
        self.config = self._load_config()
        self.current_song_path = None
        self.playing = False
        self.playback_speed = 1.0
        
        # Servicios de negocio
        self.piano_sound = PianoSound(0.5, profile='acoustic')
        self.midi_parser = MidiParser()
        
        # Caché
        self._notes_cache = {}
        self._metadata_cache = {}
        
        # Crear UI modular
        self._create_modular_ui()
    
    def _create_modular_ui(self):
        """Crea la UI usando componentes modulares"""
        
        # ============ HEADER ============
        self.header = HeaderComponent(self.root, {
            'on_open': self._handle_open_file,
            'on_stop': self._handle_stop,
            'on_play': self._handle_play,
            'on_practice': self._handle_practice,
            'on_settings': self._handle_settings,
            'on_speed_change': self._handle_speed_change,
            'on_sound_change': self._handle_sound_change
        })
        
        # ============ CONTENEDOR PRINCIPAL ============
        main = tk.Frame(self.root, bg=ModernTheme.BG_DARK)
        main.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # ============ BIBLIOTECA (IZQUIERDA) ============
        self.library = LibraryComponent(main, {
            'on_select': self._handle_song_select,
            'on_load': self._handle_load_song,
            'on_browse': self._handle_browse_files
        })
        
        # Cargar canciones recientes
        recent_songs = self._load_recent_songs()
        self.library.set_songs(recent_songs)
        
        # ============ PANEL DERECHO ============
        right = tk.Frame(main, bg=ModernTheme.BG_DARK)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # ============ PARTITURA ============
        self.score = ScoreComponent(right, {
            'on_progress_click': self._handle_progress_click
        })
        
        # ============ ESTADÍSTICAS ============
        self.stats = StatsComponent(right)
        
        # ============ TECLADO VIRTUAL ============
        self.keyboard = KeyboardComponent(
            right, 
            {'on_key_click': self._handle_key_click},
            num_keys=self.config.get('num_keys', 61),
            show_fingering=self.config.get('show_fingering', False)
        )
    
    # ========================================
    # HANDLERS DE EVENTOS (UI → Lógica)
    # ========================================
    
    def _handle_open_file(self):
        """Handler: Abrir archivo"""
        from tkinter import filedialog
        
        file = filedialog.askopenfilename(
            title="Abrir archivo MIDI",
            filetypes=[("MIDI files", "*.mid *.midi"), ("All files", "*.*")]
        )
        
        if file:
            self._save_recent_song(file)
            self.library.add_song(file)
            self._load_song(file)
    
    def _handle_stop(self):
        """Handler: Detener reproducción"""
        self.playing = False
        self.header.set_playing_state(False)
        
        # Detener sonidos
        try:
            import pygame
            pygame.mixer.stop()
        except:
            pass
        
        # Restaurar teclas
        for note in range(21, 109):
            self.keyboard.restore_key(note)
        
        # Resetear progreso
        self.score.update_progress(0)
    
    def _handle_play(self):
        """Handler: Reproducción automática"""
        if not self.current_song_path:
            messagebox.showwarning("Aviso", "Carga una canción primero")
            return
        
        if self.playing:
            messagebox.showwarning("Aviso", "Ya hay una reproducción en curso")
            return
        
        self.playing = True
        self.header.set_playing_state(True)
        threading.Thread(target=self._auto_play_thread, daemon=True).start()
    
    def _handle_practice(self):
        """Handler: Modo práctica"""
        if not self.current_song_path:
            messagebox.showwarning("Aviso", "Carga una canción primero")
            return
        
        if self.playing:
            messagebox.showwarning("Aviso", "Ya hay una reproducción en curso")
            return
        
        self.playing = True
        self.header.set_playing_state(True)
        threading.Thread(target=self._practice_thread, daemon=True).start()
    
    def _handle_settings(self):
        """Handler: Abrir configuración"""
        dialog = SettingsDialog(self.root, self.config, {
            'on_save': self._on_settings_save,
            'on_test_led': self._on_test_led
        })
        dialog.show()
    
    def _handle_speed_change(self, speed_text):
        """Handler: Cambio de velocidad"""
        self.playback_speed = float(speed_text.replace('x', ''))
        self.header.show_temporary_message(f"⚡ Velocidad: {speed_text}")
    
    def _handle_sound_change(self, sound_text):
        """Handler: Cambio de sonido"""
        profile = self.header.get_sound_profile()
        self.piano_sound.set_profile(profile)
        self.header.show_temporary_message(f"✅ Sonido: {sound_text}")
    
    def _on_settings_save(self, new_config):
        """Handler: Guardar configuración desde diálogo"""
        # Actualizar configuración
        self.config.update(new_config)
        self._save_config()
        
        # Aplicar cambios inmediatos
        if 'num_keys' in new_config:
            self.keyboard.set_num_keys(new_config['num_keys'])
        
        if 'show_fingering' in new_config:
            self.keyboard.set_fingering(new_config['show_fingering'])
        
        if 'volume' in new_config:
            self.piano_sound.volume = new_config['volume'] / 100.0
        
        if 'sound_profile' in new_config:
            self.piano_sound.set_profile(new_config['sound_profile'])
        
        messagebox.showinfo(
            "Configuración Guardada",
            "Los cambios se han aplicado correctamente"
        )
    
    def _on_test_led(self, num_leds):
        """Handler: Probar último LED"""
        messagebox.showinfo(
            "Test LED",
            f"Probando LED #{num_leds}\n\n"
            f"El último LED debería iluminarse en rojo durante 3 segundos.\n\n"
            f"Si no lo ves, revisa las conexiones o el número de LEDs configurado."
        )
    
    def _handle_song_select(self, path):
        """Handler: Selección de canción en biblioteca"""
        # Por ahora solo preescucha, no hace nada más
        pass
    
    def _handle_load_song(self, path):
        """Handler: Cargar canción desde biblioteca"""
        self._load_song(path)
    
    def _handle_browse_files(self, files):
        """Handler: Buscar nuevos archivos"""
        for f in files:
            self._save_recent_song(f)
        self.library.set_songs(self._load_recent_songs())
    
    def _handle_progress_click(self, percent):
        """Handler: Click en barra de progreso"""
        note_events = self._notes_cache.get(self.current_song_path, [])
        if not note_events:
            return
        
        last_timestamp = note_events[-1][0]
        target_time = int((percent / 100) * last_timestamp)
        
        self.score.update_time(target_time)
        print(f"🎯 Salto a {int(percent)}% (t={target_time}ms)")
    
    def _handle_key_click(self, note):
        """Handler: Click en tecla del teclado virtual"""
        self.piano_sound.play_note(note)
        self.keyboard.highlight_key(note)
        self.root.after(300, lambda: self.keyboard.restore_key(note))
    
    # ========================================
    # LÓGICA DE NEGOCIO (Core)
    # ========================================
    
    def _load_song(self, path):
        """Carga una canción MIDI"""
        # Detener reproducción anterior
        if self.playing:
            response = messagebox.askyesno(
                "Canción en reproducción",
                "¿Deseas detener la reproducción actual?"
            )
            if response:
                self._handle_stop()
                time.sleep(0.2)
            else:
                return
        
        # Copiar a biblioteca local
        copied_path = self._copy_to_midi_folder(path)
        if copied_path:
            path = copied_path
        
        self.current_song_path = path
        
        # Actualizar UI
        name = os.path.basename(path)
        self.header.update_song_info(name)
        
        # Cargar en background
        threading.Thread(target=self._load_notes_background, args=(path,), daemon=True).start()
    
    def _load_notes_background(self, path):
        """Carga las notas del MIDI en background"""
        try:
            # Parsear archivo
            note_events, metadata = self.midi_parser.parse_file(path)
            
            print(f"🎵 Cargando: {os.path.basename(path)}")
            print(f"   Tempo: {metadata.get('bpm', 'N/A')} BPM")
            print(f"   Eventos: {len(note_events)}")
            
            # Limitar eventos
            if len(note_events) > 500:
                step = len(note_events) // 500
                note_events = [note_events[i] for i in range(0, len(note_events), step)][:500]
            
            # Guardar en caché
            self._notes_cache[path] = note_events
            self._metadata_cache[path] = metadata
            
            # Actualizar UI en main thread
            self.root.after(0, lambda: self._update_ui_after_load(metadata, note_events))
            
            print(f"✅ Cargados {len(note_events)} eventos")
            
        except Exception as e:
            print(f"❌ Error cargando MIDI: {e}")
            import traceback
            traceback.print_exc()
    
    def _update_ui_after_load(self, metadata, note_events):
        """Actualiza la UI después de cargar el MIDI"""
        # Actualizar metadata en header
        bpm = metadata.get('bpm', metadata.get('tempo', 'N/A'))
        time_sig = metadata.get('time_signature', (4, 4))
        key_sig = metadata.get('key_signature', '')
        
        self.header.update_metadata(bpm, time_sig, key_sig)
        
        # Cargar partitura
        self.score.load_notes(note_events, metadata)
        
        # Resetear estadísticas
        self.stats.reset(total_notes=len(note_events))
    
    def _auto_play_thread(self):
        """Thread de reproducción automática"""
        note_events = self._notes_cache.get(self.current_song_path, [])
        if not note_events:
            return
        
        print(f"\n▶️ Reproducción automática: {len(note_events)} eventos")
        
        start_time = time.time()
        last_timestamp = 0
        
        for i, (timestamp, note_list) in enumerate(note_events):
            if not self.playing:
                break
            
            # Calcular delay
            if i == 0:
                delay = 0
            else:
                expected_delay = (timestamp - last_timestamp) / 1000.0
                delay = expected_delay / self.playback_speed
            
            # Actualizar partitura
            self.root.after(0, lambda t=timestamp: self.score.update_time(t))
            
            if delay > 0:
                time.sleep(delay)
            
            last_timestamp = timestamp
            
            # Tocar notas
            for note, vel in note_list:
                threading.Thread(
                    target=self.piano_sound.play_note,
                    args=(note, vel),
                    daemon=True
                ).start()
                self.root.after(0, lambda n=note: self.keyboard.highlight_key(n))
            
            # Actualizar progreso
            progress = int((i / len(note_events)) * 100)
            self.root.after(0, lambda p=progress: self.score.update_progress(p))
            
            # Restaurar teclas
            for note, vel in note_list:
                self.root.after(200, lambda n=note: self.keyboard.restore_key(n))
        
        elapsed = time.time() - start_time
        print(f"✅ Reproducción completada en {elapsed:.1f}s")
        
        self.playing = False
        self.root.after(0, lambda: self.header.set_playing_state(False))
        self.root.after(0, lambda: self.score.reset())
    
    def _practice_thread(self):
        """Thread de modo práctica (similar a auto_play pero con estadísticas)"""
        # Por ahora idéntico a auto_play, pero aquí se puede añadir
        # lógica de detección de errores, puntuación, etc.
        self._auto_play_thread()
    
    # ========================================
    # PERSISTENCIA (Config y Recientes)
    # ========================================
    
    def _load_config(self):
        """Carga configuración desde archivo"""
        try:
            with open('config/config.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {'num_keys': 61, 'show_fingering': False, 'brightness': 0.4}
    
    def _save_config(self):
        """Guarda configuración en archivo"""
        try:
            os.makedirs('config', exist_ok=True)
            with open('config/config.json', 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error guardando config: {e}")
    
    def _load_recent_songs(self):
        """Carga lista de canciones recientes"""
        try:
            with open('config/recent.json', 'r') as f:
                return json.load(f)
        except:
            return []
    
    def _save_recent_song(self, path):
        """Guarda una canción en recientes"""
        recent = self._load_recent_songs()
        if path not in recent:
            recent.insert(0, path)
            recent = recent[:10]
            
            os.makedirs('config', exist_ok=True)
            with open('config/recent.json', 'w') as f:
                json.dump(recent, f, indent=2)
    
    def _copy_to_midi_folder(self, source_path):
        """Copia archivo a carpeta midi/ y crea archivo de scores"""
        try:
            import shutil
            from datetime import datetime
            
            midi_dir = os.path.join(os.path.dirname(__file__), 'midi')
            os.makedirs(midi_dir, exist_ok=True)
            
            filename = os.path.basename(source_path)
            basename = os.path.splitext(filename)[0]
            dest_path = os.path.join(midi_dir, filename)
            
            # Copiar si no existe
            if not os.path.exists(dest_path) or os.path.abspath(source_path) != os.path.abspath(dest_path):
                shutil.copy2(source_path, dest_path)
                print(f"📂 Copiado a: {dest_path}")
            
            # Crear/actualizar archivo de scores
            scores_path = os.path.join(midi_dir, f"{basename}_scores.json")
            
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
            
            scores_data["last_loaded"] = datetime.now().isoformat()
            scores_data["total_plays"] = scores_data.get("total_plays", 0) + 1
            
            with open(scores_path, 'w', encoding='utf-8') as f:
                json.dump(scores_data, f, indent=2, ensure_ascii=False)
            
            print(f"📊 Scores: {scores_path}")
            return dest_path
            
        except Exception as e:
            print(f"⚠️ Error copiando archivo: {e}")
            return None
    
    # ========================================
    # RUN
    # ========================================
    
    def run(self):
        """Ejecuta la aplicación"""
        self.root.mainloop()


if __name__ == "__main__":
    print("=" * 60)
    print("🎹 HowToPiano - ARQUITECTURA MODULAR")
    print("=" * 60)
    print("\n✨ Características:")
    print("  • Componentes UI separados por funcionalidad")
    print("  • Código limpio y mantenible")
    print("  • Separación UI / Lógica de negocio")
    print("  • Fácil de extender y testear\n")
    
    app = ModularHowToPianoGUI()
    app.run()
