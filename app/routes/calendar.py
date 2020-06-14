# -*- coding: utf-8 -*-

from flask import render_template, request
from app import app


@app.route("/logbook")
def logbook():
    return render_template("calendar.html")


@app.route('/_get_button_json/', methods=['POST'])
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
    data = request.get_json()
    # example list
    notes = [1, 4, 6, 25]
    return {"notes": notes}
