#!/usr/bin/env python

"""Tests for `ewx_pwx` package."""
import pytest, random, string,  os
from tempfile import NamedTemporaryFile

# dotenv loaded in conftest.py

from ewx_pws import ewx_pws


@pytest.fixture
def sample_stations():
    stations = ewx_pws.stations_from_env()
    return(stations)


@pytest.fixture
def sample_fixture_response():
    """Sample pytest fixture.

    See more at: http://doc.pytest.org/en/latest/fixture.html
    """
    import requests
    return requests.get('https://github.com/')


@pytest.fixture
def fake_stations_file(fake_stations_list):

    header = ['station_id', 'station_type', 'config']

    csv_file = NamedTemporaryFile(mode = 'w+', suffix='.csv', delete=False)
    csv_file_path = csv_file.name
    w = csv.writer(csv_file, delimiter=',', quotechar="'") 
    
    w.writerow(header)
    w.writerows(fake_stations_list)
    
    csv_file.close()
    
    yield(csv_file_path)
    
    os.remove(csv_file_path)

    return 

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

def test_stations_from_env():
    stations = ewx_pws.stations_from_env()
    assert len(stations) > 0
    assert isinstance(stations, dict)
    assert 'DAVIS' in list(stations.keys())

def test_get_reading(sample_stations):
    station = sample_stations['DAVIS']
    reading = ewx_pws.get_reading(station['station_type'], 
                          station['station_config'],
                          start_datetime_str = None, 
                          end_datetime_str = None)
    
    assert reading is not None
    assert isinstance(reading.resp_raw, dict)
    assert len(reading.resp_raw) > 0 
    
    assert isinstance(reading.resp_transformed, list)
    assert len(reading.resp_transformed) > 0 
    assert isinstance(reading.resp_transformed[0], dict)
    
    assert isinstance(reading.resp_transformed[0], dict)
    
    # check that we got the keys we expect.  As the weather api grows this list will need to be updated
    # or built into the class/package
    expected_column_list = ['station_id', 'request_datetime', 'data_datetime', 'atemp', 'pcpn', 'relh']
    reading_fields = list(reading.resp_transformed[0].keys())
    
    assert reading_fields == expected_column_list
   
import csv

def test_fake_stations_file(fake_stations_file):
    """test of that the fixture works to create a file"""
    with open(fake_stations_file, "r") as csvfile:
        csvreader = csv.DictReader(csvfile, quotechar="'")
        for row in csvreader:
            assert isinstance(row, dict)

def test_stations_from_file(fake_stations_file):
    stations = ewx_pws.stations_from_file(fake_stations_file)

    # TODO move this fixture
    station_fields = ['station_id', 'station_type', 'station_config']
    assert isinstance(stations, dict)
    for station in stations:
        assert isinstance(stations[station], dict)
        assert station_fields == list(stations[station].keys())

@pytest.mark.filterwarnings("ignore:emptycsv")
def test_stations_from_file_blank(fake_blank_file):
    stations = ewx_pws.stations_from_file(fake_blank_file)
    
    assert stations == None

def test_stations_from_file_invalid(fake_invalid_file):
    with pytest.raises(ValueError):
        ewx_pws.stations_from_file(fake_invalid_file)

def test_stations_from_file_noncsv(fake_noncsv_file):
    with pytest.raises(TypeError):
        ewx_pws.stations_from_file(fake_noncsv_file)