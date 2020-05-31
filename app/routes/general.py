# -*- coding: utf-8 -*-

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


@app.route('/lcd')
def display():
    """Render weather page for Waveshare LCD"""
    app.logger.debug('Loading small display page...')
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
