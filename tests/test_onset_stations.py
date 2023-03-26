from ewx_pws.onset import OnsetConfig, OnsetStation, WeatherStationConfig, WeatherStation
import pytest, re

# note: fixtures auto-imported from conftest.py
@pytest.fixture
def test_onset_station(station_configs, station_type='ONSET'):
    onset_station = OnsetStation.init_from_dict(station_configs[station_type])
    return(onset_station)
    
def test_onset_config(fake_station_configs):
    station_type = 'ONSET'
    c = OnsetConfig.parse_obj(fake_station_configs[station_type])
    assert isinstance(c, OnsetConfig)
    
def test_onset_class_fake(fake_station_configs):
    station_type = 'ONSET'
    onset_station = OnsetStation.init_from_dict(fake_station_configs[station_type])
    assert isinstance(onset_station, WeatherStation)
    assert isinstance(onset_station.id, str)
    
def test_onset_class_instantiation_from_config(station_configs):
    station_type = 'ONSET'
    onset_station = OnsetStation.init_from_dict(station_configs[station_type])
    assert isinstance(onset_station, WeatherStation)
    assert isinstance(onset_station.id, str)
    
def test_onset_auth(test_onset_station):
    # example token 2b43bb08895d00bfa37c5477348e3bdd
    token = test_onset_station._get_auth()
    assert isinstance(token, str)
    assert len(token) > 2
    token_pattern = re.compile('[0-9a-z]+')
    assert re.fullmatch(token_pattern,test_onset_station.access_token)
    
def test_onset_json_reading(test_onset_station):
    # get for current date/time
    readings = test_onset_station.get_readings()
    
    assert readings is not None
    assert test_onset_station.current_api_response is not None
    assert test_onset_station.current_api_response.status_code == 200
    
    from pprint import pprint
    pprint(vars(test_onset_station.current_api_response))
    print('-----')
    pprint(test_onset_station.current_api_response._content)



    
    
    