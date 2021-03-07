#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import shutil
import sys
import urllib.request
import urllib.parse
import yaml

try:
    import paramiko
    check_ssh = True
except ModuleNotFoundError:
    print("\nWARNING: SSH connection can not be checked, install paramiko package first.")
    check_ssh = False


########################################################################
###
### This is the configuration check tool for CAVE.
###
### It cannot be guaranteed that successfully passing this your config
### will work flawlessly. If so it's highly probable to be my fault and
### I take full responsibility and will resign from all duties. In the
### meantime feel free to contact me.
###
########################################################################

HEADER = """
---------------------
|                   |
| CAVE CONFIG CHECK |
|                   |
---------------------"""

MODULES = [["Sensors", "SENSORS", None, "raspi"],
           ["Weather", "WEATHER", None, "weather"],
           ["Remote Power Switches", "REMOTE_POWER", None, "remote"],
           ["PiGlow add-on board", "PIGLOW", None, "piglow"],
           ["Kettlebattle Generator", "KETTLEBATTLE", None, "kbgen"],
          ]

#######################
###     MODULES     ###
#######################

def check_modules():
    mods = []
    print(section_header("modules", "#"))
    for num, item in enumerate(MODULES):
        modname, varname, _, _ = item
        try:
            var = c[varname]
            if isinstance(var, bool):
                print("{} set to {}. OK.".format(modname, var))
                MODULES[num][2] = var
                mods.append(var)
            else:
                print(var_inst_error(modname, varname, "bool"))
        except AttributeError:
            print(attr_error(modname, varname))
    return mods

############################
###     RASPBERRY PI     ###
############################

