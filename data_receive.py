#!/usr/bin/python



'''

This receives license plate data from openalpr running at gatehouse eventually.

In the openALPR web interface, click Configuration -> Webhooks and put the address of this script.

Note that after this a Python script (image_uploader.py) on the Agent laptop checks sinkingsensation.com/gatekeeper/image_upload_queue.php for images that need to be uploaded.

Can run as "./plate_receive.py debug" to be in debug mode

Can also run as "./plate_receive.py bozac" to use that plate (and will then use data from "output_raw_debug.txt", except time and plate number).



To do:


- when a plate arrives need to check the flags table to see if it's banned or a known government agency. If so, set is_banned and/or is_government. Also send the alerts...

- disregard dupes. If they're entering again in same 2 minutes, disregard it?

- get working with two cameras.... How to differentiate? Maybe iterate results for a camera and discard any nearby?

- save every error to error_msg string, and write it at end of processing

- count vehicles inside the property

- when showing recent entries, need more pages... (ability to see previous 20 vehicles etc)

- interface for banned plates. And send text message blast when they enter...

- make that damn footer sticky! make a stripped down example and post to a forum?


Current debug plate: 15113C1


API use:
https://www.autocheck.com/consumer-api/meta/v1/summary/plate/".$plate."/state/".$region;



'''



# for testing
disable_alerts = 0


import warnings

import json, time, sys, os, datetime

import urllib

import cgi

# will output errors to html?
#import cgitb
#cgitb.enable()

import pymysql

#import pickle
import dill # like pickle except it can pickle string objects

from helper_functions import *


# if true, will use the file sample.txt as the data
use_debug = 0

# append session data to the log file?
save_to_log_file = 1

# if saving to log, this is the log
log_file = os.path.abspath("gatekeeper_logfile.txt")




# get commands from CLI
debug_plate=False
try:
    if "debug" in sys.argv[1]: use_debug=1
    else:
        debug_plate=sys.argv[1]
        session_code=debug_plate
except: pass



print ("Content-type: text/html\n")


# this will ignore pymysel warnings 
warnings.filterwarnings('ignore', category=pymysql.Warning)


def timestamp():
    dt = datetime.datetime.now()
    return dt.strftime('%Y-%m-%d %-H-%M-%S').lower()

def write_to_log(msg):
    print "Error! %s" % msg

    if save_to_log_file:
        h = open(log_file, "a")
        h.write(msg + "\n")
        h.close()
    


# use the same timestamp for everything in this session
session_code = timestamp()
error_msg = ""


if use_debug:

    debug_method = 2

    if debug_method==1:

        print ("Using pickled data....")

        # open the pickled data (pickled by dill, since needed to be able to serialize/pickle strings)
        h = open('pickled.dill', 'rb')
        data = dill.load(h)
        h.close()

        #data = json.loads( str(data.encode('unicode_escape') ) )

        #print type(data)


    elif debug_method==2:

        # processs a saved file
        fname = "output/2020-06-18 22-25-59.json"
        

        print ("Using a previous session... %s" % fname)

        with open(fname) as json_file:
            data = json.load(json_file)

    else:
        print ("Using text file debug data....")

        # processs a saved file
        fname = "sample.txt"

        with open(fname) as json_file:
            data = json.load(json_file)

        

    






