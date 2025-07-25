#!/usr/bin/env python3

from urllib.parse import urlparse 
import requests
import time
import sys
import json
from pathlib import Path
from snipe_funcs import get_snipe_assets, checkout_asset_to_user, replace_snipe_asset_tag


RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
RESET = '\033[0m'


# Blueprint  

# This code impliments #2 below.

# 1. We need to generate a csv file with all doc libs under a site.
# 2. We need to read a csv and create folder under a doc lib path (old path and new folder name)
# 3. We need read the same csv and teh ShareGate Report to generate a list of permission that will need to be applied.
# 4. We need to write code to recursively copy th content of old DL into the new folder.


# === App Registration Config ===
TENANT_ID = 'f6b6dd5b-f02f-441a-99a0-162ac5060bd2'
CLIENT_ID = '77571b91-7a3c-4a4b-af8c-581ddb72cdaa'
SCOPES = ["Files.ReadWrite.All openid People.Read Presence.Read Presence.Read.All profile Sites.Read.All Sites.ReadWrite.All Tasks.ReadWrite User.Read User.ReadBasic.All User.ReadWrite"]


# === Step 1: Get device code ===
device_code_url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/devicecode"
payload = {
    "client_id": CLIENT_ID,
    "scope": " ".join(SCOPES)
}
resp = requests.post(device_code_url, data=payload)
resp.raise_for_status()
device_data = resp.json()

print("\n\n"+RED+"=== Sign In Required ==="+ RESET)
print(f"Visit: {device_data['verification_uri']}")
print(f"Enter code: {device_data['user_code']}")
print("========================\n")

# === Step 2: Poll for token ===
token_url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
payload = {
    "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
    "client_id": CLIENT_ID,
    "device_code": device_data["device_code"]
}

print(YELLOW + "DEBUG" + RESET + " Waiting for sign-in...")
while True:
    token_resp = requests.post(token_url, data=payload)
    if token_resp.status_code == 200:
        break
    elif token_resp.status_code in (400, 401):
        error = token_resp.json().get("error")
        if error == "authorization_pending":
            continue
        else:
            raise Exception("OAuth error:", error)
    else:
        token_resp.raise_for_status()

access_token = token_resp.json()["access_token"]
print(GREEN + " Authenticated.\n" + RESET)



# ------------------------------------------
def get_site_id(site_path):

   # Step 4. Get the SRC Site ID.
   print(YELLOW + "DEBUG" + RESET + " Getting SRC Site ID...")
   endpoint = f"https://graph.microsoft.com/v1.0/sites/uwnetid.sharepoint.com:{site_path}"

   print(YELLOW + "DEBUG" + RESET +  f" EndPoint: {endpoint}")

   response = requests.get(endpoint, headers=headers )
   response.raise_for_status()
   resp = response.json()

   print(GREEN + "INFO" + RESET + f" SiteID: for {site_path}:"+resp['id'])

   return resp['id']


# ------------------------------------------
def get_list_id(site_id, list_name):

   # Step 5. Get SRC Library/Drive ID 
   print()
   print(YELLOW + "DEBUG" + RESET + " Getting SRC Drive ID...")
   endpoint = f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists"
   print(YELLOW + "DEBUG" + RESET +  f" EndPoint: {endpoint}")

   response = requests.get(endpoint, headers=headers )
   response.raise_for_status()
   resp = response.json()

   #print("--------------------------------- \n Drives for this Site:")
   #print(json.dumps(resp, indent=3))

   list_id = False;
   for list in resp['value']:
      #print("List: " + list['name'])
      if list['name'] == list_name :
          print(GREEN + "INFO" + RESET + f" Found our SRC Drive:{list_name}  ID: " + list['id'])
          return list['id']

   print(f"Unable to find List ID for List: {list_name}")
   return False 




def get_list_columns(site_id, list_id):
# ------------------------------------------
   #GET https://graph.microsoft.com/v1.0/sites/{site-id}/lists/{list-id}/columns

   print(YELLOW + "DEBUG" + RESET + " Getting SRC Drive ID...")
   endpoint = f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/{list-id}/columns"
   print(YELLOW + "DEBUG" + RESET +  f" EndPoint: {endpoint}")

   response = requests.get(endpoint, headers=headers )
   response.raise_for_status()
   resp = response.json()

   print("--------------------------------- \n Drives for this Site:")
   print(json.dumps(resp, indent=3))


headers = {
 "Authorization": f"Bearer {access_token}"
}

site_id = get_site_id("/sites/ischoolteams/InformationTechnology/Inventory")
list_id = get_list_id(site_id, "Inventory" )

print(f"\n\n--------------------------------- \n We have the listID: {list_id} ")


snipe_assets = get_snipe_assets()


list_endpoint = f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/{list_id}/items?expand=fields(select=UW_x0020_Inventory_x0020_Tag,LinkTitle)"

while (list_endpoint):

   headers = {
      "Authorization": f"Bearer {access_token}"
   }
   
   response = requests.get(list_endpoint, headers=headers )
   response.raise_for_status()
   resp = response.json()
   
   # Display the permissions
   #print("\n\n--------------------------------- \n Permissions for the document library:")
   #print(YELLOW + "DEBUG" + RESET +  f" EndPoint: {list_endpoint}")
   #print(json.dumps(resp, indent=3))
   #print(f"Rows ={len(resp['value'])}")

   if '@odata.nextLink' in resp :
      list_endpoint =  resp['@odata.nextLink']
   else:
      list_endpoint = False
   
   for entry in resp['value']:
      #print(json.dumps(entry, indent=3))

      if (not 'UW_x0020_Inventory_x0020_Tag' in entry['fields']) or (not 'LinkTitle' in entry['fields']):
         continue
      serial = entry['fields']['LinkTitle']
      asset_tag = entry['fields']['UW_x0020_Inventory_x0020_Tag']
      #print(f"Entry {serial} - {asset_tag} ")
      if serial in snipe_assets and snipe_assets[serial] != asset_tag:
         print(f"The Eagle has landed - We have serial:{serial} - Snipe-asset: {snipe_assets[serial]} - asset-tag: {asset_tag}")
         replace_snipe_asset_tag(snipe_assets[serial], asset_tag)
         time.sleep(0.5)


