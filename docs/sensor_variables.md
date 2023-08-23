# EWX PWS Variable Documentation

This is a summary of how sensor values are stored in database columns (variables) per stations, with all sensors/variables 
in one place, with differences across weather station types. 

## Air Temperature

Variable name: atemp
Units: C


## Precipitation

Variable name : pcpn
Units: mm

## Relative Humidity

database variable name: relh
Units (unitless %)

## Leaf wetness 
from a discussion w/Keith. 

Big picture is to determine if the sensors are the same (show time series )

variable name : `lw0` or `lws0` for standard sensor, canopy sensor could be lws1 on EWX network stations, but not on PWS stations

It was prosed to use different variable names per station type (DAVIS leaf wetness would be da-lws0).  For the PWS since the data from 
many stations are stored in one table, this would mean multiple columns for leaf wetness.   Instead the data will be normalized and all stored 
in variable `lws0` for readings. 


Station Configurations:

- LOCOMOS (same as Zentra) threshold  > 460  = {0,1}
- DAVIS = 0-15?  threshold > 6 = {0,1}
- ZENTRA =  s ~400 to ? threshold > 450  ( 450 is company standard, 460 if it's dirty) = {0,1}
- ONSET = percent wet per 5 minutes, threshold > 50% = {0,1}
- SPECTRUM = 0 - 15, threshold > 6 = {0,1}
- RAINWISE = minutes wet: 0 - 15 minutes, with some values 16 or 30?  
    not sure what threshold here.  If we summarize those > 6 = {0,1}


From tracy, transforms the : n wet/n periods/hour => hourly %wet > 0.25 => {0,1}


MAWN / Campbell program calculates hourly %wet



## Windspeed

## Wind direction


## Solar Radiation







