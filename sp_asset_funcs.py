#!/usr/bin/env python3

from urllib.parse import urlparse 
import requests
import time
import sys
import json
from pathlib import Path
from sassafras_funcs import get_sass_displays_serial_model


RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
RESET = '\033[0m'

debug = False

# Blueprint 

# This code impliments #2 below.

# 1. We need to generate a csv file with all doc libs under a site.
# 2. We need to read a csv and create folder under a doc lib path (old path and new folder name)
# 3. We need read the same csv and teh ShareGate Report to generate a list of permission that will need to be applied.
# 4. We need to write code to recursively copy th content of old DL into the new folder.

sp_asset_entry = {}


# === App Registration Config ===
TENANT_ID = 'f6b6dd5b-f02f-441a-99a0-162ac5060bd2'
CLIENT_ID = '77571b91-7a3c-4a4b-af8c-581ddb72cdaa'
SCOPES = ["Files.ReadWrite.All openid People.Read Presence.Read Presence.Read.All profile Sites.Read.All Sites.ReadWrite.All Tasks.ReadWrite User.Read User.ReadBasic.All User.ReadWrite"]

def ms_auth_get_access_token():

   global access_token

   # === Step 1: Get device code ===
   device_code_url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/devicecode"
   payload = {
      "client_id": CLIENT_ID,
      "scope": " ".join(SCOPES)
   }
   resp = requests.post(device_code_url, data=payload)
   resp.raise_for_status()
   device_data = resp.json()

   print("\n"+RED+"=== Sign In Required ==="+ RESET)
   print(f"Visit: {device_data['verification_uri']}")
   print(f"Enter code: {device_data['user_code']}")
   print("========================")

   # === Step 2: Poll for token ===
   token_url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
   payload = {
      "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
      "client_id": CLIENT_ID,
      "device_code": device_data["device_code"]
   }

   print(RED + "===  Waiting for sign-in === " + RESET, end="", flush=True)
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
   print(" ... " + GREEN + "Authenticated.\n" + RESET)


# ------------------------------------------
def get_site_id(site_path):

   global access_token

   headers = {
    "Authorization": f"Bearer {access_token}"
   }
  

   # Step 4. Get the SRC Site ID.
   if debug: print(YELLOW + "\tDEBUG" + RESET + " Getting SRC Site ID...")
   endpoint = f"https://graph.microsoft.com/v1.0/sites/uwnetid.sharepoint.com:{site_path}"
   if debug: print(YELLOW + "\tDEBUG" + RESET +  f" EndPoint: {endpoint}")

   response = requests.get(endpoint, headers=headers )
   response.raise_for_status()
   resp = response.json()

   print(GREEN + "INFO" + RESET + f" SiteID: for {site_path}:"+resp['id'])

   return resp['id']


# ------------------------------------------
def get_list_id(site_id, list_name):
   global access_token

   headers = {
    "Authorization": f"Bearer {access_token}"
   }

   # Step 5. Get SRC Library/Drive ID 

   if debug: print(YELLOW + "\tDEBUG" + RESET + " Getting List ID...")
   endpoint = f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists"
   if debug: print(YELLOW + "\tDEBUG" + RESET +  f" EndPoint: {endpoint}")

   response = requests.get(endpoint, headers=headers )
   response.raise_for_status()
   resp = response.json()

   #print("--------------------------------- \n Drives for this Site:")
   #print(json.dumps(resp, indent=3))

   list_id = False;
   for list in resp['value']:
      if list['name'] == list_name :
          print(GREEN + "INFO" + RESET + f" Found our List ID. List:{list_name}  ID: " + list['id'])
          return list['id']

   print(f"Unable to find List ID for List: {list_name}")
   return False 


def get_list_columns(site_id, list_id):
# ------------------------------------------
   #GET https://graph.microsoft.com/v1.0/sites/{site-id}/lists/{list_id}/columns

   headers = {
    "Authorization": f"Bearer {access_token}"
   }

   if debug: print(YELLOW + "\tDEBUG" + RESET + " Getting SRC Drive ID...")
   endpoint = f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/{list_id}/columns"
   if debug: print(YELLOW + "\tDEBUG" + RESET +  f" EndPoint: {endpoint}")

   response = requests.get(endpoint, headers=headers )
   response.raise_for_status()
   resp = response.json()

   print("--------------------------------- \n Drives for this Site:")
   print(json.dumps(resp, indent=3))


def load_sp_assets(debug_arg=debug):

   global debug 
   debug = debug_arg
   global sp_asset_entry

   sp_assets = {}

   ms_auth_get_access_token()
   site_id = get_site_id("/sites/ischoolteams/InformationTechnology/Inventory")
   list_id = get_list_id(site_id, "Inventory")

   # get_list_columns(site_id, list_id)
   
   print(GREEN + f"---------------------------------> " + RESET + "Loading Assets ... Please Wait ...")

   list_endpoint = f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/{list_id}/items?expand=fields(select=UW_x0020_Inventory_x0020_Tag,LinkTitle,brand,model)"

   while (list_endpoint):
      headers = {
         "Authorization": f"Bearer {access_token}"
      }
   
      response = requests.get(list_endpoint, headers=headers )
      response.raise_for_status()
      resp = response.json()
   
      if '@odata.nextLink' in resp :
         list_endpoint =  resp['@odata.nextLink']
      else:
         list_endpoint = False
      
      for entry in resp['value']:
         #print(json.dumps(entry, indent=3))
   
         if (not 'UW_x0020_Inventory_x0020_Tag' in entry['fields']) or (not 'LinkTitle' in entry['fields']):
            continue
   
         serial = entry['fields']['LinkTitle']
         entry['fields']['Serial'] = serial
         
         asset_tag = entry['fields']['UW_x0020_Inventory_x0020_Tag']
         sp_assets[asset_tag] = entry['fields']
   

   print(GREEN + f"--------------------------------- Loading Assets .. Done! " + RESET)
   sp_asset_entry = sp_assets
   return 


def sp_lookup_asset(asset_tag, debug_arg=debug):
   global sp_asset_entry

   if not sp_asset_entry:
     load_sp_assets(debug_arg)

   if asset_tag in sp_asset_entry:
      #formatted_data = json.dumps(sp_asset_entry[asset_tag], indent=4)
      #print(f"Asset {asset_tag} found SharePoint Data:\n {formatted_data}")
 
      return sp_asset_entry[asset_tag]
   else:
      return False



