# DAVIS WIP

import collections, hashlib, hmac
import json,pytz
from requests import Session, Request
from datetime import datetime, timezone

from pydantic import Field
from ewx_pws.weather_stations import WeatherStationConfig, WeatherStation, STATION_TYPE

class DavisConfig(WeatherStationConfig):
        station_id     : str
        station_type   : STATION_TYPE = 'DAVIS'
        sn             : str #  The serial number of the device.
        apikey         : str # The user's API access key. 
        apisec         : str # API security that is used to compute the hash.
        tz             : str = 'ET' #  The time zone.  Defaults to Eastern Time.

class DavisStation(WeatherStation):
    @classmethod
    def init_from_dict(cls, config:dict):
        """ accept a dictionary to create this class, rather than the Type class"""

        # this will raise error if config dictionary is not correct
        station_config = DavisConfig.parse_obj(config)
        return(cls(station_config))

    
    def __init__(self,config:DavisConfig):
        self.apisig = None
        super().__init__(config)  
        
    def _check_config(self,start_datetime, end_datetime):
        return True
    
    def _get_readings(self, start_datetime:datetime, end_datetime:datetime):
        """ Builds, sends, and stores raw response from Davis API"""
        t = int(datetime.now().timestamp())

        self._compute_signature(t, start_datetime, end_datetime)
        self.current_api_request = Request('GET',
                               url='https://api.weatherlink.com/v2/historic/' + self.config.sn,
                               params={'api-key': self.config.apikey,
                                       't': t,
                                       'start_date': start_datetime,
                                       'end_date': end_datetime,
                                       'api-signature': self.apisig}).prepare()
        
        api_response = Session().send(self.current_api_request)


    def _compute_signature(self, t, start_datetime:datetime, end_datetime:datetime):
        """
        This method computes the API signature used to call the Davis API via the nested function compute_signature_engine.
        """
        def compute_signature_engine():  # compute_engine
            """
            This method computes the API signature used to call the Davis API.

            Returns
            -------
            sig : HMAC
                  A hash based message authentication code. 
            """

            data = ""
            for key in params:
                data = data + key + str(params[key])

            sig = hmac.new(
                self.config.apisec.encode('utf-8'),
                data.encode('utf-8'),
                hashlib.sha256).hexdigest()
            return sig

        if start_datetime and end_datetime:
            params = {'api-key': self.config.apikey,
                        'station-id': self.config.sn,
                        't': t,
                        'start-timestamp': start_datetime,
                        'end-timestamp': end_datetime}
            params = collections.OrderedDict(sorted(params.items()))
            self.apisig = compute_signature_engine()
        else:
            params = {'api-key': self.config.apikey, 'station-id': self.config.sn, 't': self.config.t}
            params = collections.OrderedDict(sorted(params.items()))
            self.apisig = compute_signature_engine()

        return self.apisig
    def _handle_error(self):
        """ place holder to remind that we need to add err handling to each class"""
        pass
