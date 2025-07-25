import json
from sp_asset_funcs import sp_lookup_asset
from sassafras_funcs import sass_lookup_asset 
 
def lookup_asset(asset_tag):

   print()
   print()
   sp_asset_info = sp_lookup_asset(asset_tag)
   if sp_asset_info:
      formatted_data = json.dumps(sp_asset_info, indent=4)
      print(f"Asset {asset_tag}: SharePoint Data:\n {formatted_data}")
   else:
      print(f"Asset {asset_tag}: SharePoint Data: Not found")

   
   if sp_asset_info:
      serial = sp_asset_info['Serial']
      sass_asset_info = sass_lookup_asset(serial)
      if sass_asset_info:
         formatted_data = json.dumps(sass_asset_info, indent=4)
         print(f"Asset {asset_tag}: Sassafras Data:\n {formatted_data}")
      else:
         print(f"Asset {asset_tag}: Sassafras Data: Not Found")


lookup_asset('30236665')
lookup_asset('30236625')
lookup_asset('31236625')

while True:
    try:
        asset_tag = input("Enter Asset Tag or  press Ctrl+D to exit): ")
        # Process the received input
        asset_tag.strip()
        lookup_asset(asset_tag)
    except EOFError:
        # Exit the loop gracefully when Ctrl+D (EOF) is pressed
        print("\nExiting.")
        exit()
