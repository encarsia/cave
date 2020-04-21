#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# TODO css val -> bartext
# TODO css mobile theme
# TODO kettlebattle: tabata timer
# TODO soil sensor: add script for calibration
# TODO update example configs
# TODO subpage admin mode: load config into text editor and reload config (send apache reload command)
# TODO footer, about+admin page links

import os
from logging.config import dictConfig
import yaml

from flask import Flask
from flask.logging import create_logger

# load logging configuration from file (dictConfig)
with open(os.path.join("app", "logging.yaml")) as f:
    try:
        config = yaml.load(f, Loader=yaml.FullLoader)
    except AttributeError:
        # FullLoader available for PyYaml 5.1+
        config = yaml.load(f)
    dictConfig(config)

app = Flask(__name__)
app.__version__ = '0.1'
app.name = "cave"

# TODO only use in development, use flaskenv
# test mode:
#       - emails will not be sent while True
#       - scheduler will not be started, all scheduled tasks are executed
#         immediately
app.testing = False
app.debug = True

# load default config that basically disables all modules so you can
# start CAVE with an empty config file to see if it runs at all
# you will only see an empty index and the about page
with open(os.path.join("app", "default.cfg")) as f:
    try:
        config = yaml.load(f, Loader=yaml.FullLoader)
    except AttributeError:
        # FullLoader available for PyYaml 5.1+
        config = yaml.load(f)
app.config.update(config)
app.logger.debug("Default configuration loaded.")

# try to load configuration file, order: server config YAML format > server
# config Python format > client YAML > client Python
for mode in ("server", "client"):
    try:
        with open(f"{mode}_conf.yaml") as f:
            try:
                config = yaml.load(f, Loader=yaml.FullLoader)
            except AttributeError:
                # FullLoader available for PyYaml 5.1+
                config = yaml.load(f)
        app.config.update(config)
        app.logger.info(f"{mode.title()} configuration loaded from YAML.")
        break
    except FileNotFoundError:
        try:
            app.config.from_pyfile(mode)
            app.logger.info(f"{mode.title()} configuration loaded from "
                            f"Python file.")
            break
        except FileNotFoundError:
            app.logger.error(f"There is no {mode} config.")
else:
    app.logger.error("There is no CAVE config - you must have a server or "
                     "client config to make it work (see README and example "
                     "configs for details).")
    raise SystemExit

if mode == "client":
    # change name, will appear in logfile to be certain what mode CAVE is
    # runing with
    app.name = "cave client"

    app.logger = create_logger(app)
    app.logger.debug("~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    app.logger.debug("CAVE CLIENT HAS BEEN STARTED")
    app.logger.debug("~~~~~~~~~~~~~~~~~~~~~~~~~~~~")

    from app.config import client
    from app import schedule

elif mode == "server":
    app.name = "cave server"

    # Flask starts the logger but pylint bitches about invalid function use
    # assigning a "new" logger solves the problem
    app.logger = create_logger(app)
    app.logger.debug("~~~~~~~~~~~~~~~~~~~~~")
    app.logger.debug("CAVE HAS BEEN STARTED")
    app.logger.debug("~~~~~~~~~~~~~~~~~~~~~")

    from app.config import server
    from app import schedule
    from app import context
    from app.routes import index
    from app.routes import pi
    from app.routes import general
    from app.routes import power
    from app.routes import kbgen

else:
    # this should not happen
    app.logger.error(f"Something is wrong here. {mode}, {app.name}")
    raise SystemExit
