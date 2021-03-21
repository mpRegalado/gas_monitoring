#! /usr/bin/python3.7
from raspi_lora import LoRa, ModemConfig
import colorama
from colorama import Fore, Style
import RPi.GPIO as GPIO
import requests
import json
import datetime
from enum import Enum

#Wrapper with only one argument in order to use in the map function.
def int16(str):
    return int(str,16)

# Converts a 32 bit unsigned integer into a signed integer
def unsigned2signed(value):
    if (value & (1 << 31)):
        value = value - (1 << 32)
    return value

def chunks(a,l):
    count = len(a)//l
    out = []
    for i in range(count):
        out.append(a[i*l:i*l+l])
    return out

# This is our callback function that runs when a message is received
def on_recv(payload):
    [session_id, gas_high, gas_avg, latitude, longitude, date, time] =map(int.from_bytes,chunks(payload.message,4))

    if (date != 0):
        latitude = unsigned2signed(latitude)/1000000.0
        longitude = unsigned2signed(longitude)/1000000.0
        date_time = datetime.datetime(2000+date%100, (date//100)%100, (date//10000), time//1000000, (time//10000)%100, (time//100)%100 )
        print(row_format.format(session_id, gas_high, gas_avg, latitude, longitude, date_time.strftime("%x"), date_time.strftime("%X")))
        out_data = {
            'session_id': session_id,
            'gas_high' : gas_high,
            'gas_avg': gas_avg,
            'latitude': latitude,
            'longitude': longitude,
            'date_time': date_time.strftime("%Y-%m-%d %X")
        }
    else:
        latitude = longitude = date = time = date_time = "No Fix"
        print(row_format.format(session_id, count, gas_received, latitude, longitude, date, time))
        out_data = {
            'session_id': session_id,
            'count': count,
            'gas_reading': gas_received,
            'latitude': latitude,
            'longitude': longitude,
            'date_time': date_time
        }

    out_json = json.dumps(out_data)
    logfile.write(out_json)
    logfile.write('\n\r')
    for url in post_urls:
        response = requests.post(url, headers={'Content-type':'application/json'}, data=out_json)
        print("Posted to ",url," and got ",response)


try:
    post_urls=['http://localhost:8000/sessions/post/']
    filename = datetime.datetime.now().strftime("%Y-%m-%d") + ".log"
    logfile = open(filename,'a+')

    class Modem(Enum):
        CustomConfig = (0x82, 0x94, 0x04)

    lora = MyLora(0, 25, 2,freq=868.1, receive_all=True, modem_config=Modem.CustomConfig)
    lora.on_recv = on_recv
    lora.set_mode_rx()

    print("LoRa receiving: ")
    expected_data = ["ID","Count", "Gas Reading","Latitude","Longitude","Date","Time"]
    row_format ="{:>15}"*(len(expected_data))
    print(row_format.format(*expected_data))

    while True:
        pass

except KeyboardInterrupt:
    print("Closing Lora")
finally:
    lora.close()
    logfile.close()
    GPIO.cleanup()