else:

    try:

        fs = cgi.FieldStorage()
        #print data
        #print data["openalpr_webhook"].value

        # save the data raw data
        output_fname = "output_raw/%s.txt" % (session_code)
        
        try: os.makedirs( os.path.dirname(output_fname) )
        except: pass
        h = open(output_fname, "w")
        h.write( str(fs) )
        h.close()

        if debug_plate:
            # if we're doing a debug session by passing a plate (for example "./plate_receive.py bozac") use the output_raw_debug.txt session for the data
            fs = open("output_raw_debug.txt", "r").read()
        

        # cheesy workaround way to process the FieldStorage as a string. Ugh!!!!
        data_str = str(fs)
        data_str = data_str.lstrip("FieldStorage(None, None, '")
        data_str = data_str.rstrip("')")
        #data_str = data_str.strip('"') # remove bracketing quotes
        #data_str = data_str.replace('\\"', '"') # convert the escaped quotes

        
        # convert to json (NO NEED, and converting again adds extra quotes)
        #data = json.dumps(data_str, indent = 4)


        # this converts the cheesy json string to proper json
        data = json.loads( str(data_str.encode('unicode_escape') ) )

        #print (data)


        # save / pickle the data object
        fname =  "pickled.dill"
        handle = open(fname, 'w') 
        #pickle.dump(data, handle)
        dill.dump(data, handle)
                
        
        

    except Exception as e:
        print "Error! %s" % e
        
        output_fname = "errors/%s.txt" % (session_code)
        try: os.makedirs( os.path.dirname(output_fname) )
        except: pass
        msg = time.strftime('%Y-%m-%d %-I:%M %p').lower()
        msg += ": Error processing request!\n\n"
        msg += str(e)
        handle = open(output_fname, "w")
        handle.write(msg)
        handle.close()
        print (msg)

        error_msg+=msg
        write_to_log(msg)




# save the json as human readable
try:
    output_fname = "output/%s.json" % (session_code)
    try: os.makedirs( os.path.dirname(output_fname) )
    except: pass
    with open(output_fname, 'w') as outfile:
        json.dump(data, outfile, indent=2)
except Exception as e:
    msg = "Error writing json! %s" % e
    print (msg)
    error_msg+=msg
    write_to_log(msg)



# convert the epoch MS to epoch seconds 
epoch = data["epoch_start"] / 1000
#print (epoch)


dt = datetime.datetime.fromtimestamp(epoch)

if debug_plate: dt=datetime.datetime.now()

date_human = dt.strftime('%Y-%m-%d %-I:%M %p').lower()
date_human2 = dt.strftime('%-I:%M%p on %-m/%-d').lower()
print (date_human2)

camera_name = data["web_server_config"]["camera_label"]

# figure out the direction. This will be different for each camera!
direction = int(data["travel_direction"])

if camera_name=="camera1":
    print "Evaluating direction of camera %s" % camera_name
    if direction > 270 or direction < 90: direction_str = "enter"
    else: direction_str = "exit"
else:
    print "Evaluating direction (2) of camera %s" % camera_name
    if direction < 180: direction_str = "enter"
    else: direction_str = "exit"
    
print ("direction_str=%s" % direction_str)


best_plate_number = data["best_plate_number"]
if debug_plate: best_plate_number=debug_plate


write_to_log("\n%s %s:" % (best_plate_number, timestamp()) )


best_plate_confidence = round(data["best_plate"]["confidence"], 0) # converting from float
best_region = data["best_region"]
best_region = best_region.lstrip("us-") # get rid of the "us-ca"
best_region_confidence = round(data["best_region_confidence"], 0)

print ("Plate: %s" % best_plate_number)

try:
    plate1 = data["candidates"][0]["plate"]
    plate1_confidence = round(data["candidates"][0]["confidence"], 0)
except Exception as e:
    plate1 = "none"
    plate1_confidence=0

try:
    plate2 = data["candidates"][1]["plate"]
    plate2_confidence = round(data["candidates"][1]["confidence"], 0)
except Exception as e:
    plate2 = "none"
    plate2_confidence=0

try:
    plate3 = data["candidates"][2]["plate"]
    plate3_confidence = round(data["candidates"][2]["confidence"], 0)
except Exception as e:
    plate3 = "none"
    plate3_confidence=0

try:
    plate4 = data["candidates"][3]["plate"]
    plate4_confidence = round(data["candidates"][3]["confidence"], 0)
except Exception as e:
    plate4 = "none"
    plate4_confidence=0



# for the vehicle data, just use the top guess. It gives a few guesses though.
try:
    vehicle_make = data["vehicle"]["make"][0]["name"]
    vehicle_model = data["vehicle"]["make_model"][0]["name"]
    vehicle_color = data["vehicle"]["color"][0]["name"]
    vehicle_body = data["vehicle"]["body_type"][0]["name"]
    vehicle_year = data["vehicle"]["year"][0]["name"]
