from bottle import route, run, get, post, request
import os
import time
import json
import pprint
from slackclient import SlackClient

pp = pprint.PrettyPrinter(indent=1)

# starterbot's ID as an environment variable
BOT_ID = os.environ.get("BOT_ID")

# instantiate Slack client
sc = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))

# channels
channels = {}
channels["mentor"] = "#dev-mentor-slackbot"

@post('/mentor')
def mentor():
    """
    Usage: /mentor [category]
    Requests a mentor for a particular category.
    """
    category = request.forms.get("text")
    user = request.forms.get("user_name")
    user_id = request.forms.get("user_id")
    requestText = user + " is looking for a mentor for " + category + "! "
    sendMentorConfirm(channels["mentor"], requestText, user_id)

@post('/buttons')
def buttons():
    """
    Callback URL for interactive buttons.
    """
    payload = json.loads(request.forms.get("payload"))
    callback_id = payload["callback_id"]
    message_ts = payload["message_ts"]
    mentee_id = payload["actions"][0]["value"]
    mentor_id = payload["user"]["id"]
    mentor_name = payload["user"]["name"]
    if callback_id == "mentor_confirm":
        """
        Called when a mentor accepts a mentee's help request. Opens a
        multi-party message between the mentee, mentor, and the slackbot.
        Change mentor status to "checked-in" in the database if they have not
        done so yet.
        """
        new_im = (sc.api_call(
            "mpim.open",
            users=mentee_id + "," + mentor_id + "," + BOT_ID
        ))
        sendMentorFinish(new_im["group"]["name"], "Hey there! " + mentor_name + " will be able to help you.")
        sc.api_call(
            "chat.update",
            ts=message_ts,
            channel=payload["channel"]["id"],
            text="*Assigned* " + mentor_name + " to: " + payload["original_message"]["text"],
            as_user=True,
            attachments=[]
        )
    elif callback_id == "mentor_finish":
        """
        Change mentor status in database to "finished" and closes IM channel between mentor and mentee.
        """
        sc.api_call(
            "mpim.close",
            channel=payload["channel"]["id"]
        )
        sc.api_call(
            "chat.update",
            ts=message_ts,
            channel=payload["channel"]["id"],
            text="We hope we were able to help you! This thread is now closed.",
            as_user=True,
            attachments=[]
        )

def sendTextMessage(channel, text):
    """
    Sends text message to specific channel.
    """
    return sc.api_call(
        "chat.postMessage",
        channel=channel,
        text=text,
        as_user=True
    )

def sendMentorConfirm(channel, text, user_id):
    """
    Sends a one-button help request confirmation message to a channel.
    """
    return sc.api_call(
        "chat.postMessage",
        channel=channel,
        text=text,
        as_user=True,
        attachments=json.dumps(
        [
            {
                "text":"Choose an action",
                "fallback":"You are unable to choose an option",
                "callback_id":"mentor_confirm",
                "color":"#3AA3E3",
                "attachment_type":"default",
                "actions":[
                    {
                        "name":"mentor confirm",
                        "text":"Yay",
                        "type":"button",
                        "value":user_id
                    }
                ]
            }
        ])
    )

def sendMentorFinish(channel, text):
    """
    Sends a message with a "done" button allowing mentor/mentee to close the
    thread. Mentor status will now be set as "free" in database.
    """
    return sc.api_call(
        "chat.postMessage",
        channel=channel,
        text=text,
        as_user=True,
        attachments=json.dumps(
        [
            {
                "text":"When you guys are finished, feel free to click the button below.",
                "fallback":"You are unable to choose an option",
                "callback_id":"mentor_finish",
                "color":"#3AA3E3",
                "attachment_type":"default",
                "actions":[
                    {
                        "name":"mentor finish",
                        "text":"Done!",
                        "type":"button",
                        "value":True
                    }
                ]
            }
        ])
    )

if __name__ == "__main__":
    # activates and runs the server
    run(host='0.0.0.0', port=8080)