def raspi(mod):
    print(section_header(mod))
    # check sensor data path
    try:
        # check filetype
        if not isinstance(c["APP_DATA"], str):
            print(var_inst_error("data storage", "APP_DATA", "str"))
            return
        # create subfolder if not already existing
        check_dir(c["APP_DATA"], "data storage")
    except NameError:
        print(attr_error("data storage", "APP_DATA"))
    # check PI_LIST type
    try:
        if not isinstance(c["PI_LIST"], dict):
            print(var_inst_error("Raspberry Pi list", "PI_LIST", "dict"))
            return
    except NameError:
        print(attr_error("Raspberry Pi list", "PI_LIST"))

    pinames = []
    for pi in c["PI_LIST"]:
        print(section_header(pi, "~"))
        if not isinstance(c["PI_LIST"][pi], dict):
            print(var_inst_error("RPi in list", "PI_LIST[pi]", "dict"))
            return
        check_dir(os.path.join(c["APP_DATA"], pi), f"{pi} subfolder")
        check_dir(os.path.join(c["APP_DATA"], pi, "sensor_air"),
                  f"{pi} air sensor subfolder")
        check_dir(os.path.join(c["APP_DATA"], pi, "sensor_soil"),
                  f"{pi} soil sensor subfolder")
        check_dir(os.path.join("app", "static", "plots", pi),
                  f"{pi} static files subfolder")

        # check for duplicate pi names
        if pi in pinames:
            print("ERROR IN CONFIG: duplicate Raspberry Pi name:\n\tchoose "
                  "unique label")
            continue
        pinames.append(pi)
        # check for soil sensor
        try:
            if not isinstance(c["PI_LIST"][pi]["soil sensor"], bool):
                print(var_inst_error("soil sensor",
                                     "PI_LIST[pi][\"soil sensor\"]",
                                     "bool"))
            else:
                # check pots if soil sensor is enabled
                if c["PI_LIST"][pi]["soil sensor"]:
                    if not isinstance(c["PI_LIST"][pi]["pots"], list):
                        print("WARNING: soil sensor requires additional variable")
                        print(var_inst_error("plants",
                                             "PI_LIST[pi][\"pots\"]",
                                             "list"))
                    else:
                        print(f"INFO: soil sensor(s) configured ("
                              f"{c['PI_LIST'][pi]['pots']}).")
                else:
                    print("INFO: soil sensor configured.")

        except (NameError, KeyError):
            print(attr_error("soil sensor", "PI_LIST[pi][\"soil sensor\"]"))
        # check for air sensor
        try:
            if not isinstance(c["PI_LIST"][pi]["air sensor"], bool):
                print(var_inst_error("air sensor",
                                     "PI_LIST[pi][\"air sensor\"]",
                                     "bool"))
            else:
                print("INFO: air sensor configured.")
        except (NameError, KeyError):
            print(attr_error("air sensor", "PI_LIST[pi][\"air sensor\"]"))
        # connect to network devices and download data files if available
        if "address" in c["PI_LIST"][pi] != "" and check_ssh:
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            try:
                ssh_client.connect(hostname=c["PI_LIST"][pi]["address"],
                                   username=c["PI_LIST"][pi]["username"],
                                   password=c["PI_LIST"][pi]["password"],
                                   )
                # download available data from network devices
                ftp_client = ssh_client.open_sftp()
                print("INFO: SSH connection established. OK.")
                try:
                    ftp_client.chdir(os.path.join(c["PI_LIST"][pi]["installdir"],
                                                  c["APP_DATA"],
                                                  pi)
                                     )
                except FileNotFoundError:
                    print("ERROR: no access to path. Check installdir/name.")
                    return
                counter = 0
                for sub in ["sensor_air", "sensor_soil"]:
                    try:
                        for f in ftp_client.listdir(sub):
                            try:
                                ftp_client.get(os.path.join(sub, f),
                                               os.path.join(c["APP_DATA"],
                                                            pi,
                                                            sub,
                                                            f,
                                                            )
                                               )
                                counter += 1
                            except FileNotFoundError:
                                print(f"INFO: No files here ({sub}). OK.")
                    except FileNotFoundError:
                        print(f"INFO: No sub {sub} here. OK.")
                print(f"INFO: downloaded {counter} data files from network "
                      f"device.")
                ftp_client.close()
                ssh_client.close()
            except (paramiko.ssh_exception.AuthenticationException,
                    paramiko.ssh_exception.NoValidConnectionsError) as e:
                print(f"ERROR TRYING TO ESTABLISH A SSH CONNECTION:\n\t{e}")
    # copy plots to static folder
    print("\nINFO: copy existing plots to static folder...")
    for pi in c["PI_LIST"]:
        for path, sub, files in os.walk(os.path.join(c["APP_DATA"], pi)):
            for f in files:
                if f.endswith(".png"):
                    shutil.copy(os.path.join(path, f),
                                os.path.join("app", "static", "plots", pi, f))

#######################
###     WEATHER     ###
#######################

def weather(mod):
    print(section_header(mod))
    try:
        url = "http://api.openweathermap.org/data/2.5/weather?id={}&appid={}".format(c["LOCATION_ID"], c["APPID"])
        data = urllib.request.urlopen(url).read().decode('utf-8')
        parsed = json.loads(data)
        citycode = "{},{}".format(parsed['name'], parsed['sys']['country'])
        print("""Location ID {} matches {}.""".format(c["LOCATION_ID"], citycode))
    except AttributeError:
        print("""WARNING: no location id given
\ttry by city name...""")
        try:
            if isinstance(c["LOCATION"], str):
                print("Location is set to '{}'.".format(c["LOCATION"]))
            else:
                print(var_inst_error("location", "LOCATION", "string"))
        except AttributeError:
            print(attr_error("location", "LOCATION or LOCATION_ID"))
            return
    except urllib.error.HTTPError:
        print("""ERROR IN CONFIG: location id is definitely wrong
\tcorrect id or try with city name""")
        return
    try:
        print("Language is set to {}.".format(c["LANGUAGE"]))
    except AttributeError:
        print("Language variable not set, English will be used.")
    try:
        print("Weathermap.com app ID is '{}'.".format(c["APPID"]))
    except AttributeError:
        print(attr_error("weathermap.com app ID", "APPID"))
        return

