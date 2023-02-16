#!/usr/bin/env python
"""Console script for ewx_pws."""
import argparse
import sys, os

from ewx_pws import ewx_pws

def main():
    """Console script for ewx_pws."""
    parser = argparse.ArgumentParser()
    parser.add_argument('csvfile', help="CSV file of stations with config")
    parser.add_argument('-s', '--start', help="start time UTC in format ")
    parser.add_argument('-e', '--end',help="end time UTC in format ")
    # parser.add_argument('_', nargs='*')

    args = parser.parse_args()

    csvfile = args.csvfile
    if os.path.exists(csvfile):
        # try
        stations =  ewx_pws.stations_from_file(csvfile)
        print(f"file has {len(stations)} stations")
    else:
        print(f"file not found {csvfile}")
        return(1)
    
    # get recent data for now (ignore start and end times)
    weather_data = ewx_pws.get_readings(stations)
    print(weather_data)
    return 0


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
