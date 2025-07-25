import http.client
import json
import re
from urllib.parse import quote
import html
import time

DISP_CAT_ID = 34
SNIPE_HOST = "it-inventory"

#DISP_CAT_ID = 5
#SNIPE_HOST = "it-inventory-test"

def open_snipe_connection():
   try: 
       return http.client.HTTPSConnection(f"{SNIPE_HOST}.ischool.uw.edu", port=443)

   except (http.client.HTTPException, ConnectionError) as http_err:
      print(f"HTTP connection/request error: {http_err}")


def get_snipe_access_token():
   with open(f"{SNIPE_HOST}.access-token","r") as file:
     return file.readline().rstrip()


def get_snipe_manufacturers():

   global snipe_connection
   global snipe_access_token

   snipe_api_url = quote(f"/api/v1/manufacturers", safe=":/?=")

   headers = {
      "accept": "application/json",
      "Content-Type": "application/json",
      "Authorization": f"Bearer {snipe_access_token}"
   }

   snipe_connection.request(method="GET", url=snipe_api_url, headers=headers)
   response = snipe_connection.getresponse()

   raw_data = response.read()
   data = json.loads(raw_data)
   formatted_data = json.dumps(data, indent=4)
   
   manufacturer = {}

   for row in data['rows']:
      manufacturer[row['name']] = row['id'] 

   return manufacturer

def get_snipe_models(category_id, name = False):

   global snipe_connection
   global snipe_access_token

   there_is_more = True
   offset = 0

   models = {}

   while True:
     

      endpoint =  f"/api/v1/models?limit=50&offset={offset}"
      if name:
         endpoint = endpoint + f"&search={name}"

      if category_id:
         endpoint = endpoint + f"&category_id={category_id}"

      snipe_api_url = quote(endpoint, safe=":/?=&")
      #print(snipe_api_url)

      headers = {
         "accept": "application/json",
         "Content-Type": "application/json",
         "Authorization": f"Bearer {snipe_access_token}"
      }

      snipe_connection.request(method="GET", url=snipe_api_url, headers=headers)
      response = snipe_connection.getresponse()

      raw_data = response.read()
      data = json.loads(raw_data)
      formatted_data = json.dumps(data, indent=4)
      #print(formatted_data)
     
      if not data['rows']:
          return models

      for row in data['rows']:
         model_name = html.unescape(row['name'])

         if 'manufacturer' in row and row['manufacturer']:
            manf_name = html.unescape(row['manufacturer']['name'])
         else:
            manf_name = "N/A"
         

         #print(f"{manf_name} {model_name}" )
         models[row['model_number']] = (row['id'] , f"{manf_name} {model_name}" )
  
      offset += len(data['rows'])
      time.sleep(0.4999)
	 
      if (offset >= data['total'] ):
         return models


def get_snipe_status_id(name):
   global snipe_connection
   global snipe_access_token

   endpoint = f"/api/v1/statuslabels?name={name}"
   snipe_api_url = quote(endpoint, safe=":/?=&")

   headers = {
      "accept": "application/json",
      "Content-Type": "application/json",
      "Authorization": f"Bearer {snipe_access_token}"
   }

   snipe_connection.request(method="GET", url=snipe_api_url, headers=headers)
   response = snipe_connection.getresponse()

   raw_data = response.read()
   data = json.loads(raw_data)
   formatted_data = json.dumps(data, indent=4)

   if not 'total' in data:
      print(f"Someting went wrong: name={name}")
      print(f"endpoint: {snipe_api_url}")
      print(f"result: {formatted_data}")
      return False
   
   elif int(data['total']) == 0:
      print(f"Unable to find status in Snipe: name={name}")
      return False
   elif int(data['total']) > 1:
      print(f"Unable to find unique status in Snipe: name={name} got {data['total']} rows!")
      return False
   else:
      return data['rows'][0]['id']
   

def get_snipe_assets():

   global snipe_connection
   global snipe_access_token

   there_is_more = True
   offset = 0

   assets = {}

   while True:
      
      snipe_api_url = quote(f"/api/v1/hardware?limit=50&offset={offset}", safe=":/?=&")
      print(snipe_api_url)

      headers = {
         "accept": "application/json",
         "Content-Type": "application/json",
         "Authorization": f"Bearer {snipe_access_token}"
      }

      snipe_connection.request(method="GET", url=snipe_api_url, headers=headers)
      response = snipe_connection.getresponse()

      raw_data = response.read()
      data = json.loads(raw_data)
      formatted_data = json.dumps(data, indent=4)
     
      if not data['rows']:
          return assets

      for row in data['rows']:

         #if not '_snipeit_sassafras_id_5' in row :
         if not 'serial' in row :
            continue

         #print(f"{row['serial']} = {row['asset_tag']}")
         assets[row['serial']] = row['asset_tag']
  
      offset += len(data['rows'])
	 
      if (offset >= data['total'] ):
         return assets

