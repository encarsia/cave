# -*- coding: utf-8 -*-

import csv
import getpass
import json
import os
import platform
import random
import socket
import statistics
import subprocess
import sys
import time
import urllib.request
import urllib.parse

from datetime import datetime, timedelta

import flask
from flask_mail import Mail, Message
from app import app


def connect():
    ssh, ftp = dict(), dict()
    for pi in app.config["PI_LIST"]:
        if 'address' in app.config["PI_LIST"][pi]:
            try:
                ssh_client = paramiko.SSHClient()
                ssh_client.set_missing_host_key_policy(
                    paramiko.AutoAddPolicy())
                ssh_client.connect(
                    hostname=app.config["PI_LIST"][pi]['address'],
                    username=app.config["PI_LIST"][pi]['username'],
                    password=app.config["PI_LIST"][pi]['password'],
                )
                ssh[pi] = ssh_client
                ftp[pi] = ssh_client.open_sftp()
                app.logger.info(f'[{pi}] SSH connection established.')
            except (paramiko.ssh_exception.SSHException,
                    paramiko.ssh_exception.NoValidConnectionsError,
                    OSError):
                app.logger.error(f'[{pi}] SSH connection failed. ')
    return ssh, ftp


# returns the current day formatted as YYYY-MM-DD formatted which is
# used for sensor data logging and plots
# optional arg for timedelta, today(-1) returns yesterday's date

def today(delta=0):
    string = str((datetime.now() + timedelta(days=delta)).strftime('%Y-%m-%d'))
    return string


def now_hour():
    t = int(datetime.now().strftime('%H'))
    return t


def now_time():
    return datetime.now().strftime('%H:%M')


def read_csv(filename, rows=3, complete=False):
    try:
        with open(filename) as f:
            reader = csv.reader(x.replace('\0', '') for x in f)
            data = list(reader)
    except FileNotFoundError:
        app.logger.warning(f'Data file does not exist. Returned values '
                           f'will be \'None\' ({filename}).')
        values = [list().append(None) for _ in range(rows)]
        return values
    # return all lines, only used seldom like creating the log table
    if complete:
        return data
    try:
        values = data[-1]
    except (IndexError, ValueError):
        app.logger.warning(f'Error trying to read the file. Returned values '
                           f'will be \'None\' ({filename}).')
        values = [list().append(None) for _ in range(rows)]
    return values


def read_remote_csv(pi, filename, complete=False):
    try:
        with FTP_CONNECTION[pi].open(filename) as f:
            reader = csv.reader(x.replace('\0', '') for x in f)
            data = list(reader)
    except (FileNotFoundError, IndexError, KeyError, TypeError):
        return  [None, None, None]
    if complete:
        return data
    return data[-1]


def get_weather(loc, id_call, appid, lang='en'):
    loc = urllib.parse.quote(loc)
    url = API_URL.format('weather', id_call, loc, lang, appid)
    # json expects variable as string instead of bytes
    # this is fixed in Python 3.6
    data = urllib.request.urlopen(url).read().decode('utf-8')
    parsed = json.loads(data)
    weather = None
    if parsed.get('weather'):
        weather = {'descr': parsed['weather'][0]['description'],
                   'icon': parsed['weather'][0]['icon'],
                   'temp': int(parsed['main']['temp']),
                   'hum': parsed['main']['humidity'],
                   'wind': float(parsed['wind']['speed']),
                   'clouds': parsed['clouds']['all'],
                   'city': parsed['name'],
                   'city_id': parsed['id'],
                   }
    url = API_URL.format('forecast', id_call, loc, lang, appid)
    # json expects variable as string instead of bytes
    # this is fixed in Python 3.6
    data = urllib.request.urlopen(url).read().decode('utf-8')
    parsed = json.loads(data)
    # take first data row of forecast to collect rain/snow data
    parsed = parsed['list'][0]
    for item in ['rain', 'snow']:
        if parsed.get(item):
            weather[item] = '{0:.1f} mm'.format(parsed[item]['3h'])
        else:
            weather[item] = None
    wind = get_wind(weather['wind'])
    return weather, wind


def get_wind(wind):
    bft = get_bft(wind)
    # show wind description in language set in openweathermap settings if
    # available
    try:
        descr = app.config["WIND_DESCR"][app.config["LANGUAGE"]][WIND_BFT[bft]]
    except KeyError:
        descr = WIND_BFT[bft]
    data = {'wind_ms': wind,
            'wind_km': int(wind * 3.6),
            'bft': bft,
            'descr': descr,
            }
    return data


