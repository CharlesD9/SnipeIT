import re
import json
from time import sleep

from sassafras_funcs import get_sass_displays_serial_model

from sp_asset_funcs import load_sp_assets

from snipe_funcs import get_snipe_models, DISP_CAT_ID

RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
RESET = '\033[0m'

#DISP_CAT_ID = 34

#snipe_models = get_snipe_models(DISP_CAT_ID)
#for model in snipe_models:
#   print(f"Model {model} :- Snipe Data:\n {snipe_models[model]}")


sp_assets = load_sp_assets()

models_seen = {}

for asset in sp_assets :
   formatted_data = json.dumps(sp_assets[asset], indent=4)
   #print(f"Asset {asset} :- SharePoint Data:\n {formatted_data}")

   if 'Model' in sp_assets[asset]:
      model = sp_assets[asset]['Model']
      if not re.search(r"U[0-9]+", model ):
         continue
      
      if model in models_seen:
         continue;
      else:
         models_seen[model] = True
    
      matching_keys = []
      snipe_models = get_snipe_models(False, model)

      formatted_data = json.dumps(snipe_models, indent=4)
      print(formatted_data)

      for key in snipe_models.keys():
         pattern = fr"{model}$"
         if re.search(pattern, key):
            matching_keys.append(key)

      if len(matching_keys) > 1:
          print(RED + f"{asset} - {model} - {len(matching_keys)}" + RESET)
      elif len(matching_keys) == 1:
         print(GREEN + f"{asset} - {model} - {len(matching_keys)}" + RESET )
      else:
          print(f"{asset} - {model} - {len(matching_keys)}" )
      sleep(0.4999)

sass_assets = get_sass_displays_serial_model()
for asset in sass_assets :
   formatted_data = json.dumps(sass_assets[asset], indent=4)
   #print(f"Asset {asset} :- Sassafras Data:\n {formatted_data}")

   if 'Model Number' in sass_assets[asset]:
      model = sass_assets[asset]['Model Number']

      if model in models_seen:
         continue;
      else:
         models_seen[model] = True

      snipe_models = get_snipe_models(False, model)
      matching_keys = []
      
      for key in snipe_models.keys():
         pattern = fr"{model}$"
         if re.search(pattern, key):
            matching_keys.append(key)

      if len(matching_keys) > 1:
         print(RED + f"{asset} - {model} - {len(matching_keys)}" + RESET )
      elif len(matching_keys) == 1:
         print(GREEN + f"{asset} - {model} - {len(matching_keys)}" + RESET )
      else:
         print(f"{asset} - {model} - {len(matching_keys)}" )
 
      sleep(0.4999)

