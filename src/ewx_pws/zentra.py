# ZENTRA WIP ###################

import json
from requests import Session, Request
from datetime import datetime, timezone

from pydantic import Field
from ewx_pws.weather_stations import WeatherStationConfig, WeatherStation

class ZentraConfig(WeatherStationConfig):
    station_type : str = 'ZENTRA'
    username : str = None
    sid : str = Field(description="Site id, assigned by Rainwise.")
    pid : str = Field(description="Password id, assigned by Rainwise.")
    mac : str = Field(description="MAC of the weather station. Must be in the group assigned to username.")
    ret_form : str = Field(description="Values xml or json; returns the data as JSON or XML.")
    sensor_sn : dict[str,str] = Field(description="A dict of sensor serial numbers.  Defaults to None.")
    
    # access_token : str = Field('', description="needed for api auth, filled in by auth request ")
    
    # TODO class ZentraSensor() of elements in sensor_sn


class ZentraStation(WeatherStation):
    """ config is ZentraConfig type """
    @classmethod
    def init_from_dict(cls, config:dict):
        """ accept a dictionary to create this class, rather than the Type class"""

        # this will raise error if config dictionary is not correct
        station_config = ZentraConfig.parse_obj(config)
        return(cls(station_config))

    def __init__(self,config: ZentraConfig):
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
        self.request = Request('GET',
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
