
import json,pytz
from requests import Session, Request
from datetime import datetime, timezone

from pydantic import Field
from ewx_pws.weather_stations import WeatherStationConfig, WeatherStationReading, WeatherStationReadings, WeatherStation, STATION_TYPE

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
    
    def _get_readings(self,start_datetime:datetime, end_datetime:datetime):
        """ request weather data from the specconnect API for a range of dates"""
        start_datetime_str = self._format_time(start_datetime)
        end_datetime_str = self._format_time(end_datetime)
        
        self.current_api_request = Request('GET',
                                   url='https://api.specconnect.net:6703/api/Customer/GetDataInDateTimeRange',
                                   params={'customerApiKey': self.config.apikey, 'serialNumber': self.config.sn,
                                           'startDate': start_datetime_str, 'endDate': end_datetime_str}).prepare()
        self.request_datetime = datetime.utcnow()
        self.current_response = Session().send(self.current_api_request)
        
        self.response_data = json.loads(self.current_response.content)
        return(self.current_response)

    def _transform(self):
        """
        Transforms data into a standardized format and returns it as a WeatherStationReadings object.
        """
        readings_list = WeatherStationReadings()

        if 'EquipmentRecords' not in self.response_data.keys():
            return readings_list
        for record in self.response_data['EquipmentRecords']:
            temp = SpectrumReading(station_id=record['SerialNumber'],
                            request_datetime=self.request_datetime,
                            data_datetime=record['TimeStamp'],
                            atemp=round((record['SensorData'][1]["DecimalValue"] - 32) * 5 / 9, 2),
                            pcpn=round(record['SensorData'][0]["DecimalValue"] * 25.4, 2),
                            relh=round(record['SensorData'][2]["DecimalValue"], 2))
            readings_list.readings.append(temp)

        return readings_list

    def _handle_error(self):
        """ place holder to remind that we need to add err handling to each class"""
        pass

class SpectrumReading(WeatherStationReading):
    station_id : str
    request_datetime : datetime or None = None # UTC
    data_datetime : datetime           # UTC
    atemp : float or None = None       # celsius 
    pcpn : float or None = None        # mm, > 0
    relh : float or None = None        # percent
