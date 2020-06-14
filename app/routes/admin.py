# -*- coding: utf-8 -*-

from flask import render_template, request
from app import app, utils


@app.route('/admin')
def config():
    """Render admin page, load configuration file into codemirror editor"""
    app.logger.debug("Loading admin page...")
    if app.config["CONF_FILE"].split(".")[1] == "yaml":
        format = "yaml"
    else:
        format = "python"

    with open(app.config["CONF_FILE"]) as f:
        code = f.read()

    return render_template("admin.html",
                           code=code,
                           format=format,
                           pis=app.config["PI_LIST"],
                           )


@app.route('/_get_content_json/', methods=['POST'])
def get_content_json():
    data = request.get_json()
    utils.save_config_file(data["content"])

    return {"message": f"File saved, previous version has been backuped. "
                       f"You have to reload the webserver to "
                       f"apply changes. If you do not reload now the "
                       f"server will do so at midnight."}


@app.route('/_restart_apache/', methods=['POST'])
def restart_apache():
    # send restart command to subprocess
    message = utils.reload_apache()
    return {"message": message}
