# HX711 für CraftBeerPi 4

Fork von [PiBrewing/cbpi4-hx711-loadcell](https://github.com/PiBrewing/cbpi4-hx711-loadcell). Der Sensor heißt weiter **HX711 Load Cell**, vorhandene Sensoren bleiben erhalten.

Gegenüber der Originalfassung:

- Offset und Scale bleiben Kommazahlen, auch mit Minus. Ein kleiner Scale wird nicht mehr durch 1 ersetzt.
- Beim Start wird nicht neu tariert. Der gespeicherte Offset bleibt der Nullpunkt.
- Jede Anzeige ist der Median aus 15 Messungen. Unter **Samples** sind 5, 10, 15, 20 und 30 wählbar.

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
3. **Samples** auf **15** stellen. Wenn die Anzeige danach noch springt, 20 oder 30 nehmen.
4. **Offset** und **Scale** aus der Kalibrierung eintragen. Ein Minuszeichen stehen lassen.
5. Speichern und CraftBeerPi neu starten:

```bash
sudo systemctl restart craftbeerpi
```

Die drei Punkte für Tarieren und Kalibrieren stehen am Sensor-Widget auf dem Dashboard. Dafür in den Widget-Eigenschaften **Action** auf **Yes** setzen.

## Kalibrieren

1. Kessel leeren.
2. Am Widget **Calibrate Sensor** wählen.
3. Das bekannte Gewicht in **Gramm** eintragen, zum Beispiel `5000` für 5 kg. Noch nichts auf die Waage stellen.
4. Auf **Next Step** warten, das Gewicht aufstellen, dann **Next Step** bestätigen.
5. In der Meldung stehen Offset und Scale. Beide in den Sensor übernehmen, speichern, CraftBeerPi neu starten.

Ist der Scale kleiner als 0,5, wird er nicht zur Übernahme angeboten. Dann heben sich die vier Wägezellen noch gegenseitig auf, und die Verdrahtung muss zuerst stimmen.

## Tarieren

**Tare Sensor** setzt den aktuellen Rohwert als Nullpunkt. Die Meldung nennt den Offset. Diesen Wert in den Sensor eintragen, sonst gilt nach einem Neustart wieder der alte Offset.
