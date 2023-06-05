#!/usr/bin/env python

"""Tests for `ewx_pwx` package."""
import pytest, random, string,  os, logging
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
    for station in stations:
        assert type(station) in ewx_pws.STATION_CLASS_TYPES.values()
   
import csv

def test_fake_stations_file(fake_stations_file):
    """test of that the fixture works to create a file"""
    with open(fake_stations_file, "r") as csvfile:
        csvreader = csv.DictReader(csvfile, quotechar="'")
        for row in csvreader:
            assert isinstance(row, dict)

def test_stations_from_file(fake_stations_file):
    stations = ewx_pws.stations_from_file(fake_stations_file)

    for station in stations:
        assert type(station) in ewx_pws.STATION_CLASS_TYPES.values()

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