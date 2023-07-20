"""
Module to hold constants, types  and parent class for weather stations.  weather station modules 
will import this module. 

WeatherStation.getreadings returns a complex type that is a list of dictionary (should it be a class?)
"""

import requests, pytz, json, warnings, logging
from datetime import datetime, timedelta, timezone
# from pytz import timezone
from requests import Response, Request
from abc import ABC, abstractmethod
from uuid import uuid4


# typing and Pydantic 
from pydantic import BaseModel, Field, ValidationError, validator
from typing import Literal

# package local
from ewx_pws.time_intervals import is_tz_aware, is_utc, previous_fourteen_minute_period, DatetimeUTC # previous_fifteen_minute_period, fifteen_minute_mark
from importlib.metadata import version

##########################################################
########          GLOBALS and TYPE MODELS         ########
##########################################################

# station type type, like an enum
STATION_TYPE = Literal['ZENTRA', 'ONSET', 'DAVIS', 'RAINWISE', 'SPECTRUM', 'LOCOMOS', 'GENERIC'] 
STATION_TYPE_LIST =   ['ZENTRA', 'ONSET', 'DAVIS', 'RAINWISE', 'SPECTRUM', 'LOCOMOS', 'GENERIC']
TIMEZONE_CODE = Literal['HT','AT','PT','MT','CT','ET']        
TIMEZONE_CODE_LIST = {
            'HT': 'US/Hawaii',
            'AT': 'US/Alaska',
            'PT': 'US/Pacific',
            'MT': 'US/Mountain',
            'CT': 'US/Central',
            'ET': 'US/Eastern'
        }

class WeatherStationConfig(BaseModel):
    """Base station configuration, includes common meta-data config common to all station types.  Must include a valid US Timezone 
    Station-specifc config.  """
    station_id : str 
    station_type : STATION_TYPE = "GENERIC"
    tz : TIMEZONE_CODE = Field(default='ET', description="US two-character time zone of the station location ( 'HT','AT','PT','MT','CT','ET')") 
    _tzlist: dict[str:str] = {
            'HT': 'US/Hawaii',
            'AT': 'US/Alaska',
            'PT': 'US/Pacific',
            'MT': 'US/Mountain',
            'CT': 'US/Central',
            'ET': 'US/Eastern'
            }
    
    def pytz(self):
        """return valide python timezone from 2-char timezone code in config 
        for use in datetime module
        """
        return(self._tzlist[self.tz])

    class Config:
        """ allow private member for timezone conversion"""
        underscore_attrs_are_private = True

# ws = WeatherStationConfig.parse_obj( {'station_id' : 'fakestation', 'station_type' : "GENERIC", 'tz' : "ET" })
class GenericConfig(WeatherStationConfig):
    """This configuration is used for testing, dev and for base class.  Station specific config is simply stored
    in a dictionary"""
    config:dict = {}


class datetimeUTC(BaseModel):
    """a datetime object guaranteed to be UTC tz aware"""
    value: datetime 
    @validator('value')
    def check_datetime_utc(cls, d):
        assert d.tzinfo == pytz.utc
        return d

class WeatherStationReading(BaseModel):
    station_id : str
    request_datetime : datetimeUTC # UTC
    data_datetime : datetimeUTC    # UTC
    atemp : float or None       # celsius 
    pcpn : float or None        # mm, > 0
    relh : float or None        # percent

class WeatherStationReadings(BaseModel):
    readings: list[WeatherStationReading] = list()


##########################################################
########        WeatherStation Base Class         ########
##########################################################

