
import os,json, csv
from ewx_pws.ewx_pws import stations_from_file
from ewx_pws.weather_stations import WeatherAPIData,WeatherStationReadings, WeatherStation
from ewx_pws.time_intervals import UTCInterval


class WeatherCollector():
    """ for list of stations, methods for reading and saving raw and structured reading data"""

    def __init__(self, stations:list[WeatherStation], base_path="../weatherdata"):
        """create collector from list of stations and path to save output"""
        self.stations = stations
        self.base_path = base_path
        self.raw_path = os.path.join(base_path, 'raw')
        self.data_path = os.path.join(base_path, 'data')

        os.makedirs(self.raw_path, exist_ok=True)
        os.makedirs(self.data_path,exist_ok=True)

 
    @classmethod
    def init_from_station_file(cls, station_file, base_path=None):
        """ create collector from csv file of station configs and path to save output"""
        stations = stations_from_file(station_file)

        if base_path:
            return(cls(stations = stations,base_path = base_path))
        else:
            # use the default set in init
            return(cls(stations = stations))

    def save_raw(self,  weather_api_data: WeatherAPIData)->str:
        """given weather api data, save some"""
        filename = f"{weather_api_data.key()}.json"
        file_path = os.path.join(self.raw_path, filename)
        with open(file_path, "+w") as f:
            f.write(weather_api_data.json())

        return(file_path)
       
    def save_readings(self, weather_data:WeatherStationReadings ) ->str:
        """save readings as csv"""

        fieldnames = list(weather_data.readings[0].dict().keys())

        data_filename = os.path.join(self.data_path, f"weather_data_{weather_data.key()}.csv")

        with open(data_filename, 'w') as csvfile:
            data_writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            data_writer.writeheader()
            for reading in weather_data.readings:
                data_writer.writerow(reading.dict())

        return(data_filename)

    def collect(self, station:WeatherStation, interval:UTCInterval):        
        """ for one station, collect raw data and transformned data and save both"""
        rawapi = station.get_readings(interval.start, interval.end)
        readings = station.transform(rawapi)
        return(rawapi, readings)


    def collect_and_save(self, station:WeatherStation, interval:UTCInterval):
        """ for one station, collect raw data and transformned data and save both"""
        rawapi, readings = self.collect(station, interval)
        raw_file = self.save_raw(rawapi)
        readings_file = self.save_readings(readings)
        return(raw_file, readings_file)
    

    def collect_readings(self, interval = UTCInterval.previous_fifteen_minutes()):
        """ combine transformed readings for all loaded stations into single array of dict.  
        The output can be loaded into a pandas data frame with df=pandas.DataFrame(readings)

        this is a temporary version that does not save any raw outputs """
        readings  = []

        # TOO also collect raw outputs into a standardized serializable format
        for station in self.stations:
            # this could use threads here, or launch sub processes
            raw,data = self.collect(station, interval)
            readings += data.for_csv()

        return readings
    

    def collect_all_stations(self, interval = UTCInterval.previous_fifteen_minutes()):
        """ collect and save from all stations in class"""
        rawfiles = []
        readingsfiles = []
        for station in self.stations:
            raw_file, readings_file = self.collect_and_save(station, interval)
            rawfiles.append(raw_file)
            readingsfiles.append(readings_file)

        return( rawfiles, readingsfiles)
    
