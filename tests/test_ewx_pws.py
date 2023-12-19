"""Tests for `ewx_pwx` package."""

import pytest, os, logging, csv
from pprint import pprint
from tempfile import NamedTemporaryFile
from ewx_pws import ewx_pws
from weather_stations import STATION_TYPE_LIST

@pytest.fixture
def sample_fixture_response():
    """Sample pytest fixture.

    See more at: http://doc.pytest.org/en/latest/fixture.html
    """
    import requests
    return requests.get('https://github.com/')


@pytest.fixture
def fake_blank_file():
    csv_file = NamedTemporaryFile(mode = 'w+', suffix='.csv', delete=False)
    csv_file_path = csv_file.name
    csv_file.close()
    
    yield(csv_file_path)
    
    os.remove(csv_file_path)
    return 

@pytest.fixture
def fake_invalid_file():
    csv_file = NamedTemporaryFile(mode = 'w+', suffix='.csv', delete=False)
    csv_file_path = csv_file.name

    csv_file.write("This is not a csv that is set up, correctly, ,a, w\n")
    csv_file.write("This is not , correctly, ,a , w\n")
    csv_file.write("This ist a cs thatis set up, correctly, a, , w\n")
    csv_file.close()
    
    yield(csv_file_path)
    
    os.remove(csv_file_path)
    return 

@pytest.fixture
def fake_noncsv_file():
    csv_file = NamedTemporaryFile(mode = 'w+', suffix='.csv', delete=False)
    csv_file_path = csv_file.name

    csv_file.write("This is not, a, csv\n")
    csv_file.write("it is just a normal file, written with text possibly with\n")
    csv_file.write("some commas scattered throughout but nothing special.\n")
    csv_file.close()
    
    yield(csv_file_path)
    
    os.remove(csv_file_path)

    return 

def test_fake_station_config_file(fake_station_config_file):
    """test of that the fixture from conftest.py works to create a file"""
    with open(fake_station_config_file, "r") as csvfile:
        csvreader = csv.DictReader(csvfile, quotechar="'")
        for row in csvreader:
            assert isinstance(row, dict)

# ######################
# ## fake config file testing

def test_can_read_station_config_fake_file(fake_station_config_file):
    """ test the function that reads in the configs prior to creating stations"""
    fake_station_configs = ewx_pws.read_station_configs(fake_station_config_file)

    assert len(fake_station_configs) > 0 
    assert isinstance(fake_station_configs, dict)
    # loop through each config
    for fake_station_id in fake_station_configs:
        fake_station_config = fake_station_configs[fake_station_id]
        for field_name in ['station_type','station_id','install_date','tz']:
            assert(field_name in fake_station_config)

        assert(fake_station_config['station_type'] in STATION_TYPE_LIST)

    logging.debug(fake_station_configs)

def test_can_instantiate_stations_from_fake_file(fake_station_config_file):
    
    stations = ewx_pws.station_dict_from_file(fake_station_config_file)

    assert isinstance(stations, dict)
    pprint(stations)
    assert len(stations) > 0 
   
    for station_id in stations:
        station = stations[station_id]
        assert type(station) in list(ewx_pws.STATION_CLASS_TYPES.values())

@pytest.mark.filterwarnings("ignore:emptycsv")
def test_will_error_with_file_blank(fake_blank_file):
     with pytest.raises(Exception) as e_info:
        stations = ewx_pws.station_dict_from_file(fake_blank_file)    
        # assert stations == {}



def test_stations_from_file_invalid(fake_invalid_file):
    with pytest.raises(ValueError):
        ewx_pws.stations_from_file(fake_invalid_file)

def test_stations_from_file_noncsv(fake_noncsv_file):
    with pytest.raises(Exception):
        ewx_pws.stations_from_file(fake_noncsv_file)

######################
### valid csv file test (sent via parameter)

def test_is_station_file_readable(station_file):
    logging.debug(station_file)

    row_count = 0   

    with open(station_file, "r") as csvfile:
        csvreader = csv.DictReader(csvfile, quotechar="'")
        
        for row in csvreader:
            row_count = row_count+1
            assert isinstance(row, dict)

    assert row_count > 0

def test_can_read_station_config_file(station_file):
    """ test the function that reads in the configs prior to creating stations"""
    logging.debug(station_file)
    station_configs = ewx_pws.read_station_configs(station_file)

    assert len(station_configs) > 0 
    assert isinstance(station_configs, dict)
    # loop through each config
    for station_id in station_configs:
        station_config = station_configs[station_id]
        for field_name in ['station_type','station_id','install_date','tz']:
            assert(field_name in station_config)

        assert(station_config['station_type'] in STATION_TYPE_LIST)

def test_can_instantiate_station_config_file(station_file):
    stations = ewx_pws.station_dict_from_file(station_file)

    assert isinstance(stations, dict)
    assert len(stations) > 0 
   
    for station_id in stations:
        station = stations[station_id]
        assert type(station) in list(ewx_pws.STATION_CLASS_TYPES.values())

def test_filter_by_station_type(station_file):
    logging.debug("this test ignored the station_type parameter")
    stations = ewx_pws.station_dict_from_file(station_file)
    for station_type in STATION_TYPE_LIST:
        station_subset = ewx_pws.stations_of_type(stations = stations, station_type = station_type)
        for s in station_subset:
            assert s.config.station_type == station_type

    
