"""RAINWISE specific station tests"""
from ewx_pws.rainwise import RainwiseStation, WeatherStation

# this is a placeholder , add rainwise-specific test if ever needed
def test_rainwise_station(station_configs):
    station = RainwiseStation.init_from_dict(station_configs['RAINWISE'])
    assert isinstance(station, WeatherStation)
    assert station.config.station_type == 'RAINWISE'
