"""test_all_station_types.py common set of tests to apply to all types of stations"""

import pytest, logging, json
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, available_timezones

from ewx_pws import ewx_pws

from ewx_pws.weather_stations import WeatherStation, WeatherAPIData, WeatherAPIResponse, \
    WeatherStationReading, WeatherStationReadings, TIMEZONE_CODE

@pytest.fixture
def test_station(station_type, station_configs):
    #### TODO
    #### the station csv file has multiple stations in it, so 
    station = [station_type].init_from_dict(station_configs)
    return(station)
  

def test_station_config(station_type, fake_station_configs):
    """ simple test that a station config type can be instantiated from example data
    params
    station_type : string of the type of station
    fake_station_configs: fixture, dictionary of some test configs, keyed on station type
    station_config_types: dictionary of config classes keyed on station type
    """
    
    assert station_type in ewx_pws.CONFIG_CLASS_TYPES
    StationConfigType = ewx_pws.CONFIG_CLASS_TYPES[station_type]

    # The code is retrieving the available station configurations of a specific station type from the
    # `fake_station_configs` dictionary. It then iterates over each configuration and performs some
    # operations on it.
    available_configs = ewx_pws.configs_of_type(fake_station_configs, station_type)
    for config in available_configs:
        c = StationConfigType.parse_obj(config)
        # will this work? 
        assert isinstance(c, StationConfigType)

def test_station_class_with_fake_config(station_type, fake_station_configs):

    assert station_type in ewx_pws.CONFIG_CLASS_TYPES
    StationClass = ewx_pws.STATION_CLASS_TYPES[station_type]

    available_configs = ewx_pws.configs_of_type(fake_station_configs, station_type)
    for config in available_configs:
        station = StationClass.init_from_dict(config)
        assert isinstance(station, WeatherStation)
        assert isinstance(station.id, str)
        # timezone data and info check. 
        # chose to store timezone as two-char timezone, but zoneinfo doesn't use those codes
        # so checking the lookup stored in the config object
        assert station.config.tz in station.config._tzlist.keys()
        station_zoneinfo = station.config._tzlist[station.config.tz]
        assert station_zoneinfo in available_timezones()

        assert isinstance(station.interval_min, int)
        assert station.interval_min in [5,15,30]
           
def test_station_readings(station_config, utc_time_interval):
    """ run one for each row in the config file sent"""
    station_type = station_config['station_type']
    logging.debug(f"testing type {station_type}")

    assert station_type in ewx_pws.STATION_TYPE_LIST
    StationClass =  ewx_pws.STATION_CLASS_TYPES[station_type]
    
    # from ewx_pws.zentra import ZentraStation
    # StationClass = ZentraStation
    
    test_station = StationClass.init_from_dict(config = station_config)
    # first just check that our test station has a non-zero length station_type and is one on the list
    assert len(test_station.config.station_type) > 0 
    assert test_station.config.station_type == station_type 

    sdt,edt = utc_time_interval

    ######## READING TESTS
    weather_api_data= test_station.get_readings(start_datetime=sdt,end_datetime=edt)
            
    assert test_station.current_response is not None

    assert isinstance(test_station.current_response, list)
    assert test_station.current_response[0].status_code == '200'

    assert isinstance(test_station.current_response[0], WeatherAPIResponse)
    d = json.loads(test_station.current_response[0].text)
    assert isinstance(d, dict)
    assert isinstance(test_station.current_response_data, WeatherAPIData) 
    assert isinstance(weather_api_data.station_type, str)
    assert weather_api_data.station_type == test_station.config.station_type

    
    ###### TRANSFORM TESTS
    # these are included in this test becuase of the Zentra timeout problem

    weather_station_readings = test_station.transform(weather_api_data)

    assert isinstance(weather_station_readings, WeatherStationReadings)

    #pull out the one element
    assert len(weather_station_readings.readings) > 0
    
    # print first element 
    for weather_station_reading in weather_station_readings.readings:
        assert isinstance(weather_station_reading.station_id, str)
        assert isinstance(weather_station_reading.data_datetime, datetime)
        assert isinstance(weather_station_reading.atemp, float)
        assert isinstance(weather_station_reading.pcpn, float)
        assert isinstance(weather_station_reading.relh, float)
        if test_station.config.station_type == "LOCOMOS":
            assert isinstance(weather_station_reading.lws0, float)
