#!/usr/bin/env python

import pytest
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from pydantic import ValidationError

from ewx_pws import time_intervals
from ewx_pws.time_intervals import fifteen_minute_mark,previous_fifteen_minute_period, previous_fourteen_minute_period, \
                                    DatetimeUTC, \
                                    DatetimeInterval, previous_fourteen_minute_interval,previous_fifteen_minute_interval

@pytest.fixture
def test_timestamp():
    """return a random timestamp, but just now for now"""
    return datetime.now(timezone.utc)

@pytest.fixture()
def just_past_two():
    return(datetime(datetime.now().year,1,1,hour=2, minute=1, second=0))

def test_15minutemark(test_timestamp):
    """test that we get something always on 15 minutes"""

    # no args
    dtm = fifteen_minute_mark()
    assert dtm.minute % 15 == 0

    # with args
    dtm = fifteen_minute_mark(test_timestamp)
    assert dtm.minute % 15 == 0

    just_past_two = datetime(2022,1,1,hour=2, minute=1, second=0)
    two = datetime(2022,1,1,hour=2, minute=0, second=0)
    assert fifteen_minute_mark(just_past_two) == two

    time_with_seconds  = datetime(2022,1,1,hour=2, minute=1, second=10)
    assert fifteen_minute_mark(time_with_seconds) == two
    


def test_previous_fifteen_minute_period():
    
    pfmp = previous_fifteen_minute_period()
    assert len(pfmp) == 2
    assert pfmp[1] > pfmp[0]
    assert pfmp[0].minute % 15 == 0
    assert pfmp[1].minute % 15 == 0
    start_minute = pfmp[0].minute
    end_minute = pfmp[1].minute
    # if the end minute is at top of clock, call it 60 minutes instead of 0
    if end_minute == 0: end_minute = 60
    assert  abs(end_minute - start_minute) == 15

    now = datetime.utcnow()
    pfmp = previous_fifteen_minute_period(now)
    assert pfmp[1] <= now
    assert now - pfmp[0] > timedelta(minutes=15)
    
    #TODO test that it's ac
    
    sample_dt = datetime(2022,1,1,hour=2, minute=10, second=0)
    pfmp = previous_fifteen_minute_period(sample_dt)
    assert pfmp[1] == datetime(2022,1,1,hour=2, minute=0, second=0)
    assert pfmp[0] == datetime(2022,1,1,hour=1, minute=45, second=0)

def test_previous_fourteen_minute_period():
    pfmp = previous_fourteen_minute_period()
        # check that the interval is really 14 minutes
    assert len(pfmp) == 2
    assert (pfmp[1] - pfmp[0]).seconds == 14 * 60

def test_datetime_utc(just_past_two):
    nowish = datetime.now(timezone.utc)
    dtu = DatetimeUTC(datetime = nowish)
    assert isinstance(dtu.datetime, datetime)
    assert dtu.datetime.tzinfo == timezone.utc

    # fixture should not have a timezone, let's check
    assert just_past_two.tzinfo is None
    with pytest.raises(ValidationError):
        DatetimeUTC(datetime = just_past_two)

    # add a tz and check again  
    
    dt_with_tz = just_past_two.astimezone(ZoneInfo('US/Eastern'))  
    dtu = DatetimeUTC(datetime = dt_with_tz)
    assert isinstance(dtu.datetime, datetime)
    assert dtu.datetime.tzinfo == timezone.utc

