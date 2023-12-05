
import json,pytz
from requests import get, Session, Request
from datetime import datetime, timezone

from pydantic import Field
from weather_stations.weather_station import WeatherStationConfig, WeatherStation, STATION_TYPE

class SpectrumConfig(WeatherStationConfig):
        station_type   : STATION_TYPE = 'SPECTRUM'
        sn             : str #  The station identifier. 
        apikey         : str #  The user's API access key.  

class SpectrumStation(WeatherStation):
    """ for Spectrum weather stations"""
    StationConfigClass = SpectrumConfig
    station_type = 'SPECTRUM'
    
    # time between readings in minutes for this station type
    interval_min = 5


    @classmethod
    def init_from_dict(cls, config:dict):
        """ accept a dictionary to create this class, rather than the Type class"""

        # this will raise error if config dictionary is not correct
        station_config = SpectrumConfig.model_validate(config)
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
        
        # convert UTC date to timezone of station for request
        # use the converter in config obj to get python-friendly tz string
        dt = dt.replace(tzinfo=timezone.utc).astimezone(pytz.timezone(self.config.pytz()))
 
        return(dt.strftime('%m-%d-%Y %H:%M'))
    
    def _get_readings(self,start_datetime:datetime, end_datetime:datetime):
        """ request weather data from the specconnect API for a range of dates
        
        parameters:
            start_datetime: datetime object in UTC timezone.  
            end_datetime: datetime object in UTC timezone.  
        """
        start_datetime_str = self._format_time(start_datetime)
        end_datetime_str = self._format_time(end_datetime)
        
        response = get( url='https://api.specconnect.net:6703/api/Customer/GetDataInDateTimeRange',
                        params={'customerApiKey': self.config.apikey, 
                                'serialNumber': self.config.sn,
                                'startDate': start_datetime_str, 
                                'endDate': end_datetime_str}
                        )
        
        return(response)

    def _transform(self, response_data):
        """
        Transforms data into a standardized format and returns it as a WeatherStationReadings object.
        data param if left to default tries for self.response_data processing
        """
        
        if isinstance(response_data,str):
            response_data = json.loads(response_data)

        if 'EquipmentRecords' not in response_data.keys():
            return []
        
        readings = []
        for record in response_data['EquipmentRecords']:
            reading = { 'data_datetime': self.dt_utc_from_str(record['TimeStamp']),
                        'atemp': round((record['SensorData'][1]["DecimalValue"] - 32) * 5 / 9, 2),
                        'pcpn' : round(record['SensorData'][0]["DecimalValue"] * 25.4, 2),
                        'relh' : round(record['SensorData'][2]["DecimalValue"], 2)
            }

            readings.append(reading)

        return readings

    def _handle_error(self):
        """ place holder to remind that we need to add err handling to each class"""
        pass

