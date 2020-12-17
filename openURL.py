import requests
from bs4 import BeautifulSoup
import re

def get_text_from_url(url):
    res = requests.get(url)
    soup = BeautifulSoup(res.text, "html.parser")
    text = soup.text
    textRegex = re.compile("(\n)+")
    return ''.join(textRegex.split(text))

def list_of_strings_from_soup(text):
    n = 2000
    return [text[i:i+n] for i in range(0, len(text), n)]

def compose_message(url):
    
    if len(responses := list_of_strings_from_soup(get_text_from_url(url))) > 5:
        responses = responses[:5] + ["Whoops! Sorry, your webpage is too long for me to send the rest."]
    return (responses)