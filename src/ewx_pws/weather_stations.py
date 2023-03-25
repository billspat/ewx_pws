# """WIP start on a class to hold this info, 
# not sure if a class is warranted for this yet - why would we need to preseve state?me"""

# from time_intervals import previous_fifteen_minute_period
# from multiweatherapi import multiweatherapi

import requests
from datetime import datetime, timedelta, timezone
from requests import Session, Request

# typing and Pydantic 
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field
from typing import Literal, Type

# package local
from .time_intervals import previous_fourteen_minute_period, previous_fifteen_minute_period, fifteen_minute_mark

# TEMPORARY
from multiweatherapi import multiweatherapi


#############
# GLOBALS and TYPE MODELS

DEBUG=False

_version = '0.0.1'

# station type type, like an enum
STATION_TYPE = Literal['ZENTRA', 'ONSET', 'DAVIS', 'RAINWISE', 'SPECTRUM', 'GENERIC']  # generic type is a hack for testing

# temporary type used when starting to protype station classes,  not for actual use
# WeatherStationConfig = dict

class WeatherStationConfig(BaseModel):
    station_id : str = None
    station_type : STATION_TYPE = "GENERIC"
    tz : str = "ET" # Field(description="time zone where the station is located")  # TODO create a timezone literal type
    
    
#############################
# BASE CLASS
class WeatherStation(ABC):
    """configuration and information for a weather station and it's API"""

    @classmethod
    def init_from_dict(cls, config:dict):
        """ accept a dictionary to create this class, rather than the Type class"""
    
        # this will raise error if config dictionary is not correct
        station_config = WeatherStationConfig.parse_obj(config)
        return(cls(station_config))
    
    
    def __init__(self, config:WeatherStationConfig):#### this won't work to have the 'config' fields of other classes be strong types!  
        self.config = config
        # pull out some of the elements in the dict
        self._id = config.station_id
        self.current_reading = None
        
    # convenience/hiding methods
    @property
    def id(self):
        return self._id
    
    @property
    def station_type(self):
        return(self.config['station_type'] )
    
    @property
    def station_tz(self):
        return(self.config['tz'])
    
    ##### abstract methods to be overriden
    
    @abstractmethod
    def _check_config(self)->bool:
        return(True)
        
    @abstractmethod
    def _get_reading(self,params):
        """create API request and return str of json"""
        # get auth
        print(f" this would be a reading from {self.id} for {params.get('start_datetime')} to {params.get('end_datetime')}")
        return "{}"
    
    # user api method that has optional start & end times
    def get_reading(self,start_datetime_str = None, end_datetime_str = None):
        """prepare start/end times and other params generically and then call station-specific method with that.  
        This should always be wrapped in a try/except block"""
        
        request_time = datetime.now(tz='UTC')
        
        if not start_datetime_str:
            # no start ?  Use the interval 15 minutees before present time.  see module for details.  Ignore end time if it's sent
            start_datetime,end_datetime =  previous_fourteen_minute_period()
        else:
            start_datetime = datetime.fromisoformat(start_datetime_str)
            if not end_datetime_str:
                # no end time, make end time 15 minutes from stard time given.  
                end_datetime = start_datetime + timedelta(minutes= 15)
            else:
                end_datetime = datetime.fromisoformat(end_datetime_str)

        params = self.station_config
        params['start_datetime'] = self._format_time(start_datetime)
        params['end_datetime'] = self._format_time(end_datetime)
        
        try:
            response = self._get_reading(params)
        except Exception as e:
            print("Error getting reading from station {self.id}: {e}")
            raise e
        
        
        # add meta data
        reading_metadata = {
            "station_type": "onset",
            "station_id": self.id,
            "timezone": self.config['tz'],
            "start_datetime": start_datetime,
            "end_datetime": end_datetime,
            "request_time": request_time,
            "package_version": self.debug_info['binding_ver']}
        
        
        self.response.append(metadata)
        # # includes mwapi_resp.resp_raw, and mwapi_resp.resp_transformed
        # self.current_reading = mwapi_resp
        
        # return mwapi_resp

    def get_test_reading(self):
        """ test that current config is working and station is online
        returns:
        True: station is on-line and configuration correct
        False: station is either off-line OR configuration incorrect
        """

        try:
            r = self.get_reading()
        except Exception as e:
            return(False)

        if r is not None:  # ensure that an empty reading is actually None
            return True
        return False
    
    # override as necessary for sub-classes
    def _format_time(self, dt:datetime):
        """
        This method makes sure that a datetime object is in the format "YYYY-MM-DD HH:MM:SS".
        """
        return(dt.strftime('%Y-%m-%d %H:%M:%S'))
    

# ONSET ###################