except Exception as e:
    print ("Error getting vehicle data! %s" % e)
    vehicle_make = "none"
    vehicle_model = "none"
    vehicle_color = "none"
    vehicle_body = "none"
    vehicle_year = "none"    

# make a string of the vehicle make, model, color, year, body type
#vehicle_summary = "%s / %s / %s / %s / %s" % (vehicle_make, vehicle_model, vehicle_color, vehicle_year, vehicle_body)
vehicle_summary = "%s / %s / %s / %s" % (vehicle_make, vehicle_model, vehicle_color, vehicle_year)
print (vehicle_summary)


# use the "best_uuid" as the uuid. Used for getting image, like this:
# http://10.10.10.27:8355/img/J498UOTDOQ4K5IQGVNJI01DBIMA3GKSGO1OI5XBA-161464352-1589994617471.jpg
uuid = data["best_uuid"]



#########################
# some sanity checking
#########################

# discard any plate starting with CF that isn't from CA, since those are usually bad reads from side of boats 
if best_plate_number.upper()[:2] == "CF" and best_plate_number.upper() != "CA":
    print ("I think this is a bad plate read since it starts with CF and is from out of state, discarding!")
    sys.exit()
   




    


# compose the SQL query
hostname="mysql.boofblog.com"
username="wrybread"
password="newyear"
database="alpr"

connection = pymysql.connect(host=hostname,
                             user=username,
                             password=password,
                             db=database,
                             cursorclass=pymysql.cursors.DictCursor # makes the results return a dict 
                             )

# connect to userspice db 
database2="userspice_stuff"
connection2 = pymysql.connect(host=hostname,
                             user=username,
                             password=password,
                             db=database2,
                             cursorclass=pymysql.cursors.DictCursor # makes the results return a dict 
                             )



