# -*- coding: utf-8 -*-

from app import app

# Set default config values for running in server mode

local_air, local_soil, camera = False, False, False

if app.config["SENSORS"]:
    for _, pi in app.config["PI_LIST"].items():
        if not "address" in pi:
            if pi["air sensor"]:
                local_air = True
            if pi["soil sensor"]:
                local_soil = True
        if "camera" in pi:
            if pi["camera"]:
                camera = True

app.config.update(LOCAL_AIR=local_air,
                  LOCAL_SOIL=local_soil,
                  CAMERA=camera,
                  )

# disable automatation if remote power sockets are deactivated
if not app.config["REMOTE_POWER"]:
    app.config.update(SOCKET_INTERVALS=False)

# the interval bar on the powersocket page is visualized by a table, column
# properties are set here
if app.config["SOCKET_INTERVALS"]:
    for _, socket in app.config["SOCKET_INTERVALS"].items():
        bar = dict()
        # bar for time scheduled socket
        if "start" and "stop" in socket:
            for h in range(24 + 1):
                bar[h] = {'bg': 'off',
                          'border': '',
                          'descr': '',
                          'align': ''}
                # round borders
                if h == 0:
                    bar[h]['border'] = 'start'
                    bar[h]['descr'] = '0:00'
                elif h == 24:
                    bar[h]['border'] = 'end'
                    bar[h - 1]['descr'] = '24:00'
                    bar[h]['align'] = 'right'
                # mark on and off time
                if h == socket["start"]:
                    bar[h - 1]['descr'] = f'{h}:00'
                if h == socket["stop"]:
                    bar[h - 1]['descr'] = f'{h}:00'
                    bar[h - 1]['align'] = 'right'
                # mark time interval (background colour
                if h >= socket["start"]:
                    bar[h]['bg'] = 'on'
                if h >= socket["stop"]:
                    bar[h]['bg'] = 'off'
        # bar for temperature dependent sockets
        elif "min" and "max" and "sensor" in socket:
            minimum = int(socket["min"])
            maximum = int(socket["max"])
            for h, i in enumerate(range(minimum * 10, maximum * 10 + 1)):
                bar[h] = {'border': '',
                          'descr': '',
                          'align': ''}
                # round borders
                if h == 0:
                    bar[h]['border'] = 'start'
                    bar[h]['descr'] = f"{minimum} °C"
                elif i == maximum * 10:
                    bar[h]['border'] = 'end'
                    bar[h]['descr'] = f"{maximum} °C"
                    bar[h]['align'] = 'right'
            # set state in table center

        bar['len'] = len(bar)
        socket["bar"] = bar

if app.config["KETTLEBATTLE"]:
    # split absolute repetitions for preset buttons into list of integers
    app.config.update(REPS_PRESET=[int(x) for x in app.config["REPS_PRESET"].split(",")])
    # split minimum repetitions for exercises into list of integers
    for ex, exercise in app.config["KB_EX"].copy().items():
        app.config["KB_EX"][ex] = [int(x) for x in exercise.split(",")]
