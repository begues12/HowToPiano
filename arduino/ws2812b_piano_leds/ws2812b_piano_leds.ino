/*
 * WS2812B LED Strip Controller for Piano Keys
 * Compatible with HowToPiano Python application
 * 
 * Hardware:
 * - Arduino (Uno/Nano/Mega)
 * - WS2812B LED Strip (DC 5V)
 * - Data pin: Digital Pin 6 (configurable)
 * 
 * Communication Protocol:
 * Serial commands from Python:
 * - "LED:note,r,g,b\n" - Set LED for specific note (0-87)
 * - "OFF:note\n" - Turn off LED for specific note
 * - "CLEAR\n" - Turn off all LEDs
 * - "BRIGHTNESS:value\n" - Set brightness (0-255)
 */

#include <FastLED.h>

// LED Strip Configuration
#define LED_PIN     6        // Data pin connected to WS2812B
#define NUM_LEDS    88       // 88 piano keys (21-108 MIDI)
#define LED_TYPE    WS2812B
#define COLOR_ORDER GRB
#define BRIGHTNESS  128      // Default brightness (0-255)

CRGB leds[NUM_LEDS];

void setup() {
  // Initialize serial communication at 115200 baud for fast USB response
  Serial.begin(115200);
  while (!Serial && millis() < 1000); // Wait for serial, max 1 second
  
  // Initialize FastLED with optimizations
  FastLED.addLeds<LED_TYPE, LED_PIN, COLOR_ORDER>(leds, NUM_LEDS);
  FastLED.setBrightness(BRIGHTNESS);
  FastLED.setMaxRefreshRate(120); // Maximum refresh rate for smooth updates
  
  // Clear all LEDs
  fill_solid(leds, NUM_LEDS, CRGB::Black);
  FastLED.show();
  
  // Startup animation - quick test
  startupAnimation();
  
  Serial.println("READY");
}

void loop() {
  // Process commands as fast as possible - no delays
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    
    if (command.length() > 0) {
      processCommand(command);
    }
  }
  
  // FastLED handles timing internally, no delay needed
}

void processCommand(String cmd) {
  if (cmd.startsWith("ON:")) {
    // Format: ON:note:brightness
    cmd.remove(0, 3); // Remove "ON:"
    
    int colon = cmd.indexOf(':');
    if (colon > 0) {
      int midiNote = cmd.substring(0, colon).toInt();
      int brightness = cmd.substring(colon + 1).toInt();
      
      // Convert MIDI note to note name for feedback
      String noteName = midiToNoteName(midiNote);
      
      // Turn on LED with green color (brightness controlled)
      int r = 0;
      int g = brightness * 255 / 100;  // Scale 0-100 to 0-255
      int b = 0;
      
      setNoteLED(midiNote, r, g, b);
      
      // Send feedback
      Serial.print("LED ON: ");
      Serial.print(noteName);
      Serial.print(" (MIDI ");
      Serial.print(midiNote);
      Serial.print(", LED index ");
      Serial.print(midiNote - 21);
      Serial.println(")");
    }
  }
  else if (cmd.startsWith("LED:")) {
    // Format: LED:note,r,g,b
    cmd.remove(0, 4); // Remove "LED:"
    
    int firstComma = cmd.indexOf(',');
    int secondComma = cmd.indexOf(',', firstComma + 1);
    int thirdComma = cmd.indexOf(',', secondComma + 1);
    
    if (firstComma > 0 && secondComma > 0 && thirdComma > 0) {
      int midiNote = cmd.substring(0, firstComma).toInt();
      int r = cmd.substring(firstComma + 1, secondComma).toInt();
      int g = cmd.substring(secondComma + 1, thirdComma).toInt();
      int b = cmd.substring(thirdComma + 1).toInt();
      
      setNoteLED(midiNote, r, g, b);
      
      // Send feedback
      String noteName = midiToNoteName(midiNote);
      Serial.print("LED: ");
      Serial.print(noteName);
      Serial.print(" RGB(");
      Serial.print(r);
      Serial.print(",");
      Serial.print(g);
      Serial.print(",");
      Serial.print(b);
      Serial.println(")");
    }
  }
  else if (cmd.startsWith("BATCH:")) {
    // Format: BATCH:note1,r,g,b;note2,r,g,b;note3,r,g,b
    // Update multiple LEDs in one command for maximum speed
    cmd.remove(0, 6); // Remove "BATCH:"
    
    int startIdx = 0;
    while (startIdx < cmd.length()) {
      int semicolon = cmd.indexOf(';', startIdx);
      if (semicolon == -1) semicolon = cmd.length();
      
      String ledCmd = cmd.substring(startIdx, semicolon);
      
      int c1 = ledCmd.indexOf(',');
      int c2 = ledCmd.indexOf(',', c1 + 1);
      int c3 = ledCmd.indexOf(',', c2 + 1);
      
      if (c1 > 0 && c2 > 0 && c3 > 0) {
        int note = ledCmd.substring(0, c1).toInt();
        int r = ledCmd.substring(c1 + 1, c2).toInt();
        int g = ledCmd.substring(c2 + 1, c3).toInt();
        int b = ledCmd.substring(c3 + 1).toInt();
        
        int ledIndex = note - 21;
        if (ledIndex >= 0 && ledIndex < NUM_LEDS) {
          leds[ledIndex] = CRGB(r, g, b);
        }
      }
      
      startIdx = semicolon + 1;
    }
    FastLED.show(); // Update all LEDs at once
  }
  else if (cmd.startsWith("OFF:")) {
    // Format: OFF:note
    int midiNote = cmd.substring(4).toInt();
    String noteName = midiToNoteName(midiNote);
    
    setNoteLED(midiNote, 0, 0, 0);
    
    // Send feedback
    Serial.print("LED OFF: ");
    Serial.print(noteName);
    Serial.print(" (MIDI ");
    Serial.print(midiNote);
    Serial.println(")");
  }
  else if (cmd == "CLEAR") {
    clearAllLEDs();
  }
  else if (cmd.startsWith("BRIGHTNESS:")) {
    // Format: BRIGHTNESS:value
    int brightness = cmd.substring(11).toInt();
    FastLED.setBrightness(constrain(brightness, 0, 255));
    FastLED.show();
  }
  else if (cmd == "TEST") {
    testAnimation();
  }
  else if (cmd == "PING") {
    // Quick response test for latency measurement
    Serial.println("PONG");
  }
}