def get_bft(wind):
    for bft_val, bft_speed in enumerate(BFT_SCALE):
        if wind > bft_speed:
            continue
        return bft_val


def get_soil(pi, pi_detail, pot):
    date, timestamp, state = current_soil_data(pi, pi_detail, pot)
    if date == today():
        date = 'Today'
    elif date == today(-1):
        date = 'Yesterday'
    elif date is None:
        date = 'None'
    else:
        date = datetime.strptime(date, '%Y-%m-%d').strftime('%d. %B')
    # 0 = moist, 1 = dry, raspi can only catch digital output
    if state == '0':
        bg = 'green'
        txt = 'okay'
    else:
        bg = 'red'
        txt = 'check plant'
    soil = {'date': date,
            'time': timestamp,
            'bg': bg,
            'txt': txt,
            'state': state,
            }
    return soil


def soil_details(pi, pi_details, pot):
    current = get_soil(pi, pi_details, pot)
    data = all_soil_data(pi, pi_details, pot)
    data.reverse()
    for day, _, state in data:
        dtday = datetime.strptime(day, '%Y-%m-%d')
        if state == current['state']:
            delta = (datetime.now() - dtday).days
            # TODO German date format
            durdate = datetime.strptime(day, '%Y-%m-%d').strftime('%d. %B')
        else:
            break
    current['dur'] = delta
    current['durdate'] = durdate
    return current


def generate_workout(abs_reps, pos):
    # generate exercise list for chosen preset
    exercises = list()
    for ex, pre in app.config["KB_EX"].items():
        exercises.append([ex, pre[pos]])
    # sum up minimum values
    min_reps = 0
    for _ in exercises:
        min_reps += pre[pos]
    # choose random exercises from list, max number given in MAX_EX variable
    dothese = random.sample(exercises, app.config["MAX_EX"])
    # add 10 repetitions to one of the random exercises to absolute repetition
    # number
    for _ in range(min_reps, abs_reps, 10):
        random.choice(dothese)[1] += 10
    return exercises


def system_info():
    # ## sysinfo page inspired by ##
    # http://www.linux-magazin.de/ausgaben/2015/01/flask/ and ##
    # http://www.ashokraja.me/post/Raspberry-Pi-System-Information-Web
    # -Application-with-Python-and-Flask.aspx ## main modifications made in
    # running subprocess command: ## use 'run' command instead of
    # depreciated 'check_output' ## avoid 'shell=True' argument because of
    # security
    sysinfo = dict()
    # get IP in network
    try:
        myip = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        myip.connect(('8.8.8.8', 80))
        sysinfo['ip'] = myip.getsockname()[0]
        myip.close()
    except StandardError:
        sysinfo['ip'] = 'Could not fetch IP address.'
    # get name of logged in user and machine name
    sysinfo['username'] = getpass.getuser()
    sysinfo['node'] = platform.node()
    # run shell commands
    for key, value in COMMANDS.items():
        try:
            sub = subprocess.run(value.split(),
                                 stdout=subprocess.PIPE,
                                 universal_newlines=True)
            sysinfo[key] = sub.stdout
        except FileNotFoundError:
            sysinfo[key] = 'N/A'
    ### string operations in shell command output
    # memory usage
    sysinfo['mem_total'] = sysinfo['mem'].splitlines()[1].split()[1]
    sysinfo['mem_available'] = sysinfo['mem'].splitlines()[1].split()[6]
    sysinfo['mem_used'] = int(sysinfo['mem_total']) - int(
        sysinfo['mem_available'])
    # processor name
    sysinfo['cpu_hardware'] = 'N/A'
    for line in sysinfo['cpu_name'].split('\n'):
        if line.startswith('model name'):
            sysinfo['cpu_name'] = line.split(':')[1].lstrip()
        if line.startswith('Hardware'):
            sysinfo['cpu_hardware'] = line.split(':')[1].lstrip()
    # distribution name
    for line in sysinfo['os_info'].split('\n'):
        if line.startswith('PRETTY_NAME'):
            sysinfo['os_info'] = line.split('=')[1][1:-1]
            break
    sysinfo['proc_info'] = int(sysinfo['proc_info'])
    return sysinfo


