""" weather_stations/models.py

pydantic models and other support classes used by weather station class
"""

from requests import Response
from datetime import datetime
from uuid import uuid4
from pydantic import BaseModel, field_validator
from typing import Literal

# package local
from ewx_pws.time_intervals import is_utc, UTCInterval
from importlib.metadata import version
from weather_stations import STATION_TYPE

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
    """Base station configuration, includes common meta-data config common to all station types.  
    Must include a valid US Timezone code. 
    Weather stations sub-class this and add field specific to their configuration.  
    """
    station_id : str 
    install_date: datetime # the date the station started collecting data in it's location
    station_type : STATION_TYPE = "GENERIC"
    tz : TIMEZONE_CODE = 'ET' # description="US two-character time zone of the station location ( 'HT','AT','PT','MT','CT','ET')") 
    _tzlist: dict[str:str] = {
            'HT': 'US/Hawaii',
            'AT': 'US/Alaska',
            'PT': 'US/Pacific',
            'MT': 'US/Mountain',
            'CT': 'US/Central',
            'ET': 'US/Eastern'
            } 
    station_config:str  

    ### timezone formatting
    def pytz(self):
        """return valide python timezone from 2-char timezone code in config 
        for use in datetime module
        """
        return(self._tzlist[self.tz])
        
    ### unserializer/serializers for db/record storage that accommodate fields in subclasses consistently
    @classmethod
    def init_from_record(cls, config_record: dict[str]):
        """ create config obj from our standard serialization format (from disk/db/etc.  In the serialization format, additional station-specific
        fields are stored as a JSON dictionary in the 'station_config.   Base class does not use this"""
        
        # convert str of datetime into datatime format
        config_record['install_date'] = datetime.fromisoformat(config_record['install_date'])

        # station-type-specific config is held as JSON in a special field (station config). 
        # This unpacks and loads any items from that 'station_config' field up into the class
        if 'station_config' in config_record:
            config_record.update(json.loads(config_record['station_config']))
        
        return(cls.model_validate(config_record))
    
    def model_dump_record(self):
        """creates dict format useful to store in db or CSV that accommodates any extra fields present in a subclass
        are smushed into JSON and stored in a field "station_config"
         This way records from all types of stations can be saved in the same table file/format """
        
        # these are the standard column headers for csv/db records
        record_fields = set('station_id', 'install_date', 'station_type','tz')

        # start by creating dict of all fields
        all_fields = self.dict()
        
        # subset for the main columns we have in db records
        record = {k: all_fields[k] for k in record_fields}
        # create dict of all remaining subclass-specific fields, if any
        station_specific = {k: all_fields[k] for k in self.__field_set__.difference(record_fields)}
        
        # put all station_specific (subclass) fields  into JSON field called 'station_config' 
        record['station_config'] = json.dumps(station_specific)

        # fix up fields as necessary for str storage
        record['install_date'] = record['install_date'].isoformat(),
    
        return(record)

class WeatherAPIResponse(BaseModel):
    """ extract data elements of a requests.Response for persisting/serializing"""
    url: str
    status_code: str
    reason: str 
    text: str 
    content: bytes
    
    @classmethod
    def from_response(cls, response:Response):
        """ create data class from a python response object. We only need a subset of properties of the response object"""
        return cls(
            url =  response.request.url,
            status_code = str(response.status_code),
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
    #
    station_id: str
    station_type: str
    request_id: str = str(uuid4())  # unique ID identifying this request event
    request_datetime: datetime
    time_interval: UTCInterval
    package_version: str  = version('ewx_pws')
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
    atemp : float or None = None   # celsius 
    pcpn  : float or None = None   # mm, > 0
    relh  : float or None = None   # percent
    lws0  : float or None = None   # this is an nominal reading or 0 or 1 (wet / not wet)
    
    @field_validator('request_datetime', 'data_datetime')
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
        return(cls.model_validate(reading))


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
