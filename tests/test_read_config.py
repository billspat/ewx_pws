from ewx_pws.ewx_pws import read_station_configs
from weather_stations import STATION_TYPE_LIST

def test_station_configs(station_file):
    station_configs = read_station_configs(station_file)
    assert isinstance(station_configs, dict)
    assert len(station_configs ) > 0
    for station_id in station_configs:
        config = station_configs[station_id]
        assert isinstance(config, dict)
        assert 'station_id' in config
        assert 'station_type' in config
        assert config['station_type'] in STATION_TYPE_LIST