class WeatherStation(ABC):
    """abstract base class for a weather station to access it's API and retrieve data"""
    
    # used by subclasses as default when there is no data from station
    empty_response = ['{}']
    
    ####### constructor #########
    def __init__(self, config:GenericConfig):
        """create station object using Config data model """    
        self.config = config
        self._id = config.station_id
        # store latest resp object as returned from request
        self.current_response = None
        # structure for saving raw data along with metadata
        self.current_response_data = None
        
    ####### alternative constructors as class methods #########
    @classmethod
    def init_from_dict(cls, config:dict):
        """ accept a dictionary to create this class, rather than the config Type class"""
    
        # this will raise error if config dictionary is not correct
        station_config = GenericConfig.parse_obj(config)
        return(cls(station_config))

    @classmethod
    def init_from_list(cls, station_config: list):
        """create station object using config stored as a list, by converting to dict and invoking 
        the other clas method. see GenericConfig type model above
        
        accept a list with the following elements in order:
        station_id; station_type, config as json str, optionally include time zone
        (in future time zone should be pulled out of this dict)
        returns: object instance using GenericConfig type
        
        """
        config_dict = json.loads(station_config[2])
        
        # TODO : update this if the proposed record format is updated to include a tz field
        if 'tz' in config_dict.keys():
            tz = config_dict['tz']
        else:
            tz = 'ET'
        # create a dictionary from list... and call the class method above  
        station_config_dict = {
            'station_id': station_config[0],
            'station_type': station_config[1],
            'tz': tz,
            'config': config_dict
        }
        cls.init_from_dict(station_config_dict)
                
    # convenience/hiding methods
    @property
    def id(self):
        return self._id
    
    @property
    def station_type(self):
        return(self.config.station_type)
    
    @property
    def station_tz(self):
        return(self.config.tz)
    

    #######################
    #### abstract methods to be implemented in subclass
    @abstractmethod
    def _check_config(self)->bool:
        return(True)        

    @abstractmethod
    def _transform(self, response_data):
        """transforms a response into a json to be exported"""
        return None
    
    @abstractmethod
    def _get_readings(self,start_datetime:datetime, end_datetime:datetime):
        """create API request and return str of json
        
        returns: either a single requests.Response object, or a list of them"""
        # get auth
        logging.info(f" this would be a reading from {self.id} for {start_datetime} to {end_datetime}")
        return self.empty_response
    
    # override as necessary for sub-classes
    def _format_time(self, dt:datetime)->str:
        """
        format date/time parameters for specific API request, convert to 
        UTC or local as needed.  The generic converter simply converts to ISO.  
        """
        
        return(dt.strftime('%Y-%m-%d %H:%M:%S'))
        
    def get_readings(self, start_datetime : datetime = None, end_datetime : datetime = None):
        """prepare start/end times and other params generically and then call station-specific method with that.
        start_datetime: date time in UTC time zone
        end_datetime: date time in UTC time zone.  If start_datetime is empty this is ignored 
        add_to: option for list to be passed in already containing metadata to be added to
        """
        
        # the time delta in this method is best for the data pipeline
        if not start_datetime:
            # use default interval, ignore end_date_time 
            start_datetime, end_datetime =  previous_fourteen_minute_period()
        else:
            if not end_datetime: 
                # use default interval end time
                end_datetime = start_datetime + timedelta(minutes= 14)

        # runtime checking that datetime is UTC, will raise an exception if not
        if not is_utc(start_datetime):
            raise ValueError("start_datetime must be UTC timezone")
        
        if not is_utc(end_datetime):
            raise ValueError("end_datetime must be UTC timezone")
        
        # call the sub-class to pull data from the station vendor API
        # save the response object in this object
        try:
            request_time = datetime.utcnow()
            responses = self._get_readings(
                    start_datetime = start_datetime,
                    end_datetime = end_datetime
            )
        except Exception as e:
            logging.error("Error getting reading from station {self.id}: {e}")
            raise e

        # ensure what is returned is a list, as some stations types return a list of responses
        if not isinstance(responses, list):
            responses = [responses]
        
        # save in object
        self.current_response = responses 

        # format the raw data and meta data into standard and save in object 
        self.current_response_data = self.compose_response_data(start_datetime, end_datetime, self.current_response)

        return(self.current_response_data)


    def compose_response_data(self, start_datetime, end_datetime, responses=None):
        """data structure to hold meta data and response content/data.  can be used to serialize response
        This is the format required by the transform methods"""
        
        responses = responses or self.current_response

        if responses is None:
            raise ValueError("no response data yet available from get_readings")
        
        response_data = {
            # unique id to join raw and transformed data
            "request_id" : uuid4(),
            # time the request was made (approximately)
            "request_datetime_utc": datetime.utcnow(), # TODO use responses[0].headers['Date']
            
            "station_type": self.config.station_type,
            "station_id": self.config.station_id,
            "timezone": self.config.tz, 

            "start_datetime": start_datetime,
            "end_datetime": end_datetime,
            "package_version": version('ewx_pws'),
 
        }
        
        # initialize station specific modifications/additions if necessary
        response_data['api_responses'] = self._compose_response_data(responses)
        
        self.current_response_data = response_data
        
        return response_data
    
    # override-able response deconstructor
    def _compose_response_data(self, responses):
        """ Default content pull for stations, assume content is JSON.  Override for specific station types
        """

        if not isinstance(responses, list):
            responses = [responses]

        responses_content = [ json.loads(r.content) for r in responses] 
        
        return(responses_content)  
    

    def transform(self, response_data = None):
        """
        Transforms data and return it in a standardized format. 
        data: optional input used to load in data if transform of existing data dictionary is required.
        """
        # TODO type checking to ensure all the data elements needed are present 

        # use either input param, object variable
        response_data = response_data or self.current_response_data

        if response_data is None:
            return None
        else:
            return self._transform(response_data)


    def dt_utc_from_str(self, datetime_str: str, in_tz: timezone = None):
        # Creates a UTC timezone aware datetime from a string and an optional timezone
        # If a timezone is passed, UTC is still returned, just adjusted for the input being a different TZ
        dt = datetime.fromisoformat(datetime_str)
        # if not in_tz:
        #     return datetimeUTC(value=pytz.utc.localize(dt))
        if not is_tz_aware(dt):
            dt =  pytz.timezone(self.config.pytz()).localize(dt)
            
        return dt.astimezone(timezone.utc) # datetimeUTC(value=in_tz.localize(dt).astimezone(pytz.utc))

    def get_readings_local(self, start_datetime_local: datetime, end_datetime_local: datetime, add_to=None):
        """ get reading for the timezone of the station.  This will be problematic for DST readings
        datetimes with a tz set to one outside of station tz are invalid.  Use UTC with get_reading() method instead
        e.g. start_datetime_local == 6:00 am, is 6:00am for the tz of the station. """            
    
        def correct_tz(dt):
            """ internal fn to adapt dt sent to local time of station.  """
            if dt.tzinfo is None:
                return( pytz.timezone(self.config.pytz()).localize(dt) )
            
            if  dt.tzinfo == pytz.timezone(self.config.pytz()):
                return(dt)

            raise ValueError(f"time argument timezone does not match station.  Remove timezone or use {self.config.tz}")         

        start_datetime_utc = correct_tz(start_datetime_local).astimezone(timezone.utc)
        end_datetime_utc   = correct_tz(end_datetime_local).astimezone(timezone.utc)
        return self.get_readings(start_datetime=start_datetime_utc, end_datetime=end_datetime_utc, add_to=add_to)


        
    def get_test_reading(self):
        """ test that current config is working and station is online
        returns:
        True: station is on-line and configuration correct
        False: station is either off-line OR configuration incorrect
        """

        try:
            r = self.get_readings()
        except Exception as e:
            warnings.warn(f"error when testing api for station {self.id}: {e}")
            return(False)

        if r is not None:  # ensure that an empty reading is actually None
            return True
        else:
            warnings.warn("empty response when testing api for station {self.id}")
            return False
    

