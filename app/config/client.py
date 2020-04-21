# -*- coding: utf-8 -*-

from app import app

# Set default config values for running in client mode

app.config.update(LOCAL_AIR=app.config["AIR_SENSOR"],
                  PI_LIST={app.config["NAME"]: { \
                               'air sensor': app.config["AIR_SENSOR"],
                               'plot axis': app.config["PLOT_AXIS"],
                               }
                          }
                  )

if app.config["PIGLOW"]:
    app.config.update(PIGLOW=app.config["NAME"])

if app.config["SOIL_SENSORS"]:
    app.config.update(LOCAL_SOIL=True)
    app.config["PI_LIST"][app.config["NAME"]["pots"] = app.config["SOIL_SENSORS"]