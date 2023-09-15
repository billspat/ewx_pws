"""
Module to hold constants, types  and parent class for weather stations.  weather station modules 
will import this module. 

## data process: 

0. read config from db, given station type ="ONSET"
1. make station
   `station = Onset(config)`
2. set time period
    s,e UTC timestamps determined by caller
   `interval = UTCInterval(s,e)` 
3. make request
   `api_data = station.get_readings(interval.start, interval.end)  # WeatherAPIData `
    - store this in the object.  raw responses are saved in api_data.responses 

4. save to raw api data database
    TBD but could just append to a log raw_api_data_log.append(api_data)

5. transform to tabular data
    readings = transform(api_data) ( list of weather_readings)
        call _transform just for response JSON 
        


WeatherStation.getreadings returns a complex type that is a list of dictionary (should it be a class?)
"""

import pytz, json, warnings, logging
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
# from pytz import timezone
from requests import Response, Request
from abc import ABC, abstractmethod
from uuid import uuid4


# typing and Pydantic 
from pydantic import BaseModel, Field, ValidationError, validator
from typing import Literal

# package local
from ewx_pws.time_intervals import is_tz_aware, is_utc, previous_fourteen_minute_period, UTCInterval
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
    install_date: datetime # the date the station started collecting data in it's location
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

class GenericConfig(WeatherStationConfig):
    """This configuration is used for testing, dev and for base class.  Station specific config is simply stored
    in a dictionary"""
    config:dict = {}

class WeatherAPIResponse(BaseModel):
    """ extract data elements of a requests.Response for persisting/serializing"""
    url: str
    status_code: str
    reason: str 
    text: str 
    content: bytes

    @classmethod
    def from_response(cls, response:Response):
        return cls(
            url =  response.request.url,
            status_code = response.status_code,
            reason = response.reason, 
            text = response.text, 
            content = response.content
        )

class WeatherAPIData(BaseModel):
    """ data structure to hold the raw response data from a request for serialization
    just the necessary and serializable elements of 
    requests.Response ( https://requests.readthedocs.io/en/latest/api/#requests.Response ) 
    along with meta data. 
    This is use to store the outputs from the API for debugging
    """
    
    station_id: str
    station_type: str
    request_id: str = Field(default =str(uuid4()))  # unique ID identifying this request event
    request_datetime: datetime
    time_interval: UTCInterval
    package_version: str  = Field(default = version('ewx_pws'))

    responses: list[WeatherAPIResponse]

    def key(self):
        """ unique string from this data for creating records or filenames"""
        if self.time_interval:
            timestamp = int(self.time_interval.start.timestamp())
            k = f"{self.station_id}_{timestamp}_{self.request_id}"
            return(k)
        else:
            raise ValueError("required time interval is blank, can't create key for this WeatherAPIData object")
        
    def model_dump_record(self):
        """ export to dict but only meta-data; keep the responses as json to store in 1 field"""
        responses_json = "[" + ",".join([response.json() for response in self.responses]) + "]"

        return {
         'station_id' : self.station_id,
        'station_type' : self.station_type,
        'request_id' : self.request_id,
        'request_datetime' : self.request_datetime,
        'time_interval' : self.time_interval,
        'package_version' : self.package_version,
        'responses' : responses_json
        }
        

class WeatherStationReading(BaseModel):
    """row of transformed weather data: combination of sensor values  
    (temperature, etc), and the metadata of their collection 
    (station, request, etc)request metadata plus transformed data from each API, 
     suitable for tabular output.  """
    station_id : str
    station_type: str
    request_id : str # unique ID of the request event to link with raw api output
    request_datetime : datetime 
    time_interval: UTCInterval

    # TODO error status of these data 
    # TODO 'source' metadata for each value, 
    # e.g. atemp_src = "API" or similar

    data_datetime : datetime    
    atemp : float or None = None      # celsius 
    pcpn  : float or None = None        # mm, > 0
    relh  : float or None = None       # percent
    lws0  : float or None = None       # this is an nominal reading or 0 or 1 (wet / not wet)

    @validator('request_datetime', 'data_datetime',allow_reuse=True)
    def check_datetime_utc(cls, field):
        if is_utc(field):
            return field
        raise ValueError("datetime fields must have a timezone and must be UTC")
    
    @classmethod
    def from_transformed_reading(cls, reading, weather_api_data: WeatherAPIData):
        """ add required metadata to dict of transformed weather data"""
        reading['station_id']  = weather_api_data.station_id
        reading['station_type'] = weather_api_data.station_type
        reading['request_id'] = weather_api_data.request_id
        reading['request_datetime'] = weather_api_data.request_datetime 
        reading['time_interval'] = weather_api_data.time_interval
        
        return(cls.parse_obj(reading))


class WeatherStationReadings(BaseModel):
    """ list of readings suitable for tabular output,
    default is an empty list"""
    readings: list[WeatherStationReading] = list()

    @classmethod
    def from_transformed_readings(cls, transformed_readings, weather_api_data : WeatherAPIData):
        """a reading above is station/request metadata for each of the 
        actual outputs from the API, which come as a list from transform
        Given list of dict of weather data output from transform, 
        and weather api (meta)data , create a list of reading models"""
        readings = []
        for reading in transformed_readings:
            wsr = WeatherStationReading.from_transformed_reading(reading, weather_api_data)
            readings.append(wsr)
        
        return(cls(readings = readings))
    
    def model_dump_record(self):
        # for future version of pydantic, use model_dump()
        return([reading.dict() for reading in self.readings])
        
    
    def key(self):
        """ create a unique value for this set of readings, using values from first reading only. 
        for storing in db or creating filenames. 
        Not a long term solution but in place to create filenames to save data
        """

        r = self.readings[0]
        timestamp = int(r.time_interval.start.timestamp())
        
        k = f"{r.station_id}_{timestamp}_{r.request_id}"

        return(k)


