from ewx_pws.weather_stations import  WeatherStationConfig, WeatherStation,ZentraConfig, ZentraStation

import pytest, json 


@pytest.fixture
def fake_stations_list():
    """this is fake data and won't connect to any real station API.  The API keys look real but are made up"""
    
    return [
        ['fake_zentra','ZENTRA','{"sn":"z1-1234","token":"d5b8f6391ac38bad6f0b51d7a718b9e3e31eec81","tz":"ET"}'],
        ['fake_davis','DAVIS','{"sn":"123456","apikey":"gtqdcbirudd1sarq6esbvorfj6tw67ao","apisec":"0286g8zxfvr77yhdx3pcwnnqqstdwqel","tz":"ET"}'],
        ['fake_spectrum','SPECTRUM','{"sn":"12345678","apikey":"c3a2f80786398e656b08677b7a511a59","tz":"ET"}']
    ]
    
    
@pytest.fixture
def fake_station_configs(fake_stations_list):
    """this is fake data and won't connect to any real station API.  The API keys look real but are made up"""
    fake_configs = [{'id':'1', 'station_type': 'generic', 'config': '{"tz":"ET"}'}]
    
    for fs in fake_stations_list:
        fake_config = json.loads(fs[2])
        station_type = fs[1]
        station_id = fs[0]
        fake_config.update({'id': station_id, 'station_type': station_type})
        fake_configs.append(fake_config)
    
    return fake_configs


def test_can_subclass_weather_station(fake_station_configs):
    
    class FakeStation( WeatherStation):
        def __init__(self, config):
            self.config = config
        def _check_config(self)->bool:
            return(True)        
        def _get_reading(self,params):
            return "{}"

    fake_config = WeatherStationConfig.parse_obj(fake_station_configs[1])
    fake_station = FakeStation(fake_config)
    
    assert isinstance(fake_station,WeatherStation)
    
def test_zentra_subclass_weather_station(fake_station_configs):
    
    zconfig = ZentraConfig.parse_obj(fake_station_configs[1])
    zstation = ZentraStation(zconfig)
    
    assert isinstance(zstation,WeatherStation)