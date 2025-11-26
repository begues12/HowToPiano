/*
 * WS2812B LED Strip Controller for Piano Keys - TEXT PROTOCOL with RGB
 * Compatible with HowToPiano Python application
 * 
 * Hardware:
 * - Arduino (Uno/Nano/Mega)
 * - WS2812B LED Strip (DC 5V)
 * - Data pin: Digital Pin 6 (configurable)
 * 
 * Text Communication Protocol:
 * Commands from Python (newline terminated):
 * 
 * Basic Commands:
 * - "ON:note:brightness\n" - Turn on LED with default green (brightness 0-100)
 *   Example: "ON:60:100\n" -> Note 60 at full brightness (green)
 * 
 * - "LED:note,r,g,b\n" - Turn on LED with RGB color
 *   Example: "LED:60,255,0,0\n" -> Note 60 in red
 * 
 * - "OFF:note\n" - Turn off LED (single note)
 *   Example: "OFF:60\n" -> Turn off note 60
 * 
 * - "BATCH_OFF:note1,note2,note3\n" - Turn off multiple LEDs at once (faster)
 *   Example: "BATCH_OFF:60,64,67\n" -> Turn off C, E, G chord
 * 
 * - "CLEAR\n" - Turn off all LEDs
 * 
 * - "BRIGHTNESS:value\n" - Set global brightness (0-255)
 *   Example: "BRIGHTNESS:128\n" -> 50% brightness
 * 
 * - "TEST\n" - Run test animation
 * 
 * - "PING\n" - Check connection (responds "PONG")
 * 
 * Batch Command (for multiple LEDs at once):
 * - "BATCH:note1,r,g,b;note2,r,g,b;note3,r,g,b\n"
 *   Example: "BATCH:60,255,0,0;62,0,255,0;64,0,0,255\n"
 *   -> Note 60 red, Note 62 green, Note 64 blue (single update)
 */

#include <FastLED.h>

// LED Strip Configuration
#define LED_PIN     6        // Data pin connected to WS2812B
#define NUM_LEDS    88       // 88 piano keys (21-108 MIDI)
#define LED_TYPE    WS2812B
#define COLOR_ORDER GRB
#define BRIGHTNESS  128      // Default brightness (0-255)

CRGB leds[NUM_LEDS];

// Pre-computed MIDI to LED index lookup table (MIDI 21-108 -> LED 0-87)
// Avoids calculation overhead during playback
int8_t midiToLed[128];  // -1 = invalid, 0-87 = valid LED index

void setup() {
  // Pre-compute MIDI to LED index lookup table
  for (int i = 0; i < 128; i++) {
    if (i >= 21 && i <= 108) {
      midiToLed[i] = i - 21;  // Valid piano key
    } else {
      midiToLed[i] = -1;  // Invalid
    }
  }
  
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
  
  // Quick startup flash
  for(int i = 0; i < 3; i++) {
    fill_solid(leds, NUM_LEDS, CRGB::White);
    FastLED.setBrightness(50);
    FastLED.show();
    delay(50);
    fill_solid(leds, NUM_LEDS, CRGB::Black);
    FastLED.show();
    delay(50);
  }
  
  FastLED.setBrightness(BRIGHTNESS);
  
  // Send ready signal
  Serial.println("READY");
  Serial.flush();
}

void loop() {
  // Process text commands - instant update, no delays
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    
    if (command.length() > 0) {
      processCommand(command);
    }
  }
}