def conf_info():
    confinfo = dict()
    modules = {'mod_raspi': app.config["SENSORS"],
               'mod_weather': app.config["WEATHER"],
               'mod_remote': app.config["REMOTE_POWER"],
               'mod_kbgen': app.config["KETTLEBATTLE"],
               'mod_email': app.config["SEND_MAIL"]
               }
    confinfo.update(modules)
    if modules['mod_raspi']:
        confinfo['raspi'] = app.config["PI_LIST"]
    if modules['mod_weather']:
        try:
            confinfo['weather_loc'] = app.config["LOCATION"]
        except AttributeError:
            confinfo['weather_loc'] = 'n/a'
        try:
            confinfo['weather_loc_id'] = app.config["LOCATION_ID"]
        except AttributeError:
            confinfo['weather_loc_id'] = 'n/a'
        confinfo['weather_lang'] = app.config["LANGUAGE"]
        confinfo['weather_appid'] = app.config["APPID"]
    if modules['mod_remote']:
        confinfo['remote_path'] = app.config["RR_PATH"]
        confinfo['switches'] = app.config["DEF_SWITCH"]
    if modules['mod_kbgen']:
        confinfo['kb_ex'] = app.config["KB_EX"]
        confinfo['kb_max'] = app.config["MAX_EX"]
        confinfo['kb_presets'] = app.config["REPS_PRESET"]
    return confinfo


def app_info():
    appinfo = {'app_version': app.__version__,
               'app_mode': app.name.split()[1],
               'flask_version': flask.__version__,
               'py_version': sys.version.split()[0],
               }
    return appinfo


