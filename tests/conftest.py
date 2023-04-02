import pytest, random, string, json

from os import environ
# from tempfile import NamedTemporaryFile
from dotenv import load_dotenv
load_dotenv()
from ewx_pws.ewx_pws import STATION_TYPES
# from ewx_pws.weather_stations import STATION_TYPE


@pytest.fixture
def random_string():
    """pytest fixture returns a string"""
    length = 10
    letters = string.ascii_lowercase
    return(''.join(random.choice(letters) for i in range(length)))

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
        ['fake_generic','GENERIC','{"sn":"fake", "tz":"ET"}']
    ]
  
    
@pytest.fixture
def fake_station_configs(fake_stations_list):
    """using the fake data above, reform into dictionaries of config
    return: dict of fake configs, only one entry per station type"""
    
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
    """build a dictionary of stations from os environemt, each in generic config format"""
    stations_available  = [s for s in STATION_TYPES if s.upper() in  environ.keys()]
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
    
    return configs