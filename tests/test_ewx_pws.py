#!/usr/bin/env python

"""Tests for `ewx_pwx` package."""

import pytest, random, string,  os
from tempfile import NamedTemporaryFile
from dotenv import load_dotenv
load_dotenv()



from ewx_pws import ewx_pws


@pytest.fixture
def random_string():
    """pytest fixture returns a string"""

    length = 10
    letters = string.ascii_lowercase
    return(''.join(random.choice(letters) for i in range(length)))


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
def fake_stations_list():
    """this is fake data and won't connect to any real station API.  The API keys look real but are made up"""
    
    return [
        ['fake_zentra','ZENTRA','{"sn":"z1-1234","token":"d5b8f6391ac38bad6f0b51d7a718b9e3e31eec81","tz":"ET"}'],
        ['fake_davis','DAVIS','{"sn":"123456","apikey":"gtqdcbirudd1sarq6esbvorfj6tw67ao","apisec":"0286g8zxfvr77yhdx3pcwnnqqstdwqel","tz":"ET"}'],
        ['fake_spectrum','SPECTRUM','{"sn":"12345678","apikey":"c3a2f80786398e656b08677b7a511a59","tz":"ET"}']
    ]
    
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

