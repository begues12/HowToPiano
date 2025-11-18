#!/usr/bin/env python3
"""
Demo de las nuevas características de la GUI
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_gui import *
import time

def demo_keyboard_clicks():
    """Demuestra el teclado clickeable"""
    print("\n" + "="*60)
    print("DEMO: Teclado Clickeable")
    print("="*60)
    print("✓ Haz click en cualquier tecla del teclado virtual")
    print("✓ La tecla se iluminará en amarillo")
    print("✓ El LED físico correspondiente se encenderá (en Raspberry Pi)")
    print("✓ Después de 300ms vuelve a su color original")
    print("\nPruébalo ahora en la GUI...")

def demo_led_test():
    """Demuestra el test de último LED"""
    print("\n" + "="*60)
    print("DEMO: Test de Último LED")
    print("="*60)
    print("1. Abre la ventana de Configuración (⚙)")
    print("2. En 'Número de LEDs' cambia el valor")
    print("3. Click en botón '💡 Test'")
    print("4. El ÚLTIMO LED de tu tira se encenderá en ROJO")
    print("5. Así sabrás si configuraste el número correcto")
    print("\nEjemplo:")
    print("  - Configuraste 88 LEDs → LED #88 se enciende")
    print("  - Si ves que se enciende el LED #50 → tienes 50 LEDs")
    print("  - Ajusta el número hasta que el último LED coincida")

def demo_score_display():
    """Demuestra la partitura visual"""
    print("\n" + "="*60)
    print("DEMO: Partitura Visual")
    print("="*60)
    print("✓ Encima del teclado verás un PENTAGRAMA")
    print("✓ Las notas ACTUALES aparecen en ROJO (iluminadas)")
    print("✓ Las notas PRÓXIMAS aparecen en NEGRO")
    print("✓ Se actualiza en tiempo real mientras tocas")
    print("\nCaracterísticas:")
    print("  - Clave de Sol (𝄞)")
    print("  - 5 líneas del pentagrama")
    print("  - Líneas adicionales para notas muy altas/bajas")
    print("  - Plicas correctas (arriba/abajo según altura)")

def demo_complete_workflow():
    """Muestra un flujo completo de uso"""
    print("\n" + "="*60)
    print("FLUJO COMPLETO DE USO")
    print("="*60)
    print("\n1️⃣ CONFIGURACIÓN INICIAL")
    print("   • Click ⚙ Configuración")
    print("   • Número de teclas: 88 (o el tuyo)")
    print("   • Número de LEDs: 88 (o los que tengas)")
    print("   • Click 💡 Test para verificar último LED")
    print("   • Ajusta hasta que coincida")
    print("   • Guardar")
    
    print("\n2️⃣ CARGAR PARTITURA")
    print("   • Click 🔍 Buscar MIDI")
    print("   • Selecciona archivo .mid")
    print("   • O usa 📂 USB si tienes memoria conectada")
    
    print("\n3️⃣ PRACTICAR")
    print("   • Elige modo:")
    print("     - 👨‍🎓 Modo Alumno: Espera cada X acordes")
    print("     - 🎹 Modo Práctica: Ilumina automáticamente")
    print("     - 🎼 Modo Maestro: Ilumina lo que tocas")
    
    print("\n4️⃣ DURANTE LA PRÁCTICA")
    print("   • Partitura muestra notas actuales en ROJO")
    print("   • Teclado virtual ilumina teclas")
    print("   • LEDs físicos iluminan piano real")
    print("   • Click en teclado virtual para probar")
    
    print("\n5️⃣ CONTROL")
    print("   • Barra de progreso muestra avance")
    print("   • Botón ⏹ DETENER para pausar")
    print("   • Archivos recientes para acceso rápido")

def show_tips():
    """Muestra tips útiles"""
    print("\n" + "="*60)
    print("💡 TIPS ÚTILES")
    print("="*60)
    print("\n🎹 Teclado Virtual:")
    print("  • Las teclas BLANCAS son las notas naturales (Do, Re, Mi...)")
    print("  • Las teclas NEGRAS son los sostenidos/bemoles (Do#, Re#...)")
    print("  • Click para probar sin tener piano físico")
    print("  • Se ilumina en amarillo al hacer click")
    
    print("\n💡 Test de LEDs:")
    print("  • IMPORTANTE: Siempre prueba el número de LEDs primero")
    print("  • Si el LED incorrecto se enciende → ajusta el número")
    print("  • El test enciende en ROJO el último LED")
    print("  • Espera 3 segundos y se apaga automáticamente")
    
    print("\n🎼 Partitura:")
    print("  • Do Central (C4) = MIDI 60 → línea adicional inferior")
    print("  • Notas rojas = tocar AHORA")
    print("  • Notas negras = próximas en la secuencia")
    print("  • Máximo 10 notas próximas visibles")
    
    print("\n⚙️ Configuración:")
    print("  • Modo LED 'Full' = distribuye uniformemente los LEDs")
    print("  • Modo LED 'Compact' = usa solo los necesarios")
    print("  • Brillo ajustable 10%-100%")
    print("  • Todo se guarda automáticamente")

def print_keyboard_layout():
    """Muestra el layout del teclado visual"""
    print("\n" + "="*60)
    print("LAYOUT DEL TECLADO VIRTUAL (88 teclas)")
    print("="*60)
    print("""
    A0  B0  C1  D1  E1  F1  G1  A1  B1  C2  D2  E2  ...  C8
    │▓│░│▓│░│▓││░│▓│░│▓││░│▓│░│▓││░│▓│░│▓││░│▓│░│▓│  ...  │░│
    
    Leyenda:
    ░ = Tecla blanca (notas naturales)
    ▓ = Tecla negra (sostenidos/bemoles)
    
    Notas MIDI:
    A0 = 21   (nota más grave en piano de 88 teclas)
    C4 = 60   (Do central)
    C8 = 108  (nota más aguda en piano de 88 teclas)
    """)

if __name__ == "__main__":
    print("\n" + "🎹"*30)
    print("   DEMOSTRACIÓN INTERACTIVA - HowToPiano GUI")
    print("🎹"*30)
    
    demo_keyboard_clicks()
    input("\nPresiona Enter para continuar...")
    
    demo_led_test()
    input("\nPresiona Enter para continuar...")
    
    demo_score_display()
    input("\nPresiona Enter para continuar...")
    
    demo_complete_workflow()
    input("\nPresiona Enter para continuar...")
    
    show_tips()
    input("\nPresiona Enter para continuar...")
    
    print_keyboard_layout()
    
    print("\n" + "="*60)
    print("¡Ahora prueba todas estas funciones en la GUI!")
    print("="*60)
    print("\nLa GUI debería estar abierta.")
    print("Si no, ejecuta: python test_gui.py")
    print()
