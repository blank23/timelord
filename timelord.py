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
DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# Instantiate Slack & Twilio clients.
slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))

# Finds the time. Currently only records SF and Sydney.
def findTime(region):
    region = region.lower()
    sf = set(["sf", "sanfran", "san francisco", "sanfrancisco", "america", "us"])
    syd = set(["syd", "sydney", "australia", "aus"])

    response = ""
    dt = None
    area = None
    if region in sf:
        dt = datetime.now(timezone('US/Pacific-New'))
        area = "SF"
    elif region in syd:
        dt = datetime.now(timezone('Australia/Sydney'))
        area = "Sydney"

    if dt == None:
        response = "Region is not defined yet."
    else:
        # Date and time variables.
        hour, minute = dt.hour, dt.minute
        day, month, year = dt.day, dt.month, dt.year

        # Process time.
        AMPM = "am"
        if hour >= 12:
            hour = hour%12
            AMPM = "pm"
        if hour == 0:
            hour = 12

        response = "It is " + str(hour) + ":" + str(minute) + AMPM + " in " + area
    return response


"""
    Receives commands directed at the bot and determines if they
    are valid commands. If so, then acts on the commands. If not,
    returns back what it needs for clarification.
"""
def handle_command(command, channel):
    response = findTime(command)
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
