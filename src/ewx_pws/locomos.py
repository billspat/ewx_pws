import time, json, pytz
from requests import post, Session, Request
from datetime import datetime, timezone

from ewx_pws.weather_stations import WeatherStationConfig, WeatherStationReading, WeatherStationReadings, WeatherStation, STATION_TYPE

class LocomosConfig(WeatherStationConfig):
        station_id     : str
        station_type   : STATION_TYPE = 'LOCOMOS'
        token          : str # Device token
        id             : str # ID field on device webpage
        tz             : str

class LocomosStation(WeatherStation):
    """Sub class for  MSU BAE LOCOMOS weather stations used for TOMCAST model"""
    @classmethod
    def init_from_dict(cls, config:dict):
        """ accept a dictionary to create this class, rather than the Type class"""

        # this will raise error if config dictionary is not correct
        station_config = LocomosConfig.parse_obj(config)
        return(cls(station_config))

    def __init__(self,config: LocomosConfig):
        """ create class from config Type"""
        super().__init__(config)
        self.var_list = {}


    def _check_config(self):
        # TODO implement 
        return(True)

    def _get_variable_list(self):
        """load ubidots variable list
        
        gets the list of variables and their IDS for this Ubidots device via the Ubidots API. 
        Ubidots is flexible and allows for multiple sensors or 'variables' each with it's own label and ID. 
        If this object already has a non-empty variable list, does not make the request a second time
        """

        if self.var_list is None or len(self.var_list) == 0:
            # object member is empty, load and save list of variables from API
            var_request = Request(method='GET',
                    url=f"https://industrial.api.ubidots.com/api/v2.0/devices/{self.config.id}/variables/", 
                    headers={'X-Auth-Token': self.config.token}, 
                    params={'page_size':'ALL'}).prepare()
            var_response = json.loads(Session().send(var_request).content)
            var_list = {}
            for result in var_response['results']:
                var_list[result['label']] = result['id']
            
            self.var_list = var_list
        
        return(self.var_list)
    
        
    def _get_readings(self, start_datetime:datetime, end_datetime:datetime):
        """
        Pull "data raw series" from UBIDOTS api.  Note they use POST rather than get.  
        See Ubidots doc : https://docs.ubidots.com/v1.6/reference/data-raw-series
        Params are start time, end time in UTC
        Returns api response in a list with metadata
        Example Curl command 
        # curl -X POST 'https://industrial.api.ubidots.com/api/v1.6/data/raw/series' \
        #     -H 'Content-Type: application/json' \
        #     -H "X-Auth-Token: $TOKEN" \
        #     -d '{"variables": ["6410e8564a53ce000ec46e46"], "columns": ["variable.name","value.value", "timestamp"], "join_dataframes": false, "start": 1679202000000, "end":1679203800000}'
        """
        
        start_milliseconds=int(start_datetime.timestamp() * 1000)
        end_milliseconds=int(end_datetime.timestamp() * 1000)
        
        response_columns = [
            'timestamp', 
            'device.name', 
            'device.label', 
            'variable.id', 
            'value.context', 
            'variable.name', 
            'value.value'
            ]
        
        request_headers = {
            'Content-Type': 'application/json',
            'X-Auth-Token': self.config.token,
        }
    
        # make a different request for each variable and store in a dict 
        # so that we can keep track of the data by variable name, not the variable ID so it's easier to transform
        data = {} # response_per_variable 
        var_list = self._get_variable_list()
        for var in var_list:
            request_params = {
                'variables': [var_list[var]],
                'columns': response_columns,
                'join_dataframes': False,
                'start': start_milliseconds,
                'end': end_milliseconds,
            }            
            response = post(url='https://industrial.api.ubidots.com/api/v1.6/data/raw/series', 
                            headers=request_headers, 
                            json=request_params)
            data[var] = json.loads(response.content)

        # # move to superclass
        # return_dict = {
        #     'station_id': self.config.station_id,
        #     'request_datetime': datetime.utcnow(),
        #     'data': data
        # }
        # convert structure to json to match other 
        self.current_response = [data]

        return self.current_response


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
                                    data_datetime=datetime.fromtimestamp(timestamp / 1000).astimezone(timezone.utc),
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
