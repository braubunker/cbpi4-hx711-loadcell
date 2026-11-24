# -*- coding: utf-8 -*-
import logging
import asyncio
from cbpi.api import *
import time
from cbpi.api.timer import Timer
from .convert import (
    STABLE_SPREAD,
    calibration_matches,
    follow_weight,
    format_scale,
    grams_from_raw,
    raw_is_usable,
    scale_from_kilograms,
    to_display,
)
from .serial_scale import SerialScale
from cbpi.api.dataclasses import NotificationType
from cbpi.api.config import ConfigType

logger = logging.getLogger(__name__)

hx = None
hx_active = False


class HX711_Config(CBPiExtension):
    def __init__(self, cbpi):
        self.cbpi = cbpi
        self._task = asyncio.create_task(self.init_sensor())

    async def init_sensor(self):
        plugin = await self.cbpi.plugin.load_plugin_list("cbpi4-hx711-loadcell")
        self.version = plugin[0].get("Version", "0.0.0")
        self.name = plugin[0].get("Name", "cbpi4-hx711-loadcell")
        await self.HX711_settings()
        port = self.cbpi.config.get("HX711_port", "auto")
        global hx
        global hx_active
        try:
            hx = SerialScale(port)
            hx.start()
            hx_active = True
            logging.info("HX711 Arduino serial started on {}".format(port))
        except Exception as error:
            hx_active = False
            logging.error("HX711 serial initialization failed: {}".format(error))

    async def HX711_settings(self):
        if self.cbpi.config.get("HX711_port", None) is None:
            try:
                await self.cbpi.config.add(
                    "HX711_port",
                    "auto",
                    type=ConfigType.STRING,
                    description="Arduino USB port. auto uses /dev/ttyUSB0 or /dev/ttyACM0",
                    source=self.name,
                )
            except Exception as error:
                logger.warning("Unable to add HX711_port: {}".format(error))


@parameters([Property.Number(label="offset",configurable = True, default_value = 0, description="Raw zero from calibration. Negative values are valid and are kept."),
    Property.Number(label="scale",configurable = True, default_value = 0, description="Raw counts per gram. Small values such as 0.0035 are valid. Do not round them and do not divide them for kilograms."),
    Property.Select(label="Unit", options=["kg","g"], description="Display unit. Calibration weight is entered in kilograms."),
    Property.Select(label="TareOnStart", options=["Yes","No"], description="No keeps the calibrated zero. Yes replaces it at every start, so the scale must be empty. Calibration sets this to No."),
    Property.Select(label="Samples", options=[10,15,20,30], description="Readings averaged for one result. 15 takes about two seconds."),
    Property.Select(label="Deadband", options=[0,100,200,500], description="Hide changes smaller than this many grams. A step of 3 kg or more is shown at once."),
    Property.Select(label="Interval", options=[1,2,5,10,30,60], description="Pause between readings, in seconds. Use 1 for a quicker display.")])

