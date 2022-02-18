"""
performs the google search using https://developers.google.com/docs/api/quickstart/python
"""


from googleapiclient.discovery import build   #Import the library
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")   # get an api key from https://developers.google.com/custom-search/v1/overview
cse_id = os.getenv("GOOGLE_CSE_ID")

def google_query(query, api_key=api_key, cse_id=cse_id, **kwargs):
    query_service = build("customsearch", 
                          "v1", 
                          developerKey=api_key
                          )  
    try:
        query_results = query_service.cse().list(q=query,    # Query
                                             cx=cse_id,  # CSE ID
                                             **kwargs    
                                             ).execute()
        output = query_results['items']
    except Exception as e:
        if type(e).__name__ == "HttpError": # run out of queries
            return None
        return []
    return output