def air_prot_plot(air_pis):

    def generateplot(t_min_ax, t_max_ax, h_min_ax, h_max_ax):
        # generate plot for the day
        _, ax1 = pyplot.subplots(figsize=(9, 5))
        ax1.plot(t_list)
        ax1.set_ylabel(r'Temperature (°C)', fontsize=14, color='blue')
        pyplot.axis([0, len(timestamp), t_min_ax, t_max_ax])
        for label in ax1.get_yticklabels():
            label.set_color('blue')
        ax2 = ax1.twinx()
        ax2.plot(h_list, color='darkgreen')
        ax2.set_ylabel(r'Humidity (%)', fontsize=14, color='darkgreen')
        pyplot.axis([0, len(timestamp), h_min_ax, h_max_ax])
        for label in ax2.get_yticklabels():
            label.set_color('darkgreen')
        pyplot.gcf().autofmt_xdate()
        pyplot.xticks(range(0, len(xlabels)), xlabels)
        ax1.xaxis.set_major_locator(ticker.MultipleLocator(60))
        try:
            pyplot.savefig(os.path.join(app.config["PI_DATA"],
                                        pi,
                                        'sensor_air',
                                        dayplot,
                                        ),
                           transparent=True,
                           )
            # save fig with non-transparent background	
            pyplot.savefig(os.path.join(app.config["PI_DATA"],
                                        pi,
                                        'sensor_air',
                                        dayplot_wbg,
                                        ),
                           transparent=False,
                           )
            app.logger.info(f'[{pi}] Save dayplot in data directory. OK.')
            pyplot.savefig(os.path.join('app',
                                        'static',
                                        'plots',
                                        pi,
                                        dayplot,
                                        ),
                           transparent=True,
                           )
            app.logger.info(f'[{pi}] Save dayplot in static directory. OK.')
        except FileNotFoundError:
            app.logger.error(f'[{pi}] Could not save plot in static directory.'
                             f' Check if it exists.')
        except Exception:
            app.logger.error(f'[{pi}] Saving dayplot failed. Something is '
                             f'wrong...', exc_info=True)
        pyplot.close()  # close figure

        # write statistic values to long term protocol
        with open(os.path.join(app.config["PI_DATA"],
                               pi,
                               'sensor_air',
                               'temphum_protocol.txt'),
                  'a') as f:
            f.write(yesterday)
            app.logger.info(f'[{pi}] Add today\'s data to protocol. '
                            f'Done.')

    dayta = 'dayta_{}.csv'.format(today(-1))
    dayplot = 'dayplot_{}.png'.format(today(-1))
    dayplot_wbg = 'dayplot_{}_wbg.png'.format(today(-1))

    for pi in air_pis:
        try:
            path = os.path.join(app.config["PI_DATA"],
                                pi,
                                'sensor_air',
                                dayta,
                                )
            with open(path, 'r') as f:
                # replace '\0's to avoid NULL byte error
                reader = csv.reader(x.replace('\0', '') for x in f)
                data = list(reader)
                app.logger.info(f'[{pi}] Reading yesterday\'s data '
                                f'successful...')

            t_list = list()
            h_list = list()
            timestamp = list()

            xlabels = (' ',
                       '0:00',
                       '1:00',
                       '2:00',
                       '3:00',
                       '4:00',
                       '5:00',
                       '6:00',
                       '7:00',
                       '8:00',
                       '9:00',
                       '10:00',
                       '11:00',
                       '12:00',
                       '13:00',
                       '14:00',
                       '15:00',
                       '16:00',
                       '17:00',
                       '18:00',
                       '19:00',
                       '20:00',
                       '21:00',
                       '22:00',
                       '23:00',
                       '24:00',
                       )

            for d in data:
                d[1] = float(d[1])
                d[2] = float(d[2])
                t_list.append(d[1])
                h_list.append(d[2])
                timestamp.append(d[0])

            for d in data:
                if d[1] == max(t_list):
                    max_t_time = d[0]
                elif d[1] == min(t_list):
                    min_t_time = d[0]
                if d[2] == max(h_list):
                    max_h_time = d[0]
                elif d[2] == min(h_list):
                    min_h_time = d[0]

            yesterday = (f'{today(-1)},{max(t_list)},{max_t_time},'
                         f'{min(t_list)},{min_t_time},'
                         f'{statistics.mean(t_list):.1f},'
                         f'{statistics.median_low(t_list):.1f},' \
                         f'{statistics.stdev(t_list):.2f},{max(h_list)},'
                         f'{max_h_time},{min(h_list)},{min_h_time},'
                         f'{statistics.mean(h_list):.1f},'
                         f'{statistics.median_low(h_list):.1f},'
                         f'{statistics.stdev(h_list):.2f}'
                         f'\n')

            app.logger.info(f'[{pi}] Collected data and calculated statistics.'
                            f' OK.')
        except FileNotFoundError:
            app.logger.error(f'[{pi}] Data file is not available. Could not '
                             f'generate plot.')
            continue
        try:
            # set min/max ax values
            if 'plot axis' in app.config["PI_LIST"][pi]:
                if app.config["PI_LIST"][pi]['plot axis'] == 'auto':
                    ax1min = int(min(t_list))
                    ax1max = int(max(t_list)) + 1
                    ax2min = int(min(h_list) / 10) * 10
                    ax2max = int(max(h_list) / 10) * 10 + 10
                else:
                    ax1min, ax1max = [int(x) for x in
                                      app.config["PI_LIST"][pi]["plot axis"][
                                          "temp"].split("-")]
                    ax2min, ax2max = [int(x) for x in
                                      app.config["PI_LIST"][pi]["plot axis"][
                                          "hum"].split("-")]
                generateplot(ax1min, ax1max, ax2min, ax2max)
            else:
                generateplot(14, 26, 20, 80)
        except NameError:
            app.logger.error(
                f'[{pi}] No or malformed data. No plot for today.',
                exc_info=True)

    # write daylength to file for sockets with time interval
    if app.config["SOCKET_INTERVALS"]:
        for name, socket in app.config["SOCKET_INTERVALS"].items():
            if "start" and "stop" in socket:
                daylength = socket["stop"] - socket["start"]
                if daylength < 0:
                    daylength += 24
                yesterday = (f'{today(-1)},'
                             f'{daylength},'
                             f'{socket["start"]},'
                             f'{socket["stop"]}'
                             f'\n')
                with open(os.path.join(app.config["PI_DATA"],
                                       "sockets",
                                       name,
                                       "daylength.txt"),
                          'a') as f:
                    f.write(yesterday)
                    app.logger.info(f'[{name}] Add today\'s daylength to '
                                    f'protocol. Done.')


def piglow_air(hum, temp):
    piglow.set(_HUM_LEDS, 0)
    piglow.set(_TEMP_LEDS, 0)
    for val, num in _HUM_GLOW:
        if hum >= val:
            piglow.set(num, 50)
            time.sleep(.3)
        else:
            break
    for val, num in _TEMP_GLOW:
        if temp >= val:
            piglow.set(num, 50)
            time.sleep(.3)
        else:
            break


def piglow_daemon(pi):
    _, temp, hum = current_air_data(pi, app.config["PI_LIST"][pi])
    app.logger.debug(f'Show PiGlow pattern for {pi}: {temp} °C, {hum} % '
                     f'humidity.')
    piglow_air(float(hum), float(temp))


