# """WIP start on a class to hold this info, 
# not sure if a class is warranted for this yet - why would we need to preseve state?me"""

# from multiweatherapi import multiweatherapi

import requests, pytz, json, warnings
from datetime import datetime, timedelta, timezone
# from pytz import timezone
from requests import Session, Request

# typing and Pydantic 
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field
from typing import Literal

# package local
from ewx_pws.time_intervals import previous_fourteen_minute_period, previous_fifteen_minute_period, fifteen_minute_mark


#############
# GLOBALS and TYPE MODELS

# station type type, like an enum
STATION_TYPE = Literal['ZENTRA', 'ONSET', 'DAVIS', 'RAINWISE', 'SPECTRUM', 'GENERIC']  # generic type is a hack for testing

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
    def _get_readings(self,params):
        """create API request and return str of json"""
        # get auth
        print(f" this would be a reading from {self.id} for {params.get('start_datetime')} to {params.get('end_datetime')}")
        return "{}"
    
    # override as necessary for sub-classes
    def _format_time(self, dt:datetime)->str:
        """
        ensure correctr formating of a date/time parameter for API request, convert to 
        UTC or local as needed.  The generic converter simply converts to 
        """
        return(dt.strftime('%Y-%m-%d %H:%M:%S'))
    
    # this is a separate method so that it may be overriden if necessary by sub-classes
    def _format_response(self, api_response, start_datetime_str, end_datetime_str, request_time):
        """ modify format of response for consistency and to add meta data.  """
         # TODO: add meta data to response so it can be identified for future diagnostics
        reading_metadata = {
            "station_type": self.config.station_type,
            "station_id": self.id,
            "timezone": self.config.tz, 
            "start_datetime": start_datetime_str,
            "end_datetime": end_datetime_str,
            "request_time": request_time,
            "package_version": '0.1'
        }
        
        return [reading_metadata].append(api_response)
        
    # user api method that has optional start & end times
    def get_readings(self,start_datetime_str = None, end_datetime_str = None):
        """prepare start/end times and other params generically and then call station-specific method with that.
        start_datetime_str: optional date time interpretable string in UTC time zone
        end_datetime_str: optional datetime interpretable string in UTC time zone.  If start_datetime_str is empty this is ignored 
        """
        # for meta-data
        request_time = datetime.now(tz=timezone.utc)
        
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
        
        #TODO: !!! ensure all datetimes are UTC.  perhaps that could all be in the _format_time() method

        # TODO : some of these will return a list and not a single response due to how the APIs work. Hence we need 
        # a flexible way to accept that and still be able to pull the content out.   create "content" abstract method?
        try:
            self.current_response = self._get_readings(
                start_datetime,
                end_datetime
            )

        except Exception as e:
            print("Error getting reading from station {self.id}: {e}")
            raise e        
    
        # TODO add meta data in consistent way to response data for diagnostics    
        response_data = json.loads(self.current_response.content)


        # this is saved as a class attribute but returned for other processing 
        return response_data

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
    




##################################
# Placeholder unfinished classes #
##################################

########## DAVIS ############
class DavisConfig(WeatherStationConfig):
    station_type : STATION_TYPE = "DAVIS"   
        
class DavisStation(WeatherStation):
    def __init__(self,config:WeatherStationConfig):
        self.station_type = 'davis'
        super().__init__(config)
    
    def _check_config(self):
        warnings("not implemented")
        return True
    
    def _get_readings(self):
        warnings("not implemented")
        return self.empty_response


########## RAINWISE ############
class RainwiseConfig(WeatherStationConfig):
    station_type : STATION_TYPE = "RAINWISE"

class RainwiseStation(WeatherStation):
    def __init__(self,config:WeatherStationConfig):
        self.station_type = 'rainwise'
        super().__init__(config)

    def _check_config(self):
        warnings("not implemented")
        return True
    
    def _get_readings(self):
        warnings("not implemented")
        return self.empty_response
    
########## SPECTRUM ############
class SpectrumConfig(WeatherStationConfig):
    station_type : STATION_TYPE = "SPECTRUM"

class SpectrumStation(WeatherStation):
    def __init__(self,config:WeatherStationConfig):
        self.station_type = 'spectrum'
        super().__init__(config)  
        
    def _check_config(self):
        return True
    
    def _get_readings(self):
        warnings("not implemented")
        return self.empty_response


########## ZENTRA ############
class ZentraConfig(WeatherStationConfig):
    station_type : STATION_TYPE = "ZENTRA"
    
class ZentraStation(WeatherStation):
    """Access the MeterGroup weather api for Zentra type Weather Stations"""    
    def __init__(self,config:ZentraConfig):
        super().__init__(config)
        
    def _check_config(self):
        warnings("not implemented")
        return True
    
    def _get_readings(self, params):
        warnings.warn("not implemented")
        return self.empty_response
    

    
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
    

