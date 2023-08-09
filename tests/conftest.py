"""conftest.py pytest suite configuration"""

###########################
## IMPORTS

import pytest, random, string, json
from os import environ
import sys
import importlib
from ewx_pws.ewx_pws import logging
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
# from tempfile import NamedTemporaryFile


###########################
## CONFIG FROM IMPORTED CONSTANTS
from ewx_pws.weather_stations import STATION_TYPE_LIST
# TODO improve this obvious kludge to avoid testing these types
if 'GENERIC' in STATION_TYPE_LIST:
    STATION_TYPE_LIST.remove('GENERIC')

###########################
## CONFIG FROM ENVIRONMENT
from dotenv import load_dotenv
# project wide .env
load_dotenv()
# testing .env
load_dotenv('tests/.env')

###########################
## CONFIG FROM PYTEST COMMAND LINE ARG(S)
def pytest_addoption(parser):
    parser.addoption(
        "--stationtype",
        action="store",
        default=None,
        help="station type to test, Default = All",
        choices=STATION_TYPE_LIST
    )

###########################
## PYTEST ITERATE THROUGH ALL STATION TYPES FROM CONFIG
def pytest_generate_tests(metafunc):
    """parameterize command line options to inject into every test, specifically vendor
    If a vendor is passed on command line, use that, else use all vendors"""
    # This is called for every test. Only get/set command line arguments
    # if the argument is specified in the list of test "fixturenames".

    stationtype_option = metafunc.config.getoption("stationtype")

    # for those tests that require a station_type .. use code to inject the option or check for param and also for config
    if "station_type" in metafunc.fixturenames:
        if stationtype_option is not None:
            stationtype_option = stationtype_option.upper()
            if not stationtype_option in STATION_TYPE_LIST:
                # station type on command line invalid, abort testing
                sys.exit(1)
            else:
                types_to_test = [stationtype_option]      
            
            # metafunc.parametrize('vendor', [vendor_option.upper()])
            # TODO more elegant way to bug out
            
        else:
            types_to_test = STATION_TYPE_LIST

            # metafunc.parametrize('vendor', all_vendors)
        
        # ensure there is valid configuration for the type(s) to test
        # TODO check against the fixture that loads config from disk
        # for now just assume they are all available

        testable_station_types = types_to_test

        metafunc.parametrize('station_type', testable_station_types)

###########################
## HANDY VALUES
@pytest.fixture
def random_string():
    """pytest fixture returns a string"""
    length = 10
    letters = string.ascii_lowercase
    return(''.join(random.choice(letters) for i in range(length)))

@pytest.fixture
def time_interval(tzstr='US/Eastern'):
    """ returns tuple of localized start/end time that is literal, 1am first of current month"""
    # TODO make this random day/time within 14d of current time
    tz = ZoneInfo(tzstr)
    rn = datetime.now(tz)

    # randomize time in recent past
    from random import randrange
    hour_delta = randrange(23)
    minute_delta = randrange(59)
    day_delta = randrange(1)
    
    interval_minutes = 30
    end_datetime = (rn - timedelta(days = day_delta, hours =hour_delta, minutes = minute_delta)).astimezone(tz) #  datetime(year= rn.year, month = rn.month, day=1, hour=1, minute=19, second=0).astimezone(tz)
    start_datetime = (end_datetime - timedelta(minutes = interval_minutes)).astimezone(tz)

    #sdt=datetime(year= rn.year, month = rn.month, day=1, hour=1, minute=0, second=0).astimezone(tz)
    #edt=datetime(year= rn.year, month = rn.month, day=1, hour=1, minute=19, second=0).astimezone(tz)

    return( (start_datetime, end_datetime ) )

@pytest.fixture
def utc_time_interval(time_interval):
    """ return an tuple of start/end arbitrary time interval in as timezone.utc time
    just convert the fixture above to timezone.utc"""
    s,e = time_interval
    return( (s.astimezone(timezone.utc), e.astimezone(timezone.utc)))
 

