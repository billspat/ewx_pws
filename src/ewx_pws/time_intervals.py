"""utils for editing time stamps"""

from datetime import datetime, timezone, timedelta
from pydantic import BaseModel, root_validator


def is_tz_aware(dt:datetime)->bool:
    """ based on documentation, test if a datetime is timezone aware (T) or naive (F)
    see https://docs.python.org/3/library/datetime.html#determining-if-an-object-is-aware-or-naive
    input dt a datetime object
    returns True if is aware (not naive) False if not tz aware (naive)"""
    if dt.tzinfo is not None:
        if dt.tzinfo.utcoffset(dt) is not None:
            return True
    return False
  
def is_utc(dt:datetime)->bool:
    if not is_tz_aware(dt):
        return False
    
    if not dt.tzinfo == timezone.utc:
        return False
    
    return True
 

class DatetimeUTC(BaseModel):
    """singleton type to validate datetime has a timezone and convert to UTC if so. 
    this was written for DatetimeInterval but no longer used for that. can be used to validate datetime value"""
    datetime: datetime # Needs to be UTC
    # @validator('value')
    # def check_datetime_utc(cls, d):
    #     assert d.tzinfo == UTC
    #     return d

    @root_validator(allow_reuse=True)
    def must_be_tz_aware(cls, values):
        dt = values.get('datetime')
        if dt.tzinfo is not None and dt.tzinfo.utcoffset(dt) is not None:
            values['datetime'] = dt.astimezone(timezone.utc)                
        else:
            raise ValueError('datetime must have a timezone')
        return(values)
    
    # convenience functions
    def strftime(self, *args, **kwargs):
        self.datetime.strftime(args,kwargs)

    def astimezone(self, *args, **kwargs):
         self.datetime.astimezone(args, kwargs)


class DatetimeInterval(BaseModel):
    """ Type to hold a start and end time that have timezones.  Timezones will be converted to UTC.   Note it's preferred to use UTC 
    datetimes from the beginning as local times that occur durng the DST transition will not be known for sure and will most
    likely be incorrect"""
    start: DatetimeUTC
    end: DatetimeUTC
    #
    class Config:
        allow_reuse=True
    
    # don't need this validator if using utc-enforced types     
    # @validator('start','end',allow_reuse=True)
    # def dt_must_have_timezone(cls, dt):
    #     """ensure the date times provided have timezones, and convert those to UTC"""
    #     if dt.tzinfo is not None and dt.tzinfo.utcoffset(dt) is not None:
    #         return(dt.astimezone(timezone.utc))
    #     else:
    #         raise ValueError('datetime must have a timezone')
    #
    @root_validator(allow_reuse=True,pre=True)
    def validate_utc_interval(cls, values):
        """ensure that start is before end"""
        start_dt = values.get('start')
        end_dt = values.get('end')
        #
        if not start_dt.datetime <= end_dt.datetime:
            raise ValueError('end date-time must come after start date-time')
        return(values)


def fifteen_minute_mark(dtm:datetime=datetime.now(timezone.utc))->datetime:
    """return the nearest previous 15 minute mark.  e.g. 10:49 -> 10:45, preserves timezone if any. 
    parameter dtm = optional datetime, default is 'now' using utc timezone """
    dtm -= timedelta(minutes=dtm.minute % 15,
                     seconds=dtm.second,
                     microseconds=dtm.microsecond)
    return(dtm)

def fifteen_minute_mark_utc(dtm:datetime=datetime.now(timezone.utc))->datetime:
    """return the nearest previous 15 minute mark.  e.g. 10:49 -> 10:45, preserves timezone if any. 
    parameter dtm = optional datetime, default is 'now' using utc timezone """

    if not is_utc(dtm):
        raise ValueError("dtm must have timezone set to UTC")
    
    dtm -= timedelta(minutes=dtm.minute % 15,
                     seconds=dtm.second,
                     microseconds=dtm.microsecond)
    return(dtm)

