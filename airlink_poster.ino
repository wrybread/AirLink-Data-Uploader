/*

This gets data from the Airlink using it's v1 API, and posts it to a remote server.

For example http://10.10.10.51/v1/current_conditions

Change the IP below. You'll also need to set the URL of the remote webserver where you'll be posting the data, and set your wifi credentials (search for "ssid").



And ugh, there's a bug in httpclient when it connects to the AirLink, since the AirLink sends the header "connection: close". See here for more info:
https://github.com/espressif/arduino-esp32/issues/3659
https://esp32.com/viewtopic.php?t=13952


My ugly fix: I had to modify HTTPClient.cpp (in C:\Users\MYUSERNAME\AppData\Local\Arduino15\packages\esp32\hardware\esp32\1.0.4\libraries\HTTPClient\src)
Comment out these lines (or change the conditional) (or comment out "_canReuse = false;"):

if(_canReuse && headerName.equalsIgnoreCase("Connection")) {
    if(headerValue.indexOf("close") >= 0 && headerValue.indexOf("keep-alive") < 0) {
        _canReuse = false;
    }
}

*/




// Import required libraries for wifi
#ifdef ESP32
  #include <WiFi.h>
  #include <WiFiMulti.h>
#else
  # these are untested, I've only tested with an ESP32
  #include <Arduino.h>
  #include <ESP8266WiFi.h>
  #include <Hash.h>
  #include <ESPAsyncTCP.h>
#endif



// IP of the Airlink
String airlinkIP = "10.10.10.51";

// Address of the script that receives the data
String receiverURL = "http://YOURWEBSITE.com/data_receiver.py";





#include <HTTPClient.h>

#include <ArduinoJson.h>
DynamicJsonDocument jsonDoc(5000); // remember to allow enough size!

// the WiFiMulti library allows adding multiple wifi SSID's
WiFiMulti wifiMulti;

unsigned long lastUpdateTime = -999999; 

void setup(){
  
  Serial.begin(115200);
  delay(10);

  Serial.println("Starting up!");

  
  /////////////////////////////////////////////
  // Connect to wifi (using wifimulti library)
  /////////////////////////////////////////////

  // specify SSIDs (these must be 2.4ghz networks)
  wifiMulti.addAP("your wifi network name", "your wifi password");
  wifiMulti.addAP("your other wifi network name", "your wifi password"); // can have as many networks as you want
  


  // (Note that must run wifiMulti.run() here or it will reset in a loop...)
  Serial.println("Connecting Wifi...");
  if(wifiMulti.run() == WL_CONNECTED) {
      Serial.println("");
      Serial.print("WiFi connected! ");
      Serial.print( WiFi.SSID().c_str() );
      Serial.print(" ");
      Serial.print("IP address: ");
      Serial.println(WiFi.localIP());
  }

}




void loop(){ 

  delay(200);

  HTTPClient http;  

  bool have_data=false;

  if( (wifiMulti.run() == WL_CONNECTED) && (millis() - lastUpdateTime > 60000) ) {

    // get params from the AirLink
    String airlinkURL = "http://"+airlinkIP+"/v1/current_conditions";      
    Serial.print("Getting data from Airlink: ");
    Serial.println(airlinkURL);
    http.begin(airlinkURL.c_str());
    int httpResponseCode = http.GET();
    
    if (httpResponseCode>0) {
      Serial.print("HTTP Response code: ");
      Serial.println(httpResponseCode);
  
      String payload = http.getString();
  
      // for some reason printing the entire payload causes crashes (for me)!
      //Serial.println(payload);
      
      // process the results in json
      deserializeJson(jsonDoc, payload); 
  
      String pm_2p5 = jsonDoc["data"]["conditions"][0]["pm_2p5"];
      Serial.print("The pm_2p5 is ");
      Serial.println(pm_2p5);
  
      have_data=true;
      lastUpdateTime = millis();
      
    }
    else {
      Serial.print("Error connecting to the AirLink: ");
      Serial.println(httpResponseCode);
    }
  
    http.end();
  
  
    if (have_data) {
  
      delay(1000);
  
      ////////////////////////////////////////
      // send the results to the remote server
      ////////////////////////////////////////
  
      HTTPClient http2;  
  
      // to do: figure out how to simply forward all the json retrieved from the airlink... For now, sending individual params. Oh well.
      Serial.println("Posting the data... ");        
      String receiverURLFull = receiverURL + 
        "?pm_2p5="+jsonDoc["data"]["conditions"][0]["pm_2p5"].as<String>() +
        "&pm_2p5_last_1_hour="+jsonDoc["data"]["conditions"][0]["pm_2p5_last_1_hour"].as<String>() +
        "&pm_2p5_nowcast="+jsonDoc["data"]["conditions"][0]["pm_2p5_nowcast"].as<String>() +
        "&hum="+jsonDoc["data"]["conditions"][0]["hum"].as<String>() +
        "&dew_point="+jsonDoc["data"]["conditions"][0]["dew_point"].as<String>() +
        "&temp="+jsonDoc["data"]["conditions"][0]["temp"].as<String>() +
        "&did="+jsonDoc["data"]["did"].as<String>(); 
  
      Serial.println(receiverURLFull);
      http2.begin(receiverURLFull.c_str());
      int httpResponseCode = http2.GET();
      
      if (httpResponseCode>0) {
        Serial.print("HTTP Response code: ");
        Serial.println(httpResponseCode);
        String payload2 = http2.getString();  
        Serial.println(payload2);  
      }
      else {
        Serial.print("Error posting the data: ");
        Serial.println(httpResponseCode);
      }
    
      http2.end();
        
    } // end if have data


  } // end if connected

  
} // end loop
