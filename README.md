# AirLink Data Uploader

The Davis AirLink is a great air quality monitor, but it does have a built in way of uploading it's data to a remote webserver, at least not without buying their paid service. 

So I fixed that in two ways:

- with a C script that runs on an ESP32 (an $8 Arduino-like computer) that downloads the data from the AirLink and uploads it to a remote webserver, where a Python script receives it, calculates air quality indexes, and inserts it to a database

- or with a Python script that downloads the data from the AirLink and creates air quality indexes locally, and optionally posts it to a remote webserver.

Also included is a system for displaying the data on a webpage and plotting the AQI history using the excellent flot javascript library. The end result looks like this:

http://sinkingsensation.com/aqi/sample.php
