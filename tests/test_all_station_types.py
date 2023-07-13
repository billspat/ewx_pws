"""common set of tests to apply to all types of stations"""


# TODO this set of tests uses a new format for .env - use that format in the rest of the codebase
# and remove this comment

from os import environ
from datetime import datetime
import logging
from dotenv import load_dotenv
# testing .env
load_dotenv('tests/.env')
import json

import pytest
import sys


from ewx_pws.davis import DavisStation, DavisConfig
from ewx_pws.rainwise import RainwiseStation, RainwiseConfig
from ewx_pws.spectrum import SpectrumStation, SpectrumConfig
from ewx_pws.onset import OnsetStation, OnsetConfig
from ewx_pws.zentra import ZentraStation, ZentraConfig    
from ewx_pws.ewx_pws import STATION_CLASS_TYPES, WeatherStation


@pytest.fixture
def station_config_types():
    """ manually construct our list of station types to test"""
    station_config_types = {}
    station_config_types['DAVIS'] = DavisConfig
    station_config_types['RAINWISE'] = RainwiseConfig
    station_config_types['SPECTRUM'] = SpectrumConfig
    station_config_types['ONSET'] = OnsetConfig
    station_config_types['ZENTRA'] = ZentraConfig 
    yield station_config_types 


@pytest.fixture
def station_configs(station_dict_from_env):
    """using the env entries data above, reform into dictionaries of config"""
    # TODO read from csv instead of env file or make env file keyed on STATIONID and not on STATION_TYPE
     
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
      
def test_station_readings(test_station, utc_time_interval):
    
    # first just check that our test station has a non-zero length station_type and is one on the list
    assert len(test_station.config.station_type) > 0 
    assert test_station.config.station_type in STATION_CLASS_TYPES

    sdt,edt = utc_time_interval

    # test with hard-coded time
    readings = test_station.get_readings(start_datetime=sdt,end_datetime=edt)
    
    # optional, log outputs for debug
    #use pytest -s to see this output
    logging.debug(f"{test_station.config.station_type}: {test_station.current_response}\n-----\n{test_station.current_response.content}")
    # logging.debug('{}\n-----\n{}'.format(vars(test_station.current_response), test_station.current_response.content))
        
    assert test_station.current_response is not None
    assert test_station.current_response.status_code == 200
    assert type(readings) is list
    assert len(readings) >= 2
    assert 'station_type' in readings[0].keys()
    assert readings[0]['station_type'] == test_station.config.station_type
    
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