# Development Notes

this is not intended for package documentation but a place to keep dev notes. 

see the [Roadmap](roadmpa.md) for concrete dev planning

---
# Package layout 
how to set up package for models, weather collection, e
A roadmap for setting up this package with various functionalities

```
ewx_pws
├─ ewx_pws
│  ├─ api # means to access the data 
│  │  ├─ v1
│  │  │  ├─ __init__.py
│  │  │  ├─ dependencies.py
│  │  │  └─ routes.py
│  │  ├─ __init__.py
│  │  └─ models.py  # input/output models just for the api
│  ├─ database
│  │  ├─ __init__.py
│  │  ├─ models.py
│  │  ├─ repository.py
│  │  └─ session.py
│  ├─ doc
│     ├─ ewx_pws.ipynb  # python notebook
│     ├─ database.ipynb  # python notebook
│     ├─ ROADMAP.md
│     ├─ ewx_pws.ipynb  # python notebook
│     └─ etc 
│  ├─ weather_stations  # for pulling data from the api
│     ├── __init__.py
│     ├── locomos.py
│     ├── models.py
│     ├── onset.py
│     ├── rainwise.py
│     ├── spectrum.py
|     ├── weather_stations.py
│     └── zentra.py
│  ├─ __init__.py
│  ├─ ewx_pws.py  # main coordinating program, setup up stations, db, etc
│  ├─ time_intervals.py
|  ├─ weather_store.py  # connection between stations and db?
│  └─ ?config.py # read .env config and set things up
├─ requirements
│  ├─ base.txt
│  └─ dev.txt
├─ scripts
│  ├─ create_test_db.sh
│  ├─ migrate.py
│  └─ run.sh
├─ tests
│  ├─ conftest.py
│  ├─ test_all_stations.py
│  ├─ test_ewx_pws.py
│  ├─ test_zentra.py
│  ├─ test_database.py
│  └─ test_api.py
├─ .env # config
├─ .gitignore
├─ .pre-commit-config.yaml
├─ Dockerfile
├─ Makefile
├─ README.md
├─ docker-compose.yaml
├─ example.env
└─ pyproject.toml
```

workflow / scheduler system: Dagster
```
.
└── ewx-pws-scheduler
    ├── README.md
    ├── ewx_pws_scheduler
    │   ├── __init__.py
    │   └── assets.py
    ├── ewx_pws_scheduler_tests
    │   ├── __init__.py
    │   └── test_assets.py
    ├── pyproject.toml  # dependency ewx_pws
    ├── setup.cfg
    └── setup.py

```

when installing a dagster scaffold project, it adds this to `__init__.py`

```
# __init__.py
from dagster import Definitions, load_assets_from_modules

from . import assets

all_assets = load_assets_from_modules([assets])

defs = Definitions(
    assets=all_assets,
)

```

maybe should create a stand-alone package just for ewx_pws that gets imported into a dagster project, 

1) this makes it more useable with different workflow systems
2) the 'api' to access the data etc can live there
3) ewx_pws has all the functions needed to 
    - get current weather and insert into the db, report errors, 
    - check if there are errors
    - get data for arbitrary time period from 1 station
    - get data from all stations?
    - get stations array (list)

