"""
Test del Sistema de Perfiles de Instrumentos
Valida la carga, detección y funcionalidad de perfiles
"""
import sys
from pathlib import Path

# Añadir src al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.instrument_profiles import get_profile_manager

def test_profile_manager():
    """Prueba el gestor de perfiles"""
    print("=" * 60)
    print("🧪 TEST: Gestor de Perfiles de Instrumentos")
    print("=" * 60)
    print()
    
    # Obtener instancia
    manager = get_profile_manager()
    
    # 1. Listar todos los perfiles
    print("📋 1. PERFILES DISPONIBLES")
    print("-" * 60)
    profiles = manager.get_profile_list()
    
    if not profiles:
        print("❌ No se encontraron perfiles")
        return False
    
    for p in profiles:
        print(f"  • {p['id']}")
        print(f"    Nombre: {p['name']}")
        print(f"    Tipo: {p['type']}")
        print(f"    Samples: {'✅' if p['has_samples'] else '❌'}")
        print()
    
    print(f"Total: {len(profiles)} perfiles\n")
    
    # 2. Estadísticas de cada perfil
    print("📊 2. ESTADÍSTICAS DE PERFILES")
    print("-" * 60)
    
    for p in profiles:
        stats = manager.get_profile_stats(p['id'])
        if stats:
            print(f"  {p['id']}:")
            print(f"    Config: {'✅' if stats['has_config'] else '❌'}")
            print(f"    Samples: {'✅' if stats['has_samples'] else '❌'}")
            if stats['has_samples']:
                print(f"    Cobertura: {stats['num_samples']}/88 ({stats['coverage']:.1f}%)")
            print()
    
    # 3. Verificar configuraciones
    print("⚙️  3. CONFIGURACIONES DE PERFILES")
    print("-" * 60)
    
    test_profiles = ['acoustic', 'grand']
    for profile_id in test_profiles:
        if manager.profile_exists(profile_id):
            config = manager.get_profile_config(profile_id)
            print(f"  {profile_id}:")
            print(f"    Nombre: {config['name']}")
            print(f"    Tipo: {config['type']}")
            print(f"    Armónicos: {len(config.get('harmonics', []))} valores")
            print(f"    Envelope: {list(config.get('envelope', {}).keys())}")
            print()
    
    # 4. Verificar samples WAV
    print("🎵 4. SAMPLES WAV")
    print("-" * 60)
    
    for p in profiles:
        if p['has_samples']:
            print(f"  {p['id']}: Buscando samples...")
            
            # Probar algunas notas
            test_notes = [21, 60, 108]  # A0, C4, C8
            found = 0
            for note in test_notes:
                path = manager.get_sample_path(p['id'], note)
                if path:
                    print(f"    ✅ Nota {note}: {Path(path).name}")
                    found += 1
                else:
                    print(f"    ❌ Nota {note}: No encontrada")
            
            print(f"    Total: {found}/{len(test_notes)} notas de prueba\n")
    
    # 5. Test de recarga
    print("🔄 5. TEST DE RECARGA")
    print("-" * 60)
    
    print("  Recargando perfiles...")
    manager.reload_profiles()
    new_profiles = manager.get_profile_list()
    print(f"  ✅ {len(new_profiles)} perfiles recargados\n")
    
    # Resumen final
    print("=" * 60)
    print("✅ TEST COMPLETADO")
    print("=" * 60)
    print(f"Perfiles detectados: {len(profiles)}")
    print(f"Con samples WAV: {sum(1 for p in profiles if p['has_samples'])}")
    print(f"Solo síntesis: {sum(1 for p in profiles if not p['has_samples'])}")
    print()
    
    return True

def test_piano_sound_integration():
    """Prueba la integración con PianoSound"""
    print("=" * 60)
    print("🎹 TEST: Integración con PianoSound")
    print("=" * 60)
    print()
    
    try:
        from src.piano_sound import PianoSound
        
        # Crear instancia
        print("  Inicializando PianoSound...")
        piano = PianoSound(volume=0.3, profile='acoustic')
        
        if not piano.enabled:
            print("  ⚠️  pygame no disponible - saltando test de audio")
            return True
        
        print(f"  ✅ Perfil actual: {piano.current_profile}")
        print(f"  ✅ Usando samples: {piano.use_samples}")
        print()
        
        # Probar cambio de perfil
        print("  Probando cambio de perfil...")
        test_profiles = ['grand', 'bright', 'acoustic']
        
        for profile in test_profiles:
            piano.set_profile(profile)
            print(f"    • {profile}: {piano.use_samples and '🎵 WAV' or '🎹 Síntesis'}")
        
        print()
        print("  ✅ Integración funcionando correctamente\n")
        return True
        
    except ImportError as e:
        print(f"  ❌ Error importando PianoSound: {e}\n")
        return False
    except Exception as e:
        print(f"  ❌ Error en test: {e}\n")
        return False

def main():
    """Ejecuta todos los tests"""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 10 + "TEST SUITE: INSTRUMENT PROFILES" + " " * 17 + "║")
    print("╚" + "═" * 58 + "╝")
    print()
    
    results = []
    
    # Test 1: Profile Manager
    results.append(("Profile Manager", test_profile_manager()))
    
    # Test 2: PianoSound Integration
    results.append(("PianoSound Integration", test_piano_sound_integration()))
    
    # Resumen
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 20 + "RESUMEN FINAL" + " " * 25 + "║")
    print("╚" + "═" * 58 + "╝")
    print()
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {name}")
    
    total = len(results)
    passed = sum(1 for _, r in results if r)
    
    print()
    print(f"  Total: {passed}/{total} tests pasados")
    print()
    
    if passed == total:
        print("  🎉 ¡Todos los tests pasaron exitosamente!\n")
        return 0
    else:
        print("  ⚠️  Algunos tests fallaron\n")
        return 1

if __name__ == '__main__':
    exit(main())
