
# ZENTRA

import json, logging, time
from requests import Session, Request
from datetime import datetime, timezone
import pytz # instead of zone info to be able to use current config timezone codes 

from ewx_pws.weather_stations import WeatherStationConfig, WeatherStation, STATION_TYPE

class ZentraConfig(WeatherStationConfig):
        station_type   : STATION_TYPE = 'ZENTRA'
        sn             : str #  The serial number of the device.
        token          : str # The user's access token.

class ZentraStation(WeatherStation):

    # time between readings in minutes for this station type
    interval_min = 5

    @classmethod
    def init_from_dict(cls, config:dict):
        """ accept a dictionary to create this class, rather than the Type class"""

        # this will raise error if config dictionary is not correct
        station_config = ZentraConfig.parse_obj(config)
        return(cls(station_config))

    
    def __init__(self,config:ZentraConfig, max_retries : int = 2):
        self._max_retries : int = max_retries
        super().__init__(config)  

    @property
    def max_retries(self):
        return self._max_retries

    @max_retries.setter
    def name(self, value: int):
        self._max_retries = value

    def _check_config(self):
        return True
    
    def _get_readings(self, start_datetime:datetime, end_datetime:datetime, start_mrid=None, end_mrid=None)->list:
        """ Builds, sends, and stores raw response from Zentra API
        start_datetime, end_datetime : timezone aware datetimes in UTC
        start_mrid, end_mrid = ???
        """
        self.current_api_request = Request('GET',
                               url='https://zentracloud.com/api/v3/get_readings',
                               headers={
                                   'Authorization': "Token " + self.config.token},
                               params={'device_sn': self.config.sn,
                                       'start_date': start_datetime.astimezone(pytz.timezone(self.config.pytz())),
                                       'end_date': end_datetime.astimezone(pytz.timezone(self.config.pytz())),
                                       'start_mrid': start_mrid,
                                       'end_mrid': end_mrid}).prepare()
        
        response = Session().send(self.current_api_request)

        # Handles the 1 request/60 second throttling error
        retry_counter = 0
        while response.status_code == 429 and self.max_retries > 0:
            retry_counter += 1
            if retry_counter > self.max_retries:
                err_message = f"Zentra timed out {self.max_retries} times"
                raise RuntimeError(err_message) 

            lockout = int(response.text[response.text.find("Lock out expires in ")+20:response.text.find("Lock out expires in ")+22])
            
            logging.warning("Error received for too frequent attempts, retrying in {} seconds...".format(lockout+1))

            time.sleep(lockout + 1)

            response = Session().send(self.current_api_request)

        return(response)

    def _transform(self, response_data)->list:
        """
        Transforms response text from Zentra API into a standardized format 
        params:
            response_data : JSON string from response.text or dict 
        returns:
            list of dict for each sensor reading
        """
        
        if isinstance(response_data, str):
            response_data = json.loads(response_data)

        # Return an empty list if there is no data contained in the response, this covers error 429
        print(response_data)

        if 'data' not in response_data.keys():
            logging.debug("data element not found in response_data (returning empty):")
            logging.debug(response_data)
            return []
        else:
            logging.debug("Zentra readings found")
        
        readings = []
        # Build a ZentraReading object for each and put it into the readings_list
        # the readings are sensor-wise, not timestamp-wise, so we need to collect all the timestamps from 
        # the first reading, then build our list sensor wise. 

        # to get the timestamps, previously relied on hard-coded key to get one element
        # reading in response_data['data']['Air Temperature'][0]['readings']

        # use the first sensor in data to get the list of timestamps.  
        # data is keys on sensors

    
        # hard coded sensor transform names.  Update this to add more types of sensors.  assumes there is no transform of these values needed
        sensor_transforms = {'Air Temperature':'atemp', 'Precipitation':'pcpn','Relative Humidity':'relh'}
        station_sensors = response_data['data'].keys()

        # list_of_readings_in_data = response_data['data'][station_sensors[0]][0]['readings']
        # a reading is a sensor-per-timestamp

        # a dict of dict keyed on timestamp
        readings_by_timestamp = {}

        for sensor in response_data['data']: # response_data['data'].keys()
            

            if sensor in sensor_transforms: # only include those sensors that we have transforms for
                # loop through the readings of this sensor, build up timestamp-keyed dict of dict
                for zentra_reading in response_data['data'][sensor][0]['readings']:

                    timestamp = zentra_reading['timestamp_utc']
                    # if we haven't seen this timestamp before, create a new entry in our readings dict
                    if timestamp not in readings_by_timestamp:
                        # add the datetime which would be the same for all readings with this time stamp
                        reading_datetime = datetime.fromtimestamp(timestamp).astimezone(timezone.utc)
                        readings_by_timestamp[timestamp] = {'data_datetime': reading_datetime}
                    
                    # add this sensor value to our ewx reading dict
                    ewx_field_name = sensor_transforms[sensor]
                    readings_by_timestamp[timestamp][ewx_field_name] = zentra_reading['value']



        # for reading in list_of_readings_in_data:
        #     for sensor in sensors: 

        #     response_data['data']['Air Temperature'][0]['readings']
        #     # timestamp to use as an index to find associated sensor values
        #     timestamp = reading['timestamp_utc']

        #     # dict to hold the sensor values
        #     timestamped_reading = {}
        #     timestamped_reading['data_datetime'] = datetime.fromtimestamp(reading['timestamp_utc']).astimezone(timezone.utc)
        #     timestamped_reading['atemp'] = reading['value']

        #     for reading2 in response_data['data']['Precipitation'][0]['readings']:
        #         # this appears to be able to read multiple values, overwriting until the last
        #         # rewwrite to extract without looping
        #         if reading2['timestamp_utc'] == timestamp:
        #             timestamped_reading['pcpn'] = reading2['value']
        #     for reading2 in response_data['data']['Relative Humidity'][0]['readings']:
        #         # this appears to be able to read multiple values, overwriting until the last
        #         if reading2['timestamp_utc'] == timestamp:
        #             timestamped_reading['relh'] = reading2['value']
            
        #     readings.append(timestamped_reading)

        # return just the list ()
        return readings_by_timestamp.values()
    
    def _handle_error(self):
        """ place holder to remind that we need to add err handling to each class"""
        pass
