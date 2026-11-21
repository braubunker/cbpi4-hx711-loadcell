# HX711 für CraftBeerPi 4

Fork von [PiBrewing/cbpi4-hx711-loadcell](https://github.com/PiBrewing/cbpi4-hx711-loadcell). Der Sensor heißt weiter **HX711 Load Cell**, vorhandene Sensoren bleiben erhalten.

Gegenüber der Originalfassung:

- Offset und Scale bleiben Kommazahlen, auch mit Minus. Ein kleiner Scale wird nicht mehr durch 1 ersetzt.
- Beim Start wird nicht neu tariert. Der gespeicherte Offset bleibt der Nullpunkt.
- Die Anzeige und die Kalibrierung sind in Kilogramm. Für eine Person von 85 kg wird `85` eingetragen, nicht `85000`.
- Beim Start wird die leere Waage auf 0 gestellt. Ein großer Schritt, etwa Auf- oder Absteigen, erscheint mit der nächsten Messung und bleibt nicht auf einem Zwischenwert stehen.

## Installation über das Netz

Auf dem Raspberry Pi, einmalig falls `git` fehlt:

```bash
sudo apt update
sudo apt install -y git
```

Plugin holen und das bisherige ersetzen:

```bash
pipx runpip cbpi4 install --force-reinstall "git+https://github.com/braubunker/cbpi4-hx711-loadcell.git"
sudo systemctl restart craftbeerpi
```

Dieselbe Zeile später noch einmal ausführen, wenn eine neuere Fassung in diesem Repo liegt.

## Sensor einstellen

1. CraftBeerPi öffnen.
2. **Hardware** → **Sensor** → den HX711-Sensor öffnen.
3. **Unit** auf **kg**, **TareOnStart** auf **Yes**, **Samples** auf **15**, **Deadband** auf **200** und **Interval** auf **1** stellen.
4. **Offset** und **Scale** aus der Kalibrierung eintragen. Ein Minuszeichen stehen lassen. Scale nicht durch 1000 teilen.
5. Speichern. Die Waage leer lassen und CraftBeerPi neu starten:

```bash
sudo systemctl restart craftbeerpi
```

Die drei Punkte für Tarieren und Kalibrieren stehen am Sensor-Widget auf dem Dashboard. Dafür in den Widget-Eigenschaften **Action** auf **Yes** setzen.

## Kalibrieren

1. Kessel leeren.
2. Am Widget **Calibrate Sensor** wählen.
3. Das bekannte Gewicht in **Kilogramm** eintragen. Für 85 kg also `85`. Noch nichts auf die Waage stellen.
4. Auf die Meldung warten, das Gewicht aufstellen, still stehen und erst dann **Next Step** bestätigen.
5. Die Meldung nennt eine Kontrolle in kg. Sie muss nahe am bekannten Gewicht liegen. Offset und Scale daraus eintragen, die Kommastellen von Scale behalten, speichern und mit leerer Waage neu starten.

`12.500` bedeutet 12,5 kg. Nach dem Neustart muss die Waage leer sein, sonst wird das aktuelle Gewicht als neuer Nullpunkt genommen. Ältere Punkte in der Chart sind noch in Gramm und fallen deshalb aus der Skala, bis sie aus dem Zeitraum rutschen.

Ist der Scale kleiner als 0,5, wird er nicht zur Übernahme angeboten. Dann heben sich die vier Wägezellen noch gegenseitig auf, und die Verdrahtung muss zuerst stimmen.

## Tarieren

**Tare Sensor** setzt den aktuellen Rohwert als Nullpunkt. Die Meldung nennt den Offset. Diesen Wert in den Sensor eintragen, sonst gilt nach einem Neustart wieder der alte Offset.