def air_daemon(pi, model, pin, legacy):
    try:
        if legacy:
            types = {'DHT22': Adafruit_DHT.DHT22,
                     'DHT11': Adafruit_DHT.DHT11,
                     'AM2302': Adafruit_DHT.AM2302,
                     }
            sensor = types[model]
            hum, temp = Adafruit_DHT.read_retry(sensor, pin)
        else:
            types = {'DHT22': adafruit_dht.DHT22,
                     'DHT11': adafruit_dht.DHT11,
                     'AM2302': adafruit_dht.DHT22,
                     }
            sensor = types[model](pin)
            hum, temp = sensor.humidity, sensor.temperature
        app.logger.debug(f'Current values: {temp:0.1f} °C, {hum:0.1f} %')
        data = '{0},{1:0.1f},{2:0.1f}\n'.format(
            datetime.now().strftime('%H:%M'), temp, hum)
        # store data in consecutive files, one for each day

        with open(os.path.join(app.config["PI_DATA"],
                               pi["name"],
                               'sensor_air',
                               'dayta_{}.csv'.format(today()),
                               ),
                  'a') as f:
            f.write(data)

        # show temp/hum from primary raspi
        if app.config["PIGLOW"] == pi:
            piglow_air(hum, temp)

    except FileNotFoundError:
        app.logger.error('No access to data file or it does not exist.')
    except RuntimeError as e:
        app.logger.warn(f'Could not obtain sensor data. Error message: {e}')
    except Exception:
        app.logger.error('Something went wrong running the DHT sensor '
                         'daemon. Error message: ', exc_info=True)


def soil_daemon(pi, pots):
    def get_gpio_info(data, vcc):
        gpio.output(vcc, gpio.HIGH)
        time.sleep(.1)
        state = gpio.input(data)
        gpio.output(vcc, gpio.LOW)
        return state

    def collect_data(data, vcc):
        # the returned state is 0 or 1
        # 0 = moist, 1 = dry, adjust with potentiometer
        state = get_gpio_info(data, vcc)
        sensordata = '{},{},{}\n'.format(datetime.now().strftime('%Y-%m-%d'),
                                         datetime.now().strftime('%H:%M'),
                                         state,
                                         )
        app.logger.debug(f'Sensor data: {sensordata}')
        with open(os.path.join(app.config["PI_DATA"],
                               pi,
                               'sensor_soil',
                               'pothum_{}.csv'.format(pot)),
                  'a') as f:
            f.write(sensordata)
        if app.config["PIGLOW"] == pi:
            if state == 0:
                piglow.white(10)
            else:
                piglow.white(0)
            piglow.show()

    def set_gpio(data, vcc):
        gpio.setwarnings(False)
        gpio.setmode(gpio.BOARD)
        gpio.setup(data, gpio.IN)
        gpio.setup(vcc, gpio.OUT)

    for pot in pots:
        try:
            set_gpio(pots[pot]["data pin"], pots[pot]["vcc pin"])
            collect_data(pots[pot]["data pin"], pots[pot]["vcc pin"])
            app.logger.info(f'[{pi} - {pot}] Soil data written to file.')
        except NameError:
            app.logger.error('Cannot grab sensor data due to missing '
                             'package: RPi.GPIO.')


def soil_piglow(soil_pis):
    for pi in soil_pis:
        for pot in app.config["PI_LIST"][pi]["pots"]:
            _, _, state = read_csv(os.path.join(app.config["PI_DATA"],
                                                pi,
                                                'sensor_soil',
                                                'pothum_{}.csv'.format(pot),
                                                )
                                   )
            if state == "1":
                # turn off white LEDs if any of the plants return 1 state (dry)
                piglow.white(0)
                app.logger.warning("At least one soil sensor reports water "
                                   "shortage. Check plants.")
                return
    piglow.white(10)