void processCommand(String cmd) {
  if (cmd.startsWith("ON:")) {
    // Format: ON:note:brightness (default green)
    cmd.remove(0, 3); // Remove "ON:"
    
    int colon = cmd.indexOf(':');
    if (colon > 0) {
      int midiNote = cmd.substring(0, colon).toInt();
      int brightness = cmd.substring(colon + 1).toInt();
      
      // Lookup LED index (pre-computed)
      int8_t ledIndex = midiToLed[midiNote];
      
      if (ledIndex >= 0) {
        // Green with brightness scaling
        int g = map(brightness, 0, 100, 0, 255);
        leds[ledIndex] = CRGB(0, g, 0);
        FastLED.show();
      }
    }
  }
  else if (cmd.startsWith("LED:")) {
    // Format: LED:note,r,g,b (RGB color)
    cmd.remove(0, 4); // Remove "LED:"
    
    int c1 = cmd.indexOf(',');
    int c2 = cmd.indexOf(',', c1 + 1);
    int c3 = cmd.indexOf(',', c2 + 1);
    
    if (c1 > 0 && c2 > 0 && c3 > 0) {
      int midiNote = cmd.substring(0, c1).toInt();
      int r = cmd.substring(c1 + 1, c2).toInt();
      int g = cmd.substring(c2 + 1, c3).toInt();
      int b = cmd.substring(c3 + 1).toInt();
      
      // Lookup LED index (pre-computed)
      int8_t ledIndex = midiToLed[midiNote];
      
      if (ledIndex >= 0) {
        leds[ledIndex] = CRGB(r, g, b);
        FastLED.show();
      }
    }
  }
  else if (cmd.startsWith("BATCH:")) {
    // Format: BATCH:note1,r,g,b;note2,r,g,b;note3,r,g,b
    // Update multiple LEDs in one command - ULTRA FAST
    cmd.remove(0, 6); // Remove "BATCH:"
    
    int startIdx = 0;
    bool needsUpdate = false;
    
    // Parse all notes first (no show() yet)
    while (startIdx < cmd.length()) {
      int semicolon = cmd.indexOf(';', startIdx);
      if (semicolon == -1) semicolon = cmd.length();
      
      String ledCmd = cmd.substring(startIdx, semicolon);
      
      int c1 = ledCmd.indexOf(',');
      int c2 = ledCmd.indexOf(',', c1 + 1);
      int c3 = ledCmd.indexOf(',', c2 + 1);
      
      if (c1 > 0 && c2 > 0 && c3 > 0) {
        int midiNote = ledCmd.substring(0, c1).toInt();
        int r = ledCmd.substring(c1 + 1, c2).toInt();
        int g = ledCmd.substring(c2 + 1, c3).toInt();
        int b = ledCmd.substring(c3 + 1).toInt();
        
        // Lookup LED index (pre-computed)
        int8_t ledIndex = midiToLed[midiNote];
        
        if (ledIndex >= 0) {
          leds[ledIndex] = CRGB(r, g, b);
          needsUpdate = true;
        }
      }
      
      startIdx = semicolon + 1;
    }
    
    // Single show() for all LEDs - MAXIMUM PERFORMANCE
    if (needsUpdate) {
      FastLED.show();
    }
  }
  else if (cmd.startsWith("OFF:")) {
    // Format: OFF:note - IMMEDIATE
    int midiNote = cmd.substring(4).toInt();
    int8_t ledIndex = midiToLed[midiNote];
    
    if (ledIndex >= 0) {
      leds[ledIndex] = CRGB::Black;
      FastLED.show();
    }
  }
  else if (cmd.startsWith("BATCH_OFF:")) {
    // Format: BATCH_OFF:note1,note2,note3 - Turn off multiple LEDs at once
    cmd.remove(0, 10); // Remove "BATCH_OFF:"
    
    int startIdx = 0;
    bool needsUpdate = false;
    
    while (startIdx < cmd.length()) {
      int comma = cmd.indexOf(',', startIdx);
      if (comma == -1) comma = cmd.length();
      
      int midiNote = cmd.substring(startIdx, comma).toInt();
      int8_t ledIndex = midiToLed[midiNote];
      
      if (ledIndex >= 0) {
        leds[ledIndex] = CRGB::Black;
        needsUpdate = true;
      }
      
      startIdx = comma + 1;
    }
    
    // Single show() for all OFF - MAXIMUM PERFORMANCE
    if (needsUpdate) {
      FastLED.show();
    }
  }
  else if (cmd == "CLEAR") {
    fill_solid(leds, NUM_LEDS, CRGB::Black);
    FastLED.show();
  }
  else if (cmd.startsWith("BRIGHTNESS:")) {
    // Format: BRIGHTNESS:value (0-255)
    int brightness = cmd.substring(11).toInt();
    FastLED.setBrightness(constrain(brightness, 0, 255));
    FastLED.show();
  }
  else if (cmd == "TEST") {
    testAnimation();
  }
  else if (cmd == "PING") {
    Serial.println("PONG");
  }
}

void testAnimation() {
  // Test animation - RGB sweep
  Serial.println("Running test...");
  
  // Red sweep
  for (int i = 0; i < NUM_LEDS; i++) {
    leds[i] = CRGB::Red;
    FastLED.show();
    delay(10);
    leds[i] = CRGB::Black;
  }
  
  // Green sweep
  for (int i = 0; i < NUM_LEDS; i++) {
    leds[i] = CRGB::Green;
    FastLED.show();
    delay(10);
    leds[i] = CRGB::Black;
  }
  
  // Blue sweep
  for (int i = 0; i < NUM_LEDS; i++) {
    leds[i] = CRGB::Blue;
    FastLED.show();
    delay(10);
    leds[i] = CRGB::Black;
  }
  
  fill_solid(leds, NUM_LEDS, CRGB::Black);
  FastLED.show();
  Serial.println("Test complete");
}
