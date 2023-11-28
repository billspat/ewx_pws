from typing import Literal

# read version from installed package
from importlib.metadata import version
__version__ = version("ewx_pws")

# constants used by package
# station type type, like an enum
STATION_TYPE = Literal['ZENTRA', 'ONSET', 'DAVIS', 'RAINWISE', 'SPECTRUM', 'LOCOMOS', 'GENERIC'] 
STATION_TYPE_LIST =   ['ZENTRA', 'ONSET', 'DAVIS', 'RAINWISE', 'SPECTRUM', 'LOCOMOS', 'GENERIC']

US_TIMEZONES = Literal["US/Alaska", "US/Aleutian", "US/Arizona", "US/Central", "US/East-Indiana", "US/Eastern", "US/Hawaii", "US/Indiana-Starke", "US/Michigan", "US/Mountain", "US/Pacific", "US/Samoa",
                       "Detroit/Eastern", "New York/Eastern"]