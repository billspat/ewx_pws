# RAINWISE WIP ###################

import json
from requests import Session, Request
from datetime import datetime, timezone

from ewx_pws.weather_stations import WeatherStationConfig, WeatherStationReading, WeatherStationReadings, WeatherStation, STATION_TYPE

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
        add_to: option for list to be passed in already containing metadata to be added to
        Returns api response in a list with metadata
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
        self.current_response = Session().send(self.current_api_request)
        return [self.current_response]


    def _transform(self, data=None):
        """
        Transforms data into a standardized format and returns it as a WeatherStationReadings object.
        data param if left to default tries for self.response_data processing
        """
        readings_list = WeatherStationReadings()

        # Return an empty list if there is no data contained in the response, this covers error 429
        if 'station_id' not in data.keys():
            return readings_list
        for key in data['times']:
            temp = RainwiseReading(station_id=data['station_id'],
                            transform_datetime=datetime.utcnow(),
                            data_datetime=data['times'][key],
                            atemp=round((float(data['temp'][key]) - 32) * 5/9, 2),
                            pcpn=round(float(data['precip'][key]) * 25.4, 2),
                            relh=round(float(data['hum'][key]), 2))
            readings_list.readings.append(temp)
            
        return readings_list

    def _handle_error(self):
        """ place holder to remind that we need to add err handling to each class"""
        pass

class RainwiseReading(WeatherStationReading):
    station_id : str
    transform_datetime : datetime or None = None # UTC
    data_datetime : datetime           # UTC
    atemp : float or None = None       # celsius 
    pcpn : float or None = None        # mm, > 0
    relh : float or None = None        # percent
