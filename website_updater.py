#!/usr/bin/python


'''

This gets the data from an AirLink and posts it to a remote webserver using the Airlink v1 API:

http://10.10.10.51/v1/current_conditions

Params explained here:
https://weatherlink.github.io/airlink-local-api/

Uses the Python-AQI library to calculate the AQI:
https://github.com/hrbonz/python-aqi

Tested on Python 2.7 but should work with 3 as well.

'''

import aqi # pip install python-aqi
import requests
import time
import urllib
import json
from decimal import Decimal

# IP of your AirLink
ip = "10.10.10.51"



have_data=False

try:
    response = requests.get("http://%s/v1/current_conditions" % ip)
    data = response.json()
    conditions = data["data"]["conditions"][0]
    print ("Data received from AirLink:")
    print (data)
    print ("")
    
    pm_2p5_aqi = aqi.to_aqi([
        (aqi.POLLUTANT_PM25, conditions["pm_2p5"]),
        #(aqi.POLLUTANT_PM10, conditions["pm_10_last_1_hour"])
    ])
    print ("Current AQI: %s" % pm_2p5_aqi)
    conditions["pm_2p5_aqi"]=pm_2p5_aqi

    pm_2p5_last_1_hour_aqi = aqi.to_aqi([
        (aqi.POLLUTANT_PM25, conditions["pm_2p5_last_1_hour"]),
    ])
    print ("1 Hour AQI: %s" % pm_2p5_last_1_hour_aqi)
    conditions["pm_2p5_last_1_hour_aqi"]=pm_2p5_last_1_hour_aqi

    pm_2p5_nowcast_aqi = aqi.to_aqi([
        (aqi.POLLUTANT_PM25, conditions["pm_2p5_nowcast"]),
    ])
    print ("Nowcast AQI: %s" % pm_2p5_nowcast_aqi)
    conditions["pm_2p5_nowcast_aqi"]=pm_2p5_nowcast_aqi

    print ("")
    have_data=True


except Exception as e:
    print ("Error getting data from AirLink: %s" % e)



# optionally update a remote database
try:

    if have_data:

        url = "http://your_website.com/aqi/data_receiver.py?pm_2p5_aqi=%s&pm_2p5_last_1_hour_aqi=%s&pm_2p5_nowcast_aqi=%s" % (pm_2p5_aqi, pm_2p5_last_1_hour_aqi, pm_2p5_nowcast_aqi)

        print (url)
        
        response = requests.get(url)

        print ("Response received: %s" % response.text)
        

except Exception as e:
    print ("Error posting data: %s" % e)

