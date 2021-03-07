# -*- coding: utf-8 -*-

import os

from flask import render_template, request
from app import app, utils


@app.route('/powersockets', methods=['GET', 'POST'])
def powersockets():
    """Render power socket control subpage"""
    app.logger.debug('Loading power socket control page...')
    # get socket state of temperature dependent sockets from data file and add
    # to the bar table dictionary
    if app.config["SOCKET_INTERVALS"]:
        for name, socket in app.config["SOCKET_INTERVALS"].items():
            if "min" and "max" and "sensor" in socket:
                _, state = utils.read_csv(os.path.join(app.config["APP_DATA"],
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
    return render_template('powercontrol.html',
                           form=request.form,
                           switches=app.config["DEF_SWITCH"],
                           intvls=app.config["SOCKET_INTERVALS"],
                           time=utils.now_hour(),
                           )
