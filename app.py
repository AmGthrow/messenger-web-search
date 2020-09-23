import json
import time
import random
import requests
from flask import Flask, request
from pymessenger.bot import Bot

config_file = open('config.json')
config_values = json.load(config_file)
config_file.close()

app = Flask(__name__)
APP_ID = 346924202972294
ACCESS_TOKEN = config_values["Facebook"]["ACCESS_TOKEN"]
VERIFY_TOKEN = config_values["Facebook"]["VERIFY_TOKEN"]
bot = Bot(ACCESS_TOKEN)

users = {}
MENU_ITEMS = ['beef_bibimbap', 'beef_gyudon']

# Receive requests from Facebook
@app.route('/', methods=['GET', 'POST'])
def receive_message():
    if request.method == "GET":
        # Make sure that the GET request we receive is actually from Facebook, not some third party
        token_sent = request.args.get("hub.verify_token")
        return verify_fb_token(token_sent)

    # If it's not a GET, Facebook is probably giving us a POST of a message someone sent us
    elif request.method == "POST":
        # retrieve the sent message
        output = request.get_json()
        for event in output['entry']:
            messaging = event['messaging']
            for message in messaging:
                # Get the sender's Messenger ID
                recipient_id = message['sender']['id']
                profile = requests.get(
                    f'https://graph.facebook.com/{recipient_id}?fields=first_name,last_name,profile_pic&access_token={ACCESS_TOKEN}'
                ).json()
                if recipient_id not in users:
                    users[recipient_id] = Customer(recipient_id)
                if message.get('postback'):
                    handle_postback(recipient_id, message.get('postback'), profile)
                elif message.get('message'):
                    if message['message'].get('quick_reply'):
                        handle_quick_reply(recipient_id, message.get('message'), profile)
                    else:
                        handle_message(recipient_id, message.get('message'), profile)

        return "Message Processed"


def verify_fb_token(token_sent):
    #take token sent by facebook and verify it matches the verify token you sent
    #if they match, allow the request, else return an error
    if token_sent == VERIFY_TOKEN:
        return request.args.get("hub.challenge")
    return 'Invalid verification token'


def handle_postback(recipient_id, message, profile):
    payload = message.get('payload')
    bot.send_action(recipient_id, 'mark_seen')

    response = "I don't have a protocol for that postback {%s} yet"%payload
    bot.send_text_message(recipient_id, response)


def handle_quick_reply(recipient_id, message, profile):
    payload = message['quick_reply'].get('payload')

    response = "I don't have a protocol for that quick reply {%s} yet"%payload
    bot.send_text_message(recipient_id, response)


def handle_message(recipient_id, message, profile):
    if message.get('text'):
        # if the user sent a message containing text
        response = "I'll try running a google search."
        bot.send_text_message(recipient_id, response)

    elif message.get('attachments'):
        # if the user sent a message containing an attachment
        response = "Sorry, I can't process images and attachments yet."
        bot.send_text_message(recipient_id, response)


def typing(recipient_id, wait=0.5, type=1.5):
        time.sleep(wait)
        bot.send_action(recipient_id, 'typing_on')
        time.sleep(type)
        bot.send_action(recipient_id, 'typing_off')


def take_thread_control(recipient_id):
    res = requests.post(f"https://graph.facebook.com/v2.6/me/take_thread_control?access_token={ACCESS_TOKEN}",
    data = [('recipient', "{'id':%s}"%recipient_id)])


if __name__ == '__main__':
    app.run()

