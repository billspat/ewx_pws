"""Main module."""


import json, os,csv, warnings, logging
from datetime import datetime, timedelta
from dotenv import load_dotenv

from ewx_pws.weather_stations import WeatherStation, STATION_TYPE, STATION_TYPE_LIST
from ewx_pws.davis import DavisStation, DavisConfig
from ewx_pws.locomos import LocomosStation, LocomosConfig
from ewx_pws.rainwise import RainwiseStation, RainwiseConfig
from ewx_pws.spectrum import SpectrumStation, SpectrumConfig
from ewx_pws.onset import OnsetStation, OnsetConfig
from ewx_pws.zentra import ZentraStation, ZentraConfig


from ewx_pws.time_intervals import previous_fifteen_minute_period

load_dotenv()
logging.basicConfig(level=logging.NOTSET, format='%(asctime)s-%(process)d-%(levelname)s-%(message)s')

STATION_CLASS_TYPES = {'ZENTRA': ZentraStation, 'ONSET': OnsetStation, 'DAVIS': DavisStation,'RAINWISE': RainwiseStation, 'SPECTRUM':SpectrumStation, 'LOCOMOS':LocomosStation }
CONFIG_CLASS_TYPES = {'ZENTRA': ZentraConfig, 'ONSET': OnsetConfig, 'DAVIS': DavisConfig,'RAINWISE': RainwiseConfig, 'SPECTRUM':SpectrumConfig, 'LOCOMOS':LocomosConfig }

def get_readings(stations:list,
                start_datetime_str:str = None,
                end_datetime_str:str = None,
                transformed_only = True):
    """get readings from a list of stations
    
    stations: dict
        dictionary of station configs, keyed on station_id, station_type and config
    
    """
    try:
        readings = {}
        for station in stations:
            reading = station.get_readings(
                        station_type = station['station_type'], 
                        station_config = station['station_config'],
                        start_datetime_str = start_datetime_str,
                        end_datetime_str = end_datetime_str)

            readings[station['station_id']] =  { 
                'station_id' : station['station_id'], 'station_type' : station['station_type'],
                'start': start_datetime_str,
                'end':end_datetime_str,
                'data' :  station.transform(data=reading)
            }
            if not transformed_only:
                readings[station['station_id']]['json'] = reading
    except Exception as e:
        logging.error('Could not collect readings with error {}'.format(e))
        
# TODO create a better data structure for inserting into CSV or DB table
     
    return(readings)

    
def stations_from_env():
    """ this is a temporary cludge to convert the old style dot env into new listing"""
    
    stations_available  = [s for s in STATION_TYPE_LIST if s.upper() in os.environ.keys()]
    
    stations = {}
    for station_name in stations_available:
        station_config = json.loads(os.environ[station_name])
        station_config["station_id"] = f"{station_name}_1"
        station_config["station_name"] =  station_name
        station_config["install_date"] = datetime.fromisoformat(station_config['install_date'])

        stations[station_name] = weather_station_factory(station_config)

    # most code is expecting a list, but change to use a dict
    return list(stations.values())

def read_station_configs(csv_file_path:str)->dict:
    """read CSV in standard station config format, and flatten into dict useable by station configs. 
    this method does not create stations, only formats a config file for use by package or testing
    csv_file_path: path to CSV file
    returns: list configs
    """

    configs = {}
    try:
        if not os.path.exists(csv_file_path): 
            warnings.warn(Warning("File not found {}".format(csv_file_path)))
            return None
        
        station_field_names = ['station_id','station_type','install_date','tz','station_config'] # ["station_id", "station_type", "station_config"]
        header = True

        # Checks for header, ID column, and ensures file isn't just empty
        with open(csv_file_path, "r") as csvfile:
            line = csvfile.readline()
            if not line:
                warnings.warn(Warning("emptycsv, {} read as empty".format(csv_file_path)))
                return None
            if '{' in line:
                header = False
            if line.lower().startswith("id,"):
                station_field_names.insert(0, "id")

        with open(csv_file_path, "r") as csvfile:
            csvreader = csv.DictReader(csvfile,  
                                       fieldnames = station_field_names, 
                                       delimiter=",", quotechar="'") # 
            if header:
                next(csvreader)

            for row in csvreader:
                try:
                    # config is saved as a JSON dict - the expands the config from JSON into row of station data
                    row.update(json.loads(row['station_config']))

                except ValueError as ex:
                    logging.error(("ValueError: Invalid json encountered reading in ewx_pws.py.stations_from_file {}:\n {}".format(csv_file_path, ex)))

                    raise ValueError
                
                row['install_date'] = datetime.fromisoformat(row['install_date'])
                configs[row['station_id']] = row

    except TypeError as ex:
        logging.error("TypeError: Exception encountered reading in ewx_pws.py.stations_from_file {}:\n {}".format(csv_file_path, ex))
        raise ex
    
    return(configs)


