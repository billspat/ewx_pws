from ewx_pws.davis import DavisStation, DavisConfig, WeatherStationConfig, WeatherStation
import pytest, re
from datetime import datetime
from pprint import pprint


@pytest.fixture
def station_type():
    return 'DAVIS'

@pytest.fixture
def test_station(station_configs, station_type):
    station = DavisStation.init_from_dict(station_configs[station_type])
    return(station)
    

def test_davis_config(fake_station_configs, station_type):
    zconfig = DavisConfig.parse_obj(fake_station_configs[station_type])
    
# def test_davis_subclass_weather_station(fake_station_configs, station_type):
#     zstation = DavisStation.init_from_dict(fake_station_configs[station_type])
#     assert isinstance(zstation,WeatherStation)
#     assert isinstance(zstation.id, str)
#     assert isinstance(zstation.station_tz, str)
    
#     assert isinstance(zstation.get_readings(), list)
    
#-----------------
# 
# @pytest.fixture
# def test_station(station_configs, station_type):
#     davis_station = DavisStation.init_from_dict(station_configs[station_type])
#     return(davis_station)
    
def test_davis_config(fake_station_configs, station_type):
    c = DavisConfig.parse_obj(fake_station_configs[station_type])
    assert isinstance(c, DavisConfig)
    
def test_davis_class_fake(fake_station_configs, station_type):
    davis_station = DavisStation.init_from_dict(fake_station_configs[station_type])
    assert isinstance(davis_station, WeatherStation)
    assert isinstance(davis_station.id, str)
    
def test_davis_class_instantiation_from_config(station_configs, station_type):
    davis_station = DavisStation.init_from_dict(station_configs[station_type])
    assert isinstance(davis_station, WeatherStation)
    assert isinstance(davis_station.id, str)
      
def test_davis_readings(test_station):
    
    sdt="2022-12-01 19:00:00"
    edt="2022-12-02 19:15:00" 

    # test with hard-coded time
    readings = test_station.get_readings(start_datetime_str=sdt,end_datetime_str=edt)
    
    # optional, print outputs for debug
    #use pytest -s to see this output
    pprint(vars(test_station.current_response))
    print('-----')
    pprint(test_station.current_response.content)
        
    assert test_station.current_response is not None
    assert test_station.current_response.status_code == 200
    assert type(readings) is list
    assert len(readings) >= 2
    assert 'station_type' in readings[0].keys()
    assert readings[0]['station_type'] == 'DAVIS'

    for i in range(1,len(readings)):
        transformed_reading = test_station.transform(data=readings[i])
        assert len(transformed_reading.readings) > 0
        for value in transformed_reading.readings:
            assert isinstance(value.station_id, str)
            assert isinstance(value.data_datetime, datetime)
            assert isinstance(value.atemp, float)
            assert isinstance(value.pcpn, float)
            assert isinstance(value.relh, float)

            # print (value.station_id, end=", ")
            # print (value.request_datetime, end=", ")
            # print (value.data_datetime, end=", ")
            # print (value.atemp, end=", ")
            # print (value.pcpn, end=", ")
            # print (value.relh, end="\n")
    