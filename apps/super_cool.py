import appdaemon.plugins.hass.hassapi as hass
from appdaemon.appdaemon import AppDaemon


class SmartCool(hass.Hass):
    def __init__(self, ad: AppDaemon, name, logging, args, config, app_config, global_vars):
        super().__init__(ad, name, logging, args, config, app_config, global_vars)
        self.cooldown_handle = None

    def initialize(self):
        self.log(self.args["thermostats"])
        climate = self.get_entity("climate.system_zone_1")

        start_time = self.parse_time(self.args["start_time"])
        end_time = self.parse_time(self.args["end_time"])

        self.run_daily(self.start_cooldown, start_time)
        self.run_daily(self.stop_cooldown, end_time)

        for key in climate.attributes:
            self.log('key: {0}, value: {1}'.format(key, str(climate.attributes[key])))

    def start_cooldown(self, kwargs):
        self.log("starting cooldown...")
        self.cooldown_handle = self.run_every(self.cooldown, "now", 5 * 60)

    def cooldown(self, kwargs):
        self.log("checking temp")
        climate = self.get_entity(self.args["thermostats"])
        demand = climate.attributes['demand']
        current_temp = int(climate.attributes['current_temperature'])
        set_temp = int(climate.attributes['temperature'])
        max_low_temp = int(self.args['low_temperature'])

        self.log('set temp: {0}, current temp: {1}, low temp: {2}, demand: {3}'.format(set_temp,
                                                                                       current_temp,
                                                                                       max_low_temp,
                                                                                       demand))
        if set_temp > max_low_temp:
            new_set_temp = set_temp
            if demand >= 70:
                new_set_temp = set_temp + 1
            elif demand < 50:
                new_set_temp = current_temp - 1

            climate.call_service("set_temperature", temperature=new_set_temp)
            
    def stop_cooldown(self, kwargs):
        self.log("stopping cooldown...")
        climate = self.get_entity(self.args["thermostats"])
        end_time_temp = self.args['end_time_temperature']
        climate.call_service("set_temperature", temperature=end_time_temp)

        # Stop the timer that is checking every X minutes
        self.cancel_timer(self.cooldown_handle)
