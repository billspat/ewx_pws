from typing import Literal

# read version from installed package
from importlib.metadata import version
__version__ = version("ewx_pws")


US_TIMEZONES = Literal["US/Alaska", "US/Aleutian", "US/Arizona", "US/Central", "US/East-Indiana", "US/Eastern", "US/Hawaii", "US/Indiana-Starke", "US/Michigan", "US/Mountain", "US/Pacific", "US/Samoa",
                       "Detroit/Eastern", "New York/Eastern"]