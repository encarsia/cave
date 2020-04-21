# -*- coding: utf-8 -*-

from flask import render_template, request
from app import app, utils


@app.route('/kettlebattle', methods=['GET', 'POST'])
def kettlebattle_generator():
    """Render kettlebattle page"""
    app.logger.debug('Loading kettlebattle generator...')
    if request.method == 'POST':
        if request.form['submit'] == 'generate':
            # create workout list, render template with this list instead of
            # KB_EX so values are kept
            exercises = list()
            # iterate over items from request (type ImmutableMultiDict,
            # see werkzeug API docs for details
            for name, reps in request.form.items():
                if name != "submit":
                    exercises.append([name, int(reps)])
            # create list for sharing via c&p, don't list exercises w/ 0 reps
            battle = []
            total = 0
            for ex, reps in exercises:
                if reps > 0:
                    battle.append((ex, reps))
                    total += reps
            return render_template('kettlebattle.html',
                                   form=request.form,
                                   reps=app.config["REPS_PRESET"],
                                   exc=exercises,
                                   battletext=battle,
                                   total=total,
                                   showgen=True)
        # returned value is 0 or 1
        pos = int(request.form['submit'])
        # random workout for given preset based on minimum values
        exercises = utils.generate_workout(app.config["REPS_PRESET"][pos], pos)
        return render_template('kettlebattle.html',
                               form=request.form,
                               pos=pos,
                               reps=app.config["REPS_PRESET"],
                               exc=exercises)
    # start without values in exercise list
    empty_exercises = [(x, 0) for x in app.config["KB_EX"]]
    return render_template('kettlebattle.html',
                           form=request.form,
                           reps=app.config["REPS_PRESET"],
                           exc=empty_exercises,
                           )
