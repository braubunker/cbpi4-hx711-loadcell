# HX711 über einen Arduino Nano

CraftBeerPi liest die Waage nicht mehr über die GPIO-Pins. Ein Arduino Nano misst den HX711 und schickt die Rohwerte per USB. Der Sensor in CraftBeerPi heißt weiter **HX711 Load Cell**.

Offset und Scale von der direkten GPIO-Schaltung gelten nicht mehr. Nach dem Umstellen neu kalibrieren.

## Verdrahtung

Der HX711 hängt nur am Arduino, nicht mehr am Raspberry Pi.

| HX711 | Arduino Nano |
| --- | --- |
| VCC | 5V |
| GND | GND |
| DT oder DOUT | D3 |
| SCK oder CLK | D2 |

D0 und D1 bleiben frei. Das sind die USB-Leitungen.

Die vier Wägezellen bleiben am HX711. RATE offen lassen oder auf GND, das sind 10 Messungen pro Sekunde.

## Sketch auf den Nano laden

Am Computer die [Arduino IDE](https://www.arduino.cc/en/software) öffnen.

1. Bibliothek **HX711** von Bogdan Necula installieren.
2. Board **Arduino Nano** wählen. Bei den günstigen Nachbauten unter Prozessor **ATmega328P (Old Bootloader)** nehmen, falls das Hochladen scheitert.
3. Diesen Sketch öffnen und hochladen: [hx711_nano.ino](arduino/hx711_nano/hx711_nano.ino)
4. Seriellen Monitor auf **115200** stellen. Es erscheinen Zeilen wie `R-123456`.

```cpp
#include "HX711.h"

// HX711 clock -> D2, data -> D3, VCC -> 5V, GND -> GND.
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
```

Danach das USB-Kabel vom Computer abziehen und in den Raspberry Pi stecken.

## Installation auf dem Pi

```bash
sudo apt update
sudo apt install -y git
sudo usermod -aG dialout pi
pipx runpip cbpi4 install --force-reinstall "git+https://github.com/braubunker/cbpi4-hx711-loadcell.git"
sudo systemctl restart craftbeerpi
```

`dialout` gilt erst nach einem neuen Login. Läuft CraftBeerPi als root, ist die Gruppe egal. Die Waage beim Neustart leer lassen.

Unter **Settings** steht **HX711_port**. `auto` sucht `/dev/ttyUSB0` und `/dev/ttyACM0`. Erscheint der Nano nicht, den Port eintragen, den `ls /dev/ttyUSB* /dev/ttyACM*` zeigt.

## Kalibrieren

1. Sensor öffnen. **Unit** auf **kg**, **TareOnStart** auf **Yes**, **Samples** auf **15**, **Deadband** auf **200**, **Interval** auf **1**.
2. Am Dashboard-Widget **Action** auf **Yes** stellen, damit die drei Punkte erscheinen.
3. Waage leer lassen. **Calibrate Sensor** wählen und das Gewicht in Kilogramm eintragen. Für 85 kg also `85`.
4. Erst auf die Meldung warten, dann auf die Waage stellen, still stehen und **Next Step** drücken.
5. Die Kontrolle muss nahe am bekannten Gewicht liegen. Offset und Scale eintragen, die Kommastellen behalten, speichern und mit leerer Waage neu starten.

`12.500` bedeutet 12,5 kg.
