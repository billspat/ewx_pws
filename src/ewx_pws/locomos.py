import time, json
from requests import Session, Request
from datetime import datetime, timezone

from ewx_pws.weather_stations import WeatherStationConfig, WeatherStationReading, WeatherStationReadings, WeatherStation, STATION_TYPE

class LocomosConfig(WeatherStationConfig):
        station_id     : str
        station_type   : STATION_TYPE = 'LOCOMOS'
        token          : str # Device token
        id             : str # ID field on device webpage
        tz             : str = 'ET'

class LocomosStation(WeatherStation):
    """ config is RainwiseConfig type """
    @classmethod
    def init_from_dict(cls, config:dict):
        """ accept a dictionary to create this class, rather than the Type class"""

        # this will raise error if config dictionary is not correct
        station_config = LocomosConfig.parse_obj(config)
        return(cls(station_config))

    def __init__(self,config: LocomosConfig):
        """ create class from config Type"""
        super().__init__(config)

    def _check_config(self):
        # TODO implement 
        return(True)

    def _get_readings(self, start_datetime:datetime, end_datetime:datetime):
        """
        Params are start time, end time.
        Returns api response in a list with metadata
        """

        start_milliseconds=int(time.mktime(start_datetime.timetuple())) * 1000
        end_milliseconds=int(time.mktime(end_datetime.timetuple())) * 1000

        var_request = Request(method='GET',
                url='https://industrial.api.ubidots.com/api/v2.0/devices/{}/variables/'.format(self.config.id), 
                headers={'X-Auth-Token': self.config.token}, 
                params={'page_size':'ALL'}).prepare()
        var_response = json.loads(Session().send(var_request).content)
        var_list = {}
        for result in var_response['results']:
            var_list[result['label']] = result['id']
        
        data = {}
        for var in var_list:
            request = Request(method='GET',
                url='https://industrial.api.ubidots.com/api/v1.6/variables/{}/values'.format(var_list[var]), 
                headers={'X-Auth-Token':self.config.token}, 
                params={'page_size':'ALL', 'start':int(start_milliseconds), 'end':int(end_milliseconds)}).prepare()
            response = json.loads(Session().send(request).content)
            data[var] = response
        return_dict = {
            'station_id': self.config.station_id,
            'request_datetime': datetime.utcnow(),
            'data': data
        }
        return [return_dict]


    def _transform(self, data=None, request_datetime: datetime = None):
        """
        Transforms data into a standardized format and returns it as a WeatherStationReadings object.
        data param if left to default tries for self.response_data processing
        """
        readings_list = WeatherStationReadings()

        results = data['data']
        if 'precip' not in results.keys() or 'humidity' not in results.keys() or 'temperature' not in results.keys():
            return readings_list
        timestamps = []
        for key in ['precip', 'humidity', 'temperature']:
            for entry in results[key]['results']:
                if entry['timestamp'] not in timestamps:
                    timestamps.append(entry['timestamp'])
        timestamps.sort()
        for timestamp in timestamps:
            temp = None
            precip = None
            humidity = None
            for result in results['precip']['results']:
                if result['timestamp'] == timestamp:
                    precip = result['value']
            for result in results['temperature']['results']:
                if result['timestamp'] == timestamp:
                    temp = result['value']
            for result in results['humidity']['results']:
                if result['timestamp'] == timestamp:
                    humidity = result['value']

            temp = LocomosReading(station_id=data['station_id'],
                                    request_datetime=request_datetime,
                                    data_datetime=datetime.fromtimestamp(timestamp / 1000),
                                    atemp=temp,
                                    pcpn=round(precip * 25.4, 2),
                                    relh=humidity)
            readings_list.readings.append(temp)
            
        return readings_list

    def _handle_error(self):
        """ place holder to remind that we need to add err handling to each class"""
        pass

class LocomosReading(WeatherStationReading):
    station_id : str
    request_datetime : datetime or None = None # UTC
    data_datetime : datetime           # UTC
    atemp : float or None = None       # celsius 
    pcpn : float or None = None        # mm, > 0
    relh : float or None = None        # percent
