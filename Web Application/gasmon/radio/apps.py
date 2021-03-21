from django.apps import AppConfig
from raspi_lora import LoRa, ModemConfig
import RPi.GPIO as GPIO
import requests
import json
import datetime
import pytz
from enum import Enum

#Wrapper with only one argument in order to use in the map function.
def int16(str):
    return int(str,16)

def from_big_bytes(array):
    return int.from_bytes(array,byteorder='little')
# Converts a 32 bit unsigned integer into a signed integer
def unsigned2signed(value):
    if (value & (1 << 31)):
        value = value - (1 << 32)
    return value

#Returns ann array of arrays resulting from cutting a into chunks of length l
def chunks(a,l):
    count = len(a)//l
    out = []
    for i in range(count):
        out.append(a[i*l:i*l+l])
    return out


def on_recv(payload):
    from readings.models import Session
    [session_id, gas_high, gas_avg, latitude, longitude, date, time] =map(from_big_bytes,chunks(payload.message,4))

    if Session.objects.filter(session_id=session_id):
        session = Session.objects.get(session_id=session_id)
    else:
        session = Session(session_id=session_id)
        session.save()

    measurement = session.measurement_set.create(
        gas_high=gas_high,
        gas_avg=gas_avg
    )
    if (date != 0):
        latitude = unsigned2signed(latitude)/1000000.0
        longitude = unsigned2signed(longitude)/1000000.0
        date_time = datetime.datetime(2000+date%100, (date//100)%100, (date//10000), time//1000000, (time//10000)%100, (time//100)%100 ).replace(tzinfo=pytz.UTC)
        measurement.latitude=latitude
        measurement.longitude=longitude
        measurement.date_time=date_time
        measurement.save()

class RadioConfig(AppConfig):
    name = 'radio'
    class Modem(Enum):
        CustomConfig = (0x82, 0x94, 0x04)

    lora = LoRa(0, 25, 2,freq=868.1, receive_all=True, modem_config=Modem.CustomConfig)

    def ready(self):
        self.lora.on_recv = on_recv
        self.lora.set_mode_rx()