```
ewx_pws
├── .env  # configuration
├── .gitignore
├── CHANGELOG.md
├── CONTRIBUTING.md
├── LICENSE
├── README.md
├── alembic # database migrations, not needed when installing the package, so top level
│   ├── README  # alembic 
│   ├── env.py
│   ├── script.py.mako
│   └── versions
│       └── 39d97abdc96c_create_stations_table.py
├── alembic.ini
├── bin
│   └── getweather.py  # cli interface.  
├── docs
│   ├── __init__.py
│   ├── Makefile
│   ├── _build # output of doc build makefile
│   │   ├── doctrees
│   │       └── stuff here
│   │   └── jupyter_execute
│   │       └── example.ipynb
│   ├── changelog.md
│   ├── conf.py
│   ├── contributing.md
│   ├── db-structures.md
│   ├── index.md
│   ├── make.bat  # windows script to create the docs
│   ├── notes.md
│   ├── requirements.txt # to build documentation
│   ├── roadmap.md
│   └── sensor_variables.md
├── notebooks
│   ├── __init__.py ?
│   ├── collector.ipynb
│   ├── database.ipynb
│   ├── example.ipynb
│   ├── stations.ipynb
│   └── etc...
├── poetry.lock
├── pyproject.toml
├── requirements.txt # not needed if truly using poetry
├── src # functionality when installing the package
│   ├── api # means to access the data 
│   │   ├─ v1
│   │   │  ├─ __init__.py
│   │   │  ├─ dependencies.py
│   │   │  └─ routes.py
│   │   ├─ __init__.py
│   │   └─ models.py  # input/output models just for the api
|   └── database
│   │   ├── __init.py__
│   │   ├── create db script?
│   │   ├── models.p
│   │   ├── repository.py # not sure what this is
│   │   └── session.py  # set up the connection
│   └── ewx_pws
│   │   ├── __init__.py
│   │   ├── datetime_utc.py  # not sure this is used
│   │   ├── ewx_pws.py  # 
│   │   ├── models.py  # these are mostly in 
│   │   ├── time_intervals.py # this is a collection of models _and_ functions
│   │   ├── weather_collector.py  #  move all functionality into ewx_pws
│   │   ├── weather_store.py # this may no longer be needed, use database for all persistance
│   │   └── etc ...
│   └── weather_stations  #### change this
│   │   ├── __init__.py
│   │   ├── davis.py
│   │   ├── ewx_pws.py  # remove this to level above
│   │   ├── locomos.py
│   │   ├── models.py # just for weather stations??
│   │   ├── onset.py
│   │   ├── rainwise.py
│   │   ├── spectrum.py
│   │   ├── weather_stations.py
│   │   └── zentra.py
│   └── ? other functionality of package
├── tests
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_all_station_types.py
│   ├── test_ewx_pws.py
│   ├── test_locomos_stations.py
│   ├── test_onset_auth.py
│   ├── test_read_config.py
│   ├── test_station_classes.py
│   ├── test_timeintervals.py
│   └── test_weather_collector.py
└── etc

additional files needed for configuration,
these must stay out of the git repo, but need to these for testing!  
gitignore *.db and *.csv

├── ewx_pws_dev.db
├── test_stations.csv # kept out of git! 

```
---
# DB structures for PWS project

**problem: currently conflating physical station with station API  config/use.**

StationConfig:

- Station = physical station_config, common across stations
- APIconfig = info needed to access the API, this 
- FUTURE: sensor list


### Station Class => database table

attributes:
- station type
- deployment details: location, dates
- owner
- log of station problems, moves, etc
- sensor list
    - some have sensor IDs used for the API but not all 
- api_config : char

methods:
 - database record methods
 - import from CSV!   


WeatherStation model: 
    load info  <- info class  do we _need_ a separate class?
        question : can the station class be basemodel and have db attribs????
        or just use it as db 
    load config <- config class
    api_config : str

APIConfig model:
 - station type
 - config 
 - subclasses
 - no database table
 - load from JSON

WeatherAPI class 
     ( not a model, subclass for each api type ) 
    station_type <- station table
    api_config <- apiconfig <- JSON
    get raw data() -> rawdata_class -> database
    transform raw data() -> readings_class -> database

    IF config changes (sensors add/remove), the transform may or may not work.   

### Station API Attribs

database tables: 

stations: 
    physical status: location, user, date implemented
    api connection config <- json
    
getting station info into database
    assume data is maintained elsewhere
    maintain a CSV file
    import from CSV file and remove existing stations table completely

    

## problem: don't want to re-write current Pydantic classes

Creating similar SQLalchemy orm classes would be wasted effort.  Also  want to use serialization consistently for all subclasses of a base class. 

https://stackoverflow.com/questions/66808442/writing-a-pydantic-object-into-a-sqlalchemy-json-column