def previous_fifteen_minute_period(dtm:datetime=datetime.now(timezone.utc))->tuple[datetime, datetime]:
    """ returns tuple of start/end times that is on the quarter hour and inclusive. 
    input datetime object with timezone , e.g. 03:10:15+00
    output: tuple of two datetime objects, e.g (02:45:00, 03:00:00)
    
    if called successively every 15 minutes, times will overlap , e.g. 
    (02:45:00, 03:00:00), (03:00:00, 3:15:00),(3:15:00, 03:30:00), etc
    
    """
    end_datetime = fifteen_minute_mark(dtm)
    start_datetime = end_datetime - timedelta(minutes=15)
    return((start_datetime, end_datetime))


def previous_fourteen_minute_period( dtm:datetime = datetime.now(timezone.utc) )->tuple[datetime, datetime]:
    """ returns tuple of start/end times that is on the quarter hour and not inclusive.   
    input datetime object with timezone , e.g. 03:10:15+00
    output: tuple of two datetime objects, e.g (02:46:00, 03:00:00)

    it's not inclusive so that if called successviely every 15 minutes, it will not overlap
    (02:46:00, 03:00:00), (03:01:00, 3:15:00),(3:16:00, 03:30:00), etc
    """
    end_datetime = fifteen_minute_mark(dtm)
    start_datetime =  end_datetime - timedelta(minutes=14)
    return( (start_datetime, end_datetime) )


def previous_fifteen_minute_interval(dtm:datetime=datetime.now(timezone.utc))->DatetimeInterval:
    """ returns  that is on the quarter hour and inclusive. 
    input datetime object with timezone , e.g. 03:10:15+00
    output: tuple of two datetime objects, e.g (02:45:00, 03:00:00)
    
    if called successively every 15 minutes, times will overlap , e.g. 
    (02:45:00, 03:00:00), (03:00:00, 3:15:00),(3:15:00, 03:30:00), etc
    
    """
        
    end_datetime = fifteen_minute_mark(dtm)  # must be utc
    start_datetime = end_datetime - timedelta(minutes=15)
    try:
        dti = DatetimeInterval(start = start_datetime, end = end_datetime )
    except ValueError as e:
        raise(ValueError)
        
    return(dti)

def previous_interval(dtm:datetime=datetime.now(timezone.utc), delta_mins:int=15)->DatetimeInterval:
    """ returns  that is on the quarter hour and inclusive. 
    input datetime object with timezone , e.g. 03:10:15+00
    output: tuple of two datetime objects, e.g (02:45:00, 03:00:00)
    
    if called successively every 15 minutes, times will overlap , e.g. 
    (02:45:00, 03:00:00), (03:00:00, 3:15:00),(3:15:00, 03:30:00), etc

    set arbitrary delta (15 minutes, 14 minutes, 30 minutes, etc)
    
    """
    # starter time - 
    dtm_utc = DatetimeUTC(dtm)

    # quarter hour prior to starter (11:55 ->  11:45, etc)
    end_datetime_utc = DatetimeUTC(fifteen_minute_mark(dtm_utc.datetime))
    # time previous to that for delta
    start_datetime_utc = DatetimeUTC(end_datetime_utc - timedelta(minutes=delta_mins))
    
    try:
        dti = DatetimeInterval(start = start_datetime_utc, end = end_datetime_utc )
    except ValueError as e:
        raise(ValueError)
        
    return(dti)

def previous_fourteen_minute_interval(dtm:datetime=datetime.now(timezone.utc))->DatetimeInterval:
    """ convenience method for using previous interval above for 14 intervals, 
    which are non-overlapping ranges of an hour
    00:00 - 00:14, 00:15 - 00:29, 00:30 - 00:44, 00:45 - 00:59
    """
    dti = previous_interval(dtm, delta_mins=14)
    return(dti)
