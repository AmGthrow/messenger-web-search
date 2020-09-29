import time
import requests
import os
from dotenv import load_dotenv
from flask import Flask, request
from pymessenger.bot import Bot
import search
import openURL

load_dotenv()
APP_ID = os.getenv("APP_ID")
ACCESS_TOKEN = os.getenv("FB_ACCESS_TOKEN")
VERIFY_TOKEN = os.getenv("FB_VERIFY_TOKEN")

app = Flask(__name__)
bot = Bot(ACCESS_TOKEN)


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
        response = "Hey dude!"
        bot.send_text_message(recipient_id, response)
    else:
        response = "I don't know how to reply to that: %s"%payload
        bot.send_text_message(recipient_id, response)
    return


def handle_quick_reply(recipient_id, message, profile):
    payload = message['quick_reply'].get('payload')

    response = "I don't know how to reply to that: %s"%payload
    bot.send_text_message(recipient_id, response)
    return


def handle_message(recipient_id, message, profile):
    if message.get('text'):
        # if the user sent a message containing text
        bot.send_text_message(recipient_id, f"Message received: {message.get('text')}")
        try:
            responses = openURL.compose_message(message.get('text'))
            # responses = ["Opening URL"]
        except:
            responses = run_search(message.get('text'))
        for response in responses:
            bot.send_text_message(recipient_id, response)

    elif message.get('attachments'):
        # if the user sent a message containing an attachment
        response = "Sorry, I can't process images and attachments yet."
        bot.send_text_message(recipient_id, response)
    return


def run_search(message, num=10):
    '''
    runs a google search with the query <message> and retrieves the first <num> results

    Input: 
        message - a string containing the google search query
        num - the number of results to retrieve
    
    Output:
        an array of strings which are at most 2000 characters long each containing search results
    '''
    results = search.google_query(message, num=10)  
    for i in range(len(results)):   # Extracts relevant info from the search results so it's human-readable
        result = results[i]
        results[i] = ('\n\n' + ('-'*40) + '\n' + result['title'] + f'\n({result["link"]})' + '\n\n' +  result['snippet'])

    responses = []
    response = ''
    for result in results:
        if len(response + result) > 2000:   # facebook only lets me send 2000 chars at max 
            responses.append(response)
            response = ''
        response += result
    responses.append(response)  #The last one is guaranteed to be less than 2000 characters, so I append it to responses
    return responses


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

