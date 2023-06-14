from ewx_pws.locomos import LocomosConfig, LocomosStation, WeatherStationConfig, WeatherStation
from ewx_pws.weather_stations import datetimeUTC
import pytest, logging
from datetime import datetime

# note: fixtures auto-imported from conftest.py

@pytest.fixture
def station_type():
    return 'LOCOMOS'

@pytest.fixture
def test_station(station_configs, station_type):
    station = LocomosStation.init_from_dict(station_configs[station_type])
    return(station)
    
def test_locomos_config(fake_station_configs,station_type):
    c = LocomosConfig.parse_obj(fake_station_configs[station_type])
    assert isinstance(c, LocomosConfig)
    
def test_locomos_class_fake(fake_station_configs,station_type):
    station = LocomosStation.init_from_dict(fake_station_configs[station_type])
    assert isinstance(station, WeatherStation)
    assert isinstance(station.id, str)
    
def test_locomos_class_instantiation_from_config(station_configs,station_type):
    config = station_configs[station_type]
    logging.debug('config used: {}'.format(config))
    station = LocomosStation.init_from_dict(config)
    assert isinstance(station, WeatherStation)
    assert isinstance(station.id, str)
    
def test_locomos_readings(test_station):
    
    # note as of 2023-03-26 the test best Locomos station is offline
    # use hard-coded date/time when it was on line for this test
    # TODO remove these when the station is back on-line
    sdt=test_station.dt_utc_from_str("2023-03-21 15:00:00")
    edt=test_station.dt_utc_from_str("2023-03-21 15:15:00" ) 

    # test with hard-coded time
    readings = test_station.get_readings(start_datetime=sdt,end_datetime=edt)

    # optional, log outputs for debug
    # use pytest -s to see this output
    logging.debug('{}\n'.format(test_station.current_response))
        
    assert type(readings) is list
    assert len(readings) >= 2
    assert 'station_type' in readings[0].keys()
    assert readings[0]['station_type'] == 'LOCOMOS'

    for i in range(1,len(readings)):
        resp_datetime = datetimeUTC(value=readings[0]['response_datetime_utc' + str(i)])
        transformed_reading = test_station.transform(data=readings[i], request_datetime=resp_datetime)
        assert len(transformed_reading.readings) > 0
        for value in transformed_reading.readings:
            assert isinstance(value.station_id, str)
            assert isinstance(value.data_datetime, datetime)
            assert isinstance(value.atemp, float)
            assert isinstance(value.pcpn, float)
            assert isinstance(value.relh, float)

            #logging.debug('\n{}: {}, {}, {}, {}, {}\n'.format(value.station_id,value.request_datetime,value.data_datetime,value.atemp,value.pcpn,value.relh))
