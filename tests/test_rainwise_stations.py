from ewx_pws.rainwise import RainwiseConfig, RainwiseStation, WeatherStationConfig, WeatherStation
import pytest, re, logging
from datetime import datetime

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

    logging.debug(c)
    assert isinstance(c, RainwiseConfig)

def test_rainwise_class_fake(fake_station_configs,station_type):
    station = RainwiseStation.init_from_dict(fake_station_configs[station_type])
    assert isinstance(station, WeatherStation)
    assert isinstance(station.id, str)

def test_rainwise_class_instantiation_from_config(station_configs,station_type):
    config = station_configs[station_type]
    logging.debug('config used: {}'.format(config))
    station = RainwiseStation.init_from_dict(config)
    assert isinstance(station, WeatherStation)
    assert isinstance(station.id, str)

def test_rainwise_readings(test_station):

    sdt="2022-12-01 19:00:00"
    edt="2022-12-01 19:15:00"  

    # test with hard-coded time
    readings = test_station.get_readings(start_datetime=sdt,end_datetime=edt)

    # optional, log outputs for debug
    # use pytest -s to see this output
    logging.debug('{}\n-----\n{}'.format(vars(test_station.current_response), test_station.current_response.content))
        
    assert test_station.current_response is not None
    assert test_station.current_response.status_code == 200
    assert type(readings) is list
    assert len(readings) >= 2
    assert 'station_type' in readings[0].keys()
    assert readings[0]['station_type'] == 'RAINWISE'

    for i in range(1,len(readings)):
        resp_datetime = readings[0]['response_datetime_utc' + str(i)]
        transformed_reading = test_station.transform(data=readings[i], request_datetime=resp_datetime)
        assert len(transformed_reading.readings) > 0
        for value in transformed_reading.readings:
            assert isinstance(value.station_id, str)
            assert isinstance(value.data_datetime, datetime)
            assert isinstance(value.atemp, float)
            assert isinstance(value.pcpn, float)
            assert isinstance(value.relh, float)

            #logging.debug('\n{}: {}, {}, {}, {}, {}\n'.format(value.station_id,value.request_datetime,value.data_datetime,value.atemp,value.pcpn,value.relh))
