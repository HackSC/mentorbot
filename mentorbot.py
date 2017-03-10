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
    payload = json.loads(request.forms.get("payload"))
    print (type(payload))
    callback_id = payload["callback_id"]
    pp.pprint(payload)
    if callback_id == "mentor_confirm":
        mentee_id = payload["actions"][0]["value"]
        mentor_id = payload["user"]["id"]
        sendTextMessage(channels["mentor"], "got it. Your ID is " + mentee_id)
        sc.api_call(
            "mpim.open",
            users=mentee_id + "," + mentor_id
        )

@post('/test')
def test():
    return "<p>post received<p>"

@route('/hello')
def hello():
    return "<h1>Hello World!</h1>"

def sendTextMessage(channel, text):
    return sc.api_call(
        "chat.postMessage",
        channel=channel,
        text=text,
        as_user=True
    )

def sendMentorConfirm(channel, text, user_id):
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

if __name__ == "__main__":
    # activates and runs the server
    run(host='0.0.0.0', port=8080)
