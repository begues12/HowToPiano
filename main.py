import sys
import os
import signal

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from src.ui.main_window import MainWindow

# Global reference to the window for signal handler
_window = None

def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully"""
    print("\n🛑 Cerrando aplicación...")
    if _window:
        _window.close()
    QApplication.quit()
    sys.exit(0)

def main():
    global _window
    
    # Register signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    
    app = QApplication(sys.argv)
    
    # Allow Python to process signals during Qt event loop
    timer = QTimer()
    timer.start(500)  # Check every 500ms
    timer.timeout.connect(lambda: None)  # Wake up Python interpreter
    
    _window = MainWindow()
    _window.show()
    
    try:
        sys.exit(app.exec())
    except KeyboardInterrupt:
        print("\n🛑 Cerrando aplicación...")
        _window.close()
        sys.exit(0)

if __name__ == "__main__":
    main()