###############################################
###     RADIO CONTROLLED POWER SWITCHES     ###
###############################################

def remote(mod):
    print(section_header(mod))
    try:
        if os.path.isdir(c["RR_PATH"]):
            print("Path to raspberry-remote is '{}'.".format(c["RR_PATH"]))
        else:
            print("""ERROR IN CONFIG: cannot find raspberry-remote installation:
\tgive relative path to installation dir.""")
    except AttributeError:
        print(attr_error("path to raspberry-remote", "RR_PATH"))
        return
    # check def switch var type
    try:
        if not isinstance(c["DEF_SWITCH"], dict):
            print(var_inst_error("power socket definition list", "DEF_SWITCH", "dict"))
            return
    except NameError:
        print(attr_error("power socket definition list", "DEF_SWITCH"))
        return
    check_dir(os.path.join(c["APP_DATA"], "sockets"), f"socket subfolder")
    # check switch entries
    for name, switch in c["DEF_SWITCH"].items():
        if not isinstance(switch, dict):
            print(attr_error("power socket definition", name))
            continue
        elif not ("systemCode" and "unitCode") in switch:
            print(switch_error(name))
            continue
        print(f"INFO: socket {name} configured (systemCode {switch['systemCode']}, unitCode {switch['unitCode']})")
        check_dir(os.path.join(c["APP_DATA"], "sockets", name), f"{name} socket subfolder")

    try:
        if not isinstance(c["SOCKET_INTERVALS"], dict):
            print("INFO: if you want to set temp or time ranges set the SOCKET_INTERVALS variable")
            # print(var_inst_error("power socket scheduler", "SOCKET_INTERVALS", "dict"))
            return
    except NameError:
        print(attr_error("power socket scheduler", "SOCKET_INTERVALS"))
        return
    for name, switch in c["SOCKET_INTERVALS"].items():
        if not isinstance(switch, dict):
            print(attr_error("power socket definition", "DEF_SWITCH"))
            continue
        elif ("start" and "stop") in switch:
            print(f"INFO: socket interval of {name} configured to start at {switch['start']}:00 and stop at {switch['stop']}:00)")
            continue
        elif ("min" and "max" and "sensor") in switch:
            print(f"INFO: socket interval of {name} configured to a temperature range from\n"
                  f"\t{switch['min']}°C to {switch['max']}°C from the sensor at {switch['sensor']}")
            continue
        print(interval_error(name))


######################################
###     KETTLEBATTLE GENERATOR     ###
######################################

def kbgen(mod):
    print(section_header(mod))
    try:
        if isinstance(c["MAX_EX"], int):
            print("INFO: Maximum number of exercises (presets not included) set to "
                  "{}.".format(c["MAX_EX"]))
        else:
            print(var_inst_error("maximum number of exercises",
                                 "MAX_EX",
                                 "int"))
    except AttributeError:
        print(attr_error("maximum number of exercises", "MAX_EX"))
    try:
        if isinstance(c["REPS_PRESET"], str):
            presets = [int(x) for x in c["REPS_PRESET"].split(",")]
            print(f"INFO: Preset buttons are set to {presets[0]} and {presets[1]}")
    except:
        print(var_inst_error("workout repetition presets",
                             "REPS_PRESET",
                             "string of two integers separated by a comma"))
    try:
        if not isinstance(c["KB_EX"], dict):
            print(var_inst_error("exercise definitions", "KB_EX", "dict"))
            return
    except NameError:
        print(attr_error("exercise definitions", "KB_EX"))
        return
    # check switch entries
    for ex, val in c["KB_EX"].items():
        try:
            presets = [int(x) for x in val.split(",")]
            print(f"INFO: exercise {ex} is set to {presets[0]} and {presets[1]}")
        except:
            print(var_inst_error("exercise repetition presets",
                                 ex,
                                 "string of two integers separated by a comma"))


###################################
###     PIGLOW ADD-ON BOARD     ###
###################################

