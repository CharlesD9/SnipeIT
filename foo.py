import requests
import json
from snipe_funcs import open_snipe_connection, get_snipe_access_token



def snipe_add_note():
   snipe_api_url = "/api/v1/hardware/707?note=Test%20Note"
   snipe_api_url = "/api/v1/notes"

   headers = {
      "Authorization": f"Bearer {snipe_access_token}",
      "Content-Type": "application/json",
      "accept": "application/json"

   }

   payload = json.dumps({
      "type": "asset is a test" ,
      "id": "707",
      "note": "foobar"
   })

      
   snipe_connection.request(method="POST", url=snipe_api_url, body=payload, headers=headers)
   snipe_response = snipe_connection.getresponse()
      
   #print(payload)
      
   snipe_raw_data = snipe_response.read()
   return_code = snipe_response.getcode()

   data = json.loads(snipe_raw_data)
         


   if return_code == 200:
      print(f"Note updated successfully! {repr(snipe_raw_data)}")
   else:
      print(f"Error updating note:{return_code} {repr(snipe_raw_data)}")



snipe_connection = open_snipe_connection()
snipe_access_token = get_snipe_access_token()
snipe_add_note()

