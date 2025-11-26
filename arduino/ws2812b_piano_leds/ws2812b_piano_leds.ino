/*
 * WS2812B LED Strip Controller for Piano Keys - BINARY PROTOCOL
 * Compatible with HowToPiano Python application
 * 
 * Hardware:
 * - Arduino (Uno/Nano/Mega)
 * - WS2812B LED Strip (DC 5V)
 * - Data pin: Digital Pin 6 (configurable)
 * 
 * Binary Communication Protocol (NO RESPONSES):
 * Format: [note_number][on/off][R][G][B] ... (5 bytes per LED, multiple LEDs per packet)
 * 
 * Packet structure:
 * - Byte 0: Note number (0-87, or 255 for special commands)
 * - Byte 1: State (0=OFF, 1-255=ON with brightness)
 * - Byte 2: Red (0-255)
 * - Byte 3: Green (0-255)
 * - Byte 4: Blue (0-255)
 * 
 * Special commands (note_number = 255):
 * - [255][0][0][0][0] = CLEAR all LEDs
 * - [255][1][brightness][0][0] = Set global brightness
 * - [255][2][0][0][0] = Test animation
 * 
 * Multiple LEDs can be sent in one packet: [LED1_5bytes][LED2_5bytes][LED3_5bytes]...
 */

#include <FastLED.h>

// LED Strip Configuration
#define LED_PIN     6        // Data pin connected to WS2812B
#define NUM_LEDS    88       // 88 piano keys (21-108 MIDI)
#define LED_TYPE    WS2812B
#define COLOR_ORDER GRB
#define BRIGHTNESS  128      // Default brightness (0-255)

CRGB leds[NUM_LEDS];

// Binary protocol buffer
#define PACKET_SIZE 5        // 5 bytes per LED command
byte packetBuffer[PACKET_SIZE];
int bufferIndex = 0;

void setup() {
  // Initialize serial communication at 500000 baud for MAXIMUM speed
  Serial.begin(500000);
  while (!Serial && millis() < 1000); // Wait for serial, max 1 second
  
  // Initialize FastLED with optimizations
  FastLED.addLeds<LED_TYPE, LED_PIN, COLOR_ORDER>(leds, NUM_LEDS);
  FastLED.setBrightness(BRIGHTNESS);
  FastLED.setMaxRefreshRate(120); // Maximum refresh rate for smooth updates
  FastLED.setDither(0);  // Disable dithering for speed
  
  // Clear all LEDs
  fill_solid(leds, NUM_LEDS, CRGB::Black);
  FastLED.show();
  
  // Quick startup flash (no delay animation for speed)
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
  
  // Send ready signal (only once, no more responses)
  Serial.write(0xFF); // 255 as ready signal
  Serial.flush();
}

void loop() {
  // Process binary packets - INSTANT UPDATE
  bool needsUpdate = false;
  
  // Process all available packets as fast as possible
  while (Serial.available() >= PACKET_SIZE) {
    // Read 5-byte packet
    Serial.readBytes(packetBuffer, PACKET_SIZE);
    
    byte noteNum = packetBuffer[0];
    byte state = packetBuffer[1];
    byte r = packetBuffer[2];
    byte g = packetBuffer[3];
    byte b = packetBuffer[4];
    
    // Process packet immediately
    if (noteNum == 255) {
      // Special command - executes immediately with show()
      handleSpecialCommand(state, r, g, b);
    } else if (noteNum < NUM_LEDS) {
      // LED command
      if (state == 0) {
        // OFF
        leds[noteNum] = CRGB::Black;
      } else {
        // ON with color
        leds[noteNum] = CRGB(r, g, b);
      }
      needsUpdate = true;
    }
  }
  
  // Update immediately if any LED changed
  if (needsUpdate) {
    FastLED.show();
  }
}

void handleSpecialCommand(byte cmd, byte param1, byte param2, byte param3) {
  switch(cmd) {
    case 0:
      // CLEAR all LEDs
      fill_solid(leds, NUM_LEDS, CRGB::Black);
      FastLED.show();
      break;
      
    case 1:
      // Set global brightness
      FastLED.setBrightness(param1);
      FastLED.show();
      break;
      
    case 2:
      // Test animation
      quickTestAnimation();
      break;
  }
}

void quickTestAnimation() {
  // Quick test - sweep red/green/blue without delays
  for (int color = 0; color < 3; color++) {
    for (int i = 0; i < NUM_LEDS; i += 10) {
      leds[i] = (color == 0) ? CRGB::Red : (color == 1) ? CRGB::Green : CRGB::Blue;
    }
    FastLED.show();
    delay(200);
  }
  fill_solid(leds, NUM_LEDS, CRGB::Black);
  FastLED.show();
}
