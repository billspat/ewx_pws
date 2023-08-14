"""LOCOMOS specific station tests"""

from ewx_pws.locomos import LocomosStation, WeatherStation
from ewx_pws.weather_stations import WeatherAPIData, WeatherAPIResponse
import datetime, json, logging, pytest

@pytest.fixture
def locomos_station(station_configs):
    station = LocomosStation.init_from_dict(station_configs['LOCOMOS'])
    yield station


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
    assert 'rh' in var_names
    assert 'lws1' in var_names
    assert 'temp' in var_names
    print(station.variables)



