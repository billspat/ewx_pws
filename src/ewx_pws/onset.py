# ONSET ###################

from requests import Session, Request
from pydantic import Field
from ewx_pws.weather_stations import WeatherStationConfig, WeatherStation

class OnsetConfig(WeatherStationConfig):
    station_id : str = None
    station_type : str = 'ONSET'
    sn : str  = Field(description="The serial number of the device")
    client_id : str = Field(description="client specific value provided by Onset")
    client_secret : str = Field(description="client specific value provided by Onset")
    ret_form : str = Field(description="The format data should be returned in. Currently only JSON is supported.")
    user_id : str = Field(description="alphanumeric ID of the user account This can be pulled from the HOBOlink URL: www.hobolink.com/users/<user_id>")
    sensor_sn : dict[str,str] = Field(description="a dict of sensor alphanumeric serial numbers keyed on sensor type, e.g. {'atemp':'21079936-1'}") 
    access_token : str = Field('', description="needed for api auth, filled in by auth request ")
    
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
        super().__init__(config)

    def _get_auth(self):
        """
        uses the api to generate an access token required by Onset API
        adds 'access_token' field to the config dictionary  ( will that affect the type?)

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
                                'client_id': self.config['client_id'],
                                'client_secret': self.config['client_secret']
                                }
                          ).prepare()
        resp = Session().send(request)
        if resp.status_code != 200:
            raise Exception(
                'Get Auth request failed with \'{}\' status code and \'{}\' message.'.format(resp.status_code,
                                                                                             resp.text))
        response = resp.json()
        self.config['access_token'] = response['access_token']

        
    def _get_reading(self,params):
        self._get_auth()
        # convert date/times IF needed using methods in base class
        
        print(f" this would be a reading from {self.id} for {params.get('start_datetime')} to {params.get('end_datetime')}")
        return "{}"