class OnsetConfig(WeatherStationConfig):
    station_id : str = None
    station_type : str = 'ONSET'
    sn : str  = Field(description="The serial number of the device")
    client_id : str = Field(description="client specific value provided by Onset")
    client_secret : str = Field(description="client specific value provided by Onset")
    ret_form : str = Field(description="The format data should be returned in. Currently only JSON is supported.")
    user_id : str = Field(description="alphanumeric ID of the user account This can be pulled from the HOBOlink URL: www.hobolink.com/users/<user_id>")
    sensor_sn : dict = Field(description="a dict of sensor serial numbers")
    access_token = Field('', description="needed for api auth, filled in by auth request ")
    
    # conversion_msg : str # Stores time conversion message
    
    
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

class ZentraConfig(WeatherStationConfig):
    station_type : STATION_TYPE = "ZENTRA"
    
class ZentraStation(WeatherStation):
    """Zentra Brand Weather Station"""    
    def __init__(self,config:ZentraConfig):
        super().__init__(config)
        
    def _check_config(self):
        return True
    
    def _get_reading(self):
        return('{}')
        

class DavisConfig(WeatherStationConfig):
    station_type : STATION_TYPE = "DAVIS"   
        
class DavisStation(WeatherStation):
    def __init__(self,config:WeatherStationConfig):
        self.station_type = 'davis'
        super().__init__(config)
    
    def _check_config(self):
        return True
    
    def _get_reading(self):
        return('{}')

class RainwiseConfig(WeatherStationConfig):
    station_type : STATION_TYPE = "RAINWISE"

class RainwiseStation(WeatherStation):
    def __init__(self,config:WeatherStationConfig):
        self.station_type = 'rainwise'
        super().__init__(config)

    def _check_config(self):
        return True
    
    def _get_reading(self):
        return('{}')
    
class SpectrumConfig(WeatherStationConfig):
    station_type : STATION_TYPE = "SPECTRUM"

class SpectrumStation(WeatherStation):
    def __init__(self,config:WeatherStationConfig):
        self.station_type = 'spectrum'
        super().__init__(config)  
        
    def _check_config(self):
        return True
    
    def _get_reading(self):
        return('{}')

# METHODS UTILIZING CLASS

# module var:  dictionary of station types and classes
# update this when adding new types        
_station_types = {'zentra': ZentraStation, 'onset': OnsetStation, 'davis': DavisStation,'rainwise': RainwiseStation, 'spectrum':SpectrumStation }

def weather_station_factory(station_type:STATION_TYPE, config:dict) -> type[WeatherStation]:
    """" create a station or raise an exception if can't create the station because of bad configuration"""
    try:
        station = _station_types[station_type](config)
    except Exception as e: 
        print(f"could not create station type {station_type} from config: {e}")
        raise e
    
    return station 


def validate_station_config(station_type:STATION_TYPE, station_config:dict)->bool:
    """  this tests the station configuration as correct by 1) attempting to create the station object 2) get a sample reading
    
    returns T or F only """
    
    # attempt to create the station and see what happens, return F if it doesn't work
    try:
        test_station = weather_station_factory(station_type, station_config)
    except Exception as e:
        print("station config error for {station_type}")
        return False    
    
    # attempt to get a sample reading and see what happens, return T if it works
    try:
        r = test_station.get_test_reading()
        if r:
            return True
    except Exception as e:
        print("could not get reading for station type {station_type} id {station.id}: {e}")
        return False
    # false here ==> config is incorrect OR station is offline, don't know which

    
    
    
    
    
# def get_reading(station_type, station_config,
#                 start_datetime_str = None,
#                 end_datetime_str = None):
    
#     if not start_datetime_str:
#         # no start ?  Use the internval 15 minutees before present timee.  see module for details.  Ignore end time if it's sent
#         start_datetime,end_datetime =  previous_fifteen_minute_period()
#     else:
#         start_datetime = datetime.fromisoformat(start_datetime_str)
#         if not end_datetime_str:
#             # no end time, make end time 15 minutes from stard time given.  
#             end_datetime = start_datetime + timedelta(minutes= 15)
#         else:
#             end_datetime = datetime.fromisoformat(end_datetime_str)


#     params = station_config
#     params['start_datetime'] = start_datetime
#     params['end_datetime'] = end_datetime
#     params['tz'] = 'ET'

#     try:
#         mwapi_resp = multiweatherapi.get_reading(station_type, **params)
#     except Exception as e:
#         raise e

#     # includes mwapi_resp.resp_raw, and mwapi_resp.resp_transformed

#     return mwapi_resp

#     def reading_fields():
#         """list of fields to expect in a reading, used for testing
#         """
#         return([
#             "station_id",
#             "request_datetime",
#             "data_datetime",
#             "atemp",
#             "pcpn",
#             "relh"
#             ]
#         )
    