def get_sensor_data(remote_pis):
    def locate_files(filename, sub, user, path, pi):
        src = os.path.join('/home',
                           user,
                           path,
                           app.config["PI_DATA"],
                           pi,
                           sub,
                           filename,
                           )
        dest = os.path.join(app.config["PI_DATA"],
                            pi,
                            sub,
                            filename,
                            )
        return src, dest

    for pi in remote_pis:
        if app.config["PI_LIST"][pi]['air sensor']:
            filename = 'dayta_{}.csv'.format(today(-1))
            sub = 'sensor_air'
            src, dest = locate_files(filename,
                                     sub,
                                     app.config["PI_LIST"][pi]['username'],
                                     app.config["PI_LIST"][pi]['installdir'],
                                     pi,
                                     )
            try:
                FTP_CONNECTION[pi].get(src, dest)
                app.logger.info(f'[{pi}] Copy yesterday\'s sensor data file '
                                f'({sub}). OK.')
            except FileNotFoundError:
                app.logger.error(f'[{pi}] Did not find file to copy ({src}).')
            except KeyError:
                app.logger.error(f'[{pi}] Could not copy data from network '
                                 f'device.')

        if app.config["PI_LIST"][pi]['soil sensor']:
            sub = 'sensor_soil'
            for pot in app.config["PI_LIST"][pi]["pots"]:
                filename = 'pothum_{}.csv'.format(pot)
                src, dest = locate_files(filename,
                                         sub,
                                         app.config["PI_LIST"][pi]['username'],
                                         app.config["PI_LIST"][pi][
                                             'installdir'],
                                         pi,
                                         )
                try:
                    FTP_CONNECTION[pi].get(src, dest)
                    app.logger.info(f'[{pi}] Copy yesterday\'s sensor data '
                                    f'file ({sub}). OK.')
                except FileNotFoundError:
                    app.logger.error(
                        f'[{pi}] Did not find file to copy ({src}).')
                except KeyError:
                    app.logger.error(f'[{pi}] Could not copy data from network'
                                     f' device.')


def get_pi_detail_data(pi):
    # create empty variables to avoid error when passing to template if not set
    content, sensors, pots, warn = dict(), dict(), None, False
    # read sensors settings from conf
    if app.config["PI_LIST"][pi]["air sensor"]:
        sensors["air"] = True
        time, temp, hum = current_air_data(pi,
                                           app.config["PI_LIST"][pi])
        date, t_max, t_max_t, t_min, t_min_t, t_mean, t_median, t_stdev, \
        h_max, h_max_t, h_min, h_min_t, h_mean, h_median, h_stdev \
            = read_csv(os.path.join(app.config["PI_DATA"],
                                    pi,
                                    'sensor_air',
                                    'temphum_protocol.txt',
                                    ),
                       15)
        plot = 'static/plots/{}/dayplot_{}.png'.format(pi, date)
        if date == today(-1):
            date = "Yesterday"
        else:
            date = "Last record ({})".format(date)
        content = {'time': time,
                   'temp': temp,
                   'hum': hum,
                   'date': date,
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
                   'plot': plot,
                   }
        if None in content.values():
            warn = True
    if app.config["PI_LIST"][pi]["soil sensor"]:
        sensors["soil"] = True
        pots = dict()
        for pot in app.config["PI_LIST"][pi]['pots']:
            pots[pot] = soil_details(pi, app.config["PI_LIST"][pi], pot)
            if None in pots.values():
                warn = True
    # TODO put sensors, pots and warn in content dict for better readability
    return content, sensors, pots, warn


def current_air_data(pi, pi_detail):
    if pi_detail["address"]:
        # get current data from network
        time, temp, hum = read_remote_csv(pi,
                                          os.path.join("/home",
                                                       pi_detail["username"],
                                                       pi_detail["installdir"],
                                                       app.config["PI_DATA"],
                                                       pi,
                                                       "sensor_air",
                                                       "dayta_{}.csv".format(
                                                           today()),
                                                       )
                                          )
    else:
        # get current data from locally stored data
        time, temp, hum = read_csv(os.path.join(app.config["PI_DATA"],
                                                pi,
                                                'sensor_air',
                                                'dayta_{}.csv'.format(today()),
                                                )
                                   )
    return time, temp, hum


def current_soil_data(pi, pi_detail, pot):
    if pi_detail["address"]:
        # get current data from network
        date, timestamp, state = \
            read_remote_csv(pi,
                            os.path.join("/home",
                                         pi_detail["username"],
                                         pi_detail["installdir"],
                                         app.config["PI_DATA"],
                                         pi,
                                         "sensor_soil",
                                         f"pothum_{pot}.csv",
                                         ),
                            )
    else:
        # get current data from locally stored data
        date, timestamp, state = read_csv(os.path.join(app.config["PI_DATA"],
                                                       pi,
                                                       'sensor_soil',
                                                       f'pothum_{pot}.csv',
                                                       )
                                          )
    return date, timestamp, state


def all_soil_data(pi, pi_detail, pot):
    if pi_detail["address"]:
        # get current data from network
        data = read_remote_csv(pi,
                               os.path.join("/home",
                                            pi_detail["username"],
                                            pi_detail["installdir"],
                                            app.config["PI_DATA"],
                                            pi,
                                            "sensor_soil",
                                            f"pothum_{pot}.csv",
                                            ),
                               complete=True,
                               )
    else:
        # get current data from locally stored data
        data = read_csv(os.path.join(app.config["PI_DATA"],
                                     pi,
                                     'sensor_soil',
                                     f'pothum_{pot}.csv',
                                     ),
                        complete=True,
                        )
    return data


