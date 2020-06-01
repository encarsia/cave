# -*- coding: utf-8 -*-

# Set cronjob for processing daily data (statistics and plot)

from apscheduler.schedulers.background import BackgroundScheduler
from app import app, utils


def get_pis():
    """Return air sensor and remote devices as list"""
    air_pis = list()
    soil_pis = list()
    remote_pis = list()
    if not app.config["SENSORS"]:
        app.logger.info("The use of Raspberry Pi is disabled. Sensors, "
                        "protocol, statistics and plots will not be set up.")
        return False, False, False
    for name, pi in app.config["PI_LIST"].items():
        # more convenient than looping through all devices and catching more
        # exceptions
        if pi["air sensor"]:
            air_pis.append(name)
        if pi["soil sensor"]:
            soil_pis.append(name)
        if "address" in pi:
            remote_pis.append(name)
        else:
            pi.update({"address": False})
            if  pi["air sensor"]:
                # air sensor installed on the machine CAVE is running on
                # does not require a daemon cronjob (see "sensor_scripts")
                # set up temperature/humidity lookup via apscheduler
                # this should only be one
                app.config["LOCAL_AIR"] = {"name": name, "properties": pi}
            if pi["soil sensor"]:
                # soil sensor installed on the machine CAVE is running on
                # does not require a daemon cronjob (see "sensor_scripts")
                # set up data lookup via apscheduler
                # this should only be one device but can be multiple sensors
                app.config["LOCAL_SOIL"] = pi
    app.logger.info("Information of device and sensor settings received.")
    return air_pis, soil_pis, remote_pis


# initiate scheduler
sched = BackgroundScheduler()
sched.start()

air_pis, soil_pis, remote_pis = get_pis()

# data is completely messed up if scheduler is started simultaneously for
# different devices with a for...loop
# solution: start just one job and run the loop there for consecutive code
# execution

# if in test mode do not run as cron, just execute tasks, also avoids data
# struggle
if app.testing:

    if app.config["CAMERA"]:
        # take photo with camera and collect images from other devices
        app.logger.info(f"TEST MODE: shoot picture and collect images")
        utils.camera_daemon(app.config["PI_LIST"])

    # only in server mode, ignore if raspis not set
    if app.name == "cave server" and air_pis and remote_pis:
        # get sensor data from network devices at midnight
        app.logger.info("TEST MODE: Copy yesterday's sensor data file(s)")
        utils.get_sensor_data(remote_pis)

        # generate plot for air sensor data
        app.logger.info("TEST MODE: Generate daily plot(s) for "
                        "temperature/humidity data")
        utils.air_prot_plot(air_pis)

        if app.config["PIGLOW"] is not False and app.config["LOCAL_AIR"] != app.config["PIGLOW"]:
            # read PiGlow LED usage from data file
            app.logger.info(f"TEST MODE: PiGlow usage is set to show data "
                            f"from another device ({app.config['PIGLOW']}).")
            utils.piglow_daemon(app.config["PIGLOW"])

        if app.config["SOCKET_INTERVALS"]:
            app.logger.info(f"TEST MODE: temperature configured power socket")
            for name, socket in app.config["SOCKET_INTERVALS"].items():
                if "min" and "max" and "sensor" in socket:
                    utils.power_socket_temp_daemon(name,
                                                   socket["min"],
                                                   socket["max"],
                                                   socket["sensor"],
                                                   )

        if app.config["PIGLOW"] and soil_pis:
            # read PiGlow LED usage from data file
            app.logger.info(f"TEST MODE: PiGlow shows soil sensor data")
            utils.soil_piglow(soil_pis)


    # air sensor daemon for sensor running on the same machine as CAVE
    if app.config["LOCAL_AIR"]:
        app.logger.info("TEST MODE: Run air sensor daemon")
        utils.air_daemon(app.config["LOCAL_AIR"],
                         app.config["AIR_SENSOR"],
                         app.config["AIR_DATA_PIN"],
                         app.config["ADAFRUIT_LEGACY"],
                        )

    # soil sensor daemon for sensor running on the same machine as CAVE
    if app.config["LOCAL_SOIL"]:
        app.logger.info("TEST MODE: Run soil sensor daemon")
        utils.soil_daemon(app.config["LOCAL_SOIL"], app.config["SOIL_SENSORS"])
