# -*- coding: utf-8 -*-

### CAVE configuration file ###
### edit this file to match your needs ###

### setup options:
###     * Raspberry Pi, following components available
###         - temp/humidity sensor (DHT22)
###         - digital soil moisture sensor (YL-69)
###         - 433 MHz radio controlled power sockets
###     * openweather.org local weather data
###     * Kettlebattle generator

### de-/activate modules by setting to True or False
### you can run check_config.py script for a basic validation test

########### EMAIL SETTINGS ###############

### defaults to False
# SEND_MAIL = True

MAIL_SERVER = 'smtp.yourmail.tld'
# MAIL_PORT = 465
MAIL_PORT = 25

MAIL_USE_TLS = False
MAIL_USE_SSL = True

### mail address the mail is sent from
MAIL_SENDER_ADDRESS = 'myapp@mydomain.tld'
### this often but not neccessarily corresponds to the email address
MAIL_USERNAME = 'myapp@mydomain.tlda'
MAIL_PASSWORD = 'password'

### list of e-mail addresses that shall receive reports and log
MAIL_RECIPIENTS = ['post@mydomain.tld']

########### RASPBERRY PI SETTINGS ################

### defaults to False
# SENSORS = True

### data structure is
### PI_DATA/
### PI_DATA/RASPI1/sensor_air/
### PI_DATA/RASPI1/sensor_soil/
### PI_DATA/RASPI2
### ...

### path to sensor data files, relative path from Flask app dir
### defaults to 'app/data'
# PI_DATA = 'app/data'

### LIST OF RASPBERRY PIS

### x,y axis range of air sensor plots that are generated daily
### defaults to 14..26 for temperature and 20..80 for humidity
### set to 'auto' to calculate axis to fit values

### one air sensor seems sufficient but multiple soil sensors are a
### realistic option so these can be defined in 'pots'
### data is stored in PI_DATA/Raspi/sensor_soil/pothum_plantname.csv

### see below for sensor settings running on the same machine as CAVE

PI_LIST = {
    # 'Example Pi': {# minimal setup: enable/disable sensor usage
                     # 'air sensor': False,
                     # 'soil sensor': False,

                     # [optional] if air sensor is enabled
                     # set axis of generated plots to 'auto' or range,
                     # otherwise default values are used
                     # 'plot axis': 'auto',
                     # 'plot axis': {'temp': '16-30', 'hum': '25-80'},

                     # [optional] if soil sensor is enabled
                     # name of plant(s) as configured on the machine
                     # 'pots': ['Plant 1', 'Plant 2'],

                     # [optional] login data to establish SSH connection
                     # if device is network device
                     # 'address': '192.168.178.30',
                     # 'username': 'login user',
                     # 'password': 'login user password',
                     # path in username's home on network device
                     # 'installdir': 'cave',
                     # },
}

### LOCAL SENSOR DETAILS

### soil moisture sensor (YL-69)
### GPIO pin binding provided as board numbers
### visit https://pinout.xyz/ for help
SOIL_SENSORS = {"Plant 1": {"data pin": 40, "vcc pin": 38}}

### interval to obtain soil sensor data, format must be cron-like
### examples: "6,18" to run at 6:00 AM/PM, "[0-24]" for hourly run
SOIL_INTVL = "6,18"

### temperature/humidity sensor
### specify sensor model, "DHT22" (default), "DHT11" or "AM2302" available
AIR_SENSOR = "DHT22"

### GPIO pin binding, BCM numbering (default 4)
### visit https://pinout.xyz/ for help
AIR_DATA_PIN = 4

### set to True if you want visual feedback via PiGlow
### (requires additional package)
### defaults to False
# PIGLOW = False

############ OPENWEATHERMAP SETTINGS ##############

### defaults to False
# WEATHER = True

### specify ID _or_ name of your location
### ID is preferred because of its precision
### ID is used when given both
### calling the API by city name can return multiple results
### find out your openweathermap ID on https://openweathermap.org/find
LOCATION_ID = '2950159'

### if you only want to give a location name, give a string of
### "city name,country code", use ISO 3166 country codes
### example: "Berlin,DE"
LOCATION = 'Berlin,DE'

### if not set, English wind speed terms will be displayed
### create your own translation by editing following variables:
### WIND_DESCR_LANG: replace 'LANG' with your language and complete
### dictionary, add item to WIND_LANG dict
LANGUAGE = 'de'

### use your own appid if available or get your own when running this app
### on a larger scale as this appid's free account is limited to 60 calls
### per minute
APPID = 'b6edb7c6f6dd2cb14e2493b4e577bbf8'

######## WIND SPEED DESCRIPTIONS AND CONVERSIONS ##########

WIND_DESCR = {
    "de": {
        "calm": "Stille",
        "light air": "Leiser Zug",
        "light breeze": "Leichte Brise",
        "gentle breeze": "Schwache Brise",
        "moderate breeze": "Mäßige Brise",
        "fresh breeze": "Frische Brise",
        "strong breeze": "Starker Wind",
        "near gale": "Steifer Wind",
        "(fresh) gale": "Stürmischer Wind",
        "strong gale": "Sturm",
        "whole storm": "Schwerer Sturm",
        "severe storm": "Orkanartiger Sturm",
        "hurricane": "Orkan",
        }
    #"lang": {
        # "calm": "",
        # "light air": "",
        # "light breeze" : "",
        # "gentle breeze": "",
        # "moderate breeze": "",
        # "fresh breeze": "",
        # "strong breeze": "",
        # "near gale": "",
        # "(fresh) gale": "",
        # "strong gale": "",
        # "whole storm": "",
        # "severe storm": "",
        # "hurricane": "",
        # }
}

########### REMOTE POWER SOCKET SETTINGS ################

### defaults to False
# REMOTE_POWER = True

### remote power sockets will be controlled by raspberry-remote
### see https://github.com/xkonni/raspberry-remote for details

### relative path to reaspberry-remote install dir
RR_PATH = '../Git/raspberry-remote'

### switch definitions are dictionaries containing systemCode and unitCode)
### information
DEF_SWITCH = {
    # 'switch name': {'systemCode': '12345', 'unitCode': '1'},
    'Lamp': {'systemCode': '12345', 'unitCode': '1'},
}
### power socket scheduler
### turn power sockets on/off with given time or temperature range
SOCKET_INTERVALS = {
    'switch name': {'start': 5, 'stop': 17},
    'another switch name': {'min': 20, 'max': 25, 'sensor': 'ExamplePi'},
}

############# KETTLEBATTLE STATION ##############

### defaults to False
# KETTLEBATTLE = True

### set absolute repetitions for preset buttons
REPS_PRESET = "200,300"

### kettlebell exercises (name: min at preset 1, min at preset 2)
KB_EX = {"Squats (w/o)": "50,50",
         "Squats (w/)": "0,0",
         "Swings (one arm)": "0,0",
         "Swings (two arms)": "50,100",
         "Snatches": "0,40",
         "Clean & Jerks": "30,0",
         "Rows": "0,0",
         "Figure-8 curls": "0,0",
         "Halos": "0,20",
         "Deadlifts": "0,0",
         "Kettlebell circles": "0,30",
}

### max number of exercises to generate workout, minimum presets are always counted
MAX_EX = 4
