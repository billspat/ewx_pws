
import collections, hashlib, hmac
import json,pytz, time
from requests import Session, Request
from datetime import datetime, timedelta, timezone

from pydantic import Field
from ewx_pws.weather_stations import WeatherStationConfig, WeatherStationReading, WeatherStationReadings, WeatherStation, STATION_TYPE

class DavisConfig(WeatherStationConfig):
        station_type   : STATION_TYPE = 'DAVIS'
        sn             : str #  The serial number of the device.
        apikey         : str # The user's API access key. 
        apisec         : str # API security that is used to compute the hash.

class DavisStation(WeatherStation):

    # time between readings in minutes for this station type
    interval_min = 15

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
    
    def get_intervals(self, start_datetime:datetime, end_datetime:datetime):
        """
        Public for viewing of what potential time intervals would look like
        Pass in start_datetime and end_datetime, if they're above 24hr apart,
        get nice splits that Davis can handle well in an array of tuples.
        """
        secondsdiff = (end_datetime - start_datetime).total_seconds()
        curr_start_date = start_datetime
        splits = []

        # 86400 seconds per interval
        while secondsdiff > 0:
            if secondsdiff > 86400:
                splits.append((curr_start_date, curr_start_date + timedelta(seconds=86400)))
                curr_start_date += timedelta(seconds=86400)
                secondsdiff -= 86400
            elif secondsdiff < 300:
                # Makes sure there aren't any intervals too small for Davis which result in errors.
                break
            else:
                splits.append((curr_start_date, curr_start_date + timedelta(seconds=secondsdiff)))
                secondsdiff -= secondsdiff
        return splits
    
    def _get_readings(self, start_datetime:datetime, end_datetime:datetime):
        """ 
        Builds, sends, and stores raw response from Davis API
        The Davis stations will only collect data for at most 24 hrs. 
        If a multi-day request is made, would have to return a list of responses for each daily request
        So this _always_ returns a list of responses
        """
        tsplits = self.get_intervals(start_datetime=start_datetime, end_datetime=end_datetime)
        
        response_list = []
        for tsplit in tsplits:
            start_datetime = tsplit[0]
            end_datetime = tsplit[1]
            now = pytz.utc.localize(datetime.utcnow())
            t = int(now.timestamp())

            start_timestamp=int(start_datetime.timestamp())
            end_timestamp=int(end_datetime.timestamp())

            self._compute_signature(t=t, start_timestamp=start_timestamp, end_timestamp=end_timestamp)
            self.current_api_request = Request('GET',
                                url='https://api.weatherlink.com/v2/historic/' + self.config.sn,
                                params={'api-key': self.config.apikey,
                                        't': t,
                                        'start-timestamp': start_timestamp,
                                        'end-timestamp': end_timestamp,
                                        'api-signature': self.apisig}).prepare()
            
            response = Session().send(self.current_api_request)
            response_list.append(response)

        return response_list

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

    def _transform(self, response_data):
        """
        Transforms data into a standardized format and returns it as a WeatherStationReadings object.
        data param if left to default tries for self.response_data processing
        """
        # if we can't decide to load JSON or not
        if isinstance(response_data,str):
            response_data = json.loads(response_data)

        if 'sensors' not in response_data.keys():
            return []
        
        readings = []
        for lsid in response_data['sensors']:
            for record in lsid['data']:    
                if 'temp_out' in record.keys():
                        reading = {            
                            'data_datetime': datetime.utcfromtimestamp(record['ts']).astimezone(timezone.utc),
                            'atemp': round((record['ts'] - 32) * 5 / 9, 2),
                            'pcpn': round(record['rainfall_mm'] * 25.4, 2),
                            'relh': round(record['hum_out'], 2)
                            }
                        readings.append(reading)

        return readings

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
