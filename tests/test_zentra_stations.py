"""ZENTRA specific station tests"""
from ewx_pws.zentra import ZentraStation, WeatherStation

# this is a placeholder , add type-specific test if ever needed
def test_station(station_configs):
    station = ZentraStation.init_from_dict(station_configs['ZENTRA'])
    assert isinstance(station, WeatherStation)
    assert station.config.station_type == 'ZENTRA'
