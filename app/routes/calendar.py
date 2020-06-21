# -*- coding: utf-8 -*-

from flask import render_template, request
from app import app, utils


@app.route("/logbook")
def logbook():
    return render_template("calendar.html")


@app.route('/_get_post_json/', methods=['POST'])
def get_button_json():
    data = request.get_json()
    # message = f"Button pressed for day {data}."
    # 1 has to be added to the month value because lists start at Zero
    m = int(data["month"]) + 1
    data.update(month=m)
    entry = render_template("cal_entry.html", var=data)

    return {"message": entry}

@app.route('/_get_info_json/', methods=['POST'])
def get_info_json():
    date = request.get_json()
    _year = date["year"]
    _month = str(date["month"] + 1).zfill(2)
    _notes = []
    for x in range(1, 32):
        key = f"{_year}-{_month}-{str(x).zfill(2)}"
        if key in utils.record_log.keys():
            _notes.append(x)

    return {"notes": _notes}
