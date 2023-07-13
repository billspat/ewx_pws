"""LOCOMOS specific station tests"""

from ewx_pws.locomos import LocomosStation, WeatherStation

# this is a placeholder , add rainwise-specific test if ever needed
def test_station(station_configs):
    station = LocomosStation.init_from_dict(station_configs['LOCOMOS'])
    assert isinstance(station, WeatherStation)