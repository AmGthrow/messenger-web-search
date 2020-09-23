from googleapiclient.discovery import build   #Import the library
import json
import pprint

config_file = open('config.json')
config_values = json.load(config_file)
config_file.close()

api_key = config_values['Google']['API_KEY']
cse_id = config_values['Google']['CSE_ID']
def google_query(query, api_key, cse_id, **kwargs):
    query_service = build("customsearch", 
                          "v1", 
                          developerKey=api_key
                          )  
    query_results = query_service.cse().list(q=query,    # Query
                                             cx=cse_id,  # CSE ID
                                             **kwargs    
                                             ).execute()
    return query_results['items']
my_results_list = []
my_results = google_query("apple iphone news 2019",
                          api_key, 
                          cse_id, 
                          num = 10
                          )

for result in my_results:
    print('\n\n\n' + ('-'*40) + '\n' + result['title'] + f'\n({result["link"]})' + '\n\n' +  result['snippet'])