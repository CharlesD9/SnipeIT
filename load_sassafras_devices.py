#!/usr/bin/env python3


import time
from sassafras_funcs import get_sass_displays
from snipe_funcs import get_snipe_manufacturers, get_snipe_models, load_snipe_manufacturer, load_snipe_model, load_snipe_asset, get_snipe_users, get_snipe_assets, checkout_asset_to_user


# hard coding display category ID;
DISP_CAT_ID = 34


# https://www.sassafras.com/hrl/ksp-api.html#tag/Overview
# https://snipe-it.readme.io/reference/api-overview


print("Getting Snipe Manufacturers")
snipe_manufacturers = get_snipe_manufacturers()

print("Getting Snipe Models")
snipe_models = get_snipe_models(DISP_CAT_ID)

#print("Getting Snipe users")
#snipe_users = get_snipe_users()

print("Getting Snipe Assets")
snipe_assets = get_snipe_assets()

print("Getting Sassafraz Display")
(sass_manufacturers, sass_models, sass_displays) = get_sass_displays(DISP_CAT_ID)


print("--------------\nLoading New Manufacturers")
reload = False
for manufacturer in sass_manufacturers:
  if not manufacturer in snipe_manufacturers:
     reload = True
     load_snipe_manufacturer(manufacturer)
   

if reload:
   print("Reloading Snipe Manufacturers")
   snipe_manufacturers = get_snipe_manufacturers()

print("--------------\nLoading New Models")

reload = False
for model_number in sass_models:

   (manufacturer, model_name, category_id) = sass_models[model_number]
   if not manufacturer in snipe_manufacturers:
      print(f"key Error - {manufacturer}, {model_name}, {category_id} not know in snipe_manufacturers dict")
      continue
      
   snipe_manufacturer_id =  snipe_manufacturers[manufacturer]

   if not model_number in snipe_models:
       load_snipe_model(snipe_manufacturer_id, category_id, manufacturer, model_number, model_name)
       time.sleep(1)

if reload:
   print("Reloading Snipe Models")
   snipe_models = get_snipe_models(DISP_CAT_ID)

print(f"--------------\nLoading New Display - Total {len(sass_displays)}")
for sass_id in sass_displays:

     obj =  sass_displays[sass_id]

     serial = obj['SerialNumber']

     model_number  = obj['ModelNumber']

     note = f"{obj['Building']} - {obj['Room']}"

     (model_id, name) = snipe_models[model_number] 
     # Since devices are not name, we use the Model name as the device name.

     status_id = 5
     #if sass_id in snipe_assets:
     if serial in snipe_assets:
        print(f"Asset SN:{serial} already known in Snipe...")
        time.sleep(0.2)
     else :
        id = load_snipe_asset(sass_id, status_id, model_id, name, serial, note)
        if id:
           time.sleep(2)

        #if id:   # Asset loaded into Snipe
        #   user = obj['OnLoanTo']
        #   if user and user in snipe_users:
        #       if user in snipe_users:
        #          print(f"checking out {name} to {user}")
        #          checkout_asset_to_user(id, snipe_users[user] )
        #       else:
        #          print(f"User: {user} not known in Snipe...")

     

