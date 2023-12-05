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

#TODO see some code in models.py that should be here that is a new way to organize the data classes for validation and loading
#TODO get rid of madeup 2-character timezones - just use the standard IANA timezones used by python (and Operating systems) in ZoneInfo/tzdata packages
#   see models.py for example

import json, warnings, logging
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from abc import ABC, abstractmethod
from uuid import uuid4

# package local
from ewx_pws.time_intervals import is_tz_aware, UTCInterval
from importlib.metadata import version
from weather_stations import STATION_TYPE
from weather_stations.models import WeatherStationConfig, WeatherStationReadings, WeatherAPIData, WeatherAPIResponse

class GenericConfig(WeatherStationConfig):
    """This configuration is used for testing, dev and for base class.  Station specific config is simply stored
    in a dictionary"""
    # config:dict = {}

class WeatherStation(ABC):
    """abstract base class for a weather station to access it's API and retrieve data"""
    
    StationConfigClass = GenericConfig
    station_type = 'GENERIC'

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

        if isinstance(config,self.StationConfigClass):
            self.config = config
        elif isinstance(config, dict):
            self.config = self.StationConfigClass.model_validate(config)

        self._id = config.station_id
        # store latest resp object as returned from request
        self.current_response = None
        # structure for saving raw data along with metadata
        self.current_response_data = None
        
    ####### alternative constructors as class methods #########

    @classmethod
    def init_from_record(cls, config_record:dict):
        # attempt to build config object from config record
        station_config = cls.StationConfigClass.init_from_record(config_record)
        return( cls(station_config) )

    @classmethod
    def init_from_dict(cls, config:dict):
        """ accept a dictionary to create this class, rather than the config Type class"""
    
        # this will raise error if config dictionary is not correct
        station_config = GenericConfig.model_validate(config)
                    
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
            package_version  = version('ewx_pws')
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
            api_data = WeatherAPIData.model_validate(api_data)
        
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
    

