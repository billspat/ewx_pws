"""DAVIS station type specific tests"""
from ewx_pws.davis import DavisStation, WeatherStation

# leave this as a place holder to add Davis-specific tests if ever needed
def test_davis_station(station_configs):
    station = DavisStation.init_from_dict(station_configs['DAVIS'])
    assert isinstance(station, WeatherStation)
    assert station.config.station_type == 'DAVIS'
          