##########################################################
########        WeatherStation Base Class         ########
##########################################################

class WeatherStation(ABC):
    """abstract base class for a weather station to access it's API and retrieve data"""
    
    # used by subclasses as default when there is no data from station
    empty_response = ['{}']
    
    @property
    @abstractmethod
    def interval_min(self):
        """interval between weather readings in minutes.   Hourly frequency is interval_min/60 """
        pass

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

        # TODO remove this hard-code positioning , which assumes station_config is in specific order
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
        return(cls.init_from_dict(station_config_dict))
                
    # convenience/hiding methods
    @property
    def id(self):
        return self._id
    
    @property
    def station_type(self):
        return(self.config.station_type)
    

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
    
    #######################
    #### primary class interfaces

    def get_readings(self, start_datetime : datetime = None, end_datetime : datetime = None)->WeatherAPIData:
        """prepare start/end times and other params generically and then call station-specific method with that.
        start_datetime: date time in UTC time zone
        end_datetime: date time in UTC time zone.  If start_datetime is empty this is ignored 
        add_to: option for list to be passed in already containing metadata to be added to
        """
        
        if end_datetime and start_datetime:
            interval = UTCInterval(start = start_datetime, end = end_datetime)

        elif end_datetime and not start_datetime:
            interval = UTCInterval.previous_interval(end_datetime)
        
        elif not end_datetime and start_datetime: 
            interval = UTCInterval.previous_interval(start_datetime + timedelta(minutes= 14),delta_mins=14)
        
        else : # both are null
            interval = UTCInterval.previous_fifteen_minutes()
       
        # call the sub-class to pull data from the station vendor API
        # save the response object in this object
        try:
            request_time = datetime.utcnow().astimezone(timezone.utc)
            responses = self._get_readings(
                    start_datetime = interval.start,
                    end_datetime = interval.end
            )

        except Exception as e:
            logging.error("Error getting reading from station {self.id}: {e}")
            raise e

        # ensure what is returned is a list, as some stations types return a list of responses
        if not isinstance(responses, list):
            responses = [responses]
            # list of requests.response obj

        # convert each to our serializer model 
        weather_api_responses = [WeatherAPIResponse.from_response(r) for r in responses]

        # save serializable response list and metadata in the object for debugging
        self.current_response = weather_api_responses
        self.current_response_data = WeatherAPIData(
            request_id = str(uuid4()), 
            station_id = self.id,
            station_type = self.config.station_type,
            request_datetime = request_time,
            time_interval = interval,
            responses = weather_api_responses,
            package_version  = 0.1 # version('ewx_pws')
        )

        return(self.current_response_data)


    def transform(self, api_data:WeatherAPIData = None)->WeatherStationReadings:
        """
        Transforms data and return it in a standardized format. 
        data: optional input used to load in data if transform of existing data dictionary is required.
        Usage from stored data
        dict_api_record = db.get_by_data(something) or get_by_req_id(request_id)
        api_data = optional WeatherAPIData (object or dict)
        """

        # if no data was sent, use data stored from latest request
        api_data = api_data or self.current_response_data

        # weather data must be in special format for this to work
        # this will raise exception if it's not formatted correctly
        if api_data is not None and not isinstance(api_data, WeatherAPIData) :
            # assuming api_data was unserialized (CSV, db, etc), build the 
            # data class that holds it
            # this will raise exceptions if data is not in correct format
            api_data = WeatherAPIData.parse_obj(api_data)
        
        # responses are store in array since some stations return an array (one element per day)
        # each array item when transformed will output  list of data values
        transformed_readings = []
        for weather_api_response in api_data.responses:
            # call station subclass to interpret response content into a list
            tr =  self._transform(weather_api_response.text) # JSON str
            logging.debug(f"transformed_reading type {type(tr)}: {tr}")
            if tr is not None:
                transformed_readings.extend(tr)
  
        # use data model class method to combine meta data and reading values
        readings = WeatherStationReadings.from_transformed_readings(transformed_readings, api_data)
        return readings
        
    ################### station class utilities

    def dt_utc_from_str(self, datetime_str: str)->datetime:
        """ To enable converting timestamp strings from api responses that 
            1) are in in station local time
            2) don't have a timezone info in the string (most don't)
            use the station's config timezone to convert to a timestamp str
            to a UTC timezone aware datateime
        """
        
        dt = datetime.fromisoformat(datetime_str)
        #
        if not is_tz_aware(dt):
            station_timezone_str = self.config._tzlist[self.config.tz]
            # add station timezone
            dt = dt.replace(tzinfo = ZoneInfo(station_timezone_str))
        else:
            # the string already has a timezone, could be anytimezone
            # should that be an error condition?

            pass

        return(dt.astimezone(timezone.utc))

    @property
    def station_tz(self):
        """ config class stores tz as 2-char; convert into IANA timezone
        return zoneinfo.ZoneInfo object for use with astimezone() o replace() fns
        """
        return ZoneInfo(self.config._tzlist[self.config.tz])
        
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
    