specifically want to use the auto magic ORM methods that come with Pydantic

https://roman.pt/posts/pydantic-in-sqlalchemy-fields/

### sub-problem: psuedo-nested dynamic attributes

each stations has config dict that has different values.  we want to use those as attribs in a pydantic subclass for easy validation etc etc.    but in the serialization, store that as a string of JSON so the db structure can have a single column 'config' rather than many different columns. 

Want a single table of 'stations' that can support all types of stations, so has config in a JSON string BUT currently 'station

main class for station metadata and config str (like a connection string)
StationInfo (BaseModel)

    id
    type
    tz
    station_config:str (json)

    put all the stuff to unserialize inside the station subclass
    that composes this class and station-sepcific config class
    that also keeps this class simple, and defers actions taken on config until WeatherStation instantiation

    station_config classes _never_ go to the db, they are only used to validate JSON sent to them.    
    this means the DB does not do that validation ever.   it must be in the application layer.   

```
class WeatherStationA

    ConfigType = ConfigA

    init:
        # use the base class to deserialize from db etc
        self.config = StationConfig.get_something(orm, dict etc)
        # this is the station specific thing
        self.station_config = ConfigType.parse(json.loads(config.station_config))
    
    read(self, interval):
        c = connect(config_a1 = self.station_config.config_a1, etc)
        stuff = c.get(stuff)
        reading = Reading(stuff)
        return(reading)

```

```
class Reading
    to_orm = save to dict

generic_config
    pass (no config)
    def to_json()
        dict = self.to_dict
        return (json.dumps(dict))


zentra_config(generic_config):
    sn: int
    key:str

onset_config(generic_config):
    whatever: str
    y: str
  
``` 


config classes only know about config. 
 - they are not serialized into db, only to dict, and then to config_json
 - no meta data, save for weatherstation class

```
@classmethod
    def from_orm(cls, obj: Any) -> 'Order':
        # `obj` is the orm model instance
        if hasattr(obj, 'billing'):
            obj.name = obj.billing.first_name
        return super().from_orm(obj)
```

        ClassA(BaseClass):

            config_a1
            config_a2

or 

        ConfigA(BaseModel):
            config_a1
            config_a2

    

using in StationA


ClassB(BaseClass):
    config_b1
    config_b2
    config_b3



ClassA(BaseClass)

    config_a1
    config_a2

    serialize:
        config_json: json.dumps(
            { 
              "config_a1":self.config_a1, 
              "config_a2":self.config_a2
            }
            )
        
        {id:int, type:str, tz:str, config:config_json}


---

# handling API requests
process

raw_store = XStorage()
tabuler_store = Something()

station = setup station with config, options
given start & end timestamps
responses = station.get_reading(s,e) -> save to object (why?)
response_data = station.package_raw_data(s, e,responses) -> save state why?
status <- raw_store.save(response_data) assign request ID for later retrieval


tabular output <- transform(response_data, request_id, options)
    setup returned data structure
    api response data = standard serilizaed format of API data OR
            data stored in object
    - have the subclass _transform _only_ handle the raw api output NOT metadata
        - the parent class can handle all of the metadata processing since this is 
    stored consistently in parent class or serialized data, this makes it flexible; 
        - the parent class can strip out the raw api data and hand that to _transform 
        - _transform does not need to return full rows of data, only dictionary of standardized keys
         - how to set those keys to ensure consistency from each sub class?
         - use a standard data class as we are now
         COULD have function for _each_ key.  
          def _atemp(self, response_data):
                atemp = 
                return()

---- post-hoc transform
response_data = raw_store.read(s,e,station_id, request_id???)




super class 
    get reading(s,e)
        ! store current s,e in object
        self.current_response = subclass._get_reading
        
        **need to also store start/end times that were used**

    current_response_data()
        setup structure to store data
        call subclass to work with station-specific format
        return list/dict

    transform(saved_reading)

        standard format


