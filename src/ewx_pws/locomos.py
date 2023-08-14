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

    # LOCOMOS variable names are not the same as EWX variable/column names.  
    # when adding variables, update this list
    ewx_var_mapping = {
        # LOCOMOS: EWX
        'rh':'relh',
        'temp':'atemp',
        'prep':'pcpn',
        # 'lws1':'lws1',  # wait on leaf wetness until dynamic variables in place
    }

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
        # map LOCOMOS var names to EWX database names

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
                # variables[result['label']] = result['id']
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
        """ station specific transform
        params response_data: the value of 'text' from the response object e.g. JSON
        
        returns: list of readings keyed on date/teim"""
        def rm_dev_id(colname, delim = "."):
            if(delim in colname):
                colname = delim.join(colname.split('.')[1:])
            return(colname) 

        import re
        def variable_id_from_columns(columns):
            """ some, but not all, column names are prepended with a variable id, 
            like this: 649ded97c607eb000ea8777d.value.value
            this finds the first matching colname and extracts the variable id"""
            pattern_col_with_id =  r"^[0-9a-z]+\.[a-z\.]+$"
            for colname in columns:
                if re.match(pattern_col_with_id, colname):
                    variable_id_for_this_result =  colname.split('.')[0]
                    return(variable_id_for_this_result)

        if isinstance(response_data,str):
            response_data = json.loads(response_data)

        results = response_data['results']
        columns = response_data['columns']

        # maybe switch how we create this
        # make a mapping of the Variable ID code (in the data/column names) with the EWX variables we
        # var_by_id = dict([(var_id,var_name) for var_name,var_id in self._get_variables().items() ] )

        var_by_id = dict( [(var_id,self.ewx_var_mapping[var_name]) for var_id,var_name in self._get_variables().items() if var_name in self.ewx_var_mapping.keys() ] ) 
        
        # readings dict, keyed on timestamp
        readings = {}

        # print(var_dict)
        for j in range(1, len(columns)):
            # is there data? 
            if len(results[j]) == 0:
                continue

            var_id = variable_id_from_columns(columns[j])
            # is this var one we want? 
            if var_id not in var_by_id.keys():
                continue
            else:
                var_name = var_by_id[var_id]
                print(var_name)
                
            # results are a list inside list element, one item for each reading/time interval
            # and just one sensor per result
            for result in results[j]:


                # result is list of one reading (timestamp) for one variable, but does not have varnames 
                # add the var/column names to make it easy
                simple_var_names = [ rm_dev_id(c) for c in columns[j]]
                result_dict = dict(zip(simple_var_names,result ))
                
                if result_dict['variable.id'] != var_id:
                    raise ValueError(f"named variable.id not the same as var_id: {var_id} != {result_dict['variable.id']}")
                
                # add this sensor result / value to the readings list
                # to accumlate the sensors from different readings into single diction, 
                # key it on timestamp, and build up the dict as sensor values come in. 
                # first insert a new readings dict if that timestamp is not yet present, start with data_datetime
                if result_dict['timestamp'] not in readings.keys():
                    data_datetime = datetime.fromtimestamp(result_dict['timestamp']/ 1000).astimezone(timezone.utc)
                    readings[result_dict['timestamp']] =  {'data_datetime': data_datetime}
                
                # add sensor reading to reading dict for this timestamp
                readings[result_dict['timestamp']][var_name] = result_dict['value.value']
                # end result _should_ be readings[per_timestamp] = {'temp':999, 'rh':999, 'lws1':999}


        # readings expected to be a list, not a dict as we've used here to accumulate sensors
        return(list(readings.values()))    


    def _handle_error(self):
        """ place holder to remind that we need to add err handling to each class"""
        pass

