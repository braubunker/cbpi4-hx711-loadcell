
# -*- coding: utf-8 -*-
import os
from aiohttp import web
import logging
import RPi.GPIO as GPIO
from unittest.mock import MagicMock, patch
import asyncio
import random
from cbpi.api import *
import time
from cbpi.api.timer import Timer
from HX711 import *
from .convert import (
    follow_weight,
    grams_from_raw,
    raw_is_usable,
    scale_from_kilograms,
    to_display,
    trimmed_mean,
)
from cbpi.api.dataclasses import NotificationAction, NotificationType
from cbpi.api.config import ConfigType

logger = logging.getLogger(__name__)

class HX711_Config(CBPiExtension):
    def __init__(self,cbpi):
        self.cbpi = cbpi
        self._task = asyncio.create_task(self.init_sensor())


    async def init_sensor(self):
        plugin = await self.cbpi.plugin.load_plugin_list("cbpi4-hx711-loadcell")
        self.version=plugin[0].get("Version","0.0.0")
        self.name=plugin[0].get("Name","cbpi4-hx711-loadcell")

        self.hx711_update = self.cbpi.config.get(self.name+"_update", None)

        await self.HX711_settings()
        
        self.dout = self.cbpi.config.get("HX711_dout", 5)
        self.sck = self.cbpi.config.get("HX711_sck", 6)
        global hx
        global hx_active
        try:
            hx=SimpleHX711(self.dout, self.sck)
            hx_active=True
        except Exception as e:
            hx_active = False
            logging.error(f"Error HX711 initialization: {e}")

    async def HX711_settings(self):
        global HX711_dout
        global HX711_sck
        HX711_dout = self.cbpi.config.get("HX711_dout", None)
        if HX711_dout is None:
            logger.info("INIT HX711_dout")
            try:
                await self.cbpi.config.add("HX711_dout", 5, type=ConfigType.SELECT, description="HX711 dout GPIO",
                                                                                                    source=self.name,
                                                                                        options=[{"label": "0", "value": 0},
                                                                                                {"label": "1", "value": 1},
                                                                                                {"label": "2", "value": 2},
                                                                                                {"label": "3", "value": 3},
                                                                                                {"label": "4", "value": 4},
                                                                                                {"label": "5", "value": 5},
                                                                                                {"label": "6", "value": 6},
                                                                                                {"label": "7", "value": 7},
                                                                                                {"label": "8", "value": 8},
                                                                                                {"label": "9", "value": 9},
                                                                                                {"label": "10", "value": 10},
                                                                                                {"label": "11", "value": 11},
                                                                                                {"label": "12", "value": 12},
                                                                                                {"label": "13", "value": 13},
                                                                                                {"label": "14", "value": 14},
                                                                                                {"label": "15", "value": 15},
                                                                                                {"label": "16", "value": 16},
                                                                                                {"label": "17", "value": 17},
                                                                                                {"label": "18", "value": 18},
                                                                                                {"label": "19", "value": 19},
                                                                                                {"label": "20", "value": 20},
                                                                                                {"label": "21", "value": 21},
                                                                                                {"label": "22", "value": 22},
                                                                                                {"label": "23", "value": 23},
                                                                                                {"label": "24", "value": 24},
                                                                                                {"label": "25", "value": 25},
                                                                                                {"label": "26", "value": 26},
                                                                                                {"label": "27", "value": 27}])
                                                                                                            
                HX711_dout = self.cbpi.config.get("HX711_dout", None)
            except:
                logger.warning('Unable to update database')
        else:
            if self.hx711_update == None or self.hx711_update != self.version:
                try:
                    await self.cbpi.config.add("HX711_dout", HX711_dout, type=ConfigType.SELECT, description="HX711 dout GPIO",
                                                                                                    source=self.name,
                                                                                        options=[{"label": "0", "value": 0},
                                                                                                {"label": "1", "value": 1},
                                                                                                {"label": "2", "value": 2},
                                                                                                {"label": "3", "value": 3},
                                                                                                {"label": "4", "value": 4},
                                                                                                {"label": "5", "value": 5},
                                                                                                {"label": "6", "value": 6},
                                                                                                {"label": "7", "value": 7},
                                                                                                {"label": "8", "value": 8},
                                                                                                {"label": "9", "value": 9},
                                                                                                {"label": "10", "value": 10},
                                                                                                {"label": "11", "value": 11},
                                                                                                {"label": "12", "value": 12},
                                                                                                {"label": "13", "value": 13},
                                                                                                {"label": "14", "value": 14},
                                                                                                {"label": "15", "value": 15},
                                                                                                {"label": "16", "value": 16},
                                                                                                {"label": "17", "value": 17},
                                                                                                {"label": "18", "value": 18},
                                                                                                {"label": "19", "value": 19},
                                                                                                {"label": "20", "value": 20},
                                                                                                {"label": "21", "value": 21},
                                                                                                {"label": "22", "value": 22},
                                                                                                {"label": "23", "value": 23},
                                                                                                {"label": "24", "value": 24},
                                                                                                {"label": "25", "value": 25},
                                                                                                {"label": "26", "value": 26},
                                                                                                {"label": "27", "value": 27}])
                except:
                    logger.warning('Unable to update database')

        HX711_sck = self.cbpi.config.get("HX711_sck", None)
        if HX711_dout is None:
            logger.info("INIT HX711_sck")
            try:
                await self.cbpi.config.add("HX711_sck", 6, type=ConfigType.SELECT, description="HX711 sck GPIO",
                                                                                                    source=self.name,
                                                                                        options=[{"label": "0", "value": 0},
                                                                                                {"label": "1", "value": 1},
                                                                                                {"label": "2", "value": 2},
                                                                                                {"label": "3", "value": 3},
                                                                                                {"label": "4", "value": 4},
                                                                                                {"label": "5", "value": 5},
                                                                                                {"label": "6", "value": 6},
                                                                                                {"label": "7", "value": 7},
                                                                                                {"label": "8", "value": 8},
                                                                                                {"label": "9", "value": 9},
                                                                                                {"label": "10", "value": 10},
                                                                                                {"label": "11", "value": 11},
                                                                                                {"label": "12", "value": 12},
                                                                                                {"label": "13", "value": 13},
                                                                                                {"label": "14", "value": 14},
                                                                                                {"label": "15", "value": 15},
                                                                                                {"label": "16", "value": 16},
                                                                                                {"label": "17", "value": 17},
                                                                                                {"label": "18", "value": 18},
                                                                                                {"label": "19", "value": 19},
                                                                                                {"label": "20", "value": 20},
                                                                                                {"label": "21", "value": 21},
                                                                                                {"label": "22", "value": 22},
                                                                                                {"label": "23", "value": 23},
                                                                                                {"label": "24", "value": 24},
                                                                                                {"label": "25", "value": 25},
                                                                                                {"label": "26", "value": 26},
                                                                                                {"label": "27", "value": 27}])
                                                                                                            
                HX711_sck = self.cbpi.config.get("HX711_sck", None)
            except:
                logger.warning('Unable to update database')
        else:
            if self.hx711_update == None or self.hx711_update != self.version:
                try:
                    await self.cbpi.config.add("HX711_sck", HX711_sck, type=ConfigType.SELECT, description="HX711 sck GPIO",
                                                                                                    source=self.name,
                                                                                        options=[{"label": "0", "value": 0},
                                                                                                {"label": "1", "value": 1},
                                                                                                {"label": "2", "value": 2},
                                                                                                {"label": "3", "value": 3},
                                                                                                {"label": "4", "value": 4},
                                                                                                {"label": "5", "value": 5},
                                                                                                {"label": "6", "value": 6},
                                                                                                {"label": "7", "value": 7},
                                                                                                {"label": "8", "value": 8},
                                                                                                {"label": "9", "value": 9},
                                                                                                {"label": "10", "value": 10},
                                                                                                {"label": "11", "value": 11},
                                                                                                {"label": "12", "value": 12},
                                                                                                {"label": "13", "value": 13},
                                                                                                {"label": "14", "value": 14},
                                                                                                {"label": "15", "value": 15},
                                                                                                {"label": "16", "value": 16},
                                                                                                {"label": "17", "value": 17},
                                                                                                {"label": "18", "value": 18},
                                                                                                {"label": "19", "value": 19},
                                                                                                {"label": "20", "value": 20},
                                                                                                {"label": "21", "value": 21},
                                                                                                {"label": "22", "value": 22},
                                                                                                {"label": "23", "value": 23},
                                                                                                {"label": "24", "value": 24},
                                                                                                {"label": "25", "value": 25},
                                                                                                {"label": "26", "value": 26},
                                                                                                {"label": "27", "value": 27}])
                except:
                    logger.warning('Unable to update database')

        if self.hx711_update == None or self.hx711_update != self.version:
            try:
                 await self.cbpi.config.add(self.name+"_update", self.version,type=ConfigType.STRING, description='HX711 Version update', source='hidden')
            except Exception as e:
                logger.warning('Unable to update database')
                logger.warning(e)


