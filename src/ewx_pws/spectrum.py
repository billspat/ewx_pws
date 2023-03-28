
import json,pytz
from requests import Session, Request
from datetime import datetime, timezone

from pydantic import Field
from ewx_pws.weather_stations import WeatherStationConfig, WeatherStation, STATION_TYPE

class SpectrumConfig(WeatherStationConfig):
        station_id     : str
        station_type   : STATION_TYPE = 'SPECTRUM'
        sn             : str #  The station identifier. 
        apikey         : str #  The user's API access key.  
        tz             : str = 'ET' #  The time zone.  Defaults to Eastern Time.

class SpectrumStation(WeatherStation):
    @classmethod
    def init_from_dict(cls, config:dict):
        """ accept a dictionary to create this class, rather than the Type class"""

        # this will raise error if config dictionary is not correct
        station_config = SpectrumConfig.parse_obj(config)
        return(cls(station_config))

    
    def __init__(self,config:SpectrumConfig):
        super().__init__(config)  
        
    def _check_config(self,start_datetime, end_datetime):
        return True
    
    def _format_time(self, dt:datetime)->str:
        """
        format date/time parameter for specconnect API request
        Spectrum API expects local time (zone) of the station's location for its `startDate` and `endDate`

        '%m-%d-%Y %H:%M'
        """
        
        # if dt has a time zone
        
        dt = dt.replace(tzinfo=timezone.utc).astimezone(pytz.timezone(self.tzlist[self.config.tz]))
        # convert to ET
        
        # otherwise assume it's UTC. 
        return(dt.strftime('%m-%d-%Y %H:%M'))
    
    def _get_readings(self,start_datetime, end_datetime):
        """ request weather data from the specconnect API for a range of dates"""
        start_datetime_str = self._format_time(start_datetime)
        end_datetime_str = self._format_time(end_datetime)
        
        self.current_api_request = Request('GET',
                                   url='https://api.specconnect.net:6703/api/Customer/GetDataInDateTimeRange',
                                   params={'customerApiKey': self.config.apikey, 'serialNumber': self.config.sn,
                                           'startDate': start_datetime_str, 'endDate': end_datetime_str}).prepare()
        
        api_response = Session().send(self.current_api_request)

        return(api_response)

    
    def _handle_error(self):
        """ place holder to remind that we need to add err handling to each class"""
        pass
