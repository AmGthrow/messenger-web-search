from googleapiclient.discovery import build   #Import the library
import json
import pprint

config_file = open('config.json')
config_values = json.load(config_file)
config_file.close()

api_key = config_values['Google']['API_KEY']
cse_id = config_values['Google']['CSE_ID']
def google_query(query, api_key=api_key, cse_id=cse_id, **kwargs):
    query_service = build("customsearch", 
                          "v1", 
                          developerKey=api_key
                          )  
    query_results = query_service.cse().list(q=query,    # Query
                                             cx=cse_id,  # CSE ID
                                             **kwargs    
                                             ).execute()
    return query_results['items']