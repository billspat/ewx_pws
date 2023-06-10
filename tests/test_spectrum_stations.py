from ewx_pws.spectrum import SpectrumConfig, SpectrumStation, WeatherStationConfig, WeatherStation
import pytest, re, logging
from datetime import datetime

# note: fixtures auto-imported from conftest.py

@pytest.fixture
def station_type():
    return 'SPECTRUM'

@pytest.fixture
def test_station(station_configs, station_type):
    station = SpectrumStation.init_from_dict(station_configs[station_type])
    return(station)
    
def test_spectrum_config(fake_station_configs,station_type):

    c = SpectrumConfig.parse_obj(fake_station_configs[station_type])
    assert isinstance(c, SpectrumConfig)
    
def test_spectrum_class_fake(fake_station_configs,station_type):
    station = SpectrumStation.init_from_dict(fake_station_configs[station_type])
    assert isinstance(station, WeatherStation)
    assert isinstance(station.id, str)
    
def test_spectrum_class_instantiation_from_config(station_configs,station_type):
    config = station_configs[station_type]
    logging.debug('config used: {}'.format(config))
    station = SpectrumStation.init_from_dict(config)
    assert isinstance(station, WeatherStation)
    assert isinstance(station.id, str)
    
def test_spectrum_readings(test_station):
    
    # note as of 2023-03-26 the test best Spectrum station is offline
    # use hard-coded date/time when it was on line for this test
    # TODO remove these when the station is back on-line
    sdt="2022-12-01 19:00:00"
    edt="2022-12-01 19:15:00"  

    # test with hard-coded time
    readings = test_station.get_readings(start_datetime_str=sdt,end_datetime_str=edt)

    # optional, log outputs for debug
    # use pytest -s to see this output
    logging.debug('{}\n-----\n{}'.format(vars(test_station.current_response), test_station.current_response.content))
        
    assert test_station.current_response is not None
    assert test_station.current_response.status_code == 200
    assert type(readings) is list
    assert len(readings) >= 2
    assert 'station_type' in readings[0].keys()
    assert readings[0]['station_type'] == 'SPECTRUM'

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
