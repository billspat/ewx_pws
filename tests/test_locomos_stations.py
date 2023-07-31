"""LOCOMOS specific station tests"""

from ewx_pws.locomos import LocomosStation, WeatherStation
from ewx_pws.weather_stations import WeatherAPIData, WeatherAPIResponse
import datetime, json, logging, pytest

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
    assert station.variables == {}

    station._get_variables()
    assert len(station.variables) > 0 

    var_names = station.variables.values()
    assert 'precip' in var_names
    assert 'lws' in var_names
    assert 'temperature' in var_names
    print(station.variables)


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
    weather_api_data = locomos_station.get_readings(start_datetime=times_for_broken_locomos['start'], end_datetime=times_for_broken_locomos['end'])
    logging.debug(weather_api_data)
    assert weather_api_data is not None

    assert isinstance(weather_api_data, WeatherAPIData)
    responses = weather_api_data.responses
    assert isinstance(responses, list)
    response = responses[0]
    assert isinstance(response, WeatherAPIResponse)

    readings = json.loads(response.text)
    assert 'results' in readings.keys()
    assert 'columns' in readings.keys()
    assert len(readings['results']) > 0 


