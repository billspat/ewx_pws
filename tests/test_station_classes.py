from ewx_pws.weather_stations import  WeatherStationConfig, WeatherStation, datetimeUTC, TIMEZONE_CODE
from pydantic import ValidationError
import requests
import pytest, json, pytz, datetime

@pytest.fixture
def generic_station_config():
    """ example config dictionary for generic station, note no sn, password or other info like other stations"""
    return( {'station_id' : 'fakestation', 'station_type' : "GENERIC", 'tz' : "ET" })


@pytest.fixture
def fake_station_class():
    class FakeStation( WeatherStation):
        def __init__(self, config):
            super().__init__(config)
        def _check_config(self)->bool:
            return(True)        
        def _get_readings(self,start_datetime, end_datetime):
            # this is a known fake API for testing.   
            url = 'https://jsonplaceholder.typicode.com/todos/'
            
            response = requests.get(url)
            return [response] # self.empty_response 
        def _transform(self, data = None):
            # might want to make this get tested at some point, don't
            # know how exactly it'd format to correct data? now just
            # returns empty
            return
        
    return(FakeStation)

def test_weatherstation_config_type(generic_station_config):
    # test can parse good config
    ws =  WeatherStationConfig.parse_obj(generic_station_config)
    assert isinstance(ws, WeatherStationConfig)

def test_weatherstation_config_timezone_validation(generic_station_config):    
    """ test that validation fails for incorrect tz code"""
    # test timezone validation with invalid tz
    generic_station_config['tz'] = 'XX'
    with pytest.raises(ValidationError):
        ws =  WeatherStationConfig.parse_obj(generic_station_config)

def test_tz_convert(generic_station_config):
    """basic test that the convert works for one timezone"""
    # set to a known timezone
    generic_station_config['tz'] = 'ET'
    ws =  WeatherStationConfig.parse_obj(generic_station_config)
    assert ws.pytz() == 'US/Eastern'

    

def test_can_subclass_weather_station(generic_station_config,fake_station_class):
    fake_config = WeatherStationConfig.parse_obj(generic_station_config)
    fake_station_1 = fake_station_class(fake_config)
    assert isinstance(fake_station_1,WeatherStation)
    
def test_can_instantiate_from_dict(generic_station_config,fake_station_class):
    # test class method for reading from dict
    fake_station = fake_station_class.init_from_dict(generic_station_config)
    assert isinstance(fake_station,WeatherStation)
    # test that there are at least _some_ elements
    assert isinstance(fake_station.id, str)
    assert isinstance(fake_station.station_tz, str)
    assert fake_station.station_tz == 'ET'  # this must match the fixture in conftest.py

    # test parent methods that call abstract methods
    assert fake_station._check_config() == True

def test_utc_datetimes():
    assert datetimeUTC(value=datetime.datetime(2022,10,10,15,25,0,tzinfo=pytz.utc))
    with pytest.raises(ValidationError):
        est = datetimeUTC(value=datetime.datetime(2022,10,10,15,25,0,tzinfo=pytz.timezone('US/Eastern')))
    with pytest.raises(ValidationError):
        naive = datetimeUTC(value=datetime.datetime(2022,10,10,15,25,0))