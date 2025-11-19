"""
Gestor de Perfiles de Instrumentos
Carga y gestiona perfiles de sonido desde assets/instruments/
"""
import os
import json
from pathlib import Path


class InstrumentProfileManager:
    """Gestor de perfiles de instrumentos"""
    
    def __init__(self, base_path="assets/instruments"):
        """
        Args:
            base_path: Ruta base a la carpeta de instrumentos
        """
        self.base_path = Path(base_path)
        self.profiles = {}
        self._load_all_profiles()
    
    def _load_all_profiles(self):
        """Carga todos los perfiles disponibles"""
        if not self.base_path.exists():
            print(f"⚠️ Carpeta {self.base_path} no existe")
            return
        
        # Buscar carpetas de perfiles
        for profile_dir in self.base_path.iterdir():
            if profile_dir.is_dir() and profile_dir.name != '__pycache__':
                profile_id = profile_dir.name
                profile_data = self._load_profile(profile_dir)
                
                if profile_data:
                    self.profiles[profile_id] = profile_data
                    print(f"✅ Perfil cargado: {profile_id}")
    
    def _load_profile(self, profile_dir):
        """Carga un perfil individual"""
        config_path = profile_dir / "config.json"
        
        # Leer config.json si existe
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            except Exception as e:
                print(f"❌ Error leyendo {config_path}: {e}")
                config = {}
        else:
            config = {}
        
        # Buscar samples WAV
        samples = {}
        for note_num in range(21, 109):  # MIDI 21-108 (A0 a C8)
            sample_path = profile_dir / f"note_{note_num}.wav"
            if sample_path.exists():
                samples[note_num] = str(sample_path)
        
        # Si hay samples, es un perfil sampled
        if samples:
            config['type'] = 'sampled'
            config['samples'] = samples
            config['num_samples'] = len(samples)
        
        # Añadir metadata
        config['profile_id'] = profile_dir.name
        config['path'] = str(profile_dir)
        
        return config
    
    def get_profile(self, profile_id):
        """Obtiene un perfil por ID"""
        return self.profiles.get(profile_id)
    
    def get_all_profiles(self):
        """Obtiene todos los perfiles"""
        return self.profiles
    
    def get_profile_list(self):
        """Obtiene lista de perfiles con info básica"""
        return [
            {
                'id': pid,
                'name': data.get('name', pid.title()),
                'type': data.get('type', 'synthetic'),
                'description': data.get('description', ''),
                'has_samples': 'samples' in data
            }
            for pid, data in self.profiles.items()
        ]
    
    def get_profile_config(self, profile_id):
        """Obtiene la configuración de un perfil"""
        profile = self.get_profile(profile_id)
        if not profile:
            return None
        
        return {
            'name': profile.get('name', profile_id.title()),
            'type': profile.get('type', 'synthetic'),
            'waveform': profile.get('waveform', 'complex'),
            'harmonics': profile.get('harmonics', [1.0, 0.5, 0.3]),
            'envelope': profile.get('envelope', {
                'attack': 0.01,
                'decay': 0.1,
                'sustain': 0.7,
                'release': 0.3
            }),
            'filter': profile.get('filter', {}),
            'reverb': profile.get('reverb', {}),
            'samples': profile.get('samples', {})
        }
    
    def profile_exists(self, profile_id):
        """Verifica si un perfil existe"""
        return profile_id in self.profiles
    
    def get_sample_path(self, profile_id, note_num):
        """Obtiene la ruta del sample para una nota específica"""
        profile = self.get_profile(profile_id)
        if not profile or 'samples' not in profile:
            return None
        
        return profile['samples'].get(note_num)
    
    def has_samples(self, profile_id):
        """Verifica si un perfil tiene samples WAV"""
        profile = self.get_profile(profile_id)
        return profile and 'samples' in profile and len(profile['samples']) > 0
    
    def get_fallback_profile(self):
        """Obtiene el perfil por defecto (acoustic)"""
        return self.get_profile('acoustic') or list(self.profiles.values())[0]
    
    def reload_profiles(self):
        """Recarga todos los perfiles"""
        self.profiles.clear()
        self._load_all_profiles()
    
    def create_custom_profile(self, profile_id, config):
        """Crea un nuevo perfil personalizado"""
        profile_dir = self.base_path / "custom" / profile_id
        profile_dir.mkdir(parents=True, exist_ok=True)
        
        config_path = profile_dir / "config.json"
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        # Recargar perfiles
        self.reload_profiles()
        
        return True
    
    def get_profile_stats(self, profile_id):
        """Obtiene estadísticas de un perfil"""
        profile = self.get_profile(profile_id)
        if not profile:
            return None
        
        stats = {
            'name': profile.get('name', profile_id),
            'type': profile.get('type', 'synthetic'),
            'has_config': 'envelope' in profile,
            'has_samples': 'samples' in profile,
            'num_samples': profile.get('num_samples', 0),
            'coverage': 0.0
        }
        
        if stats['has_samples']:
            stats['coverage'] = (stats['num_samples'] / 88) * 100
        
        return stats


# Instancia global (singleton)
_profile_manager = None

def get_profile_manager():
    """Obtiene la instancia global del gestor de perfiles"""
    global _profile_manager
    if _profile_manager is None:
        _profile_manager = InstrumentProfileManager()
    return _profile_manager
