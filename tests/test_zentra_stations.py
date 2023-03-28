from ewx_pws.zentra import ZentraConfig, ZentraStation, WeatherStationConfig, WeatherStation
import pytest, re
from pprint import pprint


@pytest.fixture
def station_type():
    return 'ZENTRA'

@pytest.fixture
def test_station(station_configs, station_type):
    station = ZentraStation.init_from_dict(station_configs[station_type])
    return(station)
    

def test_zentra_config(fake_station_configs, station_type):
    zconfig = ZentraConfig.parse_obj(fake_station_configs[station_type])
    
def test_zentra_subclass_weather_station(fake_station_configs, station_type):
    zstation = ZentraStation.init_from_dict(fake_station_configs[station_type])
    assert isinstance(zstation,WeatherStation)
    assert isinstance(zstation.id, str)
    assert isinstance(zstation.station_tz, str)
    
    assert isinstance(zstation.get_readings(), list)
    
#-----------------
# 
# @pytest.fixture
# def test_station(station_configs, station_type):
#     zentra_station = ZentraStation.init_from_dict(station_configs[station_type])
#     return(zentra_station)
    
def test_zentra_config(fake_station_configs, station_type):
    c = ZentraConfig.parse_obj(fake_station_configs[station_type])
    assert isinstance(c, ZentraConfig)
    
def test_zentra_class_fake(fake_station_configs, station_type):
    zentra_station = ZentraStation.init_from_dict(fake_station_configs[station_type])
    assert isinstance(zentra_station, WeatherStation)
    assert isinstance(zentra_station.id, str)
    
def test_zentra_class_instantiation_from_config(station_configs, station_type):
    zentra_station = ZentraStation.init_from_dict(station_configs[station_type])
    assert isinstance(zentra_station, WeatherStation)
    assert isinstance(zentra_station.id, str)
    
def test_zentra_auth(test_station):
    # example token 2b43bb08895d00bfa37c5477348e3bdd
    token = test_station._get_auth()
    assert isinstance(token, str)
    assert len(token) > 2
    token_pattern = re.compile('[0-9a-z]+')
    assert re.fullmatch(token_pattern,test_station.access_token)
      
def test_zentra_readings(test_station):
    
    # note as of 2023-03-26 the test best zentra station is offline
    # use hard-coded date/time when it was on line for this test
    # TODO remove these when the station is back on-line
    sdt="2022-12-01 19:00:00"
    edt="2022-12-01 19:15:00"  

    # test with hard-coded time
    readings = test_station.get_readings(start_datetime_str=sdt,end_datetime_str=edt)

    # optional, print outputs for debug
    # use pytest -s to see this output
    pprint(vars(test_station.current_response))
    print('-----')
    pprint(test_station.current_response.content)
        
    assert test_station.current_response is not None
    assert test_station.current_response.status_code == 200
    assert readings is not None
    
    
    

    
    
    




    
    
    