class CustomSensor(CBPiSensor):


    def __init__(self, cbpi, id, props):
        super(CustomSensor, self).__init__(cbpi, id, props)
        self.value = 0
        #self.dout = int(self.props.get("dout",27))
        #self.pd_sck = int(self.props.get("pd_sck",23))
        #self.gain = int(self.props.get("gain",128))
        self.Interval = int(self.props.get("Interval", 1))
        self.samples = max(1, int(self.props.get("Samples", 15)))
        self.deadband = max(0, float(self.props.get("Deadband", 200) or 0))
        self.snap = 3000.0
        self.tare_on_start = str(self.props.get("TareOnStart", "No")) == "Yes"
        self.unit = str(self.props.get("Unit", "kg") or "kg")
        self.offset = float(self.props.get("offset", 0) or 0)
        self.scale = float(self.props.get("scale", 0) or 0)
        self.calibration_active = False
        self.measurement_is_running = False
        self._shown_grams = None


        logging.info("INIT HX711:")
        #logging.info("dout: {}".format(self.dout))
        #logging.info("pd_sck: {}".format(self.pd_sck))
        #logging.info("gain: {}".format(self.gain))
        logging.info("offset: {}".format(self.offset))
        logging.info("scale: {}".format(self.scale))
        logging.info("samples: {}".format(self.samples))
        logging.info("unit: {}".format(self.unit))

        logging.info("Setup HX711")
        global hx
        global hx_active

    def _read_stats(self):
        if hx is None:
            raise RuntimeError("Arduino ist nicht verbunden")
        return hx.read_latest_stats(self.samples)

    def _stable_raw(self, samples=20):
        if hx is None:
            raise RuntimeError("Arduino ist nicht verbunden")
        return hx.read_stable(samples)

    def _grams(self, raw):
        if not self.scale:
            return 0.0
        return grams_from_raw(raw, self.offset, self.scale)

    def _tell(self, title, message, kind=NotificationType.INFO):
        self.cbpi.notification.notify(title, message, kind, [], 180000)

    def _reset_filter(self):
        self._shown_grams = None

    def _publish_grams(self, grams):
        self._shown_grams = follow_weight(self._shown_grams, grams, self.deadband, self.snap)
        self.value = to_display(self._shown_grams, self.unit)
        return self.value

    def get_unit(self):
        return self.unit

    def _tare(self):
        raw, _spread = self._stable_raw(max(self.samples, 15))
        self.offset = raw
        self._reset_filter()
        logging.info("Tare HX711 Loadcell, offset {}".format(self.offset))
        return self.offset

    @action(key="Tare Sensor", parameters=[])
    async def Reset(self, **kwargs):
        self._tare()
        self.cbpi.notify(
            "HX711 Tare",
            "Nullpunkt ist jetzt das aktuelle Gewicht und gilt bis zur naechsten Kalibrierung.",
            NotificationType.INFO,
        )

    def tarereset(self):
        self._tare()

    async def _measure(self):
        self.calibration_active = True
        try:
            return await asyncio.to_thread(self._stable_raw, 20)
        finally:
            self.calibration_active = False

    @action(key="1 Leer messen", parameters=[Property.Number(label="weight",configurable=True, default_value = 0, description="Bekanntes Gewicht in Kilogramm. Fuer 85 kg also 85. Waage jetzt leer lassen.")])
    async def CalibrateEmpty(self, weight=0, **kwargs):
        self.cal_kg = float(weight)
        if not 1 <= self.cal_kg <= 400:
            self._tell("Kalibrierung", "Gewicht in Kilogramm eintragen. Fuer 85 kg also 85, nicht 85000.", NotificationType.ERROR)
            return
        try:
            raw, spread = await self._measure()
        except Exception as error:
            self._tell("Kalibrierung", "Leermessung fehlgeschlagen: {}. Waage leer und ruhig lassen.".format(error), NotificationType.ERROR)
            return
        if not raw_is_usable(raw):
            self._tell("Kalibrierung", "Leermessung ungueltig. Waage leer lassen und noch einmal versuchen.", NotificationType.ERROR)
            return
        self.zeroValue = raw
        self.zeroSpread = spread
        self._tell("Kalibrierung", "Leerwert {} gespeichert. Jetzt {} kg aufstellen, still stehen und im Menue 2 Gewicht messen waehlen.".format(round(raw, 1), self.cal_kg))

    @action(key="2 Gewicht messen", parameters=[])
    async def CalibrateLoad(self, **kwargs):
        if not getattr(self, "cal_kg", 0) or not getattr(self, "zeroValue", None):
            self._tell("Kalibrierung", "Zuerst 1 Leer messen ausfuehren.", NotificationType.ERROR)
            return
        try:
            loaded, loaded_spread = await self._measure()
        except Exception as error:
            self._tell("Kalibrierung", "Messung verworfen: {}. Nichts gespeichert. Still stehen und noch einmal versuchen.".format(error), NotificationType.ERROR)
            return
        delta = float(loaded) - float(self.zeroValue)
        if abs(delta) < 10:
            self._tell(
                "Kalibrierung",
                "Die Waage hat sich nur um {} Zaehler bewegt. Nichts gespeichert. Das Gewicht steht nicht drauf, oder die vier Zellen arbeiten gegeneinander.".format(round(delta, 1)),
                NotificationType.ERROR,
            )
            return
        scale = scale_from_kilograms(self.zeroValue, loaded, self.cal_kg)
        if scale == 0.0:
            self._tell("Kalibrierung", "Scale ist 0. Nichts gespeichert.", NotificationType.ERROR)
            return
        try:
            check_raw, _check_spread = await self._measure()
        except Exception as error:
            self._tell("Kalibrierung", "Kontrollmessung verworfen: {}. Nichts gespeichert.".format(error), NotificationType.ERROR)
            return
        check_grams = grams_from_raw(check_raw, self.zeroValue, scale)
        check_kg = to_display(check_grams, "kg")
        if not calibration_matches(self.cal_kg, check_kg):
            self._tell(
                "Kalibrierung",
                "Verworfen. Kontrolle {} kg statt {} kg. Rohwerte leer {}, belastet {}, Kontrolle {}. Nichts gespeichert. Der Leerwert muss ungefaehr der Zahl aus cat sein, zum Beispiel -185450.".format(
                    check_kg,
                    round(self.cal_kg, 1),
                    round(self.zeroValue, 1),
                    round(loaded, 1),
                    round(check_raw, 1),
                ),
                NotificationType.ERROR,
            )
            logging.error(
                "HX711 calibration rejected empty {} ({}) loaded {} ({}) check {} scale {}".format(
                    self.zeroValue, self.zeroSpread, loaded, loaded_spread, check_raw, scale
                )
            )
            return
        self.offset = self.zeroValue
        self.scale = scale
        self._reset_filter()
        self._publish_grams(check_grams)
        self.push_update(self.value)
        stored = await self._store_calibration()
        scale_text = format_scale(scale)
        if stored:
            saved = "Offset {} und Scale {} sind gespeichert. TareOnStart steht auf No.".format(round(self.offset, 1), scale_text)
        else:
            saved = "Speichern fehlgeschlagen. Offset {} und Scale {} von Hand eintragen und TareOnStart auf No stellen.".format(round(self.offset, 1), scale_text)
        hint = ""
        if abs(delta) < 2000:
            hint = " Die Aenderung ist {} Zaehler. Die Anzeige kann schwanken, weil die Zellen kaum arbeiten.".format(round(delta, 1))
        self._tell(
            "Kalibrierung fertig",
            "Kontrolle {} kg. {} Sensor nicht speichern und CraftBeerPi nicht neu starten, solange das Gewicht noch drauf steht.{}".format(check_kg, saved, hint),
            NotificationType.SUCCESS,
        )

    async def _store_calibration(self):
        """Write the calibrated zero into the sensor without restarting it.

        Saving the sensor form stops and starts the sensor. With TareOnStart
        that start replaces the empty offset with the weight still standing
        on the scale, so 85 kg then reads as about 0 kg.
        """
        self.props["offset"] = round(float(self.offset), 1)
        self.props["scale"] = format_scale(self.scale)
        self.props["TareOnStart"] = "No"
        self.tare_on_start = False
        try:
            await self.cbpi.sensor.save()
            logging.info("HX711 calibration stored offset {} scale {}".format(self.props["offset"], self.props["scale"]))
            return True
        except Exception as error:
            logging.error("HX711 could not store calibration: {}".format(error))
            return False

    async def run(self):
        ready= False
        retries = 50
        while ready is False and retries:
            try:
                if hx is None:
                    raise RuntimeError("Arduino ist nicht verbunden")
                await asyncio.to_thread(hx.read_latest, 1, 5)
                ready=True
            except Exception as e:
                retries -=1
                logging.error("HX711 serial not ready: {}".format(e))
                await asyncio.sleep(1)

        if self.tare_on_start:
            try:
                tare_raw, _spread = await asyncio.to_thread(self._stable_raw, max(self.samples, 15))
                if raw_is_usable(tare_raw):
                    self.offset = tare_raw
                    self._reset_filter()
                    logging.info("HX711 startup tare, offset {}".format(self.offset))
                else:
                    logging.error("HX711 startup tare ignored invalid raw {}".format(tare_raw))
            except Exception as e:
                logging.error("HX711 startup tare failed: {}".format(e))

        while self.running is True:
            try:
                if self.calibration_active == False:
                    self.measurement_is_running = True
                    try:
                        raw, spread = await asyncio.to_thread(self._read_stats)
                        if spread > STABLE_SPREAD:
                            if self.value:
                                self.push_update(self.value)
                        else:
                            self._publish_grams(self._grams(raw))
                            self.log_data(self.value)
                            self.push_update(self.value)
                    finally:
                        self.measurement_is_running = False
                    await asyncio.sleep(self.Interval)
                else:
                    await asyncio.sleep(self.Interval)
            except Exception as e:
                self.measurement_is_running = False
                logging.error("HX711 read failed: {}".format(e))
                await asyncio.sleep(self.Interval)

    def get_state(self):
        return dict(value=self.value, unit=self.unit)

