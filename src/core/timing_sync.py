"""
Sistema de sincronización automática entre audio y visualización.
Mide y ajusta el offset de latencia para mantener perfecta sincronía.
"""

import time
from collections import deque
from typing import Optional, Tuple
import statistics


class TimingSyncManager:
    """
    Gestiona la sincronización temporal entre el audio y la visualización.
    
    Mide continuamente el offset real y ajusta la compensación de latencia
    para mantener las notas perfectamente sincronizadas con la música.
    """
    
    def __init__(self, initial_latency: float = 0.012):
        """
        Inicializa el gestor de sincronización.
        
        Args:
            initial_latency: Latencia inicial en segundos (12ms por defecto)
        """
        # Latencia actual
        self.current_latency = initial_latency
        
        # Historial de mediciones (últimas N mediciones)
        self.max_samples = 50
        self.timing_samples = deque(maxlen=self.max_samples)
        
        # Estadísticas
        self.total_notes_measured = 0
        self.adjustment_count = 0
        
        # Parámetros de ajuste
        self.min_latency = 0.0  # Mínimo 0ms
        self.max_latency = 0.100  # Máximo 100ms
        self.adjustment_threshold = 0.003  # Ajustar si desviación > 3ms
        self.adjustment_factor = 0.5  # Ajustar 50% del error detectado
        
        # Estado
        self.enabled = True
        self.last_adjustment_time = time.time()
        self.min_adjustment_interval = 2.0  # Mínimo 2s entre ajustes
        
    def record_note_timing(self, scheduled_time: float, actual_time: float, 
                          visual_time: float) -> None:
        """
        Registra una medición de timing cuando una nota suena.
        
        Args:
            scheduled_time: Tiempo programado para la nota (del MIDI)
            actual_time: Tiempo real cuando sonó (system time)
            visual_time: Tiempo visual cuando cruzó la línea roja
        """
        if not self.enabled:
            return
        
        # Calcular el offset real
        # Positivo = audio adelantado, Negativo = audio retrasado
        offset = visual_time - scheduled_time
        
        # Guardar muestra
        self.timing_samples.append({
            'offset': offset,
            'scheduled': scheduled_time,
            'actual': actual_time,
            'visual': visual_time,
            'timestamp': time.time()
        })
        
        self.total_notes_measured += 1
        
    def should_adjust(self) -> bool:
        """
        Determina si es momento de ajustar la latencia.
        
        Returns:
            True si se deben aplicar ajustes ahora
        """
        if not self.enabled:
            return False
        
        # Necesitamos al menos 10 muestras
        if len(self.timing_samples) < 10:
            return False
        
        # No ajustar muy frecuentemente
        if time.time() - self.last_adjustment_time < self.min_adjustment_interval:
            return False
        
        return True
    
    def calculate_adjustment(self) -> Tuple[float, dict]:
        """
        Calcula el ajuste necesario basándose en las mediciones.
        
        Returns:
            Tuple de (nuevo_valor_latencia, estadísticas)
        """
        if len(self.timing_samples) < 5:
            return self.current_latency, {}
        
        # Extraer offsets de las últimas muestras
        recent_samples = list(self.timing_samples)[-20:]  # Últimas 20
        offsets = [s['offset'] for s in recent_samples]
        
        # Calcular estadísticas
        mean_offset = statistics.mean(offsets)
        median_offset = statistics.median(offsets)
        
        try:
            stdev_offset = statistics.stdev(offsets) if len(offsets) > 1 else 0.0
        except:
            stdev_offset = 0.0
        
        # Usar mediana (más robusta a outliers)
        detected_error = median_offset
        
        # Solo ajustar si el error supera el threshold
        if abs(detected_error) < self.adjustment_threshold:
            stats = {
                'mean_offset': mean_offset,
                'median_offset': median_offset,
                'stdev_offset': stdev_offset,
                'samples': len(offsets),
                'adjustment_needed': False
            }
            return self.current_latency, stats
        
        # Calcular nuevo valor de latencia
        # Si offset > 0: audio adelantado → reducir latency
        # Si offset < 0: audio retrasado → aumentar latency
        adjustment = -detected_error * self.adjustment_factor
        new_latency = self.current_latency + adjustment
        
        # Aplicar límites
        new_latency = max(self.min_latency, min(self.max_latency, new_latency))
        
        stats = {
            'mean_offset': mean_offset,
            'median_offset': median_offset,
            'stdev_offset': stdev_offset,
            'samples': len(offsets),
            'adjustment_needed': True,
            'old_latency': self.current_latency,
            'new_latency': new_latency,
            'adjustment': adjustment,
            'detected_error': detected_error
        }
        
        return new_latency, stats
    
    def apply_adjustment(self) -> Optional[dict]:
        """
        Aplica ajuste automático si es necesario.
        
        Returns:
            Diccionario con estadísticas del ajuste, o None si no se ajustó
        """
        if not self.should_adjust():
            return None
        
        new_latency, stats = self.calculate_adjustment()
        
        if stats.get('adjustment_needed', False):
            self.current_latency = new_latency
            self.adjustment_count += 1
            self.last_adjustment_time = time.time()
            
            print(f"\n🎵 TIMING SYNC ADJUSTMENT #{self.adjustment_count}")
            print(f"   Detected offset: {stats['detected_error']*1000:.1f}ms")
            print(f"   Old latency: {stats['old_latency']*1000:.1f}ms")
            print(f"   New latency: {stats['new_latency']*1000:.1f}ms")
            print(f"   Adjustment: {stats['adjustment']*1000:.1f}ms")
            print(f"   Samples: {stats['samples']}")
            print(f"   Std dev: {stats['stdev_offset']*1000:.1f}ms\n")
            
            return stats
        
        return None
    
    def get_current_latency(self) -> float:
        """Retorna la latencia actual ajustada"""
        return self.current_latency
    
    def get_statistics(self) -> dict:
        """
        Retorna estadísticas completas del sistema de sincronización.
        
        Returns:
            Diccionario con estadísticas
        """
        if not self.timing_samples:
            return {
                'enabled': self.enabled,
                'current_latency_ms': self.current_latency * 1000,
                'total_notes': self.total_notes_measured,
                'adjustments': self.adjustment_count,
                'samples': 0
            }
        
        offsets = [s['offset'] for s in self.timing_samples]
        
        return {
            'enabled': self.enabled,
            'current_latency_ms': self.current_latency * 1000,
            'total_notes': self.total_notes_measured,
            'adjustments': self.adjustment_count,
            'samples': len(offsets),
            'mean_offset_ms': statistics.mean(offsets) * 1000,
            'median_offset_ms': statistics.median(offsets) * 1000,
            'stdev_offset_ms': statistics.stdev(offsets) * 1000 if len(offsets) > 1 else 0.0,
            'min_offset_ms': min(offsets) * 1000,
            'max_offset_ms': max(offsets) * 1000
        }
    
    def reset(self):
        """Reinicia el sistema de sincronización"""
        self.timing_samples.clear()
        self.total_notes_measured = 0
        self.adjustment_count = 0
        self.last_adjustment_time = time.time()
        print("🔄 Timing sync reset")
    
    def enable(self):
        """Activa el sistema de sincronización"""
        self.enabled = True
        print("✅ Timing sync enabled")
    
    def disable(self):
        """Desactiva el sistema de sincronización"""
        self.enabled = False
        print("❌ Timing sync disabled")
    
    def set_latency(self, latency: float):
        """
        Establece manualmente la latencia.
        
        Args:
            latency: Nueva latencia en segundos
        """
        latency = max(self.min_latency, min(self.max_latency, latency))
        old_latency = self.current_latency
        self.current_latency = latency
        print(f"🎛️ Manual latency adjustment: {old_latency*1000:.1f}ms → {latency*1000:.1f}ms")
