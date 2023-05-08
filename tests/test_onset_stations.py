from ewx_pws.onset import OnsetConfig, OnsetStation, WeatherStationConfig, WeatherStation
import pytest, re
from pprint import pprint
from datetime import datetime

# note: fixtures auto-imported from conftest.py


@pytest.fixture
def station_type():
    return 'ONSET'

@pytest.fixture
def test_station(station_configs, station_type):
    station = OnsetStation.init_from_dict(station_configs[station_type])
    return(station)

    
def test_onset_config(fake_station_configs,  station_type):
    c = OnsetConfig.parse_obj(fake_station_configs[station_type])
    assert isinstance(c, OnsetConfig)
    
def test_onset_class_fake(fake_station_configs,  station_type):
    onset_station = OnsetStation.init_from_dict(fake_station_configs[station_type])
    assert isinstance(onset_station, WeatherStation)
    assert isinstance(onset_station.id, str)
    
def test_onset_class_instantiation_from_config(station_configs,  station_type):
    onset_station = OnsetStation.init_from_dict(station_configs[station_type])
    assert isinstance(onset_station, WeatherStation)
    assert isinstance(onset_station.id, str)
    
def test_onset_auth(test_station):
    # example token 2b43bb08895d00bfa37c5477348e3bdd
    token = test_station._get_auth()
    assert isinstance(token, str)
    assert len(token) > 2
    token_pattern = re.compile('[0-9a-z]+')
    assert re.fullmatch(token_pattern,test_station.access_token)
      
def test_onset_readings(test_station):
    
    # note as of 2023-03-26 the test best onset station is offline
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
    
    onset_observation_list = readings['observation_list']
    assert len(onset_observation_list) > 0
    onset_message = readings['message']
    assert onset_message != 'OK: Found: 0 results.'
    print(onset_message)

    transformed_readings = test_station.transform()
    assert len(transformed_readings.readings) > 0
    for value in transformed_readings.readings:
        assert isinstance(value.station_id, str)
        assert isinstance(value.data_datetime, datetime)
        assert isinstance(value.atemp, float)
        assert isinstance(value.pcpn, float)
        assert isinstance(value.relh, float)
    
        # print (value.station_id)
        # print (value.request_datetime)
        # print (value.data_datetime)
        # print (value.atemp)
        # print (value.pcpn)
        # print (value.relh, end="\n")
    
    

    
    
    




    
    
    