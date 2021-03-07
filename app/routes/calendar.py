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

    key = f"{_year}-{_month}-{_day}"
    _s = False  # only show headline once on html page
    if key in utils.record_log.keys():
        for k, item in utils.record_log[key].items():
            try:
                if item["hardware"] == "socket":
                    _s = True
                    # it doesn't get more True than True so stop the loop
                    break
            except TypeError:
                # error is raised if item is not a dict
                pass
        if "note" not in utils.record_log[key]:
            utils.record_log[key]["note"] = ""

        entry = render_template("cal_entry.html",
                                data=utils.record_log[key],
                                d=_day, m=_month, y=_year, s=_s, e=True)
    else:
        entry = render_template("cal_entry.html",
                                data={"note": ""},
                                d=_day, m=_month, y=_year, s=_s, e=False)

    # store date in session data used to reload log entry when page is
    # refreshed, p.e. after uploading file (see below)
    session["date"] = [_year, _month, _day, _s]

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
    return {"notes": _notes}


@app.route("/_upload_image", methods=["POST"])
def upload_image():
    image = request.files.get("file")
    _year, _month, _day, _s = session["date"]
    key = f"{_year}-{_month}-{_day}"
    ts = int(time.time())
    ext = image.filename.split(".")[1]
    image.save(os.path.join("app",
                            "static",
                            "log_images", f"{key}_{ts}.{ext}",
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

    entry = render_template("cal_entry.html",
                            data=utils.record_log[key],
                            d=_day, m=_month, y=_year, s=_s, e=True)

    return {"message": entry}


@app.route("/_add_note", methods=["POST"])
def add_note():
    _year, _month, _day, _s = session["date"]
    key = f"{_year}-{_month}-{_day}"
    text = request.form["note"]
    # update record log dict
    utils.record_log[key]["note"] = text
    # save note as text file
    with open(os.path.join(app.config["PI_DATA"],
                           "annotations",
                           f"{key}.txt",
                           ),
              'w') as f:
        f.write(text)

    entry = render_template("cal_entry.html",
                            data=utils.record_log[key],
                            d=_day, m=_month, y=_year, s=_s, e=True)

    return {"message": entry}
