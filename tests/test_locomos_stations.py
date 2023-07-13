"""LOCOMOS specific station tests"""

from ewx_pws.locomos import LocomosStation, WeatherStation
import datetime
import json


# this is needed because as of 7/13 we only have some data from them 
def test_locomos_station(station_configs):
    station = LocomosStation.init_from_dict(station_configs['LOCOMOS'])
    assert isinstance(station, WeatherStation)

def test_locomos_variable_listing(station_configs):
    station = LocomosStation.init_from_dict(station_configs['LOCOMOS'])
    # empty to start
    assert station.var_list == {}

    station._get_variable_list()
    assert len(station.var_list) > 0 

    var_names = station.var_list.keys()
    assert 'precip' in var_names
    assert 'lws' in var_names
    assert 'temperature' in var_names
    print(station.var_list)


def test_locomos_readings(station_configs):
    station = LocomosStation.init_from_dict(station_configs['LOCOMOS'])

    sdt=datetime.datetime(year= 2023, month = 3, day=19, hour=1, minute=0, second=0).astimezone(datetime.timezone.utc)
    edt=datetime.datetime(year= 2023, month = 3, day=19, hour=1, minute=30, second=0).astimezone(datetime.timezone.utc)

    readings = station.get_readings(start_datetime=sdt, end_datetime=edt)
    print(readings)
    assert readings is not None

    r = readings[1].get('data')
    assert 'precip' in r.keys()
    assert 'lws' in r.keys()
    assert 'temperature' in r.keys()

    tlist =  json.loads(r['temperature'])
    
    assert 'results' in tlist.keys()
    
    # tdata = tlist['results'][0]


