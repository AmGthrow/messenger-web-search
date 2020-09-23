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
    if payload == 'get_started':
        take_thread_control(recipient_id)
        response = "Hey there, %s! Welcome to Seven Chunks ☺️👋" %profile.get('first_name')
        bot.send_text_message(recipient_id, response)

        typing(recipient_id)
        response = "You're currently talking to a chatbot, so the order process " + \
        "is mostly automated. However, you can also talk to a human whenever you like."
        bot.send_text_message(recipient_id, response)
         
        typing(recipient_id)
        response = "How may I help you today?"
        quick_replies = [{
            "content_type" : "text",
            "title" : "Order Now",
            "payload" : "order_now"
        },
        {
            "content_type" : "text",
            "title" : "Talk to Someone",
            "payload" : "talk_human"
        }]
        bot.send_quick_reply(recipient_id, response, quick_replies)
        return
    elif payload == 'main_menu':
        response = "Anything else I can do for you?"
        quick_replies = [{
            "content_type" : "text",
            "title" : "Order Now",
            "payload" : "order_now"
        },
        {
            "content_type" : "text",
            "title" : "Talk to Someone",
            "payload" : "talk_human"
        }]
        bot.send_quick_reply(recipient_id, response, quick_replies)
        return

    elif payload == 'order_now':
        take_thread_control(recipient_id)
        response = "Sure thing. What would you like?"
        quick_replies = [{
            "content_type" : "text",
            "title" : "Beef Bibimbap",
            "payload" : "beef_bibimbap"
        },
        {
            "content_type" : "text",
            "title" : "Beef Gyudon",
            "payload" : "beef_gyudon"
        }]
        bot.send_quick_reply(recipient_id, response, quick_replies)
        return

    elif payload == 'talk_human':
        response = "Sure thing 🙂 Someone's been notified and they'll will be with you shortly. Feel free to leave them a message!"
        bot.send_text_message(recipient_id, response)
        response = "If you want to continue talking to the bot again, press either \"Start Over\" or \"Place an Order\" from the menu buttons below."
        bot.send_text_message(recipient_id, response)
        response = requests.post(f"https://graph.facebook.com/v8.0/me/pass_thread_control",
        data=[
            ('recipient', "{'id':%s}"%recipient_id),
            ('target_app_id', "263902037430900"),
            ('access_token', ACCESS_TOKEN) 
        ])
        print(response.json())
        #TODO: message someone HAHAHAHA
        return
    else:
        response = "I don't have a protocol for that postback {%s} yet"%payload
        bot.send_text_message(recipient_id, response)


def handle_quick_reply(recipient_id, message, profile):
    payload = message['quick_reply'].get('payload')
    if payload == 'order_now':
        handle_postback(recipient_id,{'payload':'order_now'},profile)

    elif payload in MENU_ITEMS:
        users[recipient_id].add_order(message.get('text'))
        response = f"Your current order is:\n{users[recipient_id].get_order()}"
        bot.send_text_message(recipient_id, response)
        response = "Anything else?"
        quick_replies = [{
            "content_type" : "text",
            "title" : "Beef Bibimbap",
            "payload" : "beef_bibimbap"
        },
        {
            "content_type" : "text",
            "title" : "Beef Gyudon",
            "payload" : "beef_gyudon"
        },
        {
            "content_type" : "text",
            "title" : "Place Order",
            "payload" : "place_order"
        }        ]
        bot.send_quick_reply(recipient_id, response, quick_replies)

    elif payload == 'place_order':
        bot.send_text_message(recipient_id, "Great! You just placed an order.")
        bot.send_text_message(recipient_id, "This is as far as the bot goes right now, I still need to collect your contact details (I haven't implemented that yet).")
        users[recipient_id].clear_order()
        handle_postback(recipient_id,{'payload':'main_menu'},profile)
        #TODO: Continue processing the order

    elif payload == 'talk_human':
        handle_postback(recipient_id, {'payload':'talk_human'}, 'profile')


    else:
        response = f"You just sent me the quick reply: {payload}"
        bot.send_text_message(recipient_id, response)


def handle_message(recipient_id, message, profile):
    if message.get('text'):
        # if the user sent a message containing text
        response = f"I'm sorry, I don't recognize the command \"{message.get('text')}\"."
        bot.send_text_message(recipient_id, response)
        typing(recipient_id)
        response = "You're talking to a chatbot right now, but you can talk to someone from " + \
                   "our team at any time by pressing the \"Talk to Someone\" button."
        bot.send_text_message(recipient_id, response)
        handle_postback(recipient_id, {'payload':'main_menu'}, 'profile')

    if message.get('attachments'):
        # if the user sent a message containing an attachment
        response = "Thanks for sending this! Someone from our team will come and review it."
        handle_postback(recipient_id, {'payload':'main_menu'}, 'profile')


def typing(recipient_id, wait=0.5, type=1.5):
        time.sleep(wait)
        bot.send_action(recipient_id, 'typing_on')
        time.sleep(type)
        bot.send_action(recipient_id, 'typing_off')


class Customer():
    menu = {
        "Beef Bibimbap" : 200,
        "Beef Gyudon" : 150
    }
    def __init__(self, psid):
        self.psid = psid
        self.orders = {}

    def add_order(self, order):
        try:
            self.orders[order] += 1
        except KeyError:
            self.orders[order] = 1

    def get_order(self):
        order_summary = []
        for (order, num_order) in self.orders.items():
            if num_order != 0:
                order_summary.append(f'{num_order}x {order}')
        return('\n'.join(order_summary))
    
    def clear_order(self):
        self.orders = {}

    def set_address(self, address):
        self.address = address

    def get_address(self):
        return self.address

    def get_total(self):
        return sum([menu[order] * num_order for (order, num_order) in self.orders.items()])


def take_thread_control(recipient_id):
    res = requests.post(f"https://graph.facebook.com/v2.6/me/take_thread_control?access_token={ACCESS_TOKEN}",
    data = [('recipient', "{'id':%s}"%recipient_id)])


if __name__ == '__main__':
    app.run()

