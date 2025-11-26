/*
 * SIMPLE Arduino Test Sketch
 * Use this to verify basic serial communication
 * Upload this first to test if Arduino is working
 */

void setup() {
  // Start serial at 115200 baud
  Serial.begin(115200);
  
  // Wait for serial port to be ready
  while (!Serial && millis() < 2000);
  
  // Send startup message
  Serial.println("Arduino Starting...");
  delay(500);
  Serial.println("READY");
  
  // Blink built-in LED to show it's alive
  pinMode(LED_BUILTIN, OUTPUT);
  for (int i = 0; i < 3; i++) {
    digitalWrite(LED_BUILTIN, HIGH);
    delay(100);
    digitalWrite(LED_BUILTIN, LOW);
    delay(100);
  }
}

void loop() {
  // Echo back anything received
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    
    if (command.length() > 0) {
      // Special responses for known commands
      if (command == "PING") {
        Serial.println("PONG");
      }
      else if (command == "TEST") {
        Serial.println("Running test...");
        // Blink LED
        for (int i = 0; i < 5; i++) {
          digitalWrite(LED_BUILTIN, HIGH);
          delay(100);
          digitalWrite(LED_BUILTIN, LOW);
          delay(100);
        }
        Serial.println("Test complete");
      }
      else {
        // Echo back the command
        Serial.print("Received: ");
        Serial.println(command);
      }
    }
  }
  
  // Send heartbeat every 5 seconds
  static unsigned long lastHeartbeat = 0;
  if (millis() - lastHeartbeat > 5000) {
    Serial.println("Heartbeat");
    lastHeartbeat = millis();
  }
}
