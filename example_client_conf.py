# -*- coding: utf-8 -*-

### CAVE client configuration file ###

### only for setting ip one Raspberry Pi with sensors running on it
### available components:
###     - temp/humidity sensor (DHT22)
###     - digital soil moisture sensor (YL-69)

### edit this file to match your needs ###

### path to sensor data files, relpath from Flask app dir
# APP_DATA = 'app/data'

### device name, data will be stored in APP_DATA/NAME/...
NAME = 'ExamplePi'

### [optional] Raspberry Pi camera module
# CAMERA = True

### AIR SENSOR ###

### x,y axis range of air sensor plots that are generated daily
### defaults to 14..26 for temperature and 20..80 for humidity
### set to 'auto' to calculate axis to fit values

### one air sensor seems sufficient but multiple soil sensors are a
### realistic option so these can be defined in 'pots'
### data is stored in APP_DATA/NAME/sensor_soil/pothum_plantname.csv

AIR_SENSOR = True
PLOT_AXIS = 'auto',
SOIL_SENSOR = True
POTS = ['Sanseveria']

### temperature/humidity sensor
### specify sensor model, "DHT22" (default), "DHT11" or "AM2302" available
AIR_SENSOR = "DHT22"

### GPIO pin binding, BCM numbering (default 4)
# ##visit https://pinout.xyz/ for help
AIR_DATA_PIN = 4

### SOIL SENSOR(S) ###

### soil moisture sensor (YL-69)
### GPIO pin binding provided as board numbers
### visit https://pinout.xyz/ for help
SOIL_SENSORS = {"Sanseveria": {"data pin": 40, "vcc pin": 38}}

### interval to obtain soil sensor data, format must be cron-like
### examples: "6,18" to run at 6:00 AM/PM, "[0-24]" for hourly run
SOIL_INTVL = "6,18"
