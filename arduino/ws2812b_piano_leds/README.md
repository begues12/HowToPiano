# WS2812B LED Strip Setup for Piano

## Hardware Requirements

- **Arduino Board**: Uno, Nano, Mega, or compatible
- **WS2812B LED Strip**: DC 5V, 88 LEDs (one per piano key)
- **Power Supply**: 5V, at least 2A (depending on LED count and brightness)
- **Resistor**: 470Ω between Arduino data pin and LED strip (recommended)
- **Capacitor**: 1000µF 6.3V across power supply (recommended)

## Wiring Diagram

```
Arduino                    WS2812B Strip
  GND -------------------- GND
  5V  -------------------- 5V (or external power supply)
  D6  ---[470Ω]---------- DIN (Data In)
```

**Important Notes:**
- If using external power supply, connect Arduino GND to power supply GND
- For more than 30 LEDs, use external 5V power supply (not Arduino 5V pin)
- Add 470Ω resistor between Arduino data pin and LED strip data pin
- Add 1000µF capacitor between 5V and GND near LED strip for stability

## Arduino Library Installation

1. Open Arduino IDE
2. Go to **Sketch → Include Library → Manage Libraries**
3. Search for **"FastLED"**
4. Install **FastLED by Daniel Garcia**

## Upload Instructions

1. Connect Arduino to computer via USB
2. Open `ws2812b_piano_leds.ino` in Arduino IDE
3. Select your board: **Tools → Board**
4. Select your port: **Tools → Port**
5. Click **Upload** button (→)

## Configuration

Edit these constants in the sketch if needed:

```cpp
#define LED_PIN     6        // Change if using different pin
#define NUM_LEDS    88       // Number of LEDs (88 for full piano)
#define BRIGHTNESS  128      // Default brightness (0-255)
```

## Serial Commands

The Arduino accepts these commands via Serial (115200 baud):

| Command | Format | Description | Example |
|---------|--------|-------------|---------|
| LED | `LED:note,r,g,b\n` | Light up specific note with RGB color | `LED:60,255,0,0` (Middle C red) |
| OFF | `OFF:note\n` | Turn off specific note | `OFF:60` |
| CLEAR | `CLEAR\n` | Turn off all LEDs | `CLEAR` |
| BRIGHTNESS | `BRIGHTNESS:value\n` | Set brightness (0-255) | `BRIGHTNESS:200` |
| TEST | `TEST\n` | Run test animation | `TEST` |

## LED Mapping

- **MIDI Note 21** (A0) → LED Index 0
- **MIDI Note 60** (C4/Middle C) → LED Index 39
- **MIDI Note 108** (C8) → LED Index 87

Formula: `LED_Index = MIDI_Note - 21`

## Testing

1. Open Arduino IDE Serial Monitor (Tools → Serial Monitor)
2. Set baud rate to **115200**
3. Type `TEST` and press Enter
4. Watch the LED animation

Test individual notes:
```
LED:60,255,0,0    (Middle C - Red)
LED:64,0,255,0    (E - Green)
LED:67,0,0,255    (G - Blue)
CLEAR             (Turn all off)
```

## Power Consumption

Each LED can draw up to 60mA at full white brightness:
- 88 LEDs × 60mA = 5.28A (maximum theoretical)
- Typical usage: 1-2A (mixed colors, not all LEDs on)
- At 128/255 brightness: ~50% power draw

**Power Supply Recommendations:**
- **30 LEDs or less**: Arduino 5V pin (500mA max)
- **31-60 LEDs**: 2A 5V power supply
- **61-88 LEDs**: 3-5A 5V power supply

## Troubleshooting

### LEDs don't light up
- Check wiring (GND, 5V, Data pin)
- Verify LED strip is WS2812B (not WS2811 or other)
- Check if strip needs 5V (some strips are 12V)
- Try adding 470Ω resistor on data line

### LEDs flicker or show wrong colors
- Add 1000µF capacitor between 5V and GND
- Use shorter wires (under 1 meter)
- Check power supply capacity
- Lower brightness with `BRIGHTNESS:100`

### First LED works, others don't
- Check strip direction (DIN → DOUT)
- Verify strip is not damaged
- Check power supply connections

### Serial commands don't work
- Verify baud rate is 115200
- Check USB connection
- Try pressing Arduino reset button
- Verify correct COM port selected

## Integration with HowToPiano

The Arduino will automatically be detected by the Python application if:
1. Arduino is connected via USB
2. Sketch is uploaded and running
3. Serial port is available (no Serial Monitor open in Arduino IDE)

The application will send LED commands automatically when notes are played.

## Alternative Configurations

### Fewer LEDs (e.g., 61 keys)

Change in Arduino sketch:
```cpp
#define NUM_LEDS    61       // For 61-key keyboard
```

Adjust LED mapping to match your keyboard range.

### Different Pin

Change data pin:
```cpp
#define LED_PIN     7        // Use pin 7 instead of 6
```

### Multiple Strips

For very long runs, split into multiple strips with separate data pins:
```cpp
#define LED_PIN_1   6
#define LED_PIN_2   7
#define NUM_LEDS_1  44
#define NUM_LEDS_2  44
```

## Safety Notes

- Never connect/disconnect LED strip while powered
- Use proper gauge wire for power (18-20 AWG recommended)
- Ensure proper ventilation for power supply
- Don't exceed LED strip voltage rating (5V for WS2812B)
