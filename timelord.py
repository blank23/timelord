import os
import time
from slackclient import SlackClient

from datetime import datetime
from pytz import timezone


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

# Finds the datetime. Currently only records SF and Sydney.
def getDateTime(command):
    command = command.split()
    mode = None
    modes = (["dt", "date", "time"])
    if len(command) == 1:
        mode = "time"
    elif len(command) == 2:
        mode, region = command

    mode = mode.lower()
    region = region.lower()

    # Colloquial terms for Sydney and SF.
    sf = set(["sf", "sanfran", "san francisco", "sanfrancisco", "america", "us"])
    syd = set(["syd", "sydney", "australia", "aus"])

    dt = None
    if region in sf:
        dt = datetime.now(timezone('US/Pacific-New'))
        region = "San Francisco"
    elif region in syd:
        dt = datetime.now(timezone('Australia/Sydney'))
        region = "Sydney"

    response = ""
    if dt == None:
        response = "Region is not defined yet."
    elif mode not in modes:
        response = "Mode does not exist. Check out '@timelord help'!"
    else:
        # Date and time variables.
        hour, minute = dt.hour, dt.minute
        day, month, year = dt.day, dt.month, dt.year

        ordinalDay = ORDINAL_NUM[day-1]
        calendarMonth, weekday = MONTHS[month-1], DAYS[dt.weekday()]

        # Process time.
        AMPM = "am"
        if hour >= 12:
            hour = hour%12
            AMPM = "pm"
        if hour == 0:
            hour = 12

        #Time response: It is 2:12am in Sydney
        #Date response: It is Monday, 29th October in Sydney
        #DT response: It is Monday, 29th October (2:12am) in Sydney
        time = str(hour) + ":" + str(minute) + AMPM
        date = weekday + ", " + ordinalDay + " " + month
        if mode == "time":
            response = "It is " + time + " in " + region
        elif mode == "dt":
            response = "It is " + date + " (" + time + ") in " + region
        elif mode == "date":
            response = "It is " + date + " in " + region
    return response


"""
    Receives commands directed at the bot and determines if they
    are valid commands. If so, then acts on the commands. If not,
    returns back what it needs for clarification.
"""
def handle_command(command, channel):
    response = ""
    if command == "help":
        response = "Current commands include:\n   {region}\n   time {region}\n   date {region}\n   dt {region}\n"
    response = getDateTime(command)
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
