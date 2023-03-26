from ewx_pws.onset import OnsetConfig, OnsetStation, WeatherStationConfig, WeatherStation

# note: fixtures auto-imported from conftest.py

def test_onset_config(fake_station_configs):
    station_type = 'ONSET'
    c = OnsetConfig.parse_obj(fake_station_configs[station_type])
    assert isinstance(c, OnsetConfig)
    
def test_onset_class_fake(fake_station_configs):
    station_type = 'ONSET'
    onset_station = OnsetStation.init_from_dict(fake_station_configs[station_type])
    assert isinstance(onset_station, WeatherStation)
    assert isinstance(onset_station.id, str)
    
def test_onset_class_instantiation_from_config(station_configs):
    station_type = 'ONSET'
    onset_station = OnsetStation.init_from_dict(station_configs[station_type])
    assert isinstance(onset_station, WeatherStation)
    assert isinstance(onset_station.id, str)


    
    
    