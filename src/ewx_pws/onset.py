# ONSET ###################

import json
from requests import Session, Request
from datetime import datetime, timezone

from pydantic import Field
from ewx_pws.weather_stations import WeatherStationConfig, WeatherStation
from ewx_pws.time_intervals import fifteen_minute_mark, previous_fifteen_minute_period


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
    station_id : str = None
    station_type : str = 'ONSET'
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
        # debug printing - enabling will spill secrets in the log! 
        # print('client_id: \"{}\"'.format(self.config.client_id))
        # print('client_secret: \"{}\"'.format(self.client_secret))

        request = Request('POST',
                          url='https://webservice.hobolink.com/ws/auth/token',
                          headers={
                              'Content-Type': 'application/x-www-form-urlencoded'},
                          data={'grant_type': 'client_credentials',
                                'client_id': self.config.client_id,
                                'client_secret': self.config.client_secret
                                }
                          ).prepare()
        resp = Session().send(request)
        if resp.status_code != 200:
            raise Exception(
                'Get Auth request failed with \'{}\' status code and \'{}\' message.'.format(resp.status_code,
                                                                                             resp.text))
        response = resp.json()
        # store this in the object
        self.access_token = response['access_token']
        return self.access_token
 
    def _format_time(self, dt:datetime)->str:
        """
        format date/time parameter for Onset API request
        """
        return(dt.strftime('%Y-%m-%d %H:%M:%S'))
    

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
            
        self.current_api_request = Request('GET',
                url=f"https://webservice.hobolink.com/ws/data/file/{self.config.ret_form}/user/{self.config.user_id}",
                headers={'Authorization': "Bearer " + access_token},
                params={'loggers': self.config.sn,
                    'start_date_time': start_datetime_str,
                    'end_date_time': start_datetime_str}).prepare()
        
        api_response = Session().send(self.current_api_request)
        
        ## prepare response as a list.   All responses are to be wrapped in a list as some APIs require multiple requests
        
        return(api_response)
        
    def _handle_error(self):
        """ place holder to remind that we need to add err handling to each class"""
        pass

