from ewx_pws.weather_stations import  WeatherStationConfig, WeatherStation

import pytest, json 

@pytest.fixture
def fake_station_class():
    class FakeStation( WeatherStation):
        def __init__(self, config):
            super().__init__(config)
        def _check_config(self)->bool:
            return(True)        
        def _get_reading(self,params):
            return self.empty_response 
    return(FakeStation)

def test_can_subclass_weather_station(fake_station_configs,fake_station_class):
    fake_config = WeatherStationConfig.parse_obj(fake_station_configs['GENERIC'])
    fake_station_1 = fake_station_class(fake_config)
    assert isinstance(fake_station_1,WeatherStation)
    
def test_can_instantiate_from_dict(fake_station_configs,fake_station_class):
    # test class method for reading from dict
    fake_station = fake_station_class.init_from_dict(fake_station_configs['GENERIC'])
    assert isinstance(fake_station,WeatherStation)
    # test that there are at least _some_ elements
    assert isinstance(fake_station.id, str)
    assert isinstance(fake_station.station_tz, str)
    assert fake_station.station_tz == 'ET'  # this must match the fixture in conftest.py

    # test parent methods that call abstract methods
    assert fake_station._check_config() == True
    assert isinstance(fake_station.get_readings(), list)
