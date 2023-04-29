# DAVIS WIP

import collections, hashlib, hmac
import json,pytz
from requests import Session, Request
from datetime import datetime, timezone

from pydantic import Field
from ewx_pws.weather_stations import WeatherStationConfig, WeatherStationReading, WeatherStationReadings, WeatherStation, STATION_TYPE

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

    def _get_readings(self, start_timestamp:int, end_timestamp:int):
        """ 
        Builds, sends, and stores raw response from Davis API
        NOTE: Conversion from datetime to unix timestamp is done before the function, in
        """
        t = int(datetime.now().timestamp())

        self._compute_signature(t=t, start_timestamp=start_timestamp, end_timestamp=end_timestamp)
        self.current_api_request = Request('GET',
                               url='https://api.weatherlink.com/v2/historic/' + self.config.sn,
                               params={'api-key': self.config.apikey,
                                       't': t,
                                       'start-timestamp': start_timestamp,
                                       'end-timestamp': end_timestamp,
                                       'api-signature': self.apisig}).prepare()
        
        self.request_datetime = datetime.utcnow()
        self.current_response = Session().send(self.current_api_request)
        
        self.response_data = json.loads(self.current_response.content)
        return self.current_response

    def _compute_signature(self, t:int, start_timestamp:int, end_timestamp:int):
        """
        This method computes the API signature used to call the Davis API historic endpoint.
        NOTE: datetimes should be in unix timestamp format already
        More info on this process can be found at https://weatherlink.github.io/v2-api/api-signature-calculator
        """

        msg = 'api-key{}end-timestamp{}start-timestamp{}station-id{}t{}'.format(self.config.apikey,end_timestamp,start_timestamp,self.config.sn,t)
        self.apisig = hmac.new(
            self.config.apisec.encode('utf-8'),
            msg.encode('utf-8'),
            hashlib.sha256).hexdigest()
        return self.apisig

    def _transform(self):
        """
        Transforms data into a standardized format and returns it as a WeatherStationReadings object.
        """
        readings_list = WeatherStationReadings()

        if 'sensors' not in self.response_data.keys():
            return readings_list
        for lsid in self.response_data['sensors']:
            for record in lsid['data']:
                if 'temp_out' in record.keys():
                    temp = DavisReading(station_id=self.response_data['station_id'],
                                    request_datetime=self.request_datetime,
                                    data_datetime=datetime.utcfromtimestamp(record['ts']),
                                    atemp=round((record['ts'] - 32) * 5 / 9, 2),
                                    pcpn=round(record['rainfall_mm'] * 25.4, 2),
                                    relh=round(record['hum_out'], 2))
                    readings_list.readings.append(temp)

        return readings_list

    def _handle_error(self):
        """ place holder to remind that we need to add err handling to each class"""
        pass

class DavisReading(WeatherStationReading):
        station_id : str
        request_datetime : datetime or None = None # UTC
        data_datetime : datetime           # UTC
        atemp : float or None = None       # celsius 
        pcpn : float or None = None        # mm, > 0
        relh : float or None = None        # percent