try:
    cursor = connection.cursor()

    cursor2 = connection2.cursor() # the cursor of the userspace_stuff db    

    # Need to query the flags table to see if this is a known plate_alias
    query = "SELECT * FROM `flags` WHERE `plate_aliases` LIKE '%"+best_plate_number+"%'";
    cursor.execute(query)
    result = cursor.fetchone()
    try: corrected_plate=result["plate"]
    except: corrected_plate=None
    if corrected_plate:
        print "This is a known plate_alias for %s! Using that instead." % corrected_plate
        best_plate_number = corrected_plate

        




    
 
    # Need to query the flags DB to see if this is a known government or banned plate
    # keep these as 0 or 1 so the SQL insert statement works 
    is_government=0
    is_government_no_alert=0
    is_banned=0
    alert_recipients_usernames=""
    other_alert_recipients=""

    if direction_str == "enter": is_on_property=1
    else: is_on_property=0


    # check to see if the plate has the format of a ca exempt plate (eg 1340538 - all numbers and 7 digits and CA region) 
    if len(best_plate_number)==7 and best_plate_number.isdigit() and best_region=="ca": is_government=1


    # check for dupes? Query alpr table and see when the last entry for this plate was
    # I wonder if OpenALPR has a better built-in method? Their dashboard does a good job.
    lockout_period = 90
    query = "SELECT epoch FROM traffic WHERE plate LIKE '%s' AND hidden=0 ORDER BY epoch DESC LIMIT 1" % best_plate_number;
    cursor.execute(query)
    result = cursor.fetchone()
    try:
        last_activity_time = result["epoch"]
        seconds_since_last_activity = int(time.time() - last_activity_time)
        print seconds_since_last_activity
        if seconds_since_last_activity < lockout_period:
            print "It's a dupe! Skip it."
            os._exit(0)
            
    except Exception, e:
        #print "Error! %s" % e
        pass # prob no entry for this plate    


    
    
    # Create a new record in the traffic table
    query = "INSERT INTO traffic \
(epoch, date_human, date_human2, camera_name, vehicle_summary, direction, direction_str, plate1, plate1_confidence, plate2, plate2_confidence, plate3, plate3_confidence, plate4, plate4_confidence, best_region, best_region_confidence, plate, plate_confidence, uuid, is_government ) VALUES \
('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')" % \
(epoch, date_human, date_human2, camera_name, vehicle_summary, direction, direction_str, plate1, plate1_confidence, plate2, plate2_confidence, plate3, plate3_confidence, plate4, plate4_confidence, best_region, best_region_confidence, best_plate_number, best_plate_confidence, uuid, is_government)
    cursor.execute(query)

    #print query

    
    
    # check to see if there's an entry for this plate in the flags table
    query = "SELECT * FROM flags WHERE plate LIKE '%s' ORDER BY epoch" % best_plate_number;
    cursor.execute(query)
    flag_result = cursor.fetchone()
    
    if flag_result:
        # a record exists in the flags table, check to see if they have any relevant flags (banned, government)
        if flag_result["is_banned"]: is_banned=1
        else: is_banned=0
        if flag_result["is_government_no_alert"]: is_government_no_alert=1
        else: is_government_no_alert=0
        if flag_result["is_government"]: is_government=1
        else: is_government=0
        alert_recipients_usernames = flag_result["alert_recipients_usernames"]
        other_alert_recipients = flag_result["other_alert_recipients"]

        # update all the records now so we can track if he's on property (not updating govt here, so we can uncheck it from flags to not track it...)
        # Can probably remove best_region from this update statement, since in theory we get it when they first enter. Or maybe it's best to constantly update it?
        query = "UPDATE flags SET last_direction_str='%s', is_on_property='%s', uuid='%s', last_sighting='%s', best_region='%s' WHERE plate='%s'" % (direction_str, is_on_property, uuid, int(time.time()), best_region, best_plate_number)
        #print query
        cursor.execute(query)
        result = cursor.fetchone()
        
    else:
        # no record exists in flags table, create one 
        query = "INSERT INTO flags \
(plate, best_region, epoch, date_human, last_direction_str, is_on_property, uuid, is_government, last_sighting ) VALUES \
('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')" % \
(best_plate_number, best_region, epoch, date_human, direction_str, is_on_property, uuid, is_government, int(time.time()) )
        cursor.execute(query)
        result = cursor.fetchone()
    




    #%%%
    # Check the flags table to see if we already have an API confirmation for this plate (currently from autocheck)
    query = "SELECT * FROM `flags` WHERE `plate` LIKE '%"+best_plate_number+"%'";
    cursor.execute(query)
    result = cursor.fetchone()

    try:
        api_confirmed_plate=result["api_confirmed_plate"]
        api_confirmed_region=result["api_confirmed_region"]
        if api_confirmed_plate: print "We already have a confirmation of the region of this plate (%s)." % api_confirmed_region.upper()
    except: api_confirmed_plate=0

    # If we don't already have a confirmation from the API about this plate, look it up
    if not api_confirmed_plate:
        api_deets = api_lookup(best_plate_number, best_region)
        if api_deets["found"]:
            #print api_deets
            query = "UPDATE flags SET api_vehicle_summary1='%s', api_vehicle_summary2='%s', api_vehicle_summary3='%s', api_confirmed_region='%s', api_confirmed_plate=1 \
WHERE plate='%s'" % (api_deets["vehicle_summary1"], api_deets["vehicle_summary2"], api_deets["vehicle_summary3"], api_deets["confirmed_region"], best_plate_number)        
        else:
            # set api_confirmed_plate=-1 so we know we tried looking it up but didn't find anything
            query = "UPDATE flags SET api_confirmed_plate=-1 WHERE plate='%s'" % (best_plate_number)  

        cursor.execute(query)



    # make an entry about how many times this vehicle has entered and exited? (used when generating reports)
    # count number of times we've seen the plate
    query = "SELECT epoch FROM traffic WHERE plate LIKE '%s' AND hidden=0 ORDER BY epoch DESC" % best_plate_number;
    cursor.execute(query)
    result = cursor.fetchall()
    total_sightings = len(result)

    query = "SELECT epoch FROM traffic WHERE plate LIKE '%s' AND hidden=0 AND direction_str='enter' ORDER BY epoch DESC" % best_plate_number;
    cursor.execute(query)
    result = cursor.fetchall()
    total_entries = len(result)

    query = "SELECT epoch FROM traffic WHERE plate LIKE '%s' AND hidden=0 AND direction_str='exit' ORDER BY epoch DESC" % best_plate_number;
    cursor.execute(query)
    result = cursor.fetchall()
    total_exits = len(result)

    # update flags table with the tallies
    query = "UPDATE flags SET total_entries='%s', total_exits='%s', total_sightings='%s' \
WHERE plate='%s'" % (total_entries, total_exits, total_sightings, best_plate_number)        
    cursor.execute(query)




    ###################
    # send any alerts?
    ###################

    send_alerts_to=[]
    usernames_to_receive=[]
    wait_for_image = True

    if is_banned:
        # get all the usernames from userspice_db users table that are marked as receivesbannedalerts
        #query = "SELECT username, cellphone, email, display_name FROM alpr_users WHERE is_active=1 AND member_banned_group=1"
        query = "SELECT * FROM users WHERE is_active=1 AND receivesbannedalerts=1"
        cursor2.execute(query)
        result = cursor2.fetchall()
        for row in result:
            email = row["email"]
            cellphone = row["cellphone"]
            if email and email not in send_alerts_to: send_alerts_to.append(email)
            if cellphone and cellphone not in send_alerts_to: send_alerts_to.append(cellphone)

    if is_government and not is_government_no_alert:
        # get all the usernames that are included in receivesgovtalerts. If it's daylight make sure the value is at least 1, if it's night make sure it's 2
        #query = "SELECT username, cellphone, email, display_name FROM alpr_users WHERE is_active=1 AND member_government_group=1"

        # clumsy way to determine if it's day (between 6am and 8pm)
        hour = int(time.strftime("%H"))
        if hour > 6 and hour < 20: is_day=True
        else: is_day=False

        if is_day: query = "SELECT * FROM users WHERE is_active=1 AND receivesgovtalerts>0"
        else: query = "SELECT * FROM users WHERE is_active=1 AND receivesgovtalerts>1"
        
        cursor2.execute(query)
        result = cursor2.fetchall()
        for row in result:
            email = row["email"]
            cellphone = row["cellphone"]
            if email and email not in send_alerts_to: send_alerts_to.append(email)
            if cellphone and cellphone not in send_alerts_to: send_alerts_to.append(cellphone)
        
        
    # get a list of usernames from the alert_recipients_usernames field in the flags DB for this plate
    if alert_recipients_usernames:
        arr = alert_recipients_usernames.split(",")
        usernames_to_receive+=arr

    # go through each username and translate to cellphone or email from the users table in userspice_stuff db
    for username in usernames_to_receive:
        
        #query = "SELECT * FROM alpr_users WHERE username='%s' AND is_active=1" % username
        query = "SELECT * FROM users WHERE fname='%s' AND is_active=1" % username
        cursor2.execute(query)
        r = cursor2.fetchone()
        
        try: cellphone=r["cellphone"]
        except: cellphone=username # note that this isn't none... This way can put an SMS number in the alerts group (but not an email!).
        
        if cellphone and cellphone not in send_alerts_to: send_alerts_to.append(cellphone)
        try: email=r["email"]
        except: email=None
        if email and email not in send_alerts_to: send_alerts_to.append(email)


    # build a list of alert emails from other_alert_recipients text field (one per line)
    if other_alert_recipients:
        arr = other_alert_recipients.split("\r")
        for contact in arr:
            contact=contact.replace("\n", "")
            contact=contact.replace(",", "")
            contact=contact.replace(" ", "")
            if contact not in send_alerts_to: send_alerts_to.append(contact)
    

    friendly_recipients = [
        "415-305-2155",
        "209-327-1354", # ed parsons
        "415-250-9082", # jerry carter
        "415-342-4707", # tom carter
        "707-458-9755", # christian
        "707-953-7038", # willy
        "707-338-2240", # sarah
        "415-858-8150", # nick 
        "925-321-6881", # kris
        "415-209-3800", # jeff akers
        "707-338-1878", # doug
        "415-626-2006", # coco
        "415-706-8981", # ethan
        "415-505-7200", # razz
        "707-953-3294", # john hadley
        "707-779-9784", # dale
        "415-269-0765", # jim ericson
        "415-305-2155", # me
        "515-520-0787", # gueseppe
        ]

    try: custom_alert_message = flag_result["custom_alert_message"].strip()
    except: custom_alert_message = None

    # send an alert to each of the SMS's and emails in send_alerts_to array
    for addy in send_alerts_to:

        try: first_char = addy[0]
        except: first_char = ""
        if first_char == "#": continue # skipped commented out ones

        try: nickname=flag_result["nickname"]
        except: nickname=None

        if is_banned:
            subject = "Banned plate %s" % best_plate_number
            body = "The banned plate %s just %s the property!" % (best_plate_number, (direction_str+"ed"))
            if nickname: body += "\n\nThe name associated with this plate is %s" % nickname
        elif is_government:
            subject = "Government plate %s" % best_plate_number
            body = "The government plate %s just %s the property." % (best_plate_number, (direction_str+"ed"))
            if nickname: body += "\n\nThe name associated with this plate is %s" % nickname
            #if custom_alert_message: body += "\n\n%s" % custom_alert_message
            
        elif addy in friendly_recipients:
            
            if nickname:
                subject = "Flagged plate %s (%s)" % (best_plate_number, nickname)
                if direction_str=="enter": body = "%s is in the house!" % (nickname)
                else: body = "%s just left!" % (nickname)
            else:
                subject = "Flagged plate %s" % best_plate_number
                body = "The flagged plate %s just %s the property." % (best_plate_number, (direction_str+"ed"))
    
        else:
            if nickname:
                subject = "Flagged plate %s (%s)" % (best_plate_number, nickname)
                body = "%s just %s the property!\n\nLicense plate %s" % (nickname, (direction_str+"ed"), best_plate_number)
            else:
                subject = "Flagged plate %s" % best_plate_number
                body = "The flagged plate %s just %s the property." % (best_plate_number, (direction_str+"ed"))


        if custom_alert_message: body += "\n\n%s" % custom_alert_message

        if flag_result:
            #if flag_result["nickname"]: body += "\n\nThe name associated with this plate is %s" % flag_result["nickname"]
            #if flag_result["is_speeder"]: body += "\n\nSpeeder"
            #if flag_result["is_sasquatch"]: body += "\n\nSasquatch"
            #if flag_result["is_nice"]: body += "\n\nNice"
            #if flag_result["is_jerk"]: body += "\n\n\"Difficult\""
            #if flag_result["incident_reports"]: body += "\n\nIncident reports:%s" % flag_result["incident_reports"]
            pass





        body += "\n\nA picture will be here shortly:\n\nhttp://sinkingsensation.com/gatekeeper/plates/%s.jpg" % (uuid)

        body += "\n\n-The Lawsons Landing Gatekeeper"

        url = "http://sinkingsensation.com/gatekeeper/alert_sender.php?recipient=%s&subject=%s&body=%s&uuid=%s" % (urllib.quote(addy), urllib.quote(subject), urllib.quote(body), uuid)
        if not disable_alerts:
            print ("Alerting %s body %s" % (addy, body) )
            #print (url)
            print
            f = urllib.urlopen(url)
            response = f.read()
            #print(response)                
                        
    



    # connection is not autocommit by default. So you must commit to save
    # your changes.
    connection.commit()

    print ("Successfully entered to the db.")

except Exception, e:
    msg = "Error in end section! %s" % e
    write_to_log(msg)



finally:
    connection.close()

    


