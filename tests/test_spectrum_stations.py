"""SPECTRUM specific tests"""
from ewx_pws.spectrum import SpectrumStation, WeatherStation

# this is a placeholder for SPECTRUM specific tests, if ever needed
def test_station(station_configs, station_type):
    station = SpectrumStation.init_from_dict(station_configs['SPECTRUM'])
    assert isinstance(station, WeatherStation)
    assert station.config.station_type == 'SPECTRUM'