@parameters([Property.Number(label="offset",configurable = True, default_value = 0, description="Raw zero from calibration. Negative values are valid and are kept."),
    Property.Number(label="scale",configurable = True, default_value = 0, description="Raw counts per gram from calibration. Leave this value as calibrated. Do not divide it when showing kilograms."),
    Property.Select(label="Unit", options=["kg","g"], description="Display unit. Calibration weight stays in grams. 85 kg is entered as 85000."),
    Property.Select(label="TareOnStart", options=["Yes","No"], description="Set the empty scale to 0 at every start. Leave the scale empty while CraftBeerPi starts."),
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
        self.tare_on_start = str(self.props.get("TareOnStart", "Yes")) != "No"
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

    def _read_raw(self):
        try:
            values = [int(value) for value in hx.getValues(self.samples)]
            if values:
                return trimmed_mean(values)
        except Exception as e:
            logging.warning("HX711 sample burst failed, using median read: {}".format(e))
        return float(hx.read(Options(self.samples, ReadType.Median)))

    def _averaged_raw(self, bursts=3, samples=20):
        previous = self.samples
        self.samples = samples
        try:
            self._read_raw()
            total = 0.0
            for _ in range(bursts):
                total += self._read_raw()
            return total / float(bursts)
        finally:
            self.samples = previous

    def _grams(self, raw):
        return grams_from_raw(raw, self.offset, self.scale)

    def _reset_filter(self):
        self._shown_grams = None

    def _publish_grams(self, grams):
        self._shown_grams = follow_weight(self._shown_grams, grams, self.deadband, self.snap)
        self.value = to_display(self._shown_grams, self.unit)
        return self.value

    def get_unit(self):
        return self.unit

    def _tare(self):
        self.offset = self._read_raw()
        self._reset_filter()
        logging.info("Tare HX711 Loadcell, offset {}".format(self.offset))
        return self.offset

    @action(key="Tare Sensor", parameters=[])
    async def Reset(self, **kwargs):
        self._tare()
        self.cbpi.notify(
            "HX711 Tare",
            "Nullpunkt gesetzt. Beim nächsten Start wird die leere Waage wieder auf 0 gestellt.",
            NotificationType.INFO,
        )

    def tarereset(self):
        self._tare()

    @action(key="Calibrate Sensor", parameters=[Property.Number(label="weight",configurable=True, default_value = 0, description="Gewicht in Kilogramm. Für 85 kg also 85 eintragen. Waage dabei leer lassen.")])
    async def Calibrate(self ,weight = 0, **kwargs):
        self.next = False
        self.weight = float(weight)
        if not 1 <= self.weight <= 400:
            self.cbpi.notify(
                "Kalibrierung",
                "Gewicht in Kilogramm eintragen. Für 85 kg also 85, nicht 85000.",
                NotificationType.ERROR,
            )
            return
        logging.info(weight)
        self.calibration_active = True
        while self.measurement_is_running is not False:
            logging.info("Waiting for Sensor")
            await asyncio.sleep(self.Interval)
            pass
        logging.info("Reset")
        self.zeroValue = round(self._averaged_raw(), 1)
        if not raw_is_usable(self.zeroValue):
            self.calibration_active = False
            self.cbpi.notify("Kalibrierung", "Leermessung ungültig. Waage leer lassen und neu starten.", NotificationType.ERROR)
            return
        logging.info("Calibrate HX711 Loadcell")
        self.cbpi.notify("Loadcell Calibration", "Gewicht aufstellen, still stehen und dann Next Step drücken.", NotificationType.INFO, action=[NotificationAction("Next Step", self.NextStep)])
        while not self.next == True:
            await asyncio.sleep(1)
            pass
        self.next = False

        self.raw = self._averaged_raw()
        self.refUnit = round(scale_from_kilograms(self.zeroValue, self.raw, self.weight), 4)
        if abs(self.refUnit) < 0.5:
            self.cbpi.notify(
                "Loadcell Calibration Error",
                "Scale ist {} und damit zu klein. Die vier Zellen arbeiten noch gegeneinander.".format(self.refUnit),
                NotificationType.ERROR,
            )
        else:
            self.offset = self.zeroValue
            self.scale = self.refUnit
            self._reset_filter()
            check_raw = self._averaged_raw()
            check_grams = grams_from_raw(check_raw, self.offset, self.scale)
            check_kg = to_display(check_grams, "kg")
            self._publish_grams(check_grams)
            if abs(check_kg - self.weight) > max(2.0, self.weight * 0.15):
                self.cbpi.notify(
                    "Kalibrierung passt nicht",
                    "Kontrolle zeigt {} kg, erwartet {} kg. Waage leer starten, dann still draufstehen und wiederholen.".format(check_kg, self.weight),
                    NotificationType.ERROR,
                )
            else:
                self.cbpi.notify(
                    "Kalibrierung fertig",
                    "Kontrolle {} kg. Offset {} und Scale {} eintragen, Kommastellen behalten. Danach speichern und mit leerer Waage neu starten.".format(check_kg, self.zeroValue, self.refUnit),
                    action=[NotificationAction("Next Step", self.NextStep)],
                )
                while not self.next == True:
                    await asyncio.sleep(1)
                    pass
                self.next = False
        self.calibration_active = False

    async def NextStep(self):
        self.next = True
        pass

    async def run(self):
        ready= False
        retries = 50
        while ready is False and retries:
            try:
                hx.setUnit(Mass.Unit.G)
                # Conversion is done in Python so a fractional or negative scale is preserved.
                hx.setReferenceUnit(1)
                hx.setOffset(0)
                ready=True
            except Exception as e:
                retries -=1
                logging.error("HX711 setup failed: {}".format(e))
                await asyncio.sleep(1)

        if self.tare_on_start:
            try:
                tare_raw = self._averaged_raw(bursts=2, samples=max(self.samples, 15))
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
                    self._publish_grams(self._grams(self._read_raw()))
                    self.log_data(self.value)
                    self.push_update(self.value)
                    self.measurement_is_running = False
                    await asyncio.sleep(self.Interval)
                else:
                    await asyncio.sleep(self.Interval)
            except Exception as e:
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
