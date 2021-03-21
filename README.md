# COMMUNICATION BETWEEN A NATURAL GAS DETECTOR AND A WEB APPLICATION

This project was made as a graduation project for the grade in industrial electronics at the university of Córdoba.
It provides wireless communication to an Arduino based natural gas detector mounted on a drone, a device to send that data to a public API,
and a web application that stores and displays that data.

The project is divided in three directories to handle the three steps:
- Arduino-Data Collection: Here is the code to flash onto an Arduino Mega board.
- Raspberry-Data Reception: This is the code responsible of watching the LoRa channel and sending the information to a RESTful API
- Web Application: This directory hosts the code for a full stack web application that stores and presents the data.

## Data collection

### Hardware used
- Arduino Mega board: Any board with at least 2 serial ports and enough memory to run the TinyGPS and RH_RF95 libraries will also work.
- Natural gas sensor Integrated IR by Amphenol SGX Sensortech
- [Dragino Lora/GPS Shield](https://www.dragino.com/products/lora/item/108-lora-gps-shield.html)
- 9V battery

### Dependencies
You must install the following dependencies in your arduino IDE before compiling the code.
- [TinyGPS](https://github.com/mikalhart/TinyGPS)
- [RH_RF95](https://www.airspayce.com/mikem/arduino/RadioHead/)

### Usage

You can set up the behaviour of the code with the variables
```C
#define SENSOR_MODE 0
#define WAIT_FOR_FIX 0
```
`WAIT_FOR_FIX` is used to determine if the sensor should send natural gas readings before having a GPS connection. Set to 1 to wait for a fix.
`SENSOR_MODE` Defines the behaviour of the sensor, allowing you to simulate the input.
- Mode 0 communicates with a sensor connected at `SENSOR_SERIAL`
- Mode 1 also sends back internal information through `SENSOR_SERIAL`, useful for simulating a sensor with another serial device.
- Mode 2 simulates a sensor in the board and generates dummy data, does not use `SENSOR_SERIAL`

You can define to which ports connect the sensor and the GPS module with
```C
#define SENSOR_SERIAL Serial
#define GPS_SERIAL Serial1
```

Define the time between data transmissions with
```C
#define TX_TIME 12000
```
You can also display readings locally with the use of LEDs connected to different pins. Define the pinout and the thresholds with
```
#define GREEN_LED 13
#define GREEN_ALERT 100

#define YELLOW_LED 12
#define YELLOW_ALERT 1000

#define RED_LED 11
#define RED_ALERT 25000
```
Keep in mind the documentation of the Dragino board when you decide which pins to use.

Once you have set the variables in your code, you can flash it onto your Arduino Mega.

## Data reception

### Hardware Used
- Raspberry Pi Zero W
- [Raspberry Pi Zero LoRa shield](https://store.uputronics.com/index.php?route=product/product&product_id=99)

### Dependencies
You should have a flashed card with any OS that supports the use of Python3 and install the flollowing dependencies:
- [RPi.GPIO](https://pypi.org/project/RPi.GPIO/)
- [raspi-lora](https://github.com/mpRegalado/raspi-lora)
- colorama
- requests
- json
- datetime
- enum

### Usage
The receptor will convert the incoming LoRa datagrams to JSON objects with the following structure
```JSON
{
    'session_id': session_id,
    'count': count,
    'gas_reading': gas_received,
    'latitude': latitude,
    'longitude': longitude,
    'date_time': date_time
}
```
These objects will be saved locally in files named after the date and sent, by default, to a localhost server.
Configure the API endpoints by including them in the array at line 66
```python
post_urls=['http://localhost:8000/sessions/post/']
```