else:
    # air sensor daemon for sensor running on the same machine as CAVE
    if app.config["LOCAL_AIR"]:
        sched.add_job(
            func=utils.air_daemon,
            args=[app.config["LOCAL_AIR"],
                  app.config["AIR_SENSOR"],
                  app.config["AIR_DATA_PIN"],
                  app.config["ADAFRUIT_LEGACY"],
                 ],
            trigger="cron",
            minute="0-59",
            name="Run air sensor daemon",
        )

    # soil sensor daemon for sensor running on the same machine as CAVE
    if app.config["LOCAL_SOIL"]:
        sched.add_job(
            func=utils.soil_daemon,
            args=[app.config["LOCAL_SOIL"], app.config["SOIL_SENSORS"]],
            trigger="cron",
            hour=app.config["SOIL_INTVL"],
            name="Run soil sensor daemon",
        )

    # show soil sensor state on PiGlow
    if app.config["PIGLOW"] and soil_pis:
        # read PiGlow LED usage from data file
        utils.soil_piglow(soil_pis)
        sched.add_job(
            func=utils.soil_piglow,
            args=[soil_pis],
            trigger="cron",
            hour=app.config["SOIL_INTVL"],
            minute="30",
            name="Show soil sensor state on PiGlow",
        )

    # take photo on local device and collect remote images
    if app.config["CAMERA"]:
        sched.add_job(
            func=utils.camera_daemon,
            args=[app.config["PI_LIST"]],
            trigger="cron",
            minute="5,15,25,35,45,55",
            second="30",
            name="Collect camera images",
        )

    # only in server mode
    if app.name == "cave server":
        if app.config["SENSORS"]:
            # get sensor data from network devices at midnight
            sched.add_job(
                func=utils.get_sensor_data,
                args=[remote_pis],
                trigger="cron",
                hour="0",
                minute="1",
                name="Copy yesterday's sensor data file(s)",
            )

            # generate plot for air sensor data
            sched.add_job(
                func=utils.air_prot_plot,
                args=[air_pis],
                trigger="cron",
                hour="0",
                minute="3",
                name="Generate daily plot(s) for temperature/humidity data",
            )

        if app.config["PIGLOW"] is not False and app.config["LOCAL_AIR"] != app.config["PIGLOW"]:
            # read PiGlow LED usage from data file
            sched.add_job(
                func=utils.piglow_daemon,
                args=[app.config["PIGLOW"]],
                trigger="cron",
                minute="0-59",
                second="30",
                name=f"PiGlow usage is set to show data from {app.config['PIGLOW']}",
                max_instances=2,
            )

        if app.config["SOCKET_INTERVALS"]:
            # turn power sockets on/off
            for name, socket in app.config["SOCKET_INTERVALS"].items():
                # time interval
                if "start" and "stop" in socket:
                    sched.add_job(
                        func=utils.switch_power_socket,
                        args=[name, app.config["DEF_SWITCH"][name], "on"],
                        trigger="cron",
                        hour=socket["start"],
                        name=f"Switch {name} on",
                    )
                    sched.add_job(
                        func=utils.switch_power_socket,
                        args=[name, app.config["DEF_SWITCH"][name], "off"],
                        trigger="cron",
                        hour=socket["stop"],
                        name=f"Switch {name} off",
                    )
                elif "min" and "max" and "sensor" in socket:
                    # temp range, check every 10 minutes
                    sched.add_job(
                        func=utils.power_socket_temp_daemon,
                        args=[name, socket],
                        trigger="cron",
                        minute="0,10,20,30,40,50",
                        second="10",
                        name=f"Run power socket daemon of {name}",
                    )
                else:
                    app.logger.warning(f"{name} is not set up correctly. "
                                       f"Check the SOCKET_INTERVALS variable"
                                       f" in config.")

        # send daily report mail, only in server mode
        if app.config["SEND_MAIL"]:
            # only in server mode
            if app.name == "cave server":
                sched.add_job(
                    func=utils.send_daily_report,
                    args=[app.config["PI_LIST"]],
                    trigger="cron",
                    hour="1",
                    name="Send daily report mails",
                )
            sched.add_job(
                func=utils.send_daily_log,
                trigger="cron",
                hour="23",
                minute="59",
                name="Send daily log mail",
            )
        else:
            app.logger.debug("Sending e-mails is disabled.")
