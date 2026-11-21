# HX711 für CraftBeerPi 4

Fork von [PiBrewing/cbpi4-hx711-loadcell](https://github.com/PiBrewing/cbpi4-hx711-loadcell). Der Sensor heißt weiter **HX711 Load Cell**, vorhandene Sensoren bleiben erhalten.

Gegenüber der Originalfassung:

- Offset und Scale bleiben Kommazahlen, auch mit Minus. Ein kleiner Scale wird nicht mehr durch 1 ersetzt.
- Beim Start wird nicht neu tariert. Der gespeicherte Offset bleibt der Nullpunkt.
- Die Anzeige steht in Kilogramm. Die Kalibrierung bleibt in Gramm, Offset und Scale werden dafür nicht umgerechnet.
- Jede Anzeige ist der Median aus 30 Rohmessungen und danach noch einmal aus 5 Ergebnissen. Änderungen unter 50 g bleiben stehen.

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
3. **Unit** auf **kg** stellen. Offset und Scale nicht durch 1000 teilen.
4. **Samples** auf **30**, **Smooth** auf **5** und **Deadband** auf **50** stellen. Springt die Anzeige noch, Smooth auf 9 und Deadband auf 100 oder 200 setzen.
5. **Offset** und **Scale** aus der Kalibrierung eintragen. Ein Minuszeichen stehen lassen.
6. Speichern und CraftBeerPi neu starten:

```bash
sudo systemctl restart craftbeerpi
```

Die drei Punkte für Tarieren und Kalibrieren stehen am Sensor-Widget auf dem Dashboard. Dafür in den Widget-Eigenschaften **Action** auf **Yes** setzen.

## Kalibrieren

1. Kessel leeren.
2. Am Widget **Calibrate Sensor** wählen.
3. Das bekannte Gewicht in **Gramm** eintragen, zum Beispiel `5000` für 5 kg. Noch nichts auf die Waage stellen.
4. Auf **Next Step** warten, das Gewicht aufstellen, dann **Next Step** bestätigen.
5. In der Meldung stehen Offset und Scale. Beide unverändert in den Sensor übernehmen. Für die Kilogrammanzeige nichts umrechnen. Speichern und CraftBeerPi neu starten.

`12.500` bedeutet 12,5 kg. Ältere Punkte in der Chart sind noch in Gramm und fallen deshalb aus der Skala, bis sie aus dem Zeitraum rutschen.

Ist der Scale kleiner als 0,5, wird er nicht zur Übernahme angeboten. Dann heben sich die vier Wägezellen noch gegenseitig auf, und die Verdrahtung muss zuerst stimmen.

## Tarieren

**Tare Sensor** setzt den aktuellen Rohwert als Nullpunkt. Die Meldung nennt den Offset. Diesen Wert in den Sensor eintragen, sonst gilt nach einem Neustart wieder der alte Offset.
