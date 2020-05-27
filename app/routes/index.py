# -*- coding: utf-8 -*-

from flask import render_template
from app import app, utils


@app.route('/')
@app.route('/index')
def index():
    """Render index/start page"""
    app.logger.debug("Loading home page...")
    picurrent, weather, wind, soilcurrent = dict(), dict(), None, None
    components = {'indoor': app.config["SENSORS"],
                  'weather': app.config["WEATHER"],
                  'soil': app.config["SENSORS"],
                  }
    if components['weather']:
        app.logger.debug("Loading weather information...")
        # get openweathermap data
        try:
            weather, wind = utils.get_weather(app.config["LOCATION_ID"],
                                              'id',
                                              app.config["APPID"],
                                              app.config["LANGUAGE"],
                                              )
        except AttributeError:
            weather, wind = utils.get_weather(app.config["LOCATION"],
                                              'q',
                                              app.config["APPID"],
                                              app.config["LANGUAGE"],
                                              )
    if components['indoor']:
        app.logger.debug("Loading air sensor information...")
        # DHT22 sensor data from raspis
        picurrent = dict()
        for pi in app.config["PI_LIST"]:
            if app.config["PI_LIST"][pi]["air sensor"]:
                time, temp, hum = \
                    utils.current_air_data(pi, app.config["PI_LIST"][pi])
                dataset = {'time': time,
                           'temp': temp,
                           'hum': hum,
                           }
                picurrent[pi] = dataset
        if len(picurrent) == 0:
            components['indoor'] = False
    if components['soil']:
        app.logger.debug("Loading soil sensor information...")
        # get YL-69 soil moisture sensor data
        soilcurrent = dict()
        for name, pi in app.config["PI_LIST"].items():
            if pi["soil sensor"]:
                for pot in pi['pots']:
                    soil = utils.get_soil(name, pi, pot)
                    soilcurrent[pot] = soil
                    soilcurrent[pot]["pi"] = name
        if len(soilcurrent) == 0:
            components['soil'] = False
    return render_template('weatherpi.html',
                           comp=components,
                           **weather,
                           w=wind,
                           picurrent=picurrent,
                           soilcurrent=soilcurrent)