def piglow(mod):
    print(section_header(mod))
    try:
        import piglow
        piglow.auto_update = True
        piglow.clear_on_exit = False
        piglow.all(50)
    except ModuleNotFoundError:
        print("ERROR IN CONFIG: PiGlow is not set to False but cannot load "
              "package.")

#########################################
#########################################
#########################################

def section_header(sec, char="*"):
    underline = char*(len(sec)+9)
    txt = """
Checking {}
{}
""".format(sec, underline)
    return txt


def check_dir(path, info):
    if not os.path.isdir(path):
        os.makedirs(path)
        print("INFO: Created path for {} at {}. OK.".format(info, path))
    else:
        print("INFO: Path for {} exists. OK.".format(info))


def var_inst_error(name, var, vartype):
    txt = """ERROR IN CONFIG: {} set incorrectly:
\tvariable '{}' must be {}""".format(name, var, vartype)
    return txt


def list_error(what, item, var):
    txt = """ERROR IN CONFIG: malformed {} list item
\tconfig: {}
\t'{}' is wrong""".format(what, item, var)
    return txt


def switch_error(s):
    txt = """ERROR IN CONFIG: malformed switch
\tconfig: {}
\tswitch definition must be a dictionary containing a
\tsystemCode and unitCode value""".format(s)
    return txt

def interval_error(s):
    txt = """ERROR IN CONFIG: malformed socket interval
\tconfig: {}
\tsocket intervals must be a dictionary containing either start and stop
\tor min, max and sensor values""".format(s)
    return txt


def attr_error(attr, var):
    txt = "ERROR IN CONFIG: {} not set:\n\tvariable '{}' must be set".format(attr, var)
    return txt


def load_conf(filename):
    try:
        with open(f"{filename}.yaml") as f:
            try:
                config = yaml.load(f, Loader=yaml.FullLoader)
            except AttributeError:
                # FullLoader available for PyYaml 5.1+
                config = yaml.load(f)
            print("\nConfiguration read from YAML file.")
    except FileNotFoundError:
        try:
            conf_module = __import__(filename)
            # import filename as config
            config = dict()
            for setting in dir(conf_module):
                if setting.isupper():
                    config[setting] = getattr(conf_module, setting)
            print("\nConfiguration read from Python file.")
        except ModuleNotFoundError:
            print("Error while reading configuration. No configuration "
                  "file given, provide YAML or Python file.")
            raise SystemExit
    return config


def load_defaults():
    with open(os.path.join("app", "default.cfg")) as f:
        try:
            config = yaml.load(f, Loader=yaml.FullLoader)
        except AttributeError:
            # FullLoader available for PyYaml 5.1+
            config = yaml.load(f)
    return config


if __name__ == '__main__':
    print(HEADER)
    c = load_defaults()
    args = sys.argv
    if len(args) == 1:
        print("Try to read server configuration...")
        c.update(load_conf("server_conf"))
    elif len(args) == 2:
        if args[1] == "-c":
            print("Try to read client configuration...")
            c.update(load_conf("client_conf"))
            if c["NAME"]:
                c.update(SENSORS=True)
            c.update(PI_LIST={c["NAME"]: {'air sensor': c["AIR_SENSOR"],
                                          'plot axis': c["PLOT_AXIS"],
                                          'soil sensor': c["SOIL_SENSOR"],
                                          'pots': c["POTS"],
                                          },
                              }
                     )
        else:
            c.update(load_conf(args[1].split(".")[0]))
    else:
        print("Too many arguments given.")
    modules_configured = check_modules()
    if True in modules_configured:
        for modname, varname, value, func in MODULES:
            if value:
                exec("{}('{}')".format(func, modname))
        # also create log folder
        check_dir("logs", "logfiles directory")

    else:
        print("""
NO MODULES CONFIGURED.
\tCheck whether the given file does exist or is a configuration file at all.
\tThere is no point in running CAVE. Bye.""")
    print("\nThis is the end.")
