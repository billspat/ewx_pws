from ewx_pws.rainwise import RainwiseConfig, RainwiseStation, WeatherStationConfig, WeatherStation
import pytest, re
from datetime import datetime
from pprint import pprint

# note: fixtures auto-imported from conftest.py

@pytest.fixture
def station_type():
    return 'RAINWISE'

@pytest.fixture
def test_station(station_configs, station_type):
    station = RainwiseStation.init_from_dict(station_configs[station_type])
    return(station)

def test_rainwise_config(fake_station_configs,station_type):
    c = RainwiseConfig.parse_obj(fake_station_configs[station_type])

    print(c)
    assert isinstance(c, RainwiseConfig)

def test_rainwise_class_fake(fake_station_configs,station_type):
    station = RainwiseStation.init_from_dict(fake_station_configs[station_type])
    assert isinstance(station, WeatherStation)
    assert isinstance(station.id, str)

def test_rainwise_class_instantiation_from_config(station_configs,station_type):
    config = station_configs[station_type]
    print('config used:')
    print(config)
    station = RainwiseStation.init_from_dict(config)
    assert isinstance(station, WeatherStation)
    assert isinstance(station.id, str)

def test_rainwise_readings(test_station):

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
