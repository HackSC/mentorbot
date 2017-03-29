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
channels["mentor"] = "#developers"

# List of all mentors
mentors = []

# List of active mentors
activeMentors = []

# List of busy mentors
busyMentors = []

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

@post('/addmentor')
def addMentor():
    """
    """
    mentor = request.forms.get("text")
    mentors.append(mentor);
    sc.api_call(
        "channels.invite",
        channel=channels["mentor"],
        user=mentor
    )
    users = sc.api_call("users.list")
    pp.pprint(users)
    for user in users.members:
        usernames.append(user.name)
    print (usernames)
    print("Adding " + mentor + " to list of mentors.")
    print(mentors)

@post('/setmentorchannel')
def setMentorChannel():
    """
    """
    mentorChannel = request.forms.get("text")
    user_id = request.forms.get("user_id")
    channel_id = request.forms.get("channel_id")
    channels = sc.api_call(channels.list)
    if mentorChannel not in channels:
        sendTextMessage(channel_id, "The channel *" + mentorChannel + "* does not exist!")
    else:
        channels["mentor"] = "#" + mentorChannel
        sendTextMessage(channel_id, "Mentor channel successfully set to *" + mentorChannel + "*!")

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
                "text":"If you feel like you're the right person to take this person's issue, press the button below and we'll setup a chatroom between you two.",
                "fallback":"You are unable to choose an option",
                "callback_id":"mentor_confirm",
                "color":"#3AA3E3",
                "attachment_type":"default",
                "actions":[
                    {
                        "name":"mentor confirm",
                        "text":"Take this job!",
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
    port = int(os.environ.get("PORT", 5000))
    run(host='0.0.0.0', port=port)
