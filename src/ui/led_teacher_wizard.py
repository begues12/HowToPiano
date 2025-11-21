"""
LED Teacher Wizard - Step-by-step LED calibration for piano keys
Handles automatic LED distribution and manual fine-tuning
"""

from PyQt6.QtWidgets import (QWizard, QWizardPage, QVBoxLayout, QHBoxLayout,
                              QLabel, QPushButton, QSpinBox, QComboBox, 
                              QRadioButton, QButtonGroup, QProgressBar,
                              QGroupBox, QFormLayout, QTextEdit, QSlider,
                              QCheckBox, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor
import json
from pathlib import Path


class LedTeacherWizard(QWizard):
    """
    Wizard for LED Teacher configuration and calibration
    
    Steps:
    1. Welcome & Piano Selection
    2. Automatic LED Distribution
    3. Test First Key
    4. Manual Adjustment (if needed)
    5. Save Configuration
    """
    
    # Signal emitted when calibration is complete
    calibration_complete = pyqtSignal(dict)  # Emits LED mapping configuration
    
    def __init__(self, arduino_conn=None, parent=None):
        super().__init__(parent)
        
        self.arduino = arduino_conn
        self.led_mapping = {}  # {midi_note: {'start_led': int, 'num_leds': int}}
        self.current_calibration_note = None
        
        self.setWindowTitle("🎹 LED Teacher Setup Wizard")
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)
        self.setMinimumSize(700, 500)
        
        # Pages will be added after all classes are defined
        # See setup_pages() method at the bottom
        
        # Apply dark theme
        self.setStyleSheet("""
            QWizard {
                background-color: #2c3e50;
            }
            QWizardPage {
                background-color: #34495e;
                color: white;
            }
            QLabel {
                color: white;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #7f8c8d;
            }
            QSpinBox, QComboBox {
                background-color: #2c3e50;
                color: white;
                border: 1px solid #7f8c8d;
                padding: 5px;
                border-radius: 3px;
            }
            QRadioButton {
                color: white;
                spacing: 8px;
            }
            QRadioButton::indicator {
                width: 18px;
                height: 18px;
            }
            QGroupBox {
                color: white;
                border: 2px solid #3498db;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QProgressBar {
                border: 2px solid #7f8c8d;
                border-radius: 5px;
                text-align: center;
                background-color: #2c3e50;
                color: white;
            }
            QProgressBar::chunk {
                background-color: #27ae60;
                border-radius: 3px;
            }
        """)
    
    def setup_pages(self):
        """Add pages after all classes are defined"""
        self.addPage(WelcomePage(self))
        self.addPage(PianoConfigPage(self))
        self.addPage(AutoDistributionPage(self))
        self.addPage(VerificationPage(self))
        self.addPage(ManualCalibrationPage(self))
        self.addPage(FinalPage(self))
    
    def get_led_mapping(self):
        """Get the final LED mapping configuration"""
        return self.led_mapping


class WelcomePage(QWizardPage):
    """Page 1: Welcome and introduction"""
    
    def __init__(self, wizard):
        super().__init__()
        self.wizard = wizard
        self.setTitle("🎹 Welcome to LED Teacher Setup")
        self.setSubTitle("Let's configure your piano LED strip step by step")
        
        layout = QVBoxLayout()
        
        # Welcome message
        welcome = QLabel(
            "This wizard will help you configure your LED strip for your piano keyboard.\n\n"
            "You will need:\n"
            "• Arduino connected with WS2812B LED strip\n"
            "• 144 LEDs/meter strip (6.94mm per LED)\n"
            "• Your piano keyboard ready\n\n"
            "The process:\n"
            "1️⃣ Select your piano configuration\n"
            "2️⃣ Automatic LED distribution calculation\n"
            "3️⃣ Test and verify alignment\n"
            "4️⃣ Manual adjustment if needed\n"
            "5️⃣ Save configuration"
        )
        welcome.setWordWrap(True)
        welcome.setStyleSheet("font-size: 13px; line-height: 1.6; padding: 20px;")
        layout.addWidget(welcome)
        
        # Warning box
        warning_box = QGroupBox("⚠️ Important")
        warning_layout = QVBoxLayout()
        warning_label = QLabel(
            "Make sure your Arduino is connected and the LED strip is properly powered.\n"
            "The wizard will light up LEDs to help you verify the configuration."
        )
        warning_label.setWordWrap(True)
        warning_label.setStyleSheet("color: #f39c12; font-size: 12px;")
        warning_layout.addWidget(warning_label)
        warning_box.setLayout(warning_layout)
        layout.addWidget(warning_box)
        
        layout.addStretch()
        self.setLayout(layout)


