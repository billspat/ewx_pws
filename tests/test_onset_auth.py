"""ONSET specific station tests"""

from weather_stations.onset import OnsetStation
from ewx_pws.ewx_pws import configs_of_type
import re


def test_onset_auth(station_configs):
    onset_configs = configs_of_type(station_configs, station_type='ONSET')
    for onset_config in onset_configs:
        station = OnsetStation.init_from_dict(onset_config)
        # example token 2b43bb08895d00bfa37c5477348e3bdd
        token = station._get_auth()
        assert isinstance(token, str)
        assert len(token) > 2
        token_pattern = re.compile('[0-9a-z]+')
        assert re.fullmatch(token_pattern,station.access_token)
