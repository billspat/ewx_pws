# EWX PWS data collection solution roadmap 

## Architecture Components

### Station configuration and Metadata storage

The data collection pipeline reads from a list of stations, creates the station objects and uses those
to collect data.  The stations lists are read from a CSV file, retrieved from database or other type of 'records'

Station configuration varies across vendors, but some data is 'metadata' for this project or common across all types, all 
station specific fiels are inside the config value

**Fields**
 - station_id : alpha numeric
 - station_type : alpha, one of items in a STATION_TYPE, corresponds to the name of python class
 - tz : timezone, all stations must have a time zone but not all require it when querying
 - config : dictionary, which may contain sub dictionaries, stored as JSON string specific to station type
 
To have easy validation for complex, we will use the [Pydantic](https://docs.pydantic.dev) package which allows us to build 
models of complex types for easy converting and basic validation


### MultiweatherAPI package

as of 3/23 we are no longer using this package and pulling functionality for accessing APIs into the packabe below

Errors return empty object and error codes in raw 

### ewx_pws package


Adds testable structure to pulling from API and saving data in managed way.  

**Station APIs**

The base of the API will be Abstract Classes for

 - Config data model/validator: `WeatherStationConfig(BaseModel)`   pydantic 'BaseModel' to define configuration and metadata
 - `class WeatherStation()`: parent class that provided consistent API covers as much common functionality as possible
     - the primary methods for a weather station are to create it (`__init__`) and  `reading = station.get_reading(start, end)`
        and data transformation methods
     - to reduce copy/paste or boilerplate code, this parent class will have a method `get_readings(params)` which will then call 
        an abstract method that must be implemented in the subclasses `_get_readings(params)`
    
for each type of station, create a new file for it, and add speciliazeConfig and Station classes, e.g. 

 - data model like `class ZentraConfig(WeatherStationConfig)` 
 - api and transform subclass `class Zentra(WeatherStation)`
     - `_get_reading()` api methods to get JSON 
     - `_transform()` to convert to standardized record row format 


Getting data process : 
    validate config and create class
    authenticate and create tokens if necessary
    pull data ('readings') for dates requested, add meta data to that 
    set status to check if ok, or save error condition details for diagnostics
    tranform readings into column records, or possibly empty records if data is missing

**Station Setup Tools**
the package should have a method for confirming that a station config is correct.  
A way to accomplish that is to just attempt to create a station object from the config and get some data from it
    - validate that the config is in the correct form
    - if there is a reading we know that station is on-line AND config is correct
    - if there is no reading we know that station is either offline OR config is incorrect. 
        - external manual check is to see if you can log-in to the portal and see the station

**Package Improves**
Data time handling 
  - see 1/2 one branch date time, copy paste and delete branch
  - issue #11
  - come up with concrete things this will fix
  - enforce UTC for all input dates
  - each change of UTC to local and back. 

Documentation
 - review sphinx and markdown doc process
 - add proper docstrings to all functions etc


**LOCMOS stations**
 - add new station type
 - find documentation and attempt to use portal, get data
 - create new station class to handle it
 - will need to deal with fact that this station does not get all data types
    - new property of StationClass
        - what is function of that? when would we use it?  
 - add to ewx_pws setup

TESTS 
 - tests for structured and raw data for ewx_pws
 - test to show how to use.   


#### ewx_pws_db module

 - part of ewx_pws package
 - contains classes that know how to save raw and tx data
    - using classes so that we can have the same interface for testing ( e.g. just dump to stuff to files ) or for cloud/production (database, cloud storage)
 - the database version of these classes manages database libs and interface (psycopg or SQLAlchemy) 
 - the package should save equally to disk, output to screen, to various dbs
 - save data to database managing overwrites, no duplicates
 - station config uploaded to DB from EWX side, Airflow prefers text file for station list
     - need method for reading station list from DB and saving as config file (CSV etc)

 - class to save raw data
    - knows how to add some raw data (that has embedded meta data) to a collection of raw data
        - subclass for different types of storage (file folders, database, etc see below) 
    - save is keyed on station id
    - this could be a big list kept in memory (readings.append()), a folder structure, or cloud storage
    - could be a database table with columns for meta data (station id, timestamps, response code), and a CHAR column that just holds a string version of the JSON (that makes the most sense to me)
    - start with a folder that it gets saved to, naming readings in a way that they can be found again

- class save_transformed
    - knows how to append transformed tabular data to a data store
            - subclass for different types of storage (csvs in file folders, append to csv file, database, etc see below) 
            - subclasses would need different params to `__init__` (e.g. the database subclass would need connection string )

    - needs to be able to write to the data store concurrently, so appending to  a single big CSV file it must knows how to wait if the file is locked)
    - SQLite is an easy database choice, but again must wait if the file is locked by a concurrent process
    - Postgresql -  on local computer, or created in the cloud
    - note this is a separate class from save_raw so that they can be flexible, and because Tx data is tabular

