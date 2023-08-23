"""conftest.py pytest suite configuration"""

###########################
## IMPORTS

import pytest, random, string, json
from os import environ, path, remove
import sys
import importlib
from ewx_pws.ewx_pws import logging, read_station_configs, station_types_present
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
## CONFIG FROM PYTEST COMMAND LINE ARG(S)
def pytest_addoption(parser):

    # single station type
    parser.addoption(
        "--stationtype",
        action="store",
        default=None,
        help=f"optional single station type to test. default is all known types {STATION_TYPE_LIST}",
        choices=STATION_TYPE_LIST
    )

    parser.addoption(
        "--station_file",
        action="store",
        default="test_stations.csv",
        help="the path to a CSV file with station configs, Default file is 'test_stations.csv' in this folder"
    )

###########################
## PYTEST ITERATE THROUGH ALL STATION TYPES FROM CONFIG
def pytest_generate_tests(metafunc):
    """parameterize command line options to inject into every test, 
    - station_type : If passed on command line, use that, else use all vendors
    - station_config : from the CSV of test configuration,  THIS requires reading in the file  """
    # This is called for every test. Only get/set command line arguments
    # if the argument is specified in the list of test "fixturenames".

    
    ##### STATION CONFIGS ie STATIONS
    station_file_option = metafunc.config.getoption("station_file")

    # the the id-keyed dictionary of station configs, but use the list of configs only as we don't care about the ID here
    station_config_dict = read_station_configs(station_file_option)
    station_configs = list(station_config_dict.values())
    

    if "station_config" in metafunc.fixturenames:    
        metafunc.parametrize('station_config', station_configs)


    ##### STATION TYPES
    # for those tests that require a station_type .. use code to inject the option or check for param and also for config
    stationtype_option = metafunc.config.getoption("stationtype")
    station_types_configured = station_types_present(station_configs)

    if "station_type" in metafunc.fixturenames:
        if stationtype_option is not None:
            stationtype_option = stationtype_option.upper()
            if not stationtype_option in station_types_configured:
                # station type on command line invalid, abort testing?  or just skip this test...
                 pytest.skip(f"no config available station type {stationtype_option} in configuration file {station_file_option}")
            else:
                logging.debug(f"testing station type {stationtype_option}")
                types_to_test = [stationtype_option]      
            
            # metafunc.parametrize('vendor', [vendor_option.upper()])
            # TODO more elegant way to bug out
            
        else:
            logging.debug(f" the following types are present in config file {station_types_configured}")
            types_to_test = station_types_configured

        # TODO check against the fixture that loads config from disk
        # for now just assume they are all available

        metafunc.parametrize('station_type', types_to_test)


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
    
    interval_minutes = 90
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
@pytest.fixture(scope="session")
def fake_stations_list():
    """this is fake data and won't connect to any real station API.  The API keys look real but are made up
    return List, each station type has exactly one row (no duplicate station types)"""
    return [
        ['fake_zentra','ZENTRA','2023-05-01','ET','{"sn":"z1-1234","token":"d5b8f6391ac38bad6f0b51d7a718b9e3e31eec81","tz":"ET"}'],
        ['fake_davis','DAVIS','2023-05-01','ET','{"sn":"123456","apikey":"gtqdcbirudd1sarq6esbvorfj6tw67ao","apisec":"0286g8zxfvr77yhdx3pcwnnqqstdwqel","tz":"ET"}'],
        ['fake_spectrum','SPECTRUM','2023-05-01','ET','{"sn":"12345678","apikey":"c3a2f80786398e656b08677b7a511a59","tz":"ET"}'],
        ['fake_onset', 'ONSET','2023-05-01','ET','{"sn":"12345678","client_id":"Enviroweather_WS","client_secret":"75d2b7f58f5d0cac689f6b9716348bf264158ca9","ret_form":"JSON","user_id":"12345","sensor_sn":{"atemp":"21079936-1","pcpn":"21085496-1","relh":"21079936-2"},"tz":"ET"}'],
        ['fake_rainwise', 'RAINWISE','2023-05-01','ET','{"sid":"lc2M22K4G99pLgR4Gu09Xw35NulgZMc7","pid":"lc2M22K4G99pLgR4Gu09Xw35NulgZMc7","ret_form":"json","mac":"907592476392","username":"907592476392","tz":"ET"}'],
        ['fake_locomos', 'LOCOMOS','2023-05-01','ET','{"token":"EIBF-aGJGzUaH0tTuvYtgzpCoHW88XS6PDF","id":"XmydER6iPF7VTixSX2JXQkPd", "tz":"ET"}'],
#         ['fake_generic','GENERIC','2023-05-01','ET','{"sn":"fake", "tz":"ET"}']
    ]
    

@pytest.fixture(scope="session")
def fake_station_config_file(fake_stations_list):
    from tempfile import NamedTemporaryFile
    csv_file = NamedTemporaryFile(mode = 'w+', suffix='.csv', delete=False)
    csv_file_path = csv_file.name
    
    import csv
    writer = csv.writer(csv_file, quotechar="'")
    
    writer.writerow(['station_id','station_type','install_date','tz','station_config'])
    for row in fake_stations_list:
        writer.writerow(row)        
    csv_file.close()

    yield(csv_file_path)

    remove(csv_file_path)

@pytest.fixture(scope="session")
def fake_station_configs(fake_station_config_file):
    # this fixture assumes this function works!
    from ewx_pws.ewx_pws import read_station_configs
    fakeconfigs = read_station_configs(fake_station_config_file)
    
    return(fakeconfigs)


@pytest.fixture(scope="session")
def station_file(request):
    return(request.config.getoption("station_file"))
    

@pytest.fixture(scope="session")
def station_configs(station_file):
    """build a dictionary of stations from a CSV passed as CLI param to tests
    uses method from package to read test file """
    logging.debug(f"station_file is {station_file}")
    from ewx_pws.ewx_pws import read_station_configs
    configs = read_station_configs(station_file)
        
    return configs

###########################
## LIST OF STATION SUBCLASSES to work with when iterating on type

# this isn't needed, use ewx_pws.STATION_CLASS_TYPES instead 

# ######## TODO change this to work with CSV keyed on station_id, not type.  
# # so possibily multiple stations of the same type
# @pytest.fixture
# def station_classes(station_configs):
#     """ this creates a dicitionary of classes by importing the class from module.   
#     For this to work for a weather station named 'Xtype', 
#      - the module (file)  that contains the class must be named xtype.py and in the same directory
#      - the station class must be named XtypeStation
     
#      returns a dictionary keyed on station type with classes.
#      """
#     classes = {}
#     for station_config in station_configs:
#         station_class_name = station_config.title + "Station"
#         station_module_name  = 'ewx_pws.' + station_type.lower
#         m = importlib.import_module(station_module_name)
#         station_class = getattr(m, station_class_name)
#         classes[station_type] = station_class
    
#     yield classes

   