class PianoConfigPage(QWizardPage):
    """Page 2: Piano configuration (keys, starting note)"""
    
    def __init__(self, wizard):
        super().__init__()
        self.wizard = wizard
        self.setTitle("🎹 Piano Configuration")
        self.setSubTitle("Tell us about your piano keyboard")
        
        layout = QVBoxLayout()
        
        # Configuration form
        config_group = QGroupBox("Piano Specifications")
        form = QFormLayout()
        
        # Number of keys
        self.keys_combo = QComboBox()
        self.keys_combo.addItems(["25", "37", "49", "61", "76", "88"])
        self.keys_combo.setCurrentText("88")
        self.keys_combo.currentTextChanged.connect(self._update_estimate)
        form.addRow("Number of keys:", self.keys_combo)
        
        # Starting key
        self.start_key_combo = QComboBox()
        self.start_key_combo.addItems([
            "A0 (MIDI 21) - 88-key piano",
            "C1 (MIDI 24)",
            "C2 (MIDI 36) - 61-key keyboard",
            "C3 (MIDI 48) - 49-key keyboard",
            "C4 (MIDI 60) - 25-key keyboard"
        ])
        self.start_key_combo.currentTextChanged.connect(self._update_estimate)
        form.addRow("Starting key:", self.start_key_combo)
        
        # LED strip specs
        info_label = QLabel("LED Strip: 144 LEDs/meter (6.94mm per LED)")
        info_label.setStyleSheet("color: #3498db; font-style: italic; margin-top: 10px;")
        form.addRow("", info_label)
        
        config_group.setLayout(form)
        layout.addWidget(config_group)
        
        # Estimate display
        estimate_group = QGroupBox("📊 Estimated Configuration")
        estimate_layout = QVBoxLayout()
        
        self.estimate_label = QLabel()
        self.estimate_label.setWordWrap(True)
        self.estimate_label.setStyleSheet("font-size: 12px; padding: 10px;")
        estimate_layout.addWidget(self.estimate_label)
        
        estimate_group.setLayout(estimate_layout)
        layout.addWidget(estimate_group)
        
        layout.addStretch()
        self.setLayout(layout)
        
        # Initial estimate
        self._update_estimate()
        
        # Register fields
        self.registerField("num_keys", self.keys_combo, "currentText")
        self.registerField("start_key", self.start_key_combo, "currentText")
    
    def _update_estimate(self):
        """Calculate and display LED estimates"""
        num_keys = int(self.keys_combo.currentText())
        
        # Calculate white and black keys
        # Piano pattern: C C# D D# E F F# G G# A A# B (7 white, 5 black per octave)
        full_octaves = num_keys // 12
        remaining_keys = num_keys % 12
        
        white_keys = full_octaves * 7
        black_keys = full_octaves * 5
        
        # Count remaining keys
        remaining_pattern = [True, False, True, False, True, True, False, True, False, True, False, True]  # White=True, Black=False
        for i in range(remaining_keys):
            if remaining_pattern[i]:
                white_keys += 1
            else:
                black_keys += 1
        
        # LED calculations (144 LEDs/meter = 6.94mm per LED)
        white_key_width = 23.0  # mm (typical)
        black_key_width = 13.0  # mm (typical)
        led_spacing = 6.94  # mm (144 LEDs/meter)
        
        leds_per_white = round(white_key_width / led_spacing)
        leds_per_black = round(black_key_width / led_spacing)
        
        total_leds = (white_keys * leds_per_white) + (black_keys * leds_per_black)
        total_length = total_leds * led_spacing / 1000  # meters
        
        # Store for next page
        self.wizard.estimated_config = {
            'num_keys': num_keys,
            'white_keys': white_keys,
            'black_keys': black_keys,
            'leds_per_white': leds_per_white,
            'leds_per_black': leds_per_black,
            'total_leds': total_leds,
            'total_length': total_length
        }
        
        # Display
        self.estimate_label.setText(
            f"<b>Keys:</b> {white_keys} white + {black_keys} black = {num_keys} total<br><br>"
            f"<b>LEDs per key:</b><br>"
            f"  • White keys: ~{leds_per_white} LEDs ({white_key_width}mm ÷ {led_spacing}mm)<br>"
            f"  • Black keys: ~{leds_per_black} LEDs ({black_key_width}mm ÷ {led_spacing}mm)<br><br>"
            f"<b>Total LEDs needed:</b> ~{total_leds} LEDs<br>"
            f"<b>Strip length:</b> ~{total_length:.2f} meters<br><br>"
            f"<span style='color: #f39c12;'>⚠️ This is an estimate. We'll verify in the next steps.</span>"
        )


