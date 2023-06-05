# """WIP start on a class to hold this info, 
# not sure if a class is warranted for this yet - why would we need to preseve state?me"""

# from multiweatherapi import multiweatherapi

import requests, pytz, json, warnings, logging
from datetime import datetime, timedelta, timezone
# from pytz import timezone
from requests import Session, Request

# typing and Pydantic 
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field
from typing import Literal

# package local
from ewx_pws.time_intervals import previous_fourteen_minute_period, previous_fifteen_minute_period, fifteen_minute_mark
from importlib.metadata import version

#############
# GLOBALS and TYPE MODELS

# station type type, like an enum
STATION_TYPE = Literal['ZENTRA', 'ONSET', 'DAVIS', 'RAINWISE', 'SPECTRUM', 'LOCOMOS', 'GENERIC']  # generic type is a hack for testing
STATION_TYPE_LIST = ['ZENTRA', 'ONSET', 'DAVIS', 'RAINWISE', 'SPECTRUM', 'LOCOMOS', 'GENERIC']
        
# temporary type used when starting to protype station classes,  not for actual use
# WeatherStationConfig = dict

class WeatherStationConfig(BaseModel):
    """Base station configuration, includes common meta-data config common to all station types. 
    Station-specifc config """
    station_id : str 
    station_type : STATION_TYPE = "GENERIC"
    tz : str = "ET" # Field(description="time zone where the station is located")  # TODO create a timezone literal type
    

class GenericConfig(WeatherStationConfig):
    """This configuration is used for testing, dev and for base class.  Station specific config is simply stored
    in a dictionary"""
    config:dict = {}


class WeatherStationReading(BaseModel):
    station_id : str
    request_datetime : datetime # UTC
    data_datetime : datetime    # UTC
    atemp : float or None       # celsius 
    pcpn : float or None        # mm, > 0
    relh : float or None        # percent


#############################
#        BASE CLASS         #
#############################

class WeatherStation(ABC):
    """abstract base class for a weather station to access it's API and retrieve data"""

    # class globals
    tzlist = {
            'HT': 'US/Hawaii',
            'AT': 'US/Alaska',
            'PT': 'US/Pacific',
            'MT': 'US/Mountain',
            'CT': 'US/Central',
            'ET': 'US/Eastern'
        }
    
    # used by subclasses as default when there is no data from station
    empty_response = ['{}']
    
    ####### constructor #########
    def __init__(self, config:GenericConfig):
        """create station object using Config data model """    
        self.config = config
        self._id = config.station_id
        # store req/resp in object for debugging
        self.current_api_request = None
        self.current_response = None
        
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
    
    ##### abstract methods to be overriden
    
    @abstractmethod
    def _check_config(self)->bool:
        return(True)
        
    @abstractmethod
    def _get_readings(self,start_datetime:datetime, end_datetime:datetime):
        """create API request and return str of json"""
        # get auth
        logging.info(f" this would be a reading from {self.id} for {start_datetime} to {end_datetime}")
        return self.empty_response

    @abstractmethod
    def _transform(self, response):
        """transforms a response into a json to be exported"""
        return self.transformed_data
    
    # override as necessary for sub-classes
    def _format_time(self, dt:datetime)->str:
        """
        ensure correctr formating of a date/time parameter for API request, convert to 
        UTC or local as needed.  The generic converter simply converts to 
        """
        return(dt.strftime('%Y-%m-%d %H:%M:%S'))
    
    # this is a separate method so that it may be overriden if necessary by sub-classes
    def _initialize_metadata(self, start_datetime, end_datetime):
        """ creates list with metadata in 0th position and api response in 1st position"""
         # TODO: add meta data to response so it can be identified for future diagnostics
         # TODO: make package version based on something not hard coded in here
        
        metadata = {
            "station_type": self.config.station_type,
            "station_id": self.config.station_id,
            "timezone": self.config.tz, 
            "start_datetime": start_datetime,
            "end_datetime": end_datetime,
            "response_count": 0,
            "package_version": version('ewx_pws')
        }
        
        return [metadata]
        
    # user api method that has optional start & end times
    def get_readings(self, start_datetime_str = None, end_datetime_str = None, add_to=None):
        """prepare start/end times and other params generically and then call station-specific method with that.
        start_datetime_str: optional date time interpretable string in UTC time zone
        end_datetime_str: optional datetime interpretable string in UTC time zone.  If start_datetime_str is empty this is ignored 
        add_to: option for list to be passed in already containing metadata to be added to
        """
        
        #TODO: !!! ensure all datetimes are UTC.  if we allow 'str' inputs for date time, can't enforce that
        # create a request_interval pydantic type that requires a datetime object with a timezone, and that timezone must be UTC
        
        # for meta-data
        self.request_datetime = datetime.utcnow()
        
        # the time delta in this method is abritrary but fits with the proposed data pipeline
        if not start_datetime_str:
            # no start ?  Use the interval 15 minutees before present time.  see module for details.  Ignore end time if it's sent
            start_datetime,end_datetime =  previous_fourteen_minute_period()
        else:
            # TODO use pendulum package to accept wider variety of date/time str formats
            start_datetime = datetime.fromisoformat(start_datetime_str)
            if not end_datetime_str:
                # no end time, make end time 14 minutes from start time given.  
                end_datetime = start_datetime + timedelta(minutes= 14)
            else:
                end_datetime = datetime.fromisoformat(end_datetime_str)
        

        # TODO : some of these will return a list and not a single response due to how the APIs work. Hence we need 
        # a flexible way to accept that and still be able to pull the content out.   create "content" abstract method?
        try:
            result = self._get_readings(
                start_datetime = start_datetime,
                end_datetime = end_datetime
            )
            if len(result) > 1:
                self.current_response = result[len(result)-1]
                responses = []
                for response in result:
                    if isinstance(response, dict):
                        responses.append(response)
                    else:
                        responses.append(json.loads(response.content))
            else:
                self.current_response = result[0]
                if isinstance(self.current_response, dict):
                    responses = [result[0]]
                else:
                    responses = [json.loads(result[0].content)]
            if isinstance(self.current_response, dict):
                self.response_data = self.current_response
            else:
                self.response_data = [json.loads(self.current_response.content)]

        except Exception as e:
            logging.error("Error getting reading from station {self.id}: {e}")
            raise e
        
        # If there's nothing to add to, do standard metadata/response list creation
        if add_to is None:
            add_to = self._initialize_metadata(start_datetime, end_datetime)
        
        # Otherwise add it, increase the count of responses supposed to be contained, 
        # add this one's timestamp list, and return
        for response in responses:
            add_to[0]['response_count'] += 1
            add_to[0]['response_datetime_utc' + str(add_to[0]['response_count'])] = self.request_datetime
            add_to.append(response)
        return add_to
    
    def transform(self, data = None):
        """
        Transforms data and return it in a standardized format. 
        data: optional input used to load in data if transform of existing data dictionary is required.
        """
        if data is None:
            data = self.response_data

        return self._transform(data)

    def current_response_data(self):
        json.loads(self.current_response._content)
        
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
    
class WeatherStationReadings(BaseModel):
    readings: list[WeatherStationReading] = list()
