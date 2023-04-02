"""Main module."""


import json, os,csv, warnings
from datetime import datetime, timedelta
from multiweatherapi import multiweatherapi
from dotenv import load_dotenv

from ewx_pws.weather_stations import WeatherStation, STATION_TYPE
from ewx_pws.davis import DavisStation
from ewx_pws.rainwise import RainwiseStation
from ewx_pws.spectrum import SpectrumStation
from ewx_pws.onset import OnsetStation
from ewx_pws.zentra import ZentraStation


from ewx_pws.time_intervals import previous_fifteen_minute_period

load_dotenv()

### CONSTANTS

STATION_TYPES = ['DAVIS', 'CAMPBELL', 'ONSET', 'RAINWISE', 'SPECTRUM', 'ZENTRA']

def get_reading(station_type, station_config,
                start_datetime_str = None,
                end_datetime_str = None):
    """wrapper for MultiweatherAPI to pull from station api for speciric time period. 

    Parameters
    ----------
    station_type : str
        One of station types support by this package.  see STATION_TYPES
    start_datetime_str : str
        optional date time at the beginning of period (e.g. 1:00).  If not included, uses previous 15 minute period
    end_datetime_str : str
        optional date time str for end of period (e.g. 1:15)   If not included, uses previous 15 minute period

    Returns
    -------
    multiweatherapi resp object.  see documentation in that packabe
        dict-like object resp_raw = JSON, resp_transformed = dictionary

    Examples
    --------
    >>> reading = get_reading('DAVIS', {config:'value', etc:'value'})
    """
    if not start_datetime_str:
        # no start ?  Use the internval 15 minutees before present timee.  see module for details.  Ignore end time if it's sent
        start_datetime,end_datetime =  previous_fifteen_minute_period()
    else:
        start_datetime = datetime.fromisoformat(start_datetime_str)
        if not end_datetime_str:
            # no end time, make end time 15 minutes from stard time given.  
            end_datetime = start_datetime + timedelta(minutes= 15)
        else:
            end_datetime = datetime.fromisoformat(end_datetime_str)


    params = station_config
    params['start_datetime'] = start_datetime
    params['end_datetime'] = end_datetime
    params['tz'] = 'ET'

    try:
        mwapi_resp = multiweatherapi.get_reading(station_type, **params)
    except Exception as e:
        raise e

    # includes mwapi_resp.resp_raw, and mwapi_resp.resp_transformed

    return mwapi_resp


def get_readings(stations:dict,
                start_datetime_str:str = None,
                end_datetime_str:str = None,
                transformed_only = True):
    """get readings from a list of stations
    
    stations: dict
        dictionary of station configs, keyed on station_id, station_type and config
        
    
    """
    
    readings = {}
    for station_id in stations:
        station = stations[station_id]
        mwapi_resp = get_reading(
                    station_type = station['station_type'], 
                    station_config = station['station_config'],
                    start_datetime_str = start_datetime_str,
                    end_datetime_str = end_datetime_str)

        readings[station_id] =  { 
             'station_id' : station['station_id'], 'station_type' : station['station_type'],
             'start': start_datetime_str,
             'end':end_datetime_str,
             'json' : mwapi_resp.resp_raw,
             'data' :  mwapi_resp.resp_transformed
        }
        
# TODO create a better data structure for inserting into CSV or DB table
     
    return(readings)

    
def stations_from_env():
    """ this is a temporary cludge to convert the old style dot env into new listing"""
    
    stations_available  = [s for s in STATION_TYPES if s.upper() in os.environ.keys()]
    stations = {}
    for station_name in stations_available:
        stations[station_name] = {
            "station_id"     : f"{station_name}_1",
            "station_type"   : station_name,
            "station_config" : json.loads(os.environ[station_name])
        }
        
    return stations


def stations_from_file(csv_file_path:str):
    """ given a csv file of stations, read them into standard format
    returns a dictionary of dictionaries, keyed on 'station ID'
    
    """
    station_field_names = ["station_id", "station_type", "station_config"]
    
    if not os.path.exists(csv_file_path): 
        warnings.warn(f"file not found {csv_file_path}")
        return None
    
    stations = {}
    with open(csv_file_path, "r") as csvfile:
        csvreader = csv.DictReader(csvfile,  fieldnames = station_field_names, delimiter=",", quotechar="'") # 
        header = next(csvreader)
        for row in csvreader:
            station_id = row['station_id']
            # try
            print(row['station_config'] )
            row['station_config'] = json.loads(row['station_config'])
            stations[station_id] = row
    
    return stations    


#### using WeatherStation classes
# METHODS UTILIZING CLASS : 

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

## random python notes 
# to convert the dictionary of stations into a simple list
# station_list = [s for s in stations.values()]
#  to get the first row in the dict of dict (for testing )
# sd = stations[list(stations.keys())[0]]