# """WIP start on a class to hold this info, 
# not sure if a class is warranted for this yet - why would we need to preseve state?me"""

# from time_intervals import previous_fifteen_minute_period
# from multiweatherapi import multiweatherapi

# class WeatherStation():
#     """configuration and information for a weather station and it's API"""
    
#     def __init__(self, config:dict):
#         """
#         create and manage station meta data and config
#         :param config: single line of station config
#         :type config: dict
#         """
        
#         self.config = config
#         # pull out some of the elements in the dict
#         self._id = config['station_id']
#         self.station_type = config['station_type']
#         self.tz = "ET" # TODO check how this is set in config
        
#         self.current_reading = None
        
    
#     @property
#     def id(self):
#         return self._id

#     def test_connect(self):
#         """ test that we can connect """
#         try:
#             r = self.get_reading()
#         except Exception as e:
#             return(False)
        
#         if r is not None:
#             return True
        
#         return False
    
    
#     def get_reading(self,start_datetime_str = None, end_datetime_str = None):
        
#         if not start_datetime_str:
#             # no start ?  Use the internval 15 minutees before present timee.  see module for details.  Ignore end time if it's sent
#             start_datetime,end_datetime =  previous_fifteen_minute_period()
#         else:
#             start_datetime = datetime.fromisoformat(start_datetime_str)
#             if not end_datetime_str:
#                 # no end time, make end time 15 minutes from stard time given.  
#                 end_datetime = start_datetime + timedelta(minutes= 15)
#             else:
#                 end_datetime = datetime.fromisoformat(end_datetime_str)


#         params = self.station_config
#         params['start_datetime'] = start_datetime
#         params['end_datetime'] = end_datetime
#         params['tz'] = self.tz

#         try:
#             mwapi_resp = multiweatherapi.get_reading(self.station_type, **params)
#         except Exception as e:
#             raise e

#         # includes mwapi_resp.resp_raw, and mwapi_resp.resp_transformed
#         self.current_reading = mwapi_resp
        
#         return mwapi_resp


# def get_reading(station_type, station_config,
#                 start_datetime_str = None,
#                 end_datetime_str = None):
    
#     if not start_datetime_str:
#         # no start ?  Use the internval 15 minutees before present timee.  see module for details.  Ignore end time if it's sent
#         start_datetime,end_datetime =  previous_fifteen_minute_period()
#     else:
#         start_datetime = datetime.fromisoformat(start_datetime_str)
#         if not end_datetime_str:
#             # no end time, make end time 15 minutes from stard time given.  
#             end_datetime = start_datetime + timedelta(minutes= 15)
#         else:
#             end_datetime = datetime.fromisoformat(end_datetime_str)


#     params = station_config
#     params['start_datetime'] = start_datetime
#     params['end_datetime'] = end_datetime
#     params['tz'] = 'ET'

#     try:
#         mwapi_resp = multiweatherapi.get_reading(station_type, **params)
#     except Exception as e:
#         raise e

#     # includes mwapi_resp.resp_raw, and mwapi_resp.resp_transformed

#     return mwapi_resp

#     def reading_fields():
#         """list of fields to expect in a reading, used for testing
#         """
#         return([
#             "station_id",
#             "request_datetime",
#             "data_datetime",
#             "atemp",
#             "pcpn",
#             "relh"
#             ]
#         )
    