@parameters([Property.Number(label="Weight", description="Number of L to Tranfer", configurable=True),
             Property.Number(label="Density", description="Expected Wort Density - 1.XXX <-> 1.2", configurable=True),
             Property.Select(label="useDensity",options=["Yes","No"], description="Use Density Offset within this Step"),
             Property.Actor(label="Actor",description="Actor to switch media flow on and off"),

             Property.Sensor(label="Sensor"),
             Property.Select(label="Reset", options=["Yes","No"],description="Tare Weight before starting")])


class WeightStep(CBPiStep):

    async def on_timer_done(self,timer):
        self.summary = ""
        self.cbpi.notify(self.name, 'Step finished. Transferred {} {}.'.format(round(self.current_volume,2),'L'), NotificationType.SUCCESS)

        if self.actor is not None:
            await self.actor_off(self.actor)
        await self.next()

    async def on_timer_update(self,timer, seconds):
        await self.push_update()

    async def on_start(self):
        self.actor = self.props.get("Actor", None)
        self.target_volume = float(self.props.get("Weight",0))
        self.flowsensor = self.props.get("Sensor",None)
        logging.info(self.flowsensor)
        self.sensor = self.get_sensor(self.flowsensor)
        logging.info(self.sensor)

        self.preresetsensor = self.props.get("Reset","Yes")
        self.dens_flag = True if self.props.get("useDensity", "No") == "Yes" else False
        self.density = float(self.props.get("Density",0))
        if self.preresetsensor == "Yes":
            self.sensor.instance.tarereset()

        if self.timer is None:
            self.timer = Timer(1,on_update=self.on_timer_update, on_done=self.on_timer_done)

    async def on_stop(self):
        if self.timer is not None:
            await self.timer.stop()
        self.summary = ""
        if self.actor is not None:
            await self.actor_off(self.actor)
        await self.push_update()

    async def reset(self):
        self.timer = Timer(1,on_update=self.on_timer_update, on_done=self.on_timer_done)
        if self.actor is not None:
            await self.actor_off(self.actor)


    async def run(self):
        if self.actor is not None:
            await self.actor_on(self.actor)
        self.summary=""
        await self.push_update()
        while self.running == True:

            self.current_volume = self.get_sensor_value(self.flowsensor).get("value") * self.density if self.dens_flag == True else self.get_sensor_value(self.flowsensor).get("value")
            self.summary="Volume: {}, Target: {}".format(self.current_volume , self.target_volume)
         #   self.cbpi.notify("WaterTransfer","Current: {}L, Target {}L".format(self.current_volume,self.target_volume), NotificationType.INFO)
            await self.push_update()

            if self.current_volume >= self.target_volume and self.timer.is_running is not True:
                self.timer.start()
                self.timer.is_running = True
            await asyncio.sleep(0.2)

        return StepResult.DONE



def setup(cbpi):
    cbpi.plugin.register("HX711_Config", HX711_Config)
    cbpi.plugin.register("HX711 Load Cell", CustomSensor)
    cbpi.plugin.register("WeightStep", WeightStep)
    pass
