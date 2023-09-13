""" weather_store.py

POC database class for uploading weather data into a db

the goal is to 
1) use code to create a db structure based on the structures / fields in WeatherStation models, so 
we don't have to keep the db in parity as we add fields
  - given a station file , create stations table
  - given some weather readings, create a readings table, or insert into a table

2) get stations from this db for the weather collector class

3) basic ways to get data out of the store
    - pull readings by date and / or station

4) hourly/daily summaries
    - create the queries/views with code 
    - run views from the db (not from pandas)

5) ultimately... crud?  
    - would need to delete only if we re-downloaded data to replace
    - need to deal with keys and duplications/redundant data
        - check on insert, row by row
        - create unique constraints - easy for structure data, hard for raw data
    
"""

#TODO use typing and type hints

import pandas, sqlite3, os, logging

from ewx_pws.ewx_pws import weather_station_factory
from ewx_pws.weather_stations import WeatherStationReadings, WeatherAPIData, WeatherAPIResponse

class WeatherStore():
    """ this is a very simple class to build and use a SQLite database to 
    collect weather data.   Using Pandas to_sql commands rather than explicit SQL and fields
    while the package is under heavy development and table structure is not set"""
    
    # strategy
    # imported by collector
    # collector uses the store to get the station list
    # 
    stations_table = "STATIONS"
    raw_table = "RESPONSES"
    readings_table = "READINGS"

    def __init__(self, db_file):
        # todo check that it's a valid connection
        if not os.path.exists(db_file):
            Warning("db file {db_file} not found, creating new database")
            # build a new db
        self.conn = sqlite3.connect(db_file)
        self.conn.row_factory = sqlite3.Row
        self.stations = {}
            

    def dataframe2db(self, data_frame, if_exists = 'append'):
        """ standarized method for inserting a dataframe into our database using pandas"""
        
        try:
            nrows = data_frame.to_sql(self.conn, index=False, method = 'multi', if_exists=if_exists) 
        except Exception as e:
            logging.exception(f" pandas database insert/append failed with {self.conn}:{e}")
            return(None)
        
        return(nrows)
    

    def add_station(self, station_config):
        """ given a dict, or an array of  of a station config, insert into db"""
        if isinstance(station_config, dict):
            station_config = [station_config]

        stationdf = pandas.DataFrame(station_config)

        nrows = self.dataframe2db(stationdf)

        if nrows is None:
            logging.debug("problem adding station(s) ")


    def create_stations_table_from_file(self,station_file):
        """ creates the table and loads up the object property"""

        if os.path.exists(station_file):
            stationsdf = pandas.read_csv(station_file)
            numrows = self.dataframe2db(self, stationsdf, if_exists = 'fail')
            if numrows and numrows > 0: 
                stations = self.read_stations()
                return(stations)
            else: 
                return(None)
        else:
            raise FileExistsError(f"can't find stations file {station_file}")    


    def read_stations(self):
        """from the connection in this object, read in the stations and create a list of station objects"""
        sql = f"select * from {self.stations_table}"
        stations = {}
        for row in self.conn.execute(sql):
            station_id = row['station_id']
            stations[station_id] = weather_station_factory(row)

        # replaces and current station dict with one from DB
        self.stations = stations
        return(self.stations)
        

    def insert_readings(self,readings:WeatherStationReadings):
        """ add readings to db table.  if table does not exist, create it first. if table does exist readings fields must conform to table structure.  """

        readings_df = pandas.DataFrame(readings.model_dump_record())
        readings_df.to_sql(name = self.readings_table, con = self.conn, index= False, if_exists = "append")

    def insert_api_response(self,api_response:WeatherAPIData):
        api_response_df = api_response.model_dump_record()
        nrows = self.dataframe2db(api_response_df)
        return(nrows)
    


    

