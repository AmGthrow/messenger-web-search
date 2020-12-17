import time
from datetime import datetime
import requests
import os
from dotenv import load_dotenv
from flask import Flask, request
from pymessenger.bot import Bot
import search
import openURL
import shelve
import logging

logging.basicConfig( format='%(name)s - %(levelname)s - %(message)s', level = logging.ERROR)
logger = logging.getLogger('app.py')
logger.setLevel(logging.INFO)
logger.addHandler(logging.FileHandler('messages.log'))
# filename='messages.log', filemode='w',

logger.info(f"{str(datetime.now())} - NEW INSTANCE OF app.py")
logger.info('-' * 40)

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

                with shelve.open('users') as db:
                    # log the time he sent a request
                    try:
                        timelog = db[recipient_id]
                        timelog.append(time.time())
                    except KeyError: # means that db[recipient_id] doesn't exist yet
                        db[recipient_id] = timelog = [time.time()]

                    if len(timelog) > 3:
                        if time.time() - timelog[0] < 30:
                            logger.warning(f"{datetime.now()} - WARN - {recipient_id} - WARNED FOR SPAM")
                            response = "Sorry! You've sent too many requests really quickly. Please wait %s more second/s."%(int((30 + timelog[0]) - time.time()) + 1)
                            timelog[1] += 15
                            bot.send_text_message(recipient_id, response)
                            return "Message ignored"  
                        timelog.pop(0)
                    db[recipient_id] = timelog

                if message.get('postback'):
                    handle_postback(recipient_id, message.get('postback'))
                elif message.get('message'):
                    if message['message'].get('quick_reply'):
                        handle_quick_reply(recipient_id, message.get('message'))
                    else:
                        handle_message(recipient_id, message.get('message'))

        return "Message Processed"


def verify_fb_token(token_sent):
    #take token sent by facebook and verify it matches the verify token you sent
    #if they match, allow the request, else return an error
    if token_sent == VERIFY_TOKEN:
        return request.args.get("hub.challenge")
    return 'Invalid verification token'


def handle_postback(recipient_id, message):
    payload = message.get('payload')

    if payload == 'get_started':
        response = "Hello there! Send me something to search, or give me a URL to try visiting."
        bot.send_text_message(recipient_id, response)
    else:
        response = "I don't know how to reply to that: %s"%payload
        bot.send_text_message(recipient_id, response)
    return


def handle_quick_reply(recipient_id, message):
    payload = message['quick_reply'].get('payload')

    response = "I don't know how to reply to that: %s"%payload
    bot.send_text_message(recipient_id, response)
    return


def handle_message(recipient_id, message):
    if message.get('text'):
        # if the user sent a message containing text
        # bot.send_text_message(recipient_id, f"Message received: {message.get('text')}")
        logger.info(f"{str(datetime.now())} - INFO - {recipient_id} - \"{message.get('text')}\"")
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
    if results is None:
        return["Sorry! I can only do a finite number of searches per day and I'm all out. You can still send me URLs though!"]
    if results == []:
        return["Couldn't find any results."]

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


if __name__ == '__main__':
    app.run()

