# -*- coding: utf-8 -*-

import os
import shutil
import time

from flask import render_template, request
from app import app, utils


@app.route('/test')
def home():
    """Render test page"""
    app.logger.debug('Loading test page...')
    return '''
<html>
    <head>
        <title>Test Page - CAVE</title>
    </head>
    <body>
        <h1>Nothing to see here</h1>
    </body>
</html>'''


@app.route('/testmail', methods=['GET', 'POST'])
def send_mail():
    """Render testmail page which sends email on request"""
    app.logger.debug('Loading testmail page...')
    if request.method == 'POST':
        subject = "Test mail from your CAVE installation"
        body = "It's alive!"
        success = 'Mail sent. Check your inbox!'
        fail = "Error message: "

        message = utils.send_mail(subject, body, success, fail)

        return render_template('testmail.html',
                               form=request.form,
                               message=message)
    return render_template('testmail.html', form=request.form)


@app.route('/about')
def about():
    """Render the about page, provides application and configuration info """
    app.logger.debug('Loading about page with system info and stuff in it...')
    appinfo = utils.app_info()
    sys = utils.system_info()
    configuration = utils.conf_info()
    return render_template('about.html', **sys, **configuration, **appinfo)


@app.route('/preview')
def camera():
    app.logger.debug('Loading live camera still...')
    pis = list()
    for name, pi in app.config["PI_LIST"].items():
        if pi["camera"]:
            pis.append(name)

    return render_template('preview.html', pis=pis)


@app.route("/_save_image", methods=["POST"])
def save_image():
    image = request.get_json()["name"]
    key = utils.today()
    ts = int(time.time())
    ext = image.split(".")[1]
    shutil.copyfile(image,
                    os.path.join("app",
                                 "static",
                                 "log_images",
                                 f"{key}_{ts}.{ext}",
                                 )
                    )

    # update record log dict so the added file is displayed on page refresh
    try:
        utils.record_log[key]["images"].append(
            os.path.join("static",
                         "log_images",
                         f"{key}_{ts}.{ext}"))
    except KeyError:
        # empty dict for date if not already existing
        utils.record_log.setdefault(key, dict())
        # empty list for images
        utils.record_log[key]["images"] = list()
        utils.record_log[key]["images"].append(
            os.path.join("static",
                         "log_images",
                         f"{key}_{ts}.{ext}",
                         )
        )

    return {"message": "Image saved."}
