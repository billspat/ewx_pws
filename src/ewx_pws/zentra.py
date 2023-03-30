
# ZENTRA WIP

import json,pytz
from requests import Session, Request
from datetime import datetime, timezone

from pydantic import Field
from ewx_pws.weather_stations import WeatherStationConfig, WeatherStation, STATION_TYPE

class ZentraConfig(WeatherStationConfig):
        station_id     : str
        station_type   : STATION_TYPE = 'ZENTRA'
        sn             : str #  The serial number of the device.
        token          : str # The user's access token.
        tz             : str = 'ET' #  The time zone.  Defaults to Eastern Time.

class ZentraStation(WeatherStation):
    @classmethod
    def init_from_dict(cls, config:dict):
        """ accept a dictionary to create this class, rather than the Type class"""

        # this will raise error if config dictionary is not correct
        station_config = ZentraConfig.parse_obj(config)
        return(cls(station_config))

    
    def __init__(self,config:ZentraConfig):
        super().__init__(config)  
        
    def _check_config(self,start_datetime, end_datetime):
        return True
    
    def _get_readings(self, start_datetime:datetime, end_datetime:datetime, token, start_mrid=None, end_mrid=None):
        """ Builds, sends, and stores raw response from Zentra API"""

        self.current_api_request = Request('GET',
                               url='https://zentracloud.com/api/v3/get_readings',
                               headers={
                                   'Authorization': "Token " + self.config.token},
                               params={'device_sn': self.config.sn,
                                       'start_date': self.config.start_datetime,
                                       'end_date': self.config.end_datetime,
                                       'start_mrid': self.config.start_mrid,
                                       'end_mrid': self.config.end_mrid}).prepare()
        
        api_response = Session().send(self.current_api_request)

        return(api_response)

    
    def _handle_error(self):
        """ place holder to remind that we need to add err handling to each class"""
        pass
