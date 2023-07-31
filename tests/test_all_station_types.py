"""test_all_station_types.py common set of tests to apply to all types of stations"""

import pytest
from datetime import datetime, timezone
import logging
# from dotenv import load_dotenv
# # testing .env
# load_dotenv('tests/.env')
import json

from ewx_pws.davis import DavisStation, DavisConfig
from ewx_pws.locomos import LocomosConfig
from ewx_pws.rainwise import RainwiseStation, RainwiseConfig
from ewx_pws.spectrum import SpectrumStation, SpectrumConfig
from ewx_pws.onset import OnsetStation, OnsetConfig
from ewx_pws.zentra import ZentraStation, ZentraConfig    
from ewx_pws.ewx_pws import STATION_CLASS_TYPES, WeatherStation

from ewx_pws.weather_stations import WeatherAPIData, WeatherAPIResponse, WeatherStationReading, WeatherStationReadings

@pytest.fixture
def station_config_types():
    """ manually construct our list of station types to test"""
    station_config_types = {}
    station_config_types['DAVIS'] = DavisConfig
    station_config_types['LOCOMOS'] = LocomosConfig
    station_config_types['RAINWISE'] = RainwiseConfig
    station_config_types['SPECTRUM'] = SpectrumConfig
    station_config_types['ONSET'] = OnsetConfig
    station_config_types['ZENTRA'] = ZentraConfig 
    yield station_config_types 


@pytest.fixture
def test_station(station_type, station_configs):
    station = STATION_CLASS_TYPES[station_type].init_from_dict(station_configs[station_type])
    return(station)
  


def test_station_config(station_type, fake_station_configs,  station_config_types):
    """ simple test that a station config type can be instantiated from example data
    params
    station_type : string of the type of station
    fake_station_configs: fixture, dictionary of some test configs, keyed on station type
    station_config_types: dictionary of config classes keyed on station type
    """
    
    StationConfigType = station_config_types[station_type]
    c = StationConfigType.parse_obj(fake_station_configs[station_type])
    # will this work? 
    assert isinstance(c, StationConfigType)

def test_station_class_fake_config(station_type, fake_station_configs):

    # STATION_CLASS_TYPES imported from ewx main 
    StationClass = STATION_CLASS_TYPES[station_type]

    station = StationClass.init_from_dict(fake_station_configs[station_type])
    assert isinstance(station, WeatherStation)
    assert isinstance(station.id, str)

def test_station_class_instantiation_from_config(station_configs, station_type):
    station = STATION_CLASS_TYPES[station_type].init_from_dict(station_configs[station_type])
    assert isinstance(station, WeatherStation)
    assert isinstance(station.id, str)

@pytest.fixture
def interval_for_broken_locomos():
    sdt=datetime(year= 2023, month = 3, day=19, hour=1, minute=0, second=0).astimezone(timezone.utc)
    edt=datetime(year= 2023, month = 3, day=19, hour=1, minute=30, second=0).astimezone(timezone.utc)
    yield ( (sdt,edt))
 

def test_station_readings(test_station, utc_time_interval, interval_for_broken_locomos):
    
    # first just check that our test station has a non-zero length station_type and is one on the list
    assert len(test_station.config.station_type) > 0 
    assert test_station.config.station_type in STATION_CLASS_TYPES

    # KLUDGE TO DEAL WITH BROKEN LOCOMOS STATION
    if test_station.config.station_type == 'LOCOMOS':
        sdt,edt = interval_for_broken_locomos
    else:
        sdt,edt = utc_time_interval

    ######## READING TESTS
    weather_api_data= test_station.get_readings(start_datetime=sdt,end_datetime=edt)
    
    # logging.debug(f"{test_station.config.station_type}: {test_station.current_response}")
        
    assert test_station.current_response is not None

    assert isinstance(test_station.current_response, list)
    assert test_station.current_response[0].status_code == '200'

    assert isinstance(test_station.current_response[0], WeatherAPIResponse)
    d = json.loads(test_station.current_response[0].text)
    assert isinstance(d, dict)

    assert isinstance(test_station.current_response_data, WeatherAPIData) 
    assert isinstance(weather_api_data.station_type, str)
    assert weather_api_data.station_type == test_station.config.station_type
    print(weather_api_data.station_type)
    
    ###### TRANSFORM TESTS
    weather_station_readings = test_station.transform(weather_api_data)

    assert isinstance(weather_station_readings, WeatherStationReadings)

    #pull out the one element
    assert len(weather_station_readings.readings) > 0
    
    # print first element 
    logging.debug(weather_station_readings.readings[0])
    for weather_station_reading in weather_station_readings.readings:
        assert isinstance(weather_station_reading.station_id, str)
        assert isinstance(weather_station_reading.data_datetime, datetime)
        assert isinstance(weather_station_reading.atemp, float)
        assert isinstance(weather_station_reading.pcpn, float)
        assert isinstance(weather_station_reading.relh, float)
        #logging.debug('\n{}: {}, {}, {}, {}, {}\n'.format(weather_station_reading.station_id,weather_station_reading.request_datetime,weather_station_reading.data_datetime,weather_station_reading.atemp,weather_station_reading.pcpn,weather_station_reading.relh))