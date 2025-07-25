#!/usr/bin/env python3
import pandas as pd
import numpy as np
import sys
import http.client
import json
import ssl
import getpass
import requests
from urllib.parse import quote


make = {}
model = {}

with open("it-inventory.access-token","r") as file:
    access_token = file.readline().rstrip()


# Useage <script> <list of sassafras export of computers with Manufacturer, LastStartup, Form Factor and AssetID

file = sys.argv[1]
df = pd.read_csv(file)
df = df.replace(np.nan, None, regex=True)

manufacturer_eq = {'Apple Computer, Inc.': 'Apple Inc.'}

print("Step 1. Lets load our Makes")
unique_make = df[['Manufacturer']].drop_duplicates()
for index, row in unique_make.iterrows():
   
   manufacturer =  row['Manufacturer']

   if not manufacturer:
      continue

   if manufacturer in manufacturer_eq:
       manufacturer = manufacturer_eq[manufacturer]

   #print(index, f"->{manufacturer}<--")

   # Does this manufacturere already exist. 
   snipe_headers = {
      "accept": "application/json",
      "Content-Type": "application/json",
      "Authorization": f"Bearer {access_token}"
   }

   #snipe_connection = http.client.HTTPSConnection('it-inventory.ischool.uw.edu', port=443, context=context)
   snipe_connection = http.client.HTTPSConnection('it-inventory.ischool.uw.edu', port=443)
   snipe_api_url = quote(f"/api/v1/manufacturers?name={manufacturer}", safe=":/?=")
   # print(snipe_api_url)
   snipe_connection.request(method="GET", url=snipe_api_url, headers=snipe_headers)
   response = snipe_connection.getresponse()

   raw_data = response.read()
   data = json.loads(raw_data)
   formatted_data = json.dumps(data, indent=4)
   #print(formatted_data)
   rows = data['total']

   if (rows == 0):

       print(f"Loading {manufacturer} into SnipeIT")
       payload = json.dumps({ 'name': f"{manufacturer}" } )

       snipe_connection.request(method="POST", url=snipe_api_url, body=payload, headers=snipe_headers)
       snipe_response = snipe_connection.getresponse()

       ## print(payload)

       snipe_raw_data = snipe_response.read()
       #print(repr(snipe_raw_data))
   else:
       print(f"{manufacturer} Known in SnipeIT")
       payload = json.dumps({ 'name': f"{manufacturer}" } )
   


print("\nStep 2 - Lets get a full list of Manufacgturers");
snipe_connection = http.client.HTTPSConnection('it-inventory.ischool.uw.edu', port=443)
snipe_api_url = quote(f"/api/v1/manufacturers", safe=":/?=")
# print(snipe_api_url)
snipe_connection.request(method="GET", url=snipe_api_url, headers=snipe_headers)

response = snipe_connection.getresponse()
raw_data = response.read()
data = json.loads(raw_data)
formatted_data = json.dumps(data, indent=4)
#print(formatted_data)

manufacturer_id = {}


for row in data['rows']:
   print (f"Manufacturer: {row['name']} = id:{row['id']}" )
   manufacturer_id[row['name']] = row['id'] 
    

print("\nStep 3 - Lets get a full list of Categories ");
snipe_connection = http.client.HTTPSConnection('it-inventory.ischool.uw.edu', port=443)
snipe_api_url = quote(f"/api/v1/categories", safe=":/?=")
# print(snipe_api_url)
snipe_connection.request(method="GET", url=snipe_api_url, headers=snipe_headers)

response = snipe_connection.getresponse()
raw_data = response.read()
data = json.loads(raw_data)
formatted_data = json.dumps(data, indent=4)

category_id = {}
#print(formatted_data)

for row in data['rows']:
   print (f"Category: {row['name']} = id:{row['id']}" )
   category_id[row['name']] = row['id'] 

category_mappings = {'Laptop': 'Laptop Computer', 'Standard': 'Desktop Computer', 'Virtual': 'Virtual Machine'}


print("\bStep 3. Lets load our Models")
unique_make_model = df[['Manufacturer', 'Model', 'FormFactor']].drop_duplicates()
for index, row in unique_make_model.iterrows():
   
   make = row['Manufacturer']
   model = row['Model']
   form_factor = row['FormFactor']

   if make in manufacturer_eq:
       make = manufacturer_eq[make]

   if form_factor in category_mappings:
      category = category_mappings[form_factor]
   else:
      print(f"Not able to map form factor:{form_factor} to Category - bailing on creating model for {make}:{model}")
      continue
 
   # Sanity check on Mianufacturer - should have been added above.
   if make in manufacturer_id:
       make_id = manufacturer_id[make]
   else:
     print(f"Not able to Find Manufacturer:{make} in manufacturer_id Dict - bailing on creating model for {make}:{model}")
     continue

   if category in category_id:
      cat_id = category_id[category]
   else:
     print(f"Not able to Find Category:{category} in category_id Dict - bailing on creating model for {make}:{model}")
     continue

   # Should have everything we need.. Lets see if this model is already present.

   # Does this manufacturere already exist. 
   snipe_headers = {
      "accept": "application/json",
      "Content-Type": "application/json",
      "Authorization": f"Bearer {access_token}"
   }

   #snipe_connection = http.client.HTTPSConnection('it-inventory.ischool.uw.edu', port=443, context=context)
   snipe_connection = http.client.HTTPSConnection('it-inventory.ischool.uw.edu', port=443)
   snipe_api_url = quote(f"/api/v1/models?name={model}&manufacturer_id={make_id}&category_id={cat_id}" , safe=":/?=&")
   print(snipe_api_url)
   snipe_connection.request(method="GET", url=snipe_api_url, headers=snipe_headers)
   response = snipe_connection.getresponse()

   raw_data = response.read()
   data = json.loads(raw_data)
   formatted_data = json.dumps(data, indent=4)
   #print(formatted_data)

   rows = data['total']

   if (rows == 0):
       print(f"Loading Model into SnipeIT:{make},{model},{category}")
       payload = json.dumps({ 'name': model, 'manufacturer_id':make_id, 'category_id':cat_id } )
       snipe_api_url = quote(f"/api/v1/models", safe=":/?=&")
       snipe_connection.request(method="POST", url=snipe_api_url, body=payload, headers=snipe_headers)
       snipe_response = snipe_connection.getresponse()
       ## print(payload)

       snipe_raw_data = snipe_response.read()
       #print(repr(snipe_raw_data))
   else:
       print(f"Model Already Preset in SnipeIT:{make},{model},{category}")
    

    
    



    #print(index, row['Manufacturer'], row['Model'])

    
      