class AutoDistributionPage(QWizardPage):
    """Page 3: Calculate automatic LED distribution"""
    
    def __init__(self, wizard):
        super().__init__()
        self.wizard = wizard
        self.setTitle("🤖 Automatic LED Distribution")
        self.setSubTitle("Calculating LED positions for each key")
        
        layout = QVBoxLayout()
        
        info = QLabel(
            "Based on your piano configuration, we'll calculate how many LEDs "
            "each key should have.\n\n"
            "Standard widths:\n"
            "• White keys: ~23mm (≈3-4 LEDs at 144 LEDs/meter)\n"
            "• Black keys: ~13mm (≈2 LEDs at 144 LEDs/meter)"
        )
        info.setWordWrap(True)
        info.setStyleSheet("padding: 10px; font-size: 12px;")
        layout.addWidget(info)
        
        # Progress bar
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        layout.addWidget(self.progress)
        
        # Results display
        results_group = QGroupBox("📋 LED Mapping")
        results_layout = QVBoxLayout()
        
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setMaximumHeight(200)
        self.results_text.setStyleSheet("""
            QTextEdit {
                background-color: #2c3e50;
                color: #ecf0f1;
                border: 1px solid #7f8c8d;
                font-family: 'Courier New', monospace;
                font-size: 10px;
            }
        """)
        results_layout.addWidget(self.results_text)
        
        results_group.setLayout(results_layout)
        layout.addWidget(results_group)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def initializePage(self):
        """Calculate LED distribution when page is shown"""
        self.progress.setValue(0)
        self.results_text.clear()
        
        # Start calculation
        QTimer.singleShot(100, self._calculate_distribution)
    
    def _calculate_distribution(self):
        """Calculate LED distribution for all keys"""
        config = self.wizard.estimated_config
        num_keys = config['num_keys']
        leds_per_white = config['leds_per_white']
        leds_per_black = config['leds_per_black']
        
        # Get starting MIDI note
        start_text = self.field("start_key")
        if "21" in start_text:
            start_midi = 21  # A0
        elif "24" in start_text:
            start_midi = 24  # C1
        elif "36" in start_text:
            start_midi = 36  # C2
        elif "48" in start_text:
            start_midi = 48  # C3
        elif "60" in start_text:
            start_midi = 60  # C4
        else:
            start_midi = 21  # Default A0
        
        # Calculate LED positions
        self.wizard.led_mapping = {}
        current_led = 0
        
        # Piano key pattern (relative to C): C=0, C#=1, D=2, D#=3, E=4, F=5, F#=6, G=7, G#=8, A=9, A#=10, B=11
        # Black keys are: 1, 3, 6, 8, 10 (C#, D#, F#, G#, A#)
        black_keys_in_octave = {1, 3, 6, 8, 10}
        
        log_text = "LED Distribution:\n" + "="*50 + "\n"
        
        for i in range(num_keys):
            midi_note = start_midi + i
            note_in_octave = midi_note % 12
            is_black = note_in_octave in black_keys_in_octave
            
            num_leds = leds_per_black if is_black else leds_per_white
            
            self.wizard.led_mapping[midi_note] = {
                'start_led': current_led,
                'num_leds': num_leds,
                'is_black': is_black
            }
            
            # Note name
            note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
            octave = (midi_note // 12) - 1
            note_name = f"{note_names[note_in_octave]}{octave}"
            
            log_text += f"MIDI {midi_note:3d} ({note_name:4s}) {'⬛' if is_black else '⬜'}: LEDs {current_led:3d}-{current_led + num_leds - 1:3d} ({num_leds} LEDs)\n"
            
            current_led += num_leds
            
            # Update progress
            progress = int((i + 1) / num_keys * 100)
            self.progress.setValue(progress)
        
        total_leds = current_led
        log_text += "="*50 + "\n"
        log_text += f"Total LEDs required: {total_leds}\n"
        
        self.results_text.setText(log_text)
        
        # Store total for reference
        self.wizard.total_leds_calculated = total_leds
        
        print(f"✅ LED distribution calculated: {num_keys} keys, {total_leds} LEDs")


class VerificationPage(QWizardPage):
    """Page 4: Test and verify LED alignment"""
    
    def __init__(self, wizard):
        super().__init__()
        self.wizard = wizard
        self.setTitle("✅ Verify LED Alignment")
        self.setSubTitle("Let's test if the LEDs align correctly with your keys")
        
        layout = QVBoxLayout()
        
        # Instructions
        instructions = QLabel(
            "We'll now light up the LEDs for each key to verify alignment.\n\n"
            "Watch your piano keyboard and confirm if the LEDs line up correctly with each key."
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("padding: 10px; font-size: 13px;")
        layout.addWidget(instructions)
        
        # Test controls
        test_group = QGroupBox("🧪 Test Controls")
        test_layout = QVBoxLayout()
        
        # Test all keys button
        test_all_btn = QPushButton("🌈 Test All Keys (Rainbow Scan)")
        test_all_btn.clicked.connect(self._test_all_keys)
        test_layout.addWidget(test_all_btn)
        
        # Test specific key
        specific_layout = QHBoxLayout()
        specific_layout.addWidget(QLabel("Test specific key:"))
        self.test_key_spin = QSpinBox()
        self.test_key_spin.setRange(21, 108)
        self.test_key_spin.setValue(60)  # Middle C
        specific_layout.addWidget(self.test_key_spin)
        test_key_btn = QPushButton("💡 Light Up")
        test_key_btn.clicked.connect(self._test_specific_key)
        specific_layout.addWidget(test_key_btn)
        test_layout.addLayout(specific_layout)
        
        # Clear LEDs button
        clear_btn = QPushButton("⚫ Turn Off All LEDs")
        clear_btn.clicked.connect(self._clear_leds)
        test_layout.addWidget(clear_btn)
        
        test_group.setLayout(test_layout)
        layout.addWidget(test_group)
        
        # Verification question
        verify_group = QGroupBox("❓ Verification")
        verify_layout = QVBoxLayout()
        
        question = QLabel("Do all the LEDs align correctly with their keys?")
        question.setStyleSheet("font-size: 13px; font-weight: bold; margin-bottom: 10px;")
        verify_layout.addWidget(question)
        
        self.alignment_group = QButtonGroup()
        self.yes_radio = QRadioButton("✅ Yes, everything is aligned perfectly")
        self.no_radio = QRadioButton("❌ No, some keys need adjustment")
        self.alignment_group.addButton(self.yes_radio)
        self.alignment_group.addButton(self.no_radio)
        verify_layout.addWidget(self.yes_radio)
        verify_layout.addWidget(self.no_radio)
        
        self.yes_radio.setChecked(True)
        
        verify_group.setLayout(verify_layout)
        layout.addWidget(verify_group)
        
        layout.addStretch()
        self.setLayout(layout)
        
        # Register field for next button
        self.registerField("alignment_ok", self.yes_radio)
    
    def _test_all_keys(self):
        """Test all keys with rainbow effect"""
        if not self.wizard.arduino or not self.wizard.arduino.is_connected:
            QMessageBox.warning(self, "Arduino Not Connected", 
                              "Please connect your Arduino in the settings first.")
            return
        
        print("🌈 Testing all keys with rainbow scan...")
        # TODO: Implement rainbow scan through all LEDs
        # This will be implemented when Arduino communication is ready
    
    def _test_specific_key(self):
        """Light up LEDs for a specific key"""
        if not self.wizard.arduino or not self.wizard.arduino.is_connected:
            QMessageBox.warning(self, "Arduino Not Connected",
                              "Please connect your Arduino in the settings first.")
            return
        
        midi_note = self.test_key_spin.value()
        if midi_note in self.wizard.led_mapping:
            mapping = self.wizard.led_mapping[midi_note]
            print(f"💡 Lighting key {midi_note}: LEDs {mapping['start_led']}-{mapping['start_led'] + mapping['num_leds'] - 1}")
            # TODO: Send command to Arduino to light up these LEDs
        else:
            QMessageBox.warning(self, "Key Not Found",
                              f"MIDI note {midi_note} is not in the current mapping.")
    
    def _clear_leds(self):
        """Turn off all LEDs"""
        if not self.wizard.arduino or not self.wizard.arduino.is_connected:
            return
        
        print("⚫ Clearing all LEDs...")
        # TODO: Send command to Arduino to clear all LEDs
    
    def nextId(self):
        """Determine next page based on alignment answer"""
        if self.no_radio.isChecked():
            # Go to manual calibration
            return self.wizard.pageIds()[4]  # ManualCalibrationPage
        else:
            # Skip manual calibration, go to final page
            return self.wizard.pageIds()[5]  # FinalPage


class ManualCalibrationPage(QWizardPage):
    """Page 5: Manual LED adjustment for individual keys"""
    
    def __init__(self, wizard):
        super().__init__()
        self.wizard = wizard
        self.setTitle("🔧 Manual Calibration")
        self.setSubTitle("Adjust LEDs for individual keys")
        
        self.current_key_index = 0
        self.keys_to_calibrate = []
        
        layout = QVBoxLayout()
        
        # Instructions
        instructions = QLabel(
            "We'll go through each key one by one. For each key:\n"
            "1. The LEDs will light up\n"
            "2. Check if they align with the key\n"
            "3. Adjust the number of LEDs if needed\n"
            "4. Click Next to move to the next key"
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("padding: 10px; font-size: 12px;")
        layout.addWidget(instructions)
        
        # Current key info
        self.key_info_group = QGroupBox("Current Key")
        key_info_layout = QVBoxLayout()
        
        self.current_key_label = QLabel("Key: -")
        self.current_key_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        key_info_layout.addWidget(self.current_key_label)
        
        self.key_position_label = QLabel("Position: -")
        key_info_layout.addWidget(self.key_position_label)
        
        self.key_info_group.setLayout(key_info_layout)
        layout.addWidget(self.key_info_group)
        
        # LED adjustment
        adjust_group = QGroupBox("🔧 LED Adjustment")
        adjust_layout = QFormLayout()
        
        self.led_count_spin = QSpinBox()
        self.led_count_spin.setRange(1, 10)
        self.led_count_spin.setValue(3)
        self.led_count_spin.valueChanged.connect(self._update_led_preview)
        adjust_layout.addRow("Number of LEDs:", self.led_count_spin)
        
        self.led_range_label = QLabel("LED Range: -")
        self.led_range_label.setStyleSheet("color: #3498db; font-weight: bold;")
        adjust_layout.addRow("", self.led_range_label)
        
        adjust_group.setLayout(adjust_layout)
        layout.addWidget(adjust_group)
        
        # Navigation buttons
        nav_layout = QHBoxLayout()
        self.prev_key_btn = QPushButton("⬅️ Previous Key")
        self.prev_key_btn.clicked.connect(self._previous_key)
        nav_layout.addWidget(self.prev_key_btn)
        
        self.next_key_btn = QPushButton("➡️ Next Key")
        self.next_key_btn.clicked.connect(self._next_key)
        nav_layout.addWidget(self.next_key_btn)
        
        layout.addLayout(nav_layout)
        
        # Progress
        self.calibration_progress = QProgressBar()
        layout.addWidget(self.calibration_progress)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def initializePage(self):
        """Initialize manual calibration"""
        # Get all keys
        self.keys_to_calibrate = sorted(self.wizard.led_mapping.keys())
        self.current_key_index = 0
        self.calibration_progress.setRange(0, len(self.keys_to_calibrate))
        self.calibration_progress.setValue(0)
        
        self._show_current_key()
    
    def _show_current_key(self):
        """Display current key for calibration"""
        if not self.keys_to_calibrate:
            return
        
        midi_note = self.keys_to_calibrate[self.current_key_index]
        mapping = self.wizard.led_mapping[midi_note]
        
        # Note name
        note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        octave = (midi_note // 12) - 1
        note_name = f"{note_names[midi_note % 12]}{octave}"
        
        self.current_key_label.setText(f"Key: {note_name} (MIDI {midi_note})")
        self.key_position_label.setText(
            f"Position: {self.current_key_index + 1} of {len(self.keys_to_calibrate)} | "
            f"Type: {'Black ⬛' if mapping['is_black'] else 'White ⬜'}"
        )
        
        self.led_count_spin.setValue(mapping['num_leds'])
        self._update_led_preview()
        
        # Update progress
        self.calibration_progress.setValue(self.current_key_index)
        
        # Update button states
        self.prev_key_btn.setEnabled(self.current_key_index > 0)
        self.next_key_btn.setEnabled(self.current_key_index < len(self.keys_to_calibrate) - 1)
        
        # Light up current key
        self._light_current_key()
    
    def _update_led_preview(self):
        """Update LED range display"""
        if not self.keys_to_calibrate:
            return
        
        midi_note = self.keys_to_calibrate[self.current_key_index]
        mapping = self.wizard.led_mapping[midi_note]
        new_count = self.led_count_spin.value()
        
        start = mapping['start_led']
        end = start + new_count - 1
        
        self.led_range_label.setText(f"LED Range: {start} to {end} ({new_count} LEDs)")
        
        # Update mapping
        self.wizard.led_mapping[midi_note]['num_leds'] = new_count
        
        # Recalculate subsequent keys
        self._recalculate_subsequent_leds()
        
        # Light up to show changes
        self._light_current_key()
    
    def _recalculate_subsequent_leds(self):
        """Recalculate LED positions for all keys after the current one"""
        current_led = 0
        for midi_note in sorted(self.wizard.led_mapping.keys()):
            mapping = self.wizard.led_mapping[midi_note]
            mapping['start_led'] = current_led
            current_led += mapping['num_leds']
    
    def _light_current_key(self):
        """Light up the current key's LEDs"""
        if not self.wizard.arduino or not self.wizard.arduino.is_connected:
            return
        
        midi_note = self.keys_to_calibrate[self.current_key_index]
        mapping = self.wizard.led_mapping[midi_note]
        
        print(f"💡 Lighting key {midi_note}: LEDs {mapping['start_led']}-{mapping['start_led'] + mapping['num_leds'] - 1}")
        # TODO: Send command to Arduino
    
    def _previous_key(self):
        """Go to previous key"""
        if self.current_key_index > 0:
            self.current_key_index -= 1
            self._show_current_key()
    
    def _next_key(self):
        """Go to next key"""
        if self.current_key_index < len(self.keys_to_calibrate) - 1:
            self.current_key_index += 1
            self._show_current_key()


class FinalPage(QWizardPage):
    """Page 6: Save configuration and finish"""
    
    def __init__(self, wizard):
        super().__init__()
        self.wizard = wizard
        self.setTitle("✅ Configuration Complete!")
        self.setSubTitle("Your LED Teacher is ready to use")
        
        layout = QVBoxLayout()
        
        # Success message
        success = QLabel(
            "🎉 Congratulations! Your LED Teacher is now configured.\n\n"
            "The LED mapping has been saved and will be used automatically when you play."
        )
        success.setWordWrap(True)
        success.setStyleSheet("font-size: 14px; padding: 20px;")
        layout.addWidget(success)
        
        # Summary
        summary_group = QGroupBox("📊 Configuration Summary")
        summary_layout = QVBoxLayout()
        
        self.summary_label = QLabel()
        self.summary_label.setWordWrap(True)
        self.summary_label.setStyleSheet("font-size: 12px; padding: 10px;")
        summary_layout.addWidget(self.summary_label)
        
        summary_group.setLayout(summary_layout)
        layout.addWidget(summary_group)
        
        # Save options
        save_group = QGroupBox("💾 Save Options")
        save_layout = QVBoxLayout()
        
        self.save_to_settings = QCheckBox("Save to application settings (recommended)")
        self.save_to_settings.setChecked(True)
        save_layout.addWidget(self.save_to_settings)
        
        self.export_to_file = QCheckBox("Export to JSON file")
        save_layout.addWidget(self.export_to_file)
        
        save_group.setLayout(save_layout)
        layout.addWidget(save_group)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def initializePage(self):
        """Show summary when page is displayed"""
        mapping = self.wizard.led_mapping
        num_keys = len(mapping)
        total_leds = sum(m['num_leds'] for m in mapping.values())
        
        # Count by type
        white_keys = sum(1 for m in mapping.values() if not m['is_black'])
        black_keys = sum(1 for m in mapping.values() if m['is_black'])
        
        self.summary_label.setText(
            f"<b>Piano Configuration:</b><br>"
            f"• Total keys: {num_keys} ({white_keys} white + {black_keys} black)<br>"
            f"• Total LEDs: {total_leds}<br>"
            f"• LED strip length: ~{total_leds * 6.94 / 1000:.2f} meters<br><br>"
            f"<b>Files:</b><br>"
            f"• Configuration: library/led_mapping.json<br>"
            f"• Settings: settings.json"
        )
    
    def validatePage(self):
        """Save configuration when Finish is clicked"""
        self._save_configuration()
        return True
    
    def _save_configuration(self):
        """Save LED mapping to file"""
        # Create config directory
        config_dir = Path('library')
        config_dir.mkdir(exist_ok=True)
        
        # Save LED mapping
        mapping_file = config_dir / 'led_mapping.json'
        with open(mapping_file, 'w', encoding='utf-8') as f:
            json.dump(self.wizard.led_mapping, f, indent=2)
        
        print(f"✅ LED mapping saved to {mapping_file}")
        
        # Emit signal with configuration
        self.wizard.calibration_complete.emit(self.wizard.led_mapping)


# Helper function to create and initialize wizard
def create_led_teacher_wizard(arduino_conn=None, parent=None):
    """
    Create and initialize LED Teacher Wizard
    
    Args:
        arduino_conn: Arduino connection object
        parent: Parent widget
    
    Returns:
        Initialized LedTeacherWizard instance
    """
    wizard = LedTeacherWizard(arduino_conn, parent)
    wizard.setup_pages()
    return wizard
