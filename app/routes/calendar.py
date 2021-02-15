# -*- coding: utf-8 -*-

import os
import time

from flask import render_template, request, session
from app import app, utils


@app.route("/logbook")
def logbook():
    return render_template("calendar.html")


@app.route('/_get_post_json/', methods=['POST'])
def get_button_json():
    date = request.get_json()

    _year = date["year"]
    # 1 has to be added to the month value because lists start at Zero
    _month = str(int(date["month"]) + 1).zfill(2)
    _day = date["day"].zfill(2)
    # store date in session data used to reload log entry when page is
    # refreshed, p.e. after uploading file (see below)
    session["date"] = [_year, _month, _day]

    key = f"{_year}-{_month}-{_day}"
    if key in utils.record_log.keys():
        _s = False  # only show headline once on html page
        for k, item in utils.record_log[key].items():
            try:
                if item["hardware"] == "socket":
                    _s = True
                    # it doesn't get more True than True so stop the loop
                    break
            except TypeError:
                # error is raised if item is not a dict
                pass
        entry = render_template("cal_entry.html",
                                data=utils.record_log[key],
                                d=_day, m=_month, y=_year, s=_s)
    else:
        entry = f"""<div class="val soil" style="background-color:orange">No records for {_day}.{_month}.{_year}</div>"""

    return {"message": entry}


@app.route('/_get_info_json/', methods=['POST'])
def get_info_json():
    date = request.get_json()

    _year = date["year"]
    _month = str(date["month"] + 1).zfill(2)
    _notes = []
    # find days with data entries (temperature, plots etc.)
    # will be marked with different colour in calendar
    for x in range(1, 32):
        key = f"{_year}-{_month}-{str(x).zfill(2)}"
        if key in utils.record_log.keys():
            _notes.append(x)
    print(_notes)
    return {"notes": _notes}


@app.route("/_upload_image", methods=["POST"])
def upload_image():
    image = request.files.get("file")
    _year, _month, _day = session["date"]
    key = f"{_year}-{_month}-{_day}"
    ts = int(time.time())
    ext = image.filename.split(".")[1]
    image.save(os.path.join("static", "log_images", f"{key}_{ts}.{ext}"))

    if key in utils.record_log.keys():
        entry = render_template("cal_entry.html",
                                data=utils.record_log[key],
                                d=_day, m=_month, y=_year)
    else:
        entry = f"""<div class="val soil" style="background-color:orange">No entries for {_day}.{_month}.{_year}</div>"""

    return {"message": entry}