###########################
## CONFIG FROM FIXTURES (made up and real)
@pytest.fixture
def fake_stations_list():
    """this is fake data and won't connect to any real station API.  The API keys look real but are made up
    return List, each station type has exactly one row (no duplicate station types)"""
    return [
        ['fake_zentra','ZENTRA','{"sn":"z1-1234","token":"d5b8f6391ac38bad6f0b51d7a718b9e3e31eec81","tz":"ET"}'],
        ['fake_davis','DAVIS','{"sn":"123456","apikey":"gtqdcbirudd1sarq6esbvorfj6tw67ao","apisec":"0286g8zxfvr77yhdx3pcwnnqqstdwqel","tz":"ET"}'],
        ['fake_spectrum','SPECTRUM','{"sn":"12345678","apikey":"c3a2f80786398e656b08677b7a511a59","tz":"ET"}'],
        ['fake_onset', 'ONSET','{"sn":"12345678","client_id":"Enviroweather_WS","client_secret":"75d2b7f58f5d0cac689f6b9716348bf264158ca9","ret_form":"JSON","user_id":"12345","sensor_sn":{"atemp":"21079936-1","pcpn":"21085496-1","relh":"21079936-2"},"tz":"ET"}'],
        ['fake_rainwise', 'RAINWISE','{"sid":"lc2M22K4G99pLgR4Gu09Xw35NulgZMc7","pid":"lc2M22K4G99pLgR4Gu09Xw35NulgZMc7","ret_form":"json","mac":"907592476392","username":"907592476392","tz":"ET"}'],
        ['fake_locomos', 'LOCOMOS','{"token":"EIBF-aGJGzUaH0tTuvYtgzpCoHW88XS6PDF","id":"XmydER6iPF7VTixSX2JXQkPd", "tz":"ET"}'],
        ['fake_generic','GENERIC','{"sn":"fake", "tz":"ET"}']
    ]
  
    
@pytest.fixture
def fake_station_configs(fake_stations_list):
    """using the fake data above, reform into dictionaries of config
    return: dict of fake configs, only one entry per station type"""
    
    # TODO: make the env file JSON dictionary keys match the config dictionary keys. 
    # THIS ASSUMES KEYS ARE IN A SPECIFIC ORDER AND DOES NOT PULL BY NAME.   
    fake_configs = {}
    for fs in fake_stations_list:
        fake_config = json.loads(fs[2])
        station_type = fs[1]
        station_id = fs[0]
        fake_config.update({'station_id': station_id, 'station_type': station_type})
        fake_configs[station_type] = fake_config
    
    return fake_configs


@pytest.fixture
def station_dict_from_env():
    """build a dictionary of stations from os environemt, each in generic config format. 
    Uses the global constant STATION_TYPE_LIST from weather_stations.py """
    stations_available  = [s for s in STATION_TYPE_LIST if s.upper() in  environ.keys()]
    stations = {}
    for station_name in stations_available:
        stations[station_name] = {
            "station_id"     : f"test_{station_name}",
            "station_type"   : station_name,
            "config" : json.loads(environ[station_name])
        }
        
    return stations

@pytest.fixture
def station_configs(station_dict_from_env):
    """using the env entries data above, reform into dictionaries of config"""
    # add generic to .env station_configs = [{'id':'TEST_GENERIC', 'station_type': 'generic', 'config': '{"tz":"ET"}'}]
    # the env are dict as json str , the method above converts to dict, with 'config' sub-dict
    # move 'config' sub-dict up a level for Config models
    configs = {}
    for station_type in station_dict_from_env:
        s_config = station_dict_from_env[station_type]
        # move all fields in sub-dict to top level so we can create a config object
        s_config.update(s_config['config'])
        # remove 'config' element no longer needed for specific config
        s_config['config'] = None
        # add to our dict of all configs
        configs[station_type]  = s_config 
    
    yield configs


###########################
## LIST OF STATION SUBCLASSES to work with when iterating on type
@pytest.fixture
def station_classes(station_dict_from_env):
    """ this creates a dicitionary of classes by importing the class from module.   
    For this to work for a weather station named 'Xtype', 
     - the module (file)  that contains the class must be named xtype.py and in the same directory
     - the station class must be named XtypeStation
     
     returns a dictionary keyed on station type with classes.
     """
    classes = {}
    for station_type in station_dict_from_env:
        station_class_name = station_type.title + "Station"
        station_module_name  = 'ewx_pws.' + station_type.lower
        m = importlib.import_module(station_module_name)
        station_class = getattr(m, station_class_name)
        classes[station_type] = station_class
    
    yield classes


   