def get_snipe_users():

   global snipe_connection
   global snipe_access_token

   there_is_more = True
   offset = 0

   users = {}

   while True:
      
      snipe_api_url = quote(f"/api/v1/users?limit=50&offset={offset}", safe=":/?=&")
      print(snipe_api_url)

      headers = {
         "accept": "application/json",
         "Content-Type": "application/json",
         "Authorization": f"Bearer {snipe_access_token}"
      }

      snipe_connection.request(method="GET", url=snipe_api_url, headers=headers)
      response = snipe_connection.getresponse()

      raw_data = response.read()
      data = json.loads(raw_data)
      formatted_data = json.dumps(data, indent=4)
     
      if not data['rows']:
          return users

      for row in data['rows']:

         #print(f"{manf_name} {model_name}" )
         users[row['username']] = row['id']
  
      offset += len(data['rows'])
	 
      if (offset >= data['total'] ):
         return users




def load_snipe_manufacturer(manufacturer):

   global snipe_connection
   global snipe_access_token

   # m = sanitize_manufacturer(manufacturer)

   snipe_api_url = quote(f"/api/v1/manufacturers?name={manufacturer}", safe=":/?=")

   headers = {
      "accept": "application/json",
      "Content-Type": "application/json",
      "Authorization": f"Bearer {snipe_access_token}"
   }

   snipe_connection.request(method="GET", url=snipe_api_url, headers=headers)
   response = snipe_connection.getresponse()

   raw_data = response.read()
   data = json.loads(raw_data)
   formatted_data = json.dumps(data, indent=4)
   #print(formatted_data)
   rows = data['total']

      
   if (rows == 0):
      print(f"Loading manufacturer into SnipeIT - {manufacturer}")

      payload = json.dumps({ 'name': f"{manufacturer}" } )
  
      snipe_connection.request(method="POST", url=snipe_api_url, body=payload, headers=headers)
      snipe_response = snipe_connection.getresponse()

      ## print(payload)

      snipe_raw_data = snipe_response.read()
      #print(repr(snipe_raw_data))
   else:
       print(f"{manufacturer} Known in SnipeIT")


def load_snipe_model(manufacturer_id, category_id, make, model_number, model_name):

   global snipe_connection
   global snipe_access_token

   snipe_api_url = quote(f"/api/v1/models?model_number={model_number}", safe=":/?=")
   print(snipe_api_url)

   headers = {
      "accept": "application/json",
      "Content-Type": "application/json",
      "Authorization": f"Bearer {snipe_access_token}"
   }

   snipe_connection.request(method="GET", url=snipe_api_url, headers=headers)
   response = snipe_connection.getresponse()

   raw_data = response.read()
   data = json.loads(raw_data)
   formatted_data = json.dumps(data, indent=4)
   #print(formatted_data)

   if 'total' in data:
      rows = data['total']
      if (rows == 0):

          print(f"Loading {make} - {model_number}:-{model_name} into SnipeIT")
          payload = json.dumps({ 'name': model_name, 'category_id': category_id, 'manufacturer_id': manufacturer_id, 'model_number': model_number  } )

          snipe_connection.request(method="POST", url=snipe_api_url, body=payload, headers=headers)
          snipe_response = snipe_connection.getresponse()

          print(payload)
   
          snipe_raw_data = snipe_response.read()
          #print(repr(snipe_raw_data))
      else:
          print(f"{make} - {model_number}:{model_name} Known in SnipeIT")
          #payload = json.dumps({ 'name': f"{manufacturer}" } )
   else:
       print("Houston we got this back\n"+formatted_data)


