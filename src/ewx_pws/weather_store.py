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

from sqlalchemy import engine,create_engine, inspect, text, insert
import pandas, sqlite3, os, logging, json, csv
from datetime import datetime

from weather_stations import WeatherStation, WeatherStationReadings, WeatherAPIData, WeatherAPIResponse

class WeatherStore():
    """ this is a very simple class to build and use a SQLite database to 
    collect weather data.   Using Pandas to_sql commands rather than explicit SQL and fields
    while the package is under heavy development and table structure is not set"""
    
    # strategy
    # imported by collector
    # collector uses the store to get the station list, 
    #      how does that get updated?   read from CSV file and throw out existing stations?  insert new station?   
    # 
    stations_table = "STATIONS"
    stations_fields = ['station_id','station_type','install_date','tz','station_config'],
    raw_table = "RESPONSES"
    readings_table = "READINGS"

    def __init__(self, db_file):
        # todo check that it's a valid connection
        if not os.path.exists(db_file):
            Warning("db file {db_file} not found, creating new database")
            # build a new db
            
        self.engine = create_engine(f"sqlite:///{db_file}")
        # create a connection object.  see if we can just use it over and over
        self.connection = self.engine.connect()

        self.stations = {}
  
    def import_stations(self, station_config_file):
        """ create station objects from a CSV file.  Doesn't create a table or records in the db"""
        with open(station_config_file) as csvfile:
            configreader = csv.DictReader(
                csvfile,  
                fieldnames = self.stations_fields,
                delimiter=",", 
                quotechar="'") 
            for config in configreader:
                self.stations[config['station_id']] =  WeatherStation.init_from_record(config)


    def load_stations(self):
        """from the connection in this object, read in the stations and create a list of station objects"""
        from ewx_pws.ewx_pws import STATION_CLASS_TYPES as station_class_types

        # check that the table exist in db we are connected to
        insp = inspect(self.engine)
        if insp.has_table(table_name = self.stations_table):
            result = self.connection.execute(text(f"select * from {self.stations_table}"))

            # build station dict
            self.stations = {}

            for row in result:
                self.stations[row['station_id']] =  WeatherStation.init_from_record(row)

        return(self.stations)


    def db2dict(self, tablename):
        # TODO ensure tablename is one we expect
        rows = []
        try:
            result = self.connection.execute(text(f"select * from {tablename}"))
            for row in result:
                rows.append = row._mapping 
        except Exception as e:
            Warning(f"no rows found in {tablename}")
    
        return(rows)
    

    def db2dataframe(self, tablename):
        """ standardized way to read an entire table"""
        # TODO ensure tablename is one we expect
    
        df = pandas.read_sql_table(tablename, self.connection) 

        # with self.engine.connect() as conn, conn.begin():  
        #     df = pandas.read_sql_table(tablename, conn)  

        return(df)
    
    def dataframe2db(self, data_frame, tablename, if_exists = 'append'):
        """ standarized method for inserting a dataframe into our database using pandas"""
        
        try:
            with engine.connect() as conn, conn.begin():  
                nrows = data_frame.to_sql(name=tablename, con=conn, index=False, if_exists=if_exists) 
        except Exception as e:
            logging.exception(f" pandas database insert/append failed with {self.connection}:{e}")
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


    def create_stations_table_from_file(self,station_config_file):
        """ creates the table and loads up the object property"""

        if os.path.exists(station_config_file):
            stationsdf = pandas.read_csv(station_config_file,header=1,quotechar="'")
            numrows = self.dataframe2db(self, stationsdf, if_exists = 'fail')
            if numrows and numrows > 0: 
                stations = self.read_stations()
                return(stations)
            else: 
                return(None)
        else:
            raise FileExistsError(f"can't find stations file {station_config_file}")    
        

    def insert_readings(self,readings:WeatherStationReadings):
        """ add readings to db table.  if table does not exist, create it first. if table does exist readings fields must conform to table structure.  """

        readings_df = pandas.DataFrame(readings.model_dump_record())
        readings_df.to_sql(name = self.readings_table, con = self.connection, index= False, if_exists = "append")

    def insert_api_response(self,api_response:WeatherAPIData):
        api_response_df = api_response.model_dump_record()
        nrows = self.dataframe2db(api_response_df)
        return(nrows)
    


    

