"""LOCOMOS specific station tests"""

from ewx_pws.locomos import LocomosStation, WeatherStation
from ewx_pws.weather_stations import WeatherAPIData, WeatherAPIResponse
from ewx_pws.ewx_pws import configs_of_type
import datetime, json, logging, pytest

@pytest.fixture(scope="module")
def locomos_configs(station_configs):
    configs = configs_of_type(station_configs, station_type='LOCOMOS')
    # just return the first one (for now)
    return(configs)


def test_locomos_variable_listing(locomos_configs):
    for locomos_config in locomos_configs:
        station = LocomosStation.init_from_dict(locomos_config)
        # empty to start
        assert station.variables == {}

        station._get_variables()
        assert len(station.variables) > 0 

        var_names = station.variables.values()
        assert 'rh' in var_names
        assert 'lws1' in var_names
        assert 'temp' in var_names
        print(station.variables)