def send_daily_report(pi_list):
    for pi in pi_list:
        # create empty variables to avoid error when passing to template if
        # not set
        content, sensors, pots, warn = get_pi_detail_data(pi)
        # TODO check if plot background should not be transparent
        # run Flask functions outside the application context like rendering
        # templates without routing
        with app.app_context():
            rendered_txt = flask.render_template("temphum_mail.txt",
                                                 sensors=sensors,
                                                 **content,
                                                 pi_name=pi,
                                                 s=pots,
                                                 warn=warn,
                                                 )
            rendered_html = flask.render_template("temphum_mail.html",
                                                  sensors=sensors,
                                                  **content,
                                                  pi_name=pi,
                                                  s=pots,
                                                  warn=warn,
                                                  )

        subject = f"[{pi}] Daily report"
        if content["plot"]:
            attach = content["plot"]
        else:
            attach = False
            app.logger.warning(f"[{pi}] Missing plot file.")
        success = f"[{pi}] Mail report sent"
        fail = (f"[{pi}] Mail report could not be sent.\n"
                f"Error message:")
        try:
            send_mail(subject, rendered_txt, success, fail,
                      rendered_html, attach, pi)
        except Exception as e:
            app.logger.error(f"Error message: {e}")


def send_daily_log():
    subject = "[CAVE] Daily log"
    with open(os.path.join("logs", "extra.log")) as f:
        body = f.read()
    success = "Daily log sent via e-mail"
    fail = (f"Daily log could not be sent via e-mail.\n'"
            f"Error message: ")
    send_mail(subject, body, success, fail)


def send_mail(subject, body, success, fail, html=False, attach=False,
              pi=False):
    msg = Message(subject,
                  sender=app.config["MAIL_SENDER_ADDRESS"],
                  recipients=app.config["MAIL_RECIPIENTS"],
                  )
    msg.body = body
    if html:
        msg.html = html
    if attach:
        try:
            with app.open_resource(attach) as f:
                msg.attach("dayplot.png", "image/png", f.read())
        except FileNotFoundError:
            app.logger.warning(f"[{pi}] No plot file. No attachment")

    mail = Mail(app)
    try:
        with app.app_context():
            mail.send(msg)
        app.logger.info(success)
        return success
    except Exception as e:
        app.logger.error(f"{fail} {e}")
        return f"{fail} {e}"


def switch_power_socket(name, socket, state):
    # generate subprocess command
    cmd = "{}/send -s {} {} {}".format(app.config["RR_PATH"],
                                       socket["systemCode"],
                                       socket["unitCode"],
                                       SWITCH_POS[state],
                                       )
    print(cmd)
    app.logger.debug(f"Execute command: {cmd}")
    subprocess.run(cmd, shell=True)
    app.logger.info(f"{name} power socket turned {state}")
    switch_socket_logentry(now_time(), name, state)


def power_socket_temp_daemon(name, socket):
    time, temp, _ = current_air_data(socket["sensor"],
                                     app.config["PI_LIST"][socket["sensor"]])
    # turn socket on/off if temperature exceeds values
    try:
        temp = float(temp)
    except TypeError:
        switch_power_socket(name, app.config["DEF_SWITCH"][name], "off")
        app.logger.info(f"[{name}] Invalid data, switch has been turned off")
    if temp > socket["max"]:
        state = "off"
        switch_power_socket(name, app.config["DEF_SWITCH"][name], state)
        app.logger.info(f"[{name}] switched {state} at {temp} °C (max is "
                        f"{socket['max']} °C)")
    elif temp < socket["min"]:
        state = "on"
        switch_power_socket(name, app.config["DEF_SWITCH"][name], state)
        app.logger.info(f"[{name}] switched {state} at {temp} °C (min is "
                        f"{socket['min']} °C)")
    else:
        # get last state
        if time == "00:00":
            _, state = read_csv(os.path.join(app.config["PI_DATA"],
                                             "sockets",
                                             name,
                                             f"runtime_protocol_{today(-1)}.txt"),
                                2)
        else:
            _, state = read_csv(os.path.join(app.config["PI_DATA"],
                                             "sockets",
                                             name,
                                             f"runtime_protocol_{today()}.txt"),
                                2)
        app.logger.info(f"[{name}] nothing to do here, socket is still"
                        f" {state}")
        switch_socket_logentry(time, name, state)


