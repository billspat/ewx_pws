# RAINWISE WIP ###################

import json
from requests import Session, Request
from datetime import datetime, timezone

from ewx_pws.weather_stations import WeatherStationConfig, WeatherStation, STATION_TYPE

class RainwiseConfig(WeatherStationConfig):
        station_id     : str
        station_type   : STATION_TYPE = 'RAINWISE'
        username       : str = None
        sid            : str # Site id, assigned by Rainwise.
        pid            : str # Password id, assigned by Rainwise.
        mac            : str # MAC of the weather station. Must be in the group assigned to username.
        ret_form       : str # Values xml or json; returns the data as JSON or XML.
        tz             : str = 'ET'

class RainwiseStation(WeatherStation):
    """ config is RainwiseConfig type """
    @classmethod
    def init_from_dict(cls, config:dict):
        """ accept a dictionary to create this class, rather than the Type class"""

        # this will raise error if config dictionary is not correct
        station_config = RainwiseConfig.parse_obj(config)
        return(cls(station_config))

    def __init__(self,config: RainwiseConfig):
        """ create class from config Type"""
        super().__init__(config)

    def _check_config(self):
        # TODO implement 
        return(True)

    def _get_readings(self, start_datetime:datetime, end_datetime:datetime, 
                      interval:int = 1):
        """
        Params are start time, end time, and interval.
        Returns raw api response.
        """
        self.current_api_request = Request('GET',
                               url='http://api.rainwise.net/main/v1.5/registered/get-historical.php',
                               params={'username': self.config.username,
                                       'sid': self.config.sid,
                                       'pid': self.config.pid,
                                       'mac': self.config.mac,
                                       'format': self.config.ret_form,
                                       'interval': interval,
                                       'sdate': start_datetime,
                                       'edate': end_datetime}).prepare()
        api_response = Session().send(self.current_api_request)
        return(api_response)

    def _handle_error(self):
        """ place holder to remind that we need to add err handling to each class"""
        pass