String midiToNoteName(int midiNote) {
  // MIDI note to note name conversion
  String noteNames[] = {"C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"};
  
  int noteIndex = midiNote % 12;
  int octave = (midiNote / 12) - 1;
  
  return noteNames[noteIndex] + String(octave);
}

void setNoteLED(int midiNote, int r, int g, int b) {
  // Convert MIDI note (21-108) to LED index (0-87)
  int ledIndex = midiNote - 21;
  
  if (ledIndex >= 0 && ledIndex < NUM_LEDS) {
    leds[ledIndex] = CRGB(r, g, b);
    FastLED.show(); // Immediate update for instant response via USB
  }
}

void clearAllLEDs() {
  fill_solid(leds, NUM_LEDS, CRGB::Black);
  FastLED.show();
}

void startupAnimation() {
  // Rainbow sweep on startup
  for (int i = 0; i < NUM_LEDS; i++) {
    leds[i] = CHSV(i * 255 / NUM_LEDS, 255, 255);
    FastLED.show();
    delay(5);
  }
  delay(200);
  
  // Fade out
  for (int brightness = 255; brightness >= 0; brightness -= 5) {
    FastLED.setBrightness(brightness);
    FastLED.show();
    delay(10);
  }
  
  // Reset brightness
  FastLED.setBrightness(BRIGHTNESS);
  clearAllLEDs();
}

void testAnimation() {
  // Test animation - light up keys in sequence
  Serial.println("Running test animation...");
  
  // Red sweep
  for (int i = 0; i < NUM_LEDS; i++) {
    leds[i] = CRGB::Red;
    FastLED.show();
    delay(20);
    leds[i] = CRGB::Black;
  }
  
  // Green sweep
  for (int i = 0; i < NUM_LEDS; i++) {
    leds[i] = CRGB::Green;
    FastLED.show();
    delay(20);
    leds[i] = CRGB::Black;
  }
  
  // Blue sweep
  for (int i = 0; i < NUM_LEDS; i++) {
    leds[i] = CRGB::Blue;
    FastLED.show();
    delay(20);
    leds[i] = CRGB::Black;
  }
  
  clearAllLEDs();
  Serial.println("Test complete");
}
