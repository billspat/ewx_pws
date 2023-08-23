"""ONSET specific station tests"""

from ewx_pws.onset import OnsetStation, WeatherStation
import re

# this is a placeholder , add type-specific test if ever needed
def test_station(station_configs):
    
    station = OnsetStation.init_from_dict(station_configs['ONSET'])
    assert isinstance(station, WeatherStation)
    assert station.config.station_type == 'ONSET'

def test_onset_auth(station_configs):
    station = OnsetStation.init_from_dict(station_configs['ONSET'])
    # example token 2b43bb08895d00bfa37c5477348e3bdd
    token = station._get_auth()
    assert isinstance(token, str)
    assert len(token) > 2
    token_pattern = re.compile('[0-9a-z]+')
    assert re.fullmatch(token_pattern,station.access_token)
