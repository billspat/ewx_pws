# ONSET ###################

import json, pytz
from dotenv import dotenv_values
from requests import get, post  # Session, Request
from datetime import datetime, timezone

from pydantic import Field
from ewx_pws.weather_stations import WeatherStationConfig, WeatherStationReading, WeatherStationReadings, WeatherStation, STATION_TYPE


### Onset Notes

# response.content  format

    # {
    # "max_results": true,
    # "message": "",
    # "observation_list": []
    # }
    
    # message example: "message":"OK: Found: 0 results."
    # "message":"OK: Found: 21 results."

class OnsetConfig(WeatherStationConfig):
    station_id : str
    station_type : STATION_TYPE  = 'ONSET'
    sn : str  = Field(description="The serial number of the device")
    client_id : str = Field(description="client specific value provided by Onset")
    client_secret : str = Field(description="client specific value provided by Onset")
    ret_form : str = Field(description="The format data should be returned in. Currently only JSON is supported.")
    user_id : str = Field(description="alphanumeric ID of the user account This can be pulled from the HOBOlink URL: www.hobolink.com/users/<user_id>")
    sensor_sn : dict[str,str] = Field(description="a dict of sensor alphanumeric serial numbers keyed on sensor type, e.g. {'atemp':'21079936-1'}") 
    
    # access_token : str = Field('', description="needed for api auth, filled in by auth request ")
    
    # TODO class OnsetSensor() of elements in sensor_sn


class OnsetStation(WeatherStation):
    """ config is OnsetConfig type """
    @classmethod
    def init_from_dict(cls, config:dict):
        """ accept a dictionary to create this class, rather than the Type class"""

        # this will raise error if config dictionary is not correct
        station_config = OnsetConfig.parse_obj(config)
        return(cls(station_config))
        
    def __init__(self,config: OnsetConfig):
        """ create class from config Type"""
        self.access_token = None
        super().__init__(config)

    def _check_config(self):
        # TODO implement 
        return(True)
    
    def _get_auth(self):
        """
        uses the api to generate an access token required by Onset API
        adds 'access_token' field to the config dictionary  ( will that affect the type?)

        note that this must be done immediately before the request, as it can 
        otherwise cause a race condition with
        Raises Exception If the return code is not 200.
        """
        # debug logging - enabling will spill secrets in the log! 
        # logging.debug('client_id: \"{}\"'.format(self.config.client_id))
        # logging.debug('client_secret: \"{}\"'.format(self.client_secret))

        response = post(url='https://webservice.hobolink.com/ws/auth/token',
                        headers={
                            'Content-Type': 'application/x-www-form-urlencoded'},
                            data={'grant_type': 'client_credentials',
                                'client_id': self.config.client_id,
                                'client_secret': self.config.client_secret
                                }
                            )
        
        if response.status_code != 200:
            raise Exception(
                'Get Auth request failed with \'{}\' status code and \'{}\' message.'.format(response.status_code,
                                                                                    response.text))
        response = response.json()
        # store this in the object
        self.access_token = response['access_token']
        return self.access_token    

    def _get_readings(self,start_datetime:datetime,end_datetime:datetime)->list:
        """ use Onset API to pull data from this station for times between start and end.  Called by the parent 
        class method get_readings().   
        
        parameters:
        start_datetime: datetime object in UTC timezone.  Does not have to have a timezone but must be UTC
        end_datetime: datetime object in UTC timezone.  Does not have to have a timezone but must be UTC
        """
            
        access_token = self._get_auth() 
            
        start_datetime_str = self._format_time(start_datetime)
        end_datetime_str = self._format_time(end_datetime)
            
        # self.current_api_request = Request('GET',
        #         url=f"https://webservice.hobolink.com/ws/data/file/{self.config.ret_form}/user/{self.config.user_id}",
        #         headers={'Authorization': "Bearer " + access_token},
        #         params={'loggers': self.config.sn,
        #             'start_date_time': start_datetime_str,
        #             'end_date_time': end_datetime_str}).prepare()
                
        # response = Session().send(self.current_api_request)

        response = get( url=f"https://webservice.hobolink.com/ws/data/file/{self.config.ret_form}/user/{self.config.user_id}",
                        headers={'Authorization': "Bearer " + access_token},
                        params={
                            'loggers': self.config.sn,
                            'start_date_time': start_datetime_str,
                            'end_date_time': end_datetime_str
                            }
                        )

        return(response)
        
    def _transform(response_data, readings_list):
        readinginfos = {}
        sensor_sns = self.config.sensor_sn
        atemp_key = sensor_sns['atemp']
        pcpn_key = sensor_sns['pcpn']
        relh_key = sensor_sns['relh']
        station_sn = data["observation_list"][0]["logger_sn"]
        
        
    def _transform_old(self, data=None, request_datetime: datetime = None):
        """
        Transforms data into a standardized format and returns it as a WeatherStationReadings object.
        data param if left to default tries for self.response_data processing
        """

        # Return an empty list if there is no data contained in the response, this covers error 429
        if 'observation_list' not in data.keys():
            return readings_list
        
        readinginfos = {}
        sensor_sns = self.config.sensor_sn
        atemp_key = sensor_sns['atemp']
        pcpn_key = sensor_sns['pcpn']
        relh_key = sensor_sns['relh']
        station_sn = data["observation_list"][0]["logger_sn"]

        # Gathering each reading into an easily formattable manner
        for reading in data["observation_list"]:
            # Remove Z's from ends of timestamps
            ts = reading["timestamp"]
            if reading["timestamp"][-1].lower() == 'z':
                    ts = ts[:-1]
            # Create new entry if time hasn't been encountered yet
            if ts not in readinginfos.keys():
                readinginfos[ts] = {}
            # Set entries to contain proper data
            if reading["sensor_sn"] == atemp_key:
                readinginfos[ts]["atemp"] = round(float(reading['si_value']), 2)
            elif reading["sensor_sn"] == pcpn_key:
                readinginfos[ts]["pcpn"] = round(float(reading['si_value']), 2)
            elif reading["sensor_sn"] == relh_key:
                readinginfos[ts]["relh"] = round(float(reading['si_value']), 2)

        # Putting that data into a WeatherStationsReading object in OnsetReading class format
        for timestamp in readinginfos:
            readings_list.readings.append(OnsetReading(station_id=station_sn,
                                    request_datetime=request_datetime,
                                    data_datetime=pytz.utc.localize(datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')),
                                    atemp=readinginfos[timestamp]['atemp'],
                                    pcpn=readinginfos[timestamp]['pcpn'],
                                    relh=readinginfos[timestamp]['relh']))
                
        return readings_list

    def _handle_error(self):
        """ place holder to remind that we need to add err handling to each class"""
        pass

class OnsetReading(WeatherStationReading):
    station_id : str
    request_datetime : datetime or None = None # UTC # should not be null
    data_datetime : datetime           # UTC
    atemp : float or None = None       # celsius 
    pcpn : float or None = None        # mm, > 0
    relh : float or None = None        # percent
