import requests
from bs4 import BeautifulSoup
import re

# Gets the raw text from the html file of the url
def get_text_from_url(url):
    try:
        res = requests.get(url)
    except:
        raise Exception('Not a URL')
    soup = BeautifulSoup(res.text, "html.parser")
    text = soup.text
    textRegex = re.compile("(\n)+")
    return ''.join(textRegex.split(text))

# I can't just send the text in one big string, so I partition them into slices to send to FB
def list_of_strings_from_soup(text):
    n = 2000    # n is the length of each "chunk" of string
    return [text[i:i+n] for i in range(0, len(text), n)]

def compose_message(url):
    
    if len(responses := list_of_strings_from_soup(get_text_from_url(url))) > 5:
        responses = responses[:5] + ["Whoops! Sorry, your webpage is too long for me to send the rest."]
    return (responses)