# -*- coding: utf-8 -*-

from app import app

components = [(app.config["REMOTE_POWER"], 'powersockets', 'Socket control'),
              (app.config["KETTLEBATTLE"],
               'kettlebattle_generator',
               'Kettlebattle!'),
             ]


@app.context_processor
def navbar():
    """Return navigation bar entries"""
    items = []
    if app.config["SENSORS"]:
        for name, pi in app.config["PI_LIST"].items():
            navitem = {'function': 'raspi',
                       'menu': name,
                       }
            items.append(navitem)
    for c in components:
        if c[0]:
            navitem = {'function': c[1],
                       'menu': c[2],
                       }
            items.append(navitem)
    return dict(navitems=items)
