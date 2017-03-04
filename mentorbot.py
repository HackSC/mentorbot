# config
from slackclient import SlackClient

slack_token = os.environ["SLACK_API_TOKEN"]
sc = SlackClient(slack_token)


# some test functions -- learning and playing with python-slackclient
print(sc.api_call("channels.list"))

sc.api_call(
  "chat.postMessage",
  channel="#dev-mentor-slackbot",
  text="Hello from my python bot huehue --justin"
)
