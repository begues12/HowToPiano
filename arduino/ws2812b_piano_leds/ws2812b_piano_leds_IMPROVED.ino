/*
 * IMPROVED WS2812B LED Strip Controller - FIXED Multiple OFF Commands
 * 
 * Key Improvement: Batched OFF commands
 * - Accumulates OFF commands and processes them together
 * - Single FastLED.show() for multiple OFF commands
 * - Prevents lost commands when multiple notes end simultaneously
 */

#include <FastLED.h>

// LED Strip Configuration
#define LED_PIN     6        // Data pin connected to WS2812B
#define NUM_LEDS    88       // 88 piano keys (21-108 MIDI)
#define LED_TYPE    WS2812B
#define COLOR_ORDER GRB
#define BRIGHTNESS  128      // Default brightness (0-255)

CRGB leds[NUM_LEDS];

// Command batching for OFF commands
#define MAX_PENDING_OFF 20
int pendingOffNotes[MAX_PENDING_OFF];
int pendingOffCount = 0;
unsigned long lastCommandTime = 0;
#define BATCH_TIMEOUT_MS 5  // Process pending OFF after 5ms of no new commands

void setup() {
  Serial.begin(115200);
  while (!Serial && millis() < 1000);
  
  FastLED.addLeds<LED_TYPE, LED_PIN, COLOR_ORDER>(leds, NUM_LEDS);
  FastLED.setBrightness(BRIGHTNESS);
  FastLED.setMaxRefreshRate(120);
  
  fill_solid(leds, NUM_LEDS, CRGB::Black);
  FastLED.show();
  
  // Startup flash
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
  Serial.println("READY");
  Serial.flush();
}

void loop() {
  // Check for pending OFF commands timeout
  if (pendingOffCount > 0 && (millis() - lastCommandTime) >= BATCH_TIMEOUT_MS) {
    processPendingOff();
  }
  
  // Process incoming commands
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    
    if (command.length() > 0) {
      processCommand(command);
      lastCommandTime = millis();
    }
  }
}

void processPendingOff() {
  // Turn off all pending LEDs in one batch
  if (pendingOffCount == 0) return;
  
  for (int i = 0; i < pendingOffCount; i++) {
    int midiNote = pendingOffNotes[i];
    int ledIndex = midiNote - 21;
    
    if (ledIndex >= 0 && ledIndex < NUM_LEDS) {
      leds[ledIndex] = CRGB::Black;
    }
  }
  
  // Single show for all OFF commands
  FastLED.show();
  
  // Clear pending list
  pendingOffCount = 0;
}

void addPendingOff(int midiNote) {
  // Add note to pending OFF list
  if (pendingOffCount < MAX_PENDING_OFF) {
    pendingOffNotes[pendingOffCount++] = midiNote;
  }
  
  // If buffer is full, process immediately
  if (pendingOffCount >= MAX_PENDING_OFF) {
    processPendingOff();
  }
}

void processCommand(String cmd) {
  if (cmd.startsWith("ON:")) {
    // Process any pending OFF first
    processPendingOff();
    
    cmd.remove(0, 3);
    int colon = cmd.indexOf(':');
    if (colon > 0) {
      int midiNote = cmd.substring(0, colon).toInt();
      int brightness = cmd.substring(colon + 1).toInt();
      int ledIndex = midiNote - 21;
      
      if (ledIndex >= 0 && ledIndex < NUM_LEDS) {
        int g = map(brightness, 0, 100, 0, 255);
        leds[ledIndex] = CRGB(0, g, 0);
        FastLED.show();
      }
    }
  }
  else if (cmd.startsWith("LED:")) {
    // Process any pending OFF first
    processPendingOff();
    
    cmd.remove(0, 4);
    int c1 = cmd.indexOf(',');
    int c2 = cmd.indexOf(',', c1 + 1);
    int c3 = cmd.indexOf(',', c2 + 1);
    
    if (c1 > 0 && c2 > 0 && c3 > 0) {
      int midiNote = cmd.substring(0, c1).toInt();
      int r = cmd.substring(c1 + 1, c2).toInt();
      int g = cmd.substring(c2 + 1, c3).toInt();
      int b = cmd.substring(c3 + 1).toInt();
      int ledIndex = midiNote - 21;
      
      if (ledIndex >= 0 && ledIndex < NUM_LEDS) {
        leds[ledIndex] = CRGB(r, g, b);
        FastLED.show();
      }
    }
  }
  else if (cmd.startsWith("BATCH:")) {
    // Process any pending OFF first
    processPendingOff();
    
    cmd.remove(0, 6);
    int startIdx = 0;
    bool needsUpdate = false;
    
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
        int ledIndex = midiNote - 21;
        
        if (ledIndex >= 0 && ledIndex < NUM_LEDS) {
          leds[ledIndex] = CRGB(r, g, b);
          needsUpdate = true;
        }
      }
      
      startIdx = semicolon + 1;
    }
    
    if (needsUpdate) {
      FastLED.show();
    }
  }
  else if (cmd.startsWith("OFF:")) {
    // Add to pending OFF instead of immediate processing
    int midiNote = cmd.substring(4).toInt();
    addPendingOff(midiNote);
    // Note: Will be processed in next loop iteration or after timeout
  }
  else if (cmd == "CLEAR") {
    processPendingOff();  // Process any pending first
    fill_solid(leds, NUM_LEDS, CRGB::Black);
    FastLED.show();
  }
  else if (cmd.startsWith("BRIGHTNESS:")) {
    processPendingOff();
    int brightness = cmd.substring(11).toInt();
    FastLED.setBrightness(constrain(brightness, 0, 255));
    FastLED.show();
  }
  else if (cmd == "TEST") {
    processPendingOff();
    testAnimation();
  }
  else if (cmd == "PING") {
    Serial.println("PONG");
  }
  else if (cmd == "FLUSH") {
    // Force process pending OFF immediately
    processPendingOff();
  }
}

void testAnimation() {
  Serial.println("Running test...");
  
  for (int i = 0; i < NUM_LEDS; i++) {
    leds[i] = CRGB::Red;
    FastLED.show();
    delay(10);
    leds[i] = CRGB::Black;
  }
  
  for (int i = 0; i < NUM_LEDS; i++) {
    leds[i] = CRGB::Green;
    FastLED.show();
    delay(10);
    leds[i] = CRGB::Black;
  }
  
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
