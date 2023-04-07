
# ZENTRA WIP

import json,pytz,time
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
        self.retry_on_throttle : bool = False
        super().__init__(config)  
        
    def _check_config(self,start_datetime, end_datetime):
        return True
    
    def _get_readings(self, start_datetime:datetime, end_datetime:datetime, start_mrid=None, end_mrid=None):
        """ Builds, sends, and stores raw response from Zentra API"""

        self.current_api_request = Request('GET',
                               url='https://zentracloud.com/api/v3/get_readings',
                               headers={
                                   'Authorization': "Token " + self.config.token},
                               params={'device_sn': self.config.sn,
                                       'start_date': start_datetime,
                                       'end_date': end_datetime,
                                       'start_mrid': start_mrid,
                                       'end_mrid': end_mrid}).prepare()
        
        api_response = Session().send(self.current_api_request)

        # Handles the 1 request/60 second throttling error
        if api_response.status_code == 429 and self.retry_on_throttle == True:
            
            lockout = int(api_response.text[api_response.text.find("Lock out expires in ")+20:api_response.text.find("Lock out expires in ")+22])
            
            print("Error received for too frequent attempts, retrying in {} seconds...".format(lockout+1))

            time.sleep(lockout + 1)

            return self._get_readings(start_datetime,end_datetime,start_mrid,end_mrid)
        
        return(api_response)

    
    def _handle_error(self):
        """ place holder to remind that we need to add err handling to each class"""
        pass
