#!/usr/bin/env python3
"""
Parser y Lector de Archivos MIDI
Extrae eventos de notas con timing preciso y soporte completo para acordes
"""
import os
from typing import List, Tuple, Dict, Set

try:
    from mido import MidiFile, tempo2bpm
    MIDO_AVAILABLE = True
except ImportError:
    MIDO_AVAILABLE = False
    print("⚠️ mido no disponible - usar modo fallback")


class MidiNote:
    """Representa una nota MIDI con su información completa"""
    def __init__(self, note: int, velocity: int, timestamp_ms: int, duration_ms: int = 0):
        self.note = note
        self.velocity = velocity
        self.timestamp_ms = timestamp_ms
        self.duration_ms = duration_ms
    
    def __repr__(self):
        return f"MidiNote(note={self.note}, vel={self.velocity}, t={self.timestamp_ms}ms, dur={self.duration_ms}ms)"


class MidiParser:
    """Parser avanzado de archivos MIDI con soporte completo"""
    
    def __init__(self):
        self.available = MIDO_AVAILABLE
    
    def parse_file(self, path: str) -> Tuple[List[Tuple[int, List[int]]], Dict]:
        """
        Parsea un archivo MIDI y extrae eventos de notas.
        
        Returns:
            Tuple[List[Tuple[int, List[int]]], Dict]:
                - Lista de eventos: [(timestamp_ms, [notas]), ...]
                - Metadata: {duration, tracks, tempo, time_sig, ...}
        """
        # Verificar que la ruta no esté vacía y el archivo exista
        if not path or not os.path.exists(path):
            print(f"⚠️ Archivo no válido: '{path}' - usando datos de ejemplo")
            return self._get_fallback_data()
        
        if not self.available:
            print("⚠️ mido no disponible - usando datos de ejemplo")
            return self._get_fallback_data()
        
        try:
            print(f"\n📖 Parseando MIDI: {os.path.basename(path)}")
            mid = MidiFile(path)
            
            # Extraer metadata
            metadata = self._extract_metadata(mid)
            print(f"   📊 Metadata: {metadata}")
            
            # Procesar notas
            note_events = self._process_tracks(mid, metadata)
            
            print(f"✅ Parseado completo: {len(note_events)} eventos únicos")
            return note_events, metadata
            
        except Exception as e:
            print(f"❌ Error parseando MIDI '{path}': {e}")
            return self._get_fallback_data()
    
    def _extract_metadata(self, mid: MidiFile) -> Dict:
        """Extrae metadata del archivo MIDI"""
        metadata = {
            'filename': '',
            'duration': mid.length,
            'ticks_per_beat': mid.ticks_per_beat,
            'num_tracks': len(mid.tracks),
            'tempo': 500000,  # Tempo por defecto (120 BPM)
            'time_signature': (4, 4),
            'key_signature': 'C',
            'type': mid.type
        }
        
        # Buscar mensajes de tempo y time signature en el primer track
        if mid.tracks:
            for msg in mid.tracks[0]:
                if msg.type == 'set_tempo':
                    metadata['tempo'] = msg.tempo
                    metadata['bpm'] = tempo2bpm(msg.tempo)
                elif msg.type == 'time_signature':
                    metadata['time_signature'] = (msg.numerator, msg.denominator)
                elif msg.type == 'key_signature':
                    metadata['key_signature'] = msg.key
        
        return metadata
    
    def _process_tracks(self, mid: MidiFile, metadata: Dict) -> List[Tuple[int, List[int]]]:
        """
        Procesa todos los tracks y combina eventos por timestamp.
        Usa el tempo real para convertir ticks a milisegundos.
        """
        # Diccionario temporal: {timestamp_ms: [notas]}
        events_by_time = {}
        
        # Información para conversión de tiempo
        ticks_per_beat = metadata['ticks_per_beat']
        tempo = metadata['tempo']
        microseconds_per_tick = tempo / ticks_per_beat
        
        # Mapa de cambios de tempo en el tiempo
        tempo_changes = []  # [(tick, tempo), ...]
        
        # Primera pasada: detectar cambios de tempo
        for track_idx, track in enumerate(mid.tracks):
            absolute_tick = 0
            for msg in track:
                absolute_tick += msg.time
                if msg.type == 'set_tempo':
                    tempo_changes.append((absolute_tick, msg.tempo))
        
        tempo_changes.sort(key=lambda x: x[0])
        
        print(f"   🎵 Procesando {len(mid.tracks)} tracks...")
        if tempo_changes:
            print(f"   🎼 {len(tempo_changes)} cambios de tempo detectados")
        
        # Segunda pasada: procesar notas con tempo variable
        all_notes = []  # Lista de MidiNote objects
        
        for track_idx, track in enumerate(mid.tracks):
            absolute_tick = 0
            track_name = self._get_track_name(track)
            note_count = 0
            
            # Mapa de notas activas: {note_number: (start_tick, velocity)}
            active_notes = {}
            
            for msg in track:
                absolute_tick += msg.time
                
                if msg.type == 'note_on' and msg.velocity > 0:
                    # Inicio de nota
                    active_notes[msg.note] = (absolute_tick, msg.velocity)
                    note_count += 1
                    
                elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                    # Fin de nota
                    if msg.note in active_notes:
                        start_tick, velocity = active_notes[msg.note]
                        
                        # Convertir ticks a milisegundos
                        start_ms = self._ticks_to_ms(start_tick, ticks_per_beat, tempo_changes, tempo)
                        end_ms = self._ticks_to_ms(absolute_tick, ticks_per_beat, tempo_changes, tempo)
                        duration_ms = max(0, end_ms - start_ms)
                        
                        # Crear objeto MidiNote
                        midi_note = MidiNote(
                            note=msg.note,
                            velocity=velocity,
                            timestamp_ms=int(start_ms),
                            duration_ms=int(duration_ms)
                        )
                        all_notes.append(midi_note)
                        
                        del active_notes[msg.note]
            
            if note_count > 0:
                print(f"      Track {track_idx} '{track_name}': {note_count} notas")
        
        # Agrupar notas por timestamp (acordes) CON VELOCIDADES
        # Nuevo formato: [(timestamp, [(note, velocity), ...]), ...]
        events_with_velocity = {}  # {timestamp: [(note, velocity), ...]}
        
        for midi_note in all_notes:
            timestamp = midi_note.timestamp_ms
            if timestamp not in events_with_velocity:
                events_with_velocity[timestamp] = []
            events_with_velocity[timestamp].append((midi_note.note, midi_note.velocity))
        
        # Convertir a lista ordenada de eventos
        note_events = []
        for timestamp in sorted(events_with_velocity.keys()):
            note_vel_pairs = events_with_velocity[timestamp]
            # Eliminar duplicados manteniendo orden
            seen = set()
            unique_pairs = []
            for note, vel in note_vel_pairs:
                if note not in seen:
                    unique_pairs.append((note, vel))
                    seen.add(note)
            note_events.append((timestamp, unique_pairs))
        
        # Estadísticas
        if note_events:
            unique_notes = set()
            for _, note_vel_pairs in note_events:
                for note, vel in note_vel_pairs:
                    unique_notes.add(note)
            
            print(f"   📈 Estadísticas:")
            print(f"      • Eventos únicos: {len(note_events)}")
            print(f"      • Notas diferentes: {len(unique_notes)}")
            print(f"      • Rango: MIDI {min(unique_notes)}-{max(unique_notes)}")
            first_notes = [f"{n}(v{v})" for n, v in note_events[0][1]]
            last_notes = [f"{n}(v{v})" for n, v in note_events[-1][1]]
            print(f"      • Primera nota: t={note_events[0][0]}ms, notas={first_notes}")
            print(f"      • Última nota: t={note_events[-1][0]}ms, notas={last_notes}")
        
        return note_events
    
    def _ticks_to_ms(self, ticks: int, ticks_per_beat: int, 
                     tempo_changes: List[Tuple[int, int]], default_tempo: int) -> float:
        """
        Convierte ticks a milisegundos considerando cambios de tempo.
        """
        if not tempo_changes:
            # Sin cambios de tempo, usar tempo por defecto
            microseconds_per_tick = default_tempo / ticks_per_beat
            return (ticks * microseconds_per_tick) / 1000.0
        
        # Con cambios de tempo, calcular segmento por segmento
        current_tick = 0
        accumulated_ms = 0.0
        current_tempo = default_tempo
        
        for change_tick, new_tempo in tempo_changes:
            if change_tick >= ticks:
                # El cambio está después del tick que buscamos
                remaining_ticks = ticks - current_tick
                microseconds_per_tick = current_tempo / ticks_per_beat
                accumulated_ms += (remaining_ticks * microseconds_per_tick) / 1000.0
                return accumulated_ms
            else:
                # Calcular hasta este cambio de tempo
                segment_ticks = change_tick - current_tick
                microseconds_per_tick = current_tempo / ticks_per_beat
                accumulated_ms += (segment_ticks * microseconds_per_tick) / 1000.0
                
                current_tick = change_tick
                current_tempo = new_tempo
        
        # Si quedan ticks después del último cambio
        remaining_ticks = ticks - current_tick
        microseconds_per_tick = current_tempo / ticks_per_beat
        accumulated_ms += (remaining_ticks * microseconds_per_tick) / 1000.0
        
        return accumulated_ms
    
    def _get_track_name(self, track) -> str:
        """Extrae el nombre de un track"""
        for msg in track:
            if msg.type == 'track_name':
                return msg.name
        return "Unnamed"
    
    def _get_fallback_data(self) -> Tuple[List[Tuple[int, List[Tuple[int, int]]]], Dict]:
        """Datos de ejemplo cuando mido no está disponible - con velocidades"""
        # Formato: [(timestamp, [(note, velocity), ...]), ...]
        events = [
            (0, [(60, 80)]),      # Do medio fuerte
            (500, [(62, 70)]),    # Re medio
            (1000, [(64, 90)]),   # Mi fuerte
            (1500, [(65, 60)]),   # Fa suave
            (2000, [(67, 85)]),   # Sol fuerte
            (2500, [(69, 75)]),   # La medio
            (3000, [(71, 95)]),   # Si muy fuerte
            (3500, [(72, 100)]),  # Do fortissimo
        ]
        
        metadata = {
            'duration': 4.0,
            'num_tracks': 1,
            'ticks_per_beat': 480,
            'tempo': 500000,
            'bpm': 120
        }
        
        return events, metadata


if __name__ == "__main__":
    # Test del parser
    print("🎼 Test de MidiParser")
    parser = MidiParser()
    
    # Buscar archivo MIDI de ejemplo
    test_file = "A06.mid"
    if os.path.exists(test_file):
        events, metadata = parser.parse_file(test_file)
        print(f"\n✅ Parseado exitoso:")
        print(f"   Eventos: {len(events)}")
        print(f"   Duración: {metadata.get('duration', 0):.1f}s")
        print(f"   BPM: {metadata.get('bpm', 120):.0f}")
    else:
        print(f"⚠️ Archivo {test_file} no encontrado")
        print("Usando datos de ejemplo...")
        events, metadata = parser.parse_file("")
        print(f"Eventos de ejemplo: {len(events)}")
