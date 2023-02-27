# EWX PWS data collection solution roadmap 

## Architecture Components

### MultiweatherAPI package

invoked to pull data into Python Object with both API JSON and transformed data
Errors return empty object and error codes in raw 

### ewx_pws package

Adds testable structure to pulling from API and saving data in managed way.  This package
will provide methods that can be called by tasks in orchestration framework

 - set the time interval to pull data from 
 - setup the destination of the data (files take no setup, DB connection)
 - read in station list (with config) from CSV (done) or DB
 - for each station
     - pull data for time interval
 - Checking for errors
     - detect if return value is error and hence empty
     - modify transformed data 
 - Validate weather data
 - split data between raw and transformed
 
 - aggregating data from multiple stations into single tabular data
 - add 'id' to download event to link transformed data row to API data output bundle
 
 - saving data
     - can save to different types of sources (file vs sqlalchemy)
     - save raw in one system, transformed in another
 - Data summaries
     - via DB SQL


#### ewx_pws_db

 - part of ewx_pws package
 - manages database libs and interface (SQLAlchemy)
 - the package should save equally to disk, output to screen, to various dbs
 - save data to database managing overwrites, no duplicates
 - station config uploaded to DB from EWX side, Airflow prefers text file for station list
     - need method for reading station list from DB and saving as config file (CSV etc)
 - can read in data for station ID and/or time interval
 

### Validation

Part of ewx_pws package, can use several techniques to add confidence to a data point pulled from PWS

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