sub class
    _getreading(s,e)
        gets and returns a response only
        
    
        converts response object + object config => reading data
            need to store 

    _response_data()

    _transform(reading)

        converts saved re



 - easy and consistent way to keep current response
 - transform needs to work on 
    1. stuff stored in the object : the response object + station config 
    2. serialized version of the above.  cant' really serialize a response?

    
 - consistent way to format and store a 'raw' response  

do we need to store the 'metadata' for a request from 

dictionary: {
    "station_type": self.config.station_type,
    "station_id": self.config.station_id,
    "timezone": self.config.tz, 
    "start_datetime_utc": start_datetime,
    "end_datetime_utc": end_datetime,
    "response_count": 0,  # why
    "package_version": version('ewx_pws')
    "api_responses": [
        {
        specific elements from response model
        }
    ]

}


```
metadata == 
    r = response.
    data already in teh class (config)
    
    request timestamp = r.headers['Date']
    status (error condition) (in request )
    status_msg : text of error condition, if any (in request)
```


IF need to make multiple requests = 

```Python

until done:
    r = r.append(request)

self.current_response 
```

ONLY need to create the response 
need to serialize only if storing for later
need a consistent structure for serializing that could be fed 
into _transform


## results members to serialize

### don' t need
'apparent_encoding'
? 'iter_content', 
? 'iter_lines', 
? 'links', 
? 'next', 

'json',  # already have content, which is json


### keep
'text', # not 'content' since not binary
'encoding'
'status_code',
'headers',  <- have secrets!  good for diagnostics
    'date'
'reason',  OK or error message


## maybe
'request', 
'url' # good for diagnostics
 

'ok', 
'raise_for_status', 

 
'history', 
'elapsed', 

---

## Enviroweather Pipeline script Notes

the pipeline / workflow should be a separate package the imports this one
### support classes

- create new wrapper function save_readings(stations, raw_data_saver, transformed_data_saver)
    - calls get readings for each station
    - checks for errors 
    - saves raw and transformed 
    - save to either SQLite or DB
    - do we ever want to save just to storage?  that would be 1) hard to search 2) hard to link with existing data

which python orm - sqlalchemy

### setup (one time)

- create stations list (unless we have to that every time)
- check api config

### pipeline

every 15 minutes
    - time_interval = previous 14 minutes block
    - for each station:
        - station.get_reading(time_interval)
        - raw_data_saver(station.raw_data)
        - save_readings(stations, raw_data_saver, transformed_data_saver)


TODO : extract from this narrative of things to do; 

1) experiment with different time intervals to see if it every breaks.  
	Will it give you a full 24 of data if you ask for data from time 00:00 to 23:59 for some day?
	how about for 2 days?
	how far back can it go? Does it go back to April 1?  

2) see if you can pull together a data set of concurrent raw data since say April 1 to now.   We haven’t talked about how to combine multiple readings of raw data, and I haven’t looked at the raw output of the LOMOCOS station you just made, but you could combine many readings of transformed data into a table (using Python).  Folks in Python use the Pandas library mostly for tabular data.  If you haven’t used it and are interested in doing python programming , it definitely a must-use package.  



The next two broad steps are 1) code to manage storing reading outputs into database or files 2) automate that every 15 minutes

The next set of tasks is https://gitlab.msu.edu/Enviroweather/ewx_pws/-/blob/main/docs/roadmap.md#ewx_pws_db-module

For this task please create new module (python file).  Either ewx_pws_db or ewx_pws_data?  The name doesn’t really matter.  

You will have to then import it into ewx_pws (or if the packaging works may be just available).   This module will have classes and code for saving outputs (raw, transformed and event information/errors).  We haven’t really talked about event data so focus on raw and transformed.  I tried to put cogent ideas for how to use a database to save these data, but feel free to edit that roadmap file, ask questions directly in it etc.   Once the bullet points in the roadmap make sense to you, create gitlab issues from them and then work from there.    You’ve been doing great at getting ideas turned into code.  

 The transformed is the most straightforward so could start with that. 
