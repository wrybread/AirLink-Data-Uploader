# AirLink Data Uploader

The Davis AirLink is a great air quality monitor, but it doesn't (currently) have a built in way of uploading it's data to a remote webserver, at least not without buying their paid service. 

So I fixed that in two ways:

- with a Python script that downloads the data from the AirLink via their V1 API and creates air quality indexes locally, and optionally posts the data to a remote webserver.

- with a C script that runs on an ESP32 (a $5 Arduino-like computer) that downloads the data from the AirLink and uploads it to a remote webserver, where a Python script receives it, calculates air quality indexes, and inserts it to a database. I'm using the Arduino IDE for that. And note that there's currently a bug in the Arduino httpclient library, see [here](https://github.com/espressif/arduino-esp32/issues/3659). "Fixed" by making the modification to the library mentioned at the [top of the script](https://github.com/wrybread/AirLink-Data-Uploader/blob/main/airlink_poster.ino). 

Also here is my Python script that receives the data from my ESP32 (sent by airlink_poster.ino). It's a bit rough but might be useful as a starting point.

You can see my Airlink uploading here:

https://lawsonslanding.com/webcam.html