- Database setup
    - install Postgresql on your computer and toy with these python classes to write to it.  
    - Which python library to use?
        - postgresql-only?  https://www.psycopg.org/
        - multidatabase SQLAlchemy, flexible but complicated. Nice ORM
        - I don't think we will ever use anything excpet for postgresql for this project

#### Data pipeline tools

 - DONE station 'factory' or dictionary the maps a string of station 'type' to the class that uses it

 - create new wrapper function save_readings(stations, raw_data_saver, transformed_data_saver)

    - calls get readings for each station
    - checks for errors 
    - saves raw and transformed using classes in ewx_pws_db module
    - saves event log of when readings were taken to help track errors

 - process to pull data using save_readings to set the time interval to pull data from 
 - setup the destination of the data (files take no setup, DB connection)
 - read in station list (with config) from CSV (done) or DB, and for each station
     - instantiate station object from station config
     - validate config 
     - start an on-going process that periodically:
        - sets time interval
        - pulls data for time interval
        - saves data
            - raw
            - transformed
 
 - Checking for errors
     - detect if return value is error and hence empty
     - modify transformed data 
 - Validate weather data
 
 - aggregating data from multiple stations into single tabular data
 - add 'id' to download event to link transformed data row to API data output bundle
 
 - saving data
     - can save to different types of sources (file vs sqlalchemy)
     - save raw in one system, transformed in another
 - Data summaries
     - via DB SQL


 

### Readings Validation

Part of ewx_pws package, can use several techniques to add confidence to a weather data points in the readings

create validator super class and classes for each type of observation that can take as input current reading and external data and return confidence score (could just start at 0 & 1)

- check if it's in wide range (e.g. -40 < temp < 120 ). 
    - set of standard checks per measurement 
- check delta from previous readings is within range depending on time period.   -20 < temp-5min-delta < 20
- check against other nearby stations
    - need to know what 'nearby' means and now to ID stations that are nearby
    - what is range of difference between stations 25/50 miles apart? 
- check deviance from simple linear regression of previous n data points.   
    - create simple set of n datapoints with time t0 to tn vs readings, create regression line and compare difference between predicted value with actual value. would work well execpt for ranges that include local minima/maxima


## Roadmap

 - get package working exactly as needed
     - can run tests from command line
     - build package and documentation
     - can run bin/file.py (done)
     - installable by uploading to pypi eg.`pip install git+https://github.com/billspat/ewx_pws.git`
     - installable as wheel
    - DB insert using sqlalchemy, use sqlite for testing
    - Need to make a wheel for airflow. Currently uses 'poetry' but should only use setup tools. 
    - can save raw and transformed as needed (raw to storage, transformed to db)

 - use it with airflow 
    - on local computer, install MWAA test environmwent 
    - test can 'install' it to airflow using wheel
    - basic DAG to import python and pull data on a simple schedule, 1 to 10 stations
    - for one weather station, use embedded config e.g. CSV file in DAG folder
    - insert data into DB via Airflow
    
 
  - ensure we can scale: dynamic airflow DAGs to scale
    - python code in the package to read from db and save as python file
    - Not necessarily as CSV.  for one weather stations embedded config
    - https://airflow.apache.org/docs/apache-airflow/stable/howto/dynamic-dag-generation.html#generating-python-code-with-embedded-meta-data

 - implement process for updating station list for Airflow
     - worst case: copy config into DAG folder manually (S3)
     - add to ewx_pws package: read from DB and write file to DAG folder (S3)
     - daily airflow schedule to update station list file 

    - **for above example** 
       - manual or other process (lambda function?)
       - read from DB
       - save as some format to storage maybe?
       - write to .py file inside Airflow storage

 - Validation system 
     - create a basic validator system, add to schema

 - Error/retry system
     - determine how to handle invalid data
     - backfill system in airflow to retry when there is an API errors
     - add to db schema to indicate what's been tried/retried



