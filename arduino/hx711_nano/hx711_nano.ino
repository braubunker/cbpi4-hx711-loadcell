#include "HX711.h"

// HX711 clock -> D2, data -> D3, VCC -> 5V, GND -> GND.
// Do not use D0 or D1. Those pins are the USB serial port.
HX711 scale;

const uint8_t PIN_DATA = 3;
const uint8_t PIN_CLOCK = 2;

void setup() {
  Serial.begin(115200);
  scale.begin(PIN_DATA, PIN_CLOCK);
  scale.set_gain(128);
  Serial.println("hx711-nano");
}

void loop() {
  if (scale.wait_ready_timeout(250)) {
    Serial.print('R');
    Serial.println(scale.read());
  }
}
