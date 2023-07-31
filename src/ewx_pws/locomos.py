import logging, json
from requests import post, Session, Request
from datetime import datetime, timezone

from ewx_pws.weather_stations import WeatherStationConfig, WeatherStationReading, WeatherStation, STATION_TYPE

class LocomosConfig(WeatherStationConfig):
        station_id     : str
        station_type   : STATION_TYPE = 'LOCOMOS'
        token          : str # Device token
        id             : str # ID field on device webpage
        tz             : str

class LocomosStation(WeatherStation):
    """Sub class for  MSU BAE LOCOMOS weather stations used for TOMCAST model"""
    @classmethod
    def init_from_dict(cls, config:dict):
        """ accept a dictionary to create this class, rather than the Type class"""
        # this will raise error if config dictionary is not correct
        station_config = LocomosConfig.parse_obj(config)
        return(cls(station_config))

    def __init__(self,config: LocomosConfig):
        """ create class from config Type"""
        super().__init__(config)
        self.variables = {}

    def _check_config(self):
        # TODO implement 
        return(True)

    def _get_variables(self):
        """load ubidots variable list
        
        gets the list of variables and their IDS for this Ubidots device via the Ubidots API. 
        Ubidots is flexible and allows for multiple sensors or 'variables' each with it's own label and ID. 

        when the LOCOMOS station is set-up, sensors are defined with standardized labels.  
        Those labels are used to transform the data to EWX standard naming

        If this object already has a non-empty variable list, does not make the request a second time

        returns : dictionary keyed on serial id and values are common names (label)
        """
        if self.variables is None or len(self.variables) == 0:
            # object member is empty, load and save list of variables from API
            var_request = Request(method='GET',
                    url=f"https://industrial.api.ubidots.com/api/v2.0/devices/{self.config.id}/variables/", 
                    headers={'X-Auth-Token': self.config.token}, 
                    params={'page_size':'ALL'}).prepare()
            var_response = json.loads(Session().send(var_request).content)

            variables = {}   
            for result in var_response['results']:
                variables[result['id']] = result['label']
            
            #TODO add logging
            self.variables = variables
        
        return(self.variables)
    
        
    def _get_readings(self, start_datetime:datetime, end_datetime:datetime):
        """
        Pull "data raw series" from UBIDOTS api.  Note they use POST rather than get.  
        See Ubidots doc : https://docs.ubidots.com/v1.6/reference/data-raw-series
        Params are start time, end time in UTC
        Returns api response in a list with metadata
        Example Curl command 
        # curl -X POST 'https://industrial.api.ubidots.com/api/v1.6/data/raw/series' \
        #     -H 'Content-Type: application/json' \
        #     -H "X-Auth-Token: $TOKEN" \
        #     -d '{"variables": ["6410e8564a53ce000ec46e46"], "columns": ["variable.name","value.value", "timestamp"], "join_dataframes": false, "start": 1679202000000, "end":1679203800000}'
        """
        
        start_milliseconds=int(start_datetime.timestamp() * 1000)
        end_milliseconds=int(end_datetime.timestamp() * 1000)
  
        request_headers = {
            'Content-Type': 'application/json',
            'X-Auth-Token': self.config.token,
        }

        variables = self._get_variables()
        if isinstance(variables, dict) and len(variables) > 0: 
            variable_ids = list(variables.keys())
        else:
            raise RuntimeError(f"LOCOMOS station {self._id} could not get variable list")

        response_columns = [
            'timestamp', 
            'device.name', 
            'device.label', 
            'variable.id', 
            'value.context', 
            'variable.name', 
            'value.value'
            ]
        
        request_params = {
                'variables': variable_ids,
                'columns': response_columns,
                'join_dataframes': False,
                'start': start_milliseconds,
                'end': end_milliseconds,
        }            
        
        response = post(url='https://industrial.api.ubidots.com/api/v1.6/data/raw/series', 
                            headers=request_headers, 
                            json=request_params)
        
        return(response)


    def _transform(self, response_data=None)->list:
        """
        Transforms response text from Zentra API into a standardized format 
        params:
            response_data : JSON string from response.text or dict 
        returns:
            list of dict for each sensor reading
        """

        if isinstance(response_data, str):
            response_data = json.loads(response_data)

        readings_list = [] # WeatherStationReadings()

        #### step 1
        # re-orient the ubidots output (one list per sensor) to rows of dict  ( one per sensor)
        # with columnnames 
        r = response_data['results'] # this contains all the values but no colum names
        c = response_data['columns'] # these are the column names for corresponding vals

        # strip off device id from columns since we don't need that
        def rm_dev_id(colname, delim = "."):
            if(delim in colname):
                colname = delim.join(colname.split('.')[1:])
            return(colname)

        # ubidots returns lists of lists 
        # 'cell' is data record from a single sensor/device
        # cells is list of all records flattened together,keys on column name
        cells = []
        for i in range(0,len(r)): # for i in 1..len(r):
            cnames = [ rm_dev_id(c) for c in c[i]]
            for j in range(0, len(r[i])):
                cells.append(dict(zip(cnames, r[i][j])))

        #### step 2
        # convert cells (single sensor value ) to rows (values for all sensors)
        # rows are keyed on timestamp the reading was taken
        rows = {}
        for cell in cells:
            # build up row keys as we 
            if cell['timestamp'] not in rows.keys():
                rows[cell['timestamp']] = {'timestamp': cell['timestamp']}

            key = cell['variable.name']
            value = cell['value.value']
            rows[cell['timestamp']][key] =  value

        #### step 3
        # convert each row to format used by ewx
        readings = []
        for row in rows.values():
            reading = {
                # TODO add leaf wetness here and in data model
                'data_datetime':datetime.fromtimestamp(row['timestamp'] / 1000).astimezone(timezone.utc),
                'atemp':row['Temperature (C)'],
                'pcpn':round(row['Precipitation (in)'] * 25.4, 2),
                'relh':row['Humidity (%)']
            }
            readings.append(reading)

        return readings

    def _handle_error(self):
        """ place holder to remind that we need to add err handling to each class"""
        pass