def load_snipe_asset(asset_tag, status_id, serial, name, model_id, note):

   global snipe_connection
   global snipe_access_token

   if not status_id:
      status_id = get_snipe_status_id('Ready to Deploy')

   if not status_id:
      raise "Unabele to get status id from Snipe"

   snipe_api_url = quote(f"/api/v1/hardware/byserial/{serial}", safe=":/?=")
   print(snipe_api_url)

   headers = {
      "accept": "application/json",
      "Content-Type": "application/json",
      "Authorization": f"Bearer {snipe_access_token}"
   }

   snipe_connection.request(method="GET", url=snipe_api_url, headers=headers)
   response = snipe_connection.getresponse()

   raw_data = response.read()
   data = json.loads(raw_data)
   formatted_data = json.dumps(data, indent=4)
   #print(formatted_data)

   if 'messages' in data: 
      if re.match( 'Asset does not exist', data['messages'] ):

         snipe_api_url = quote(f"/api/v1/hardware", safe=":/?=")

    
         print(f"Loading Asset {name} - {asset_tag}-{serial} into SnipeIT")
         
         payload = json.dumps({ 
            'name': name, 
            'asset_tag': asset_tag, 
            'status_id': status_id, 
            'model_id':model_id, 
            'serial':serial ,
            'notes': note } )

         snipe_connection.request(method="POST", url=snipe_api_url, body=payload, headers=headers)
         snipe_response = snipe_connection.getresponse()

         #print(payload)
  
         snipe_raw_data = snipe_response.read()
         return_code = snipe_response.getcode()
         data = json.loads(snipe_raw_data)
	
         print(f"Return Code:{return_code}" + repr(snipe_raw_data))
         return data['payload']['id']	

      else:
         print("Houston - expecting 'Asset does not exist.' We got this back in data['message']:"+data['messages'])
         return False
   else:
      print(f"Asset {name} - SN:{serial} SassafrasID:{asset_tag} Known in SnipeIT") 
      return False




def replace_snipe_asset_tag(old_asset_tag, new_asset_tag):

   global snipe_connection
   global snipe_access_token

   snipe_api_url = quote(f"/api/v1/hardware/bytag/{old_asset_tag}", safe=":/?=")
   print(snipe_api_url)

   headers = {
      "accept": "application/json",
      "Content-Type": "application/json",
      "Authorization": f"Bearer {snipe_access_token}"
   }

   snipe_connection.request(method="GET", url=snipe_api_url, headers=headers)
   response = snipe_connection.getresponse()

   raw_data = response.read()
   data = json.loads(raw_data)
   formatted_data = json.dumps(data, indent=4)
   #print(formatted_data)

   if 'id' in data: 

      id = data['id']
      snipe_api_url = quote(f"/api/v1/hardware/{id}", safe=":/?=")

      payload = json.dumps({ 'asset_tag': new_asset_tag } )
    
      print(f"Replacing Asset tag {old_asset_tag}-{new_asset_tag} into SnipeIT")

      snipe_connection.request(method="PUT", url=snipe_api_url, body=payload, headers=headers)
      snipe_response = snipe_connection.getresponse()

      print(snipe_api_url)
      print(payload)
      snipe_raw_data = snipe_response.read()
      return_code = snipe_response.getcode()
      data = json.loads(snipe_raw_data)
      formatted_data = json.dumps(data, indent=4)

      if 'status' in data and data['status'] == 'success' :
         #print(f"Return Code:{return_code}" + repr(snipe_raw_data))
         return data['payload']['id']	
      else:
         print(f"Snipe update asset_tag  - error: {formatted_data} ")
         return False

   else:
      print(formatted_data)
      raise Exception(f"Snipe find by asset_tag error: Asset not found - {old_asset_tag}")
      return False



def checkout_asset_to(asset_id, checkout_to_type, checkout_to_id):

   global snipe_connection
   global snipe_access_token

   if not re.match( r"{user|location|asset}", checkout_to_type ):
      error_message = f"checkout_asset_to type must be user|location|asset - given type is >{checkout_to_type}<"
      raise(error_message)

   snipe_api_url = quote(f"/api/v1/hardware/{asset_id}/checkout", safe=":/?=")
   print(snipe_api_url)

   headers = {
      "accept": "application/json",
      "Content-Type": "application/json",
      "Authorization": f"Bearer {snipe_access_token}"
   }

   payload_dict = { 'checkout_to_type': checkout_to_type }

   if checkout_to_type == "user":
      payload_dict['assigned_user']= checkout_to_id 
   elif checkout_to_type == "location": 
      payload_dict['assigned_location']= checkout_to_id 
   elif checkout_to_type == "asset": 
      payload_dict['assigned_asset']= checkout_to_id 
   else:
      error_message = f"checkout_asset_to type must be user|location|asset - given type is >{checkout_to_type}<"
      raise(error_message)

   payload = json.dumps(payload_dict)
   formatted_data = json.dumps(payload_dict, indent=4)

   print(formatted_data)

   snipe_connection.request(method="POST", url=snipe_api_url, body=payload, headers=headers)
   snipe_response = snipe_connection.getresponse()

   #print(payload)

   snipe_raw_data = snipe_response.read()
   return_code = snipe_response.getcode()
   data = json.loads(snipe_raw_data)
        
   print(f"Return Code:{return_code}" + repr(snipe_raw_data))


snipe_connection = open_snipe_connection()
snipe_access_token = get_snipe_access_token()

