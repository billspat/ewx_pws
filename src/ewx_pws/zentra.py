
# ZENTRA WIP

import json,pytz,time, logging
from requests import Session, Request
from datetime import datetime, timezone

from pydantic import Field
from ewx_pws.weather_stations import WeatherStationConfig, WeatherStationReading, WeatherStationReadings, WeatherStation, STATION_TYPE

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

    
    def __init__(self,config:ZentraConfig, max_retries : int = 0):
        self._max_retries : int = max_retries
        super().__init__(config)  

    @property
    def max_retries(self):
        return self._max_retries

    @max_retries.setter
    def name(self, value: int):
        self._max_retries = value

    def _check_config(self):
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
        
        self.current_response = Session().send(self.current_api_request)

        # Handles the 1 request/60 second throttling error
        retry_counter = 0
        while self.current_response.status_code == 429 and self.max_retries > 0:
            retry_counter += 1
            if retry_counter > self.max_retries:
                err_message = f"Zentra timed out {self.max_retries} times"
                raise RuntimeError(err_message) 

            lockout = int(self.current_response.text[self.current_response.text.find("Lock out expires in ")+20:self.current_response.text.find("Lock out expires in ")+22])
            
            logging.warning("Error received for too frequent attempts, retrying in {} seconds...".format(lockout+1))

            time.sleep(lockout + 1)

            self.current_response = Session().send(self.current_api_request)

        return([self.current_response])

    def _transform(self, data = None, request_datetime: datetime = None):
        """
        Transforms data into a standardized format and returns it as a WeatherStationReadings object.
        data param if left to default tries for self.response_data processing
        """
        readings_list = WeatherStationReadings()

        # Return an empty list if there is no data contained in the response, this covers error 429
        if 'data' not in data.keys():
            return readings_list
        
        # Build a ZentraReading object for each and put it into the readings_list
        for reading in data['data']['Air Temperature'][0]['readings']:
            temp = ZentraReading(station_id=data['data']['Air Temperature'][0]['metadata']['device_name'],request_datetime=request_datetime, data_datetime=reading['timestamp_utc'])
            temp.atemp = reading['value']
            timestamp = reading['timestamp_utc']
            for reading2 in data['data']['Precipitation'][0]['readings']:
                if reading2['timestamp_utc'] == timestamp:
                    temp.pcpn = reading2['value']
            for reading2 in data['data']['Relative Humidity'][0]['readings']:
                if reading2['timestamp_utc'] == timestamp:
                    temp.relh = reading2['value']
            readings_list.readings.append(temp)
            
        return readings_list
    
    def _handle_error(self):
        """ place holder to remind that we need to add err handling to each class"""
        pass

class ZentraReading(WeatherStationReading):
    station_id : str
    request_datetime : datetime or None = None # UTC
    data_datetime : datetime           # UTC
    atemp : float or None = None       # celsius 
    pcpn : float or None = None        # mm, > 0
    relh : float or None = None        # percent
