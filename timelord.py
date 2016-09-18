import os
from slackclient import SlackClient

import time
from datetime import datetime
from pytz import timezone

import random

# Timelord's details.
BOT_NAME = "timelord"
BOT_ID = os.environ.get("BOT_ID")

# Constants.
AT_BOT = "<@" + BOT_ID + ">"
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
#MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
ORDINAL_NUM = ["1st", "2nd", "3rd", "4th", "5th", "6th", "7th", "8th", "9th", "10th", "11th", "12th", "13th", "14th", "15th", "16th", "17th", "18th", "19th", "20th", "21st", "22nd", "23rd", "24th", "25th", "26th", "27th", "28th", "29th", "30th", "31st"]

# Instantiate Slack & Twilio clients.
slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))

# Load regions=>timezones map.
regionsToTimezonesMap = {}
f = open("regionsToTimezones.txt", "r")
for line in f:
    region, zone = line.rstrip().split(",")
    region = region.lower()
    regionsToTimezonesMap[region] = zone 
f.close()

# Capitalise region names.
def capitaliseRegionNames(region):
    regionName = region.split()
    doNotCapitalise = set(["of", "es"])
    for i in xrange(len(regionName)):		# for word in name
        if regionName[i] in doNotCapitalise:
             continue
        
        start = 0				# for letter in word
        element = regionName[i]
        if element[start] == "(":
             start = 1
        regionName[i] = element[:start] + element[start].upper() + element[start+1:]
    return " ".join(regionName)

# Given a command (action word, region), the function finds the datetime,
def getDateTime(command):
    command = command.rstrip().split()
    mode, region = command[0].lower(), " ".join(command[1:])
    region = region.lower()

    dt = None
    if region in regionsToTimezonesMap:
        zone = regionsToTimezonesMap[region]
        dt = datetime.now(timezone(zone))
        region = capitaliseRegionNames(region)

    response = ""
    if dt == None:
        response = "I'm sorry. I'm so sorry. Region is undefined."
    else:
        # Date and time variables.
        hour, minute = dt.hour, dt.minute
        day, month, year = dt.day, dt.month, dt.year
        calendarMonth, weekday, ordinalDay = MONTHS[month-1], DAYS[dt.weekday()], ORDINAL_NUM[day-1]

        # Process time.
        AMPM = "am"
        if hour >= 12:
            hour = hour%12
            AMPM = "pm"
        if hour == 0:
            hour = 12
        
        hour = str(hour)
        minute = str(minute)
        if len(minute) == 1:
            minute = "0" + minute
        
        #Time response: It is Monday, 2:12am in Sydney!
        #Date response: It is Monday, 29th October in Sydney!
        #DT response: It is Monday, 29th October (2:12am) in Sydney!
        time = str(hour) + ":" + str(minute) + AMPM
        date = weekday + ", " + ordinalDay + " " + calendarMonth
        if mode == "time":
            response = "It is " + weekday + ", " + time + " in " + region + "!"
        elif mode == "dt":
            response = "It is " + date + " (" + time + ") in " + region + "!"
        elif mode == "date":
            response = "It is " + date + " in " + region + "!"
    return response


"""
    Receives commands directed at the bot and determines if they
    are valid commands. If so, then acts on the commands. If not,
    returns back what it needs for clarification.
"""
def handle_command(command, channel):
    response = ""
    splitCommand = command.split()
    lowercaseCommand = command.lower()

    modes = set(["dt", "date", "time"])

    # Colloquial terms for Sydney and SF.
    sf = set(["sf", "sanfran", "san fran", "san francisco", "sanfrancisco", "america", "us"])
    syd = set(["syd", "sydney", "australia", "aus"]) 

    if splitCommand[0] == "help":
        response = "Current commands include:\n   @timelord {region}\n   @timelord time {region}\n   @timelord date {region}\n   @timelord dt {region}\n"
    elif splitCommand[0] in modes:
        region = " ".join(splitCommand[1:])
        if region in sf:
            command = splitCommand[0] + " san francisco"
        elif region in syd:
            command = splitCommand[0] + " sydney"
        response = getDateTime(command)
    elif lowercaseCommand in regionsToTimezonesMap or lowercaseCommand in syd or lowercaseCommand in sf:   #if command is a country
        if lowercaseCommand in regionsToTimezonesMap:
            command = "time " + command
        elif lowercaseCommand in syd:
            command = "time sydney"
        else:
            command = "time san francisco"
        response = getDateTime(command)
    else:
        catchphrases = ["Nonsense", "When I say run, run.", "Reverse the polarity of the neutron flow..", "Would you like a jelly baby?", "Sorry, I must dash!", "I wonder...", "Fine.", "Probably not the one you expected.", "No more!", "Fantastic!", "Allons-y!", "Geronimo!"]
        randomNumber = random.randint(0, len(catchphrases)-1)
        response = catchphrases[randomNumber]
    slack_client.api_call("chat.postMessage", channel=channel, text=response, as_user=True)


"""
    The Slack Real Time Messaging API is an events firehose.
    this parsing function returns None unless a message is
    directed at the Bot, based on its ID.
"""
def parse_slack_output(slack_rtm_output):
    output_list = slack_rtm_output
    if output_list and len(output_list) > 0:
        for output in output_list:
            if output and 'text' in output and AT_BOT in output['text']:
                # return text after the @ mention, whitespace removed
                return output['text'].split(AT_BOT)[1].strip().lower(), \
                       output['channel']
    return None, None


if __name__ == "__main__":
    READ_WEBSOCKET_DELAY = 1 # 1 second delay between reading from firehose
    if slack_client.rtm_connect():
        print("timelord connected and running!")
        while True:
            command, channel = parse_slack_output(slack_client.rtm_read())
            if command and channel:
                handle_command(command, channel)
            time.sleep(READ_WEBSOCKET_DELAY)
    else:
        print("Connection failed. Invalid Slack token or bot ID?")
