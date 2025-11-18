#!/bin/bash
# Script de instalación automática para HowToPiano
# Raspberry Pi Zero W / W2

echo "============================================"
echo "  HowToPiano - Instalación Automática"
echo "  Raspberry Pi Zero W/W2"
echo "============================================"
echo ""

# Verificar que se ejecuta como root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Este script debe ejecutarse con sudo"
    echo "   Usa: sudo bash install.sh"
    exit 1
fi

echo "✓ Ejecutando como root"
echo ""

# Actualizar sistema
echo "[1/6] Actualizando sistema..."
apt update && apt upgrade -y

# Instalar dependencias del sistema
echo ""
echo "[2/6] Instalando dependencias del sistema..."
apt install -y python3 python3-pip git

# Habilitar SPI (necesario para LEDs)
echo ""
echo "[3/6] Habilitando SPI..."
raspi-config nonint do_spi 0
echo "✓ SPI habilitado"

# Instalar librerías Python
echo ""
echo "[4/6] Instalando librerías Python..."
pip3 install -r requirements.txt

# Si falla, instalar manualmente las críticas
if [ $? -ne 0 ]; then
    echo "⚠ Instalación estándar falló, intentando manual..."
    pip3 install mido
    pip3 install rpi-ws281x
    pip3 install adafruit-circuitpython-neopixel
fi

# Configurar permisos GPIO
echo ""
echo "[5/6] Configurando permisos GPIO..."
usermod -a -G gpio pi
usermod -a -G spi pi

# Crear servicio systemd (opcional)
echo ""
echo "[6/6] ¿Deseas instalar HowToPiano como servicio que inicia al arrancar? (y/n)"
read -r response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    cat > /etc/systemd/system/howtopiano.service << EOF
[Unit]
Description=HowToPiano LED MIDI System
After=multi-user.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 $(pwd)/main.py --keyboard piano_88
WorkingDirectory=$(pwd)
StandardOutput=journal
StandardError=journal
Restart=on-failure
User=pi

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable howtopiano.service
    echo "✓ Servicio instalado (inicio automático)"
    echo "  Comandos útiles:"
    echo "    sudo systemctl start howtopiano   - Iniciar"
    echo "    sudo systemctl stop howtopiano    - Detener"
    echo "    sudo systemctl status howtopiano  - Ver estado"
else
    echo "⊘ Servicio no instalado"
fi

# Test de LEDs
echo ""
echo "============================================"
echo "  Instalación Completada ✓"
echo "============================================"
echo ""
echo "¿Deseas ejecutar un test de LEDs ahora? (y/n)"
read -r test_response
if [[ "$test_response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    echo ""
    echo "Ejecutando test de LEDs..."
    sudo python3 main.py --test
fi

echo ""
echo "============================================"
echo "  Siguiente paso:"
echo "  1. Conecta tu pendrive USB con archivos MIDI"
echo "  2. Ejecuta: sudo python3 main.py"
echo "  3. ¡Disfruta tu piano iluminado!"
echo "============================================"
echo ""
echo "📚 Documentación en: docs/"
echo "🐛 Problemas? Ver: docs/troubleshooting.md"
echo ""
