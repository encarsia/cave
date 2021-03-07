# -*- coding: utf-8 -*-

import os
from datetime import datetime
from flask import render_template
from app import app, utils


@app.route('/<pi>')
def raspi(pi):
    """Render Raspberry Pi detail subpage"""
    app.logger.debug(f'Loading detail page for {pi}')
    content, sensors, pots, warn = utils.get_pi_detail_data(pi)

    if app.config["PI_LIST"][pi]['air sensor']:
        lastrecords, alldays = list(), list()
        # read the protocol file
        values = utils.read_csv(os.path.join(app.config["APP_DATA"],
                                             pi,
                                             'sensor_air',
                                             'temphum_protocol.txt',
                                             ),
                                15,
                                True,
                                )
        values.reverse()
        for i in range(3):
            try:
                date, t_max, t_max_t, t_min, t_min_t, t_mean, t_median, \
                t_stdev, h_max, h_max_t, h_min, h_min_t, h_mean, \
                h_median, h_stdev = values[i]
                plot = f'static/plots/{pi}/dayplot_{date}.png'
                day = datetime.strptime(date, "%Y-%m-%d").strftime(
                    "%A, %d. %B %Y")
                dataset = {'t_max': t_max,
                           't_max_t': t_max_t,
                           't_min': t_min,
                           't_min_t': t_min_t,
                           't_mean': t_mean,
                           't_median': t_median,
                           't_stdev': t_stdev,
                           'h_max': h_max,
                           'h_max_t': h_max_t,
                           'h_min': h_min,
                           'h_min_t': h_min_t,
                           'h_mean': h_mean,
                           'h_median': h_median,
                           'h_stdev': h_stdev,
                           'date': date,
                           'day': day,
                           'plot': plot,
                           }
                lastrecords.append(dataset)
                if None in dataset:
                    warn = True

            except ValueError:
                warn = True
                app.logger.warning(f'[{pi}] Data is not available.',
                                   exc_info=True)
            except TypeError:
                warn = True
                app.logger.error(f'[{pi}] Something is wrong with the data.',
                                 exc_info=True)
            
            except IndexError:
                app.logger.debug(f"[{pi}] Cannot show last 3 days, missing data.")

        for line in values:
            try:
                date, t_max, t_max_t, t_min, t_min_t, t_mean, t_median, \
                t_stdev, h_max, h_max_t, h_min, h_min_t, h_mean, \
                h_median, h_stdev = line
                dataset = {'date': date,
                           't_max': t_max,
                           't_max_t': t_max_t,
                           't_min': t_min,
                           't_min_t': t_min_t,
                           't_mean': t_mean,
                           't_median': t_median,
                           't_stdev': t_stdev,
                           'h_max': h_max,
                           'h_max_t': h_max_t,
                           'h_min': h_min,
                           'h_min_t': h_min_t,
                           'h_mean': h_mean,
                           'h_median': h_median,
                           'h_stdev': h_stdev,
                           }
                alldays.append(dataset)
                if None in dataset:
                    warn = True

            except ValueError:
                warn = True
                app.logger.warning(f'[{pi}] Data is not available.',
                                   exc_info=True)
            except TypeError:
                warn = True
                app.logger.error(f'[{pi}] Something is wrong with the data.',
                                 exc_info=True)

    else:
        lastrecords, alldays = False, False

    return render_template('temphum.html', **content, sensors=sensors,
                           pi_name=pi, s=pots, warn=warn,
                           lastrecords=lastrecords, alldays=alldays)
