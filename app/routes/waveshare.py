# -*- coding: utf-8 -*-

import os
from flask import render_template, request
from app import app, utils


"""Render some pages to show on the Waveshare 3.2" display"""

@app.route('/weather_min')
def weather_min():
    """Render weather page for Waveshare LCD"""
    app.logger.debug('Loading LCD weather page...')
    weather, wind = dict(), None
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

    return render_template('min_weather.html',
                           page="LCD weather",
                           **weather,
                           w=wind,
                           )

@app.route('/<pi>_min')
def raspi_min(pi):
    """Render sensor page for Waveshare LCD"""
    app.logger.debug(f'Loading LCD sensor page for {pi}')
    # TODO add soil info bar later
    
    if app.config["PI_LIST"][pi]["air sensor"]:
        app.logger.debug("Loading air sensor information...")
        # DHT22 sensor data from raspis
        time, temp, hum = \
            utils.current_air_data(pi, app.config["PI_LIST"][pi])
        values = {'time': time,
                   'temp': temp,
                   'hum': hum,
                   }
    
    return render_template('min_pi_details.html',
                           page=f"LCD {pi}",
                           pi=pi,
                           values=values,
                           )


@app.route('/<pi>_preview_min')
def preview_min(pi):
    """Render preview page for Waveshare LCD"""
    app.logger.debug(f'Loading LCD preview page for {pi}')

    return render_template('min_pi_preview.html',
                           page=f"LCD {pi} preview",
                           pi=pi)


@app.route('/power_min', methods=['GET', 'POST'])
def powersockets_min():
    """Render power socket control subpage for Waveshare LCD"""
    app.logger.debug('Loading LCD power socket control page...')
    # get socket state of temperature dependent sockets from data file and add
    # to the bar table dictionary
    if app.config["SOCKET_INTERVALS"]:
        for name, socket in app.config["SOCKET_INTERVALS"].items():
            if "min" and "max" and "sensor" in socket:
                _, state = utils.read_csv(os.path.join(app.config["PI_DATA"],
                                                       "sockets",
                                                       name,
                                                       f"runtime_protocol_{utils.today()}.txt"),
                                          2,
                                          )
                socket['state'] = state
                # show state in bar
                t = {"text-align": "center", "text": state}
                socket["bar"][int(socket["bar"]["len"] / 2)].update(t)
    if request.method == 'POST':
        name, state = request.form['submit'].split()
        utils.switch_power_socket(name, app.config["DEF_SWITCH"][name], state)
    return render_template('min_powercontrol.html',
                           page="LCD power",
                           form=request.form,
                           switches=app.config["DEF_SWITCH"],
                           intvls=app.config["SOCKET_INTERVALS"],
                           time=utils.now_hour(),
                           )
