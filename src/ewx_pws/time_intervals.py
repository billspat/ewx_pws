"""utils for editing time stamps"""

from datetime import datetime, timedelta, timezone


def fifteen_minute_mark(dtm=datetime.now(timezone.utc)):
    """return the nearest previous 15 minute mark.  e.g. 10:49 -> 10:45 """
    dtm -= timedelta(minutes=dtm.minute % 15,
                     seconds=dtm.second,
                     microseconds=dtm.microsecond)
    return(dtm)


def previous_fifteen_minute_period(dtm=datetime.now(timezone.utc)):
    """ returns tuple of start/end times that is on the quarter hour and inclusive.   
    input datetime object with timezone , e.g. 03:10:15+00
    output: tuple of two datetime objects, e.g (02:45:00, 03:00:00)
    
    if called successively every 15 minutes, times will overlap , e.g. 
    (02:45:00, 03:00:00), (03:00:00, 3:15:00),(3:15:00, 03:30:00), etc
    """
    end_datetime = fifteen_minute_mark(dtm)
    start_datetime = end_datetime - timedelta(minutes=15)
    return((start_datetime, end_datetime))


def previous_fourteen_minute_period( dtm = datetime.now(timezone.utc) ):
    """ returns tuple of start/end times that is on the quarter hour and not inclusive.   
    input datetime object with timezone , e.g. 03:10:15+00
    output: tuple of two datetime objects, e.g (02:46:00, 03:00:00)

    it's not inclusive so that if called successviely every 15 minutes, it will not overlap
    (02:46:00, 03:00:00), (03:01:00, 3:15:00),(3:16:00, 03:30:00), etc
    """
    end_datetime = fifteen_minute_mark(dtm)
    start_datetime =  end_datetime - timedelta(minutes=14)
    return( (start_datetime, end_datetime))
