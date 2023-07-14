"""LOCOMOS specific station tests"""

from ewx_pws.locomos import LocomosStation, WeatherStation
import datetime
import json
import pytest

@pytest.fixture
def locomos_station(station_configs):
    station = LocomosStation.init_from_dict(station_configs['LOCOMOS'])
    yield station

@pytest.fixture
def times_for_broken_locomos():
    sdt=datetime.datetime(year= 2023, month = 3, day=19, hour=1, minute=0, second=0).astimezone(datetime.timezone.utc)
    edt=datetime.datetime(year= 2023, month = 3, day=19, hour=1, minute=30, second=0).astimezone(datetime.timezone.utc)
    yield {'start':sdt, 'end':edt}

# this is needed because as of 7/13 we only have some data from them 
def test_locomos_station(station_configs):
    station = LocomosStation.init_from_dict(station_configs['LOCOMOS'])
    assert isinstance(station, WeatherStation)

def test_locomos_variable_listing(station_configs):
    station = LocomosStation.init_from_dict(station_configs['LOCOMOS'])
    # empty to start
    assert station.var_list == {}

    station._get_variable_list()
    assert len(station.var_list) > 0 

    var_names = station.var_list.keys()
    assert 'precip' in var_names
    assert 'lws' in var_names
    assert 'temperature' in var_names
    print(station.var_list)


def test_locomos_api_details(locomos_station):
    """ this test just uses code that is similar to what's actually in LOCOMOS subclass
    this is a way to test/experiment what actually works """
    
    import requests

    # these timestamp / milliseconds were hand calculated to be in the period when the test stations were turned on   
    working_start = 1679202000000
    working_end = 1679203800000

    working_variable_id = '6410e8564a53ce000ec46e46'
    response_columns = ['timestamp', 'device.name', 'device.label', 'variable.id', 'value.context', 'variable.name', 'value.value']
    headers = {
        'Content-Type': 'application/json',
        'X-Auth-Token': locomos_station.config.token,
    }

    # this pulls for one known variable.  normally the variables ids are pulled with a seperate api call
    params = {
        'variables': [
            working_variable_id,
        ],
        'columns': response_columns,
        'join_dataframes': False,
        'start': working_start,
        'end': working_end,
    }

    response = requests.post(url='https://industrial.api.ubidots.com/api/v1.6/data/raw/series', headers=headers, json=params)

    assert response is not None
    assert isinstance(response, requests.Response)
    assert response.content is not None
    assert response.status_code == 200

 
def test_locomos_readings(locomos_station,times_for_broken_locomos):
    """ test the current sub-class can pull readings, but use the time period when the test station was actually active. """
    readings = locomos_station.get_readings(start_datetime=times_for_broken_locomos['start'], end_datetime=times_for_broken_locomos['end'])
    print(readings)
    assert readings is not None

    r = readings[1].get('data')
    assert 'precip' in r.keys()
    assert 'lws' in r.keys()
    assert 'temperature' in r.keys()

    tlist =  json.loads(r['temperature'])
    
    assert 'results' in tlist.keys()
    
    # tdata = tlist['results'][0]