def station_dict_from_file(csv_file_path:str):
    """ given a csv file of stations, read them into standard format
    param csv_file_path path to a csv file with specific format for stations
    returns a dictionary of dictionaries, keyed on 'station ID'
    """
    stations = {}
    configs = read_station_configs(csv_file_path)


    if configs is None: 
        # trying both log and warnings until system deployment is finalized
        # logging.warning("config file returned no configs")
        # warnings.warn("config file has no configs, empty station list")
        raise ValueError(f"file {csv_file_path} returned empty config list")
    
    if not isinstance(configs,dict):
        raise ValueError(f"file {csv_file_path} returned non-list")
        logging.warning("config file returned something other than a list ")
        warnings.warn("config file returned something other than a list, empty station list")
        return {}
    
    for station_id in configs:
        station_config = configs[station_id]
        logging.debug(f"instantiating {station_id}")
        if 'station_type' in station_config and station_config['station_type'] in STATION_CLASS_TYPES:
            try:
                stations[station_config['station_id']] = weather_station_factory(station_config) # row['station_type'], row['station_config'], row['station_id'])
            except TypeError as ex:
                logging.error("TypeError: Exception encountered reading in ewx_pws.py.stations_from_file {}:\n {}".format(csv_file_path, ex))
                raise ex
        else:
            raise ValueError( f"station type {station_config['station_type']} ")
    
    return stations

def stations_from_file(csv_file_path:str)->list:
    """ for some legacy code, take the dict output to read station config file, and return an unkeyed list of station objects
    The stations all have a 'id' property so can find stations without being keyed on id"""
    return list(station_dict_from_file(csv_file_path).values())

### dict or list???  these assume station lists are dicts keyed on id

def station_types_present(station_configs:dict)->list[str]:
    """which station types are present in the config dictionary sent """
    station_types = list(set([station_config['station_type'] for station_config in station_configs]))
    return(station_types)


def configs_of_type(station_configs:dict, station_type)->list:
    """given a station type, return all the stations of that type"""
    
    # allow list OR dict by converting to list if a dict is sent
    if isinstance(station_configs, dict): station_configs = station_configs.values() 

    s = list(
        filter(lambda c: station_type == c['station_type'],  station_configs)
        )

    # for station_config in station_configs.values():
    #     if station_type == station_config['station_type']:
    #         s.append(station_config)
    
    return(s)


def stations_of_type(stations, station_type)->list:
    """from a dictionary of station objects, filter out for one type of station"""
    # allow list OR dict by converting to list if a dict is sent
    if isinstance(stations, dict): stations = stations.values() 

    s = list(
        filter(lambda station: station.config.station_type == station_type,  stations)
        )

    return(s)


# def weather_station_factory(station_type:STATION_TYPE, config:dict, station_id:str) -> type[WeatherStation]:
def weather_station_factory(station_config:dict, station_class_types = STATION_CLASS_TYPES) -> type[WeatherStation]:
    """"given a dictionary of configuration information (e.g. from CSV), create a station object for that type
    raises an exception if can't create the station because of bad configuration. 
    
    station_config: single dict of station config """

    try:
        #config['station_id'] = station_id
        station_type = station_config['station_type']
        station = station_class_types[station_type].init_from_dict(station_config)
    except Exception as e: 
        logging.error(f"could not create station type {station_type} id {station_config['station_id']} from config: {e}")
        raise e
    
    return station 



def validate_station_config(station_type:STATION_TYPE, station_config:dict)->bool:
    """  this tests the station configuration as correct by 1) attempting to create the station object 2) get a sample reading
    
    returns T or F only """
    
    # attempt to create the station and see what happens, return F if it doesn't work
    try:
        test_station = weather_station_factory(station_type, station_config)
    except Exception as e:
        logging.error("station config error for {station_type}")
        return False    
    
    # attempt to get a sample reading and see what happens, return T if it works
    try:
        r = test_station.get_test_reading()
        if r:
            return True
    except Exception as e:
        logging.error("could not get reading for station type {station_type} id {station.id}: {e}")
        return False
    # false here ==> config is incorrect OR station is offline, don't know which

## random python notes 
# to convert the dictionary of stations into a simple list
# station_list = [s for s in stations.values()]
#  to get the first row in the dict of dict (for testing )
# sd = stations[list(stations.keys())[0]]


# this was in the stations_from_file function, moved into it's own function

    # try:
    #     if not os.path.exists(csv_file_path): 
    #         warnings.warn(Warning("File not found {}".format(csv_file_path)))
    #         return None
        
    #     station_field_names = ['station_id','station_type','install_date','tz','station_config'] # ["station_id", "station_type", "station_config"]
    #     stations = {}
    #     header = True

    #     # Checks for header, ID column, and ensures file isn't just empty
    #     with open(csv_file_path, "r") as csvfile:
    #         line = csvfile.readline()
    #         if not line:
    #             warnings.warn(Warning("emptycsv, {} read as empty".format(csv_file_path)))
    #             return None
    #         if '{' in line:
    #             header = False
    #         if line.lower().startswith("id,"):
    #             station_field_names.insert(0, "id")

    #     with open(csv_file_path, "r") as csvfile:
    #         csvreader = csv.DictReader(csvfile,  
    #                                    fieldnames = station_field_names, 
    #                                    delimiter=",", quotechar="'") # 
    #         if header:
    #             next(csvreader)

    #         for row in csvreader:
    #             try:
    #                 # config is saved as a JSON dict - the expands the config from JSON into row of station data
    #                 row.update(json.loads(row['station_config']))

    #             except ValueError as ex:
    #                 logging.debug(row['station_id'])
    #                 logging.debug(row['station_config'] )
    #                 logging.error(("ValueError: Invalid json encountered reading in ewx_pws.py.stations_from_file {}:\n {}".format(csv_file_path, ex)))

    #                 raise ValueError
                
    #             row['install_date'] = datetime.fromisoformat(row['install_date'])