def switch_socket_logentry(time, name, state):
    # log to file
    logentry = f"{time},{state}\n"
    with open(os.path.join(app.config["PI_DATA"],
                           "sockets",
                           name,
                           f"runtime_protocol_{today()}.txt"),
              'a') as f:
        f.write(logentry)
        app.logger.info(f'[{name}] Add socket state to protocol file. Done.')


# read temperature sensor
if app.config["LOCAL_AIR"]:
    try:
        import Adafruit_DHT

        app.config.update(ADAFRUIT_LEGACY=True)
        app.logger.debug("Loaded legacy Adafruit_DHT package.")
    except ModuleNotFoundError:
        try:
            import adafruit_dht

            app.logger.debug("Loaded adafruit_dht package.")
        except ModuleNotFoundError:
            # TODO only use local air variable
            app.config["AIR_SENSOR"] = False
            app.logger.warning('Could not load an Adafruit DHT package to '
                               'fetch air sensor data. Sensor will not be '
                               'used.')

# read soil sensor
if app.config["LOCAL_SOIL"]:
    try:
        import RPi.GPIO as gpio
    except ModuleNotFoundError:
        app.config["SOIL_SENSOR"] = False
        app.logger.warning('Could not load RPi.GPIO package to fetch soil '
                           'sensor data. Sensor will not be used.')

# plot temperature sensor data
if app.name == "cave server" and app.config["SENSORS"]:
    try:
        import matplotlib

        matplotlib.use('Agg')  # headless
        from matplotlib import pyplot
        from matplotlib import ticker
    except ModuleNotFoundError:
        app.logger.warning('Could not load matplotlib package to generate '
                           'plots from sensor data. Ignore this warning if '
                           'you do not temperature sensors at all.')
    # access network pis via SSH
    try:
        import paramiko

        SSH_CONNECTION, FTP_CONNECTION = connect()
    except ModuleNotFoundError:
        app.logger.warning('Could not load paramiko package to access network '
                           'devices via SSH. Ignore this warning if you do '
                           'not use multiple raspberry pi devices with CAVE.')

if app.config["PIGLOW"]:
    try:
        import piglow

        piglow.auto_update = True
        piglow.clear_on_exit = True
        piglow.all(1)
        piglow.white(0)
        app.logger.debug("All PiGlow LEDs turned on.")
        # humidity shown with blue and green LEDs
        _HUM_LEDS = [4, 10, 16, 3, 9, 15]
        # temperature shown with yellow, orange and red LEDs
        _TEMP_LEDS = [2, 8, 14, 1, 7, 13, 0, 6, 12]
        _HUM_GLOW = list(zip(range(30, 90, 10), _HUM_LEDS))
        _TEMP_GLOW = list(zip(range(18, 27), _TEMP_LEDS))
    except ModuleNotFoundError:
        app.logger.warning('PiGlow is enabled but loading piglow package '
                           'failed. Check if it is installed.')
        app.config["PIGLOW"] = False
    except OSError:
        app.logger.warning('PiGlow is enabled but seems not to be mounted to '
                           'GPIO. Check hardware.')
        app.config["PIGLOW"] = False

API_URL = 'http://api.openweathermap.org/data/2.5/{}?{}={' \
          '}&units=metric&lang={}&appid={} '

######## WIND SPEED DESCRIPTIONS AND CONVERSIONS ##########
### https://www.skipperguide.de/wiki/Beaufort-Tabelle

WIND_BFT = {0: 'calm',
            1: 'light air',
            2: 'light breeze',
            3: 'gentle breeze',
            4: 'moderate breeze',
            5: 'fresh breeze',
            6: 'strong breeze',
            7: 'near gale',
            8: '(fresh) gale',
            9: 'strong gale',
            10: 'whole storm',
            11: 'severe storm',
            12: 'hurricane',
            }

BFT_SCALE = [0.3, 1.6, 3.4, 5.5, 8, 10.8, 13.9,
             17.2, 20.8, 24.5, 28.5, 32.7]

COMMANDS = {'uptime': 'uptime -p',
            'starttime': 'uptime -s',
            'mem': 'free -m',
            'cpu_name': 'cat /proc/cpuinfo',
            'os_info': 'cat /etc/os-release',
            'proc_info': 'nproc',
            'core_frequency': 'vcgencmd get_config arm_freq',
            'core_volt': 'vcgencmd measure_volts',
            'cpu_temp': 'vcgencmd measure_temp',
            }

SWITCH_POS = {"on": 1, "off": 0}
