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

Die vier Wägezellen bleiben am HX711. Den RATE-Pin auf GND legen, das sind 10 Messungen pro Sekunde. Offen gelassen springt der Rohwert, und die Kalibrierung trifft das Gewicht nicht.

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

`dialout` gilt erst nach einem neuen Login. Läuft CraftBeerPi als root, ist die Gruppe egal. Der Nano läuft dabei normal weiter. Die Rohwerte in CraftBeerPi müssen dieselben sein wie die Zeilen aus `cat`, zum Beispiel `R-185450`.

Unter **Settings** steht **HX711_port**. `auto` sucht `/dev/ttyUSB0` und `/dev/ttyACM0`. Erscheint der Nano nicht, den Port eintragen, den `ls /dev/ttyUSB* /dev/ttyACM*` zeigt.

## Kalibrieren

1. Sensor öffnen. **Unit** auf **kg**, **TareOnStart** auf **No**, **Samples** auf **15**, **Deadband** auf **200**, **Interval** auf **1**. Einmal speichern, bevor jemand auf der Waage steht.
2. Am Dashboard-Widget **Action** auf **Yes** stellen, damit die drei Punkte erscheinen.
3. Waage leer lassen. Im Menü **1 Leer messen** wählen und für 85 kg `85` eintragen.
4. Nach der Meldung das Gewicht aufstellen, still stehen und **2 Gewicht messen** wählen.
5. Die Meldung muss als Kontrolle etwa dasselbe Gewicht nennen. Erst dann werden Offset und Scale gespeichert. Die Anzeige zeigt dieses Gewicht. Den Sensor nicht noch einmal speichern und CraftBeerPi nicht neu starten, solange das Gewicht noch drauf steht.

Weicht die Kontrolle stark ab, zum Beispiel 29 kg statt 87 kg, ist nichts gespeichert. Still stehen und Schritt 2 wiederholen. Stehen in der Meldung Rohwerte, die um hunderttausende auseinanderliegen, den RATE-Pin auf GND legen.

`12.500` bedeutet 12,5 kg. Ein Scale von `0.0035` ist gültig und darf nicht auf `0` oder `1` gerundet werden.

**TareOnStart** auf **Yes** stellt bei jedem Start den aktuellen Rohwert als Nullpunkt ein. Steht dabei das Kalibriergewicht noch drauf, zeigt die Waage danach etwa 0 kg statt 85 kg.
