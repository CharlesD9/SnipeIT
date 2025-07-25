import http.client
import json
import re
from urllib.parse import quote
from datetime import datetime, timedelta
import pytz

RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
RESET = '\033[0m'

sassafras_display_models = {}




ResStd = {
   '640x360': 'nHD(16:9)',
   '640x480': 'VGA(4:3)',
   '800x600': 'SVGA(4:3)',
   '1024x768': 'XGA(4:3)',
   '1280x720': 'WXGA(16:9)',
   '1280x800': 'WXGA(16:10)',
   '1280x1024': 'SXGA(5:4)',
   '1360x768': 'HD(16:9)',
   '1440x900': 'WXGA+(16:10)',
   '1536x864': 'N/A(16:9)',
   '1600x900': 'HD+(16:9)',
   '1600x1200': 'UXGA(4:3)',
   '1680x1050': 'WSXGA+(16:10)',
   '1920x1080': 'FHD(16:9)',
   '1920x1200': 'WUXGA(16:10)',
   '2048x1152': 'QWXGA(16:9)',
   '2048x1536': 'QXGA(4:3)',
   '2560x1080': 'UWFHD(21:9)',
   '2560x1440': 'QHD(16:9)',
   '2560x1600': 'WQXGA(16:10)',
   '3440x1440': 'UWQHD(≈21:9)', 
   '3840x2160': '4K UHD(16:9)',
   '5120x2880': '5K(16:9)',
   '6144x3456': '6K(16:9)',
   '7680x2160': 'DUHD(32:9)',
   '7680x4320': '8K UHD(16:9)'
}


def open_sass_connection():
   try: 
       #return http.client.HTTPSConnection('is-licensing.ischool.uw.edu', port=443)
       return http.client.HTTPSConnection('remotelab.ischool.uw.edu', port=443)

   except (http.client.HTTPException, ConnectionError) as http_err:
      print(f"HTTP connection/request error: {http_err}")

def get_sass_access_token():
   with open("is-licensing.access-token","r") as file:
      return file.readline().rstrip()


def sanitize_manufacturer(manufacturer):
   m = manufacturer
   m = re.sub(r"^HP","Hewlett-Packard",m)
   m = re.sub(r"^Hewlett.Packard","Hewlett_Packard",m)
   m = re.sub(r"^Integrated.Tech","Integrated_Tech",m)
   m = re.sub(r"^Boulder.Nonlinear.Systems","Boulder_Nonlinear_Systems",m)

   m = re.sub(r"^RGB.Systems","RGB_Systems",m)
   m = re.sub(r"^Audio.Processing.Technology","Audio_Processing_Technology",m)
   m = re.sub(r"^LENOVO","Lenovo",m)

   match = re.match(r"^[A-Za-z0-9_\-]+", m)
   m = match.group(0)
   m = re.sub(r"_"," ",m)
   
   return m


def get_sass_displays(category_id):

   global sass_connection
   global sass_access_token

   sass_manufacturers = {}
   sass_models = {}
   sass_displays = {}

   dimension = {}
   resolution = {}

   # Does this manufacturere already exist. 
   headers = {
      "accept": "application/json",
      "Content-Type": "application/json",
      "Authorization": f"Bearer {sass_access_token}"
   }
   '''
   # --------- Show fields in development
   sass_api_url = quote(f"/api/v2/device/fields", safe=":/?=")
   sass_connection.request(method="GET", url=sass_api_url, headers=headers)
   response = sass_connection.getresponse()

   raw_data = response.read()
   data = json.loads(raw_data)
   formatted_data = json.dumps(data, indent=4)
   print(formatted_data)
   print("-------------------------------------------------\n")
   exit();
   '''

   fields = "SerialNumber,Manufacturer,Model,Building,Room,OnLoanTo,Height,Width,PhysicalHeight,PhysicalWidth,ID,Name,Category,LastSeen"
   #query="(LastSeen>=@20240000000000Z)&&(Category=\"display\")"  <- not working, filter out older displays in code.
   #query="(LastSeen>=@20240000000000Z
   query="(Category=Display)"

   query = quote(f"{query}", safe=":/?=(),<>@\"'&")
   sass_api_url = quote(f"/api/v2/device/items?fields={fields}&query={query}", safe=":/?=(),<>@&'")
   #sass_api_url = quote(f"/api/v2/computer/fields", safe=":/?=")

   print(sass_api_url)
   sass_connection.request(method="GET", url=sass_api_url, headers=headers)
   response = sass_connection.getresponse()

   # Raise exception for non-2xx responses
   if response.status < 200 or response.status >= 300:
      raise Exception(f"HTTP error {response.status}: {response.reason}")

   raw_data = response.read()
   decoded_str = raw_data.decode('iso-8859-1')
   data = json.loads(decoded_str)
   #formatted_data = json.dumps(data, indent=4)
   #print(formatted_data)

   model_matches = 0;

   now = datetime.now()
   timezone = pytz.timezone('America/Los_Angeles')
   now = timezone.localize(now)

   one_year_ago = now - timedelta(days=365)

   # Pull down Sassafras data.
   for row in data:

      if not 'Model' in row :
         formatted_data = json.dumps(row, indent=4)
         #print("WTF: " + formatted_data)
         continue

      if not 'Manufacturer' in row:
         formatted_data = json.dumps(row, indent=4)
         #print("WTF: " + formatted_data)
         continue

      if not row["Category"] == "Display":
         continue;

      date_format = "%Y-%m-%dT%H:%M:%S%z"
      # Convert the string to a datetime object
      lastseen = datetime.strptime(row['LastSeen'], date_format)

      if lastseen < one_year_ago:
         continue;

      manf = sanitize_manufacturer(row['Manufacturer'])

      if manf not in sass_manufacturers:
         sass_manufacturers[manf] = manf

      if row['Model'] not in sass_models:

         model_matches += 1

         model = row['Model']

         model_number = re.sub(rf"^\s*{manf}\s*", "", row['Model'], flags=re.IGNORECASE)

         # Lookup the resolution and standards
         if 'Height' in row and 'Width' in row :
            res = f"{row['Width']}x{row['Height']}" if int(row['Width']) > 0 else ""
            std =  ResStd[res] if res in ResStd else ""
         else:
            res = ""
            std = ""

         # Calculate diagonal screen size
         if 'PhysicalHeight' in row and 'PhysicalWidth' in row and int(row['PhysicalWidth']) > 0 :
            w = row['PhysicalWidth']
            h = row['PhysicalHeight']
            dim = f"{row['PhysicalWidth']},{row['PhysicalHeight']}"
            diag =  int(( ((h**2 + w**2) ** 0.5)/2.54) // 1)      # find diagonal, conver to inches (/2.54), then get floor (//1)
            diag =  round(((h**2 + w**2) ** 0.5)/2.54)      # find diagonal, conver to inches (/2.54), then get floor (//1)
            diag = f"{diag}\""

         else:
            dim = "Undef"
            diag = ""

         model_name = f"{model_number} {diag} {res} {std}".rstrip()
         print(f"{manf} - {model_name} \t\t last seen:{row['LastSeen']}\n")
         sass_models[model] = (manf,  model_name,  category_id)

      #    fields = "Height,Width,PhysicalHeight,PhysicalWidth,ID,Name,Category,LastSeen,SerialNumber,Manufacturer,Model"
      if 'SerialNumber' in row:
         sass_displays[row['ID']] = {
            'SerialNumber': row['SerialNumber'], 
            'ModelNumber': row['Model'],
            'OnLoanTo': (row['OnLoanTo'] if 'OnLoanTo' in row else False) ,
            'Building': (row['Building'] if 'Building' in row else False) ,
            'Room': ( row['Room'] if 'Room' in row else False ) 
         }


   print(f"Display Models Found: {model_matches}")

   return (sass_manufacturers, sass_models, sass_displays)



def get_sass_displays_serial_model():

   global sass_connection
   global sass_access_token

   sass_displays = {}

   # Does this manufacturere already exist. 
   headers = {
      "accept": "application/json",
      "Content-Type": "application/json",
      "Authorization": f"Bearer {sass_access_token}"
   }

   fields = "SerialNumber,Manufacturer,Model,Building,Room,OnLoanTo,Height,Width,PhysicalHeight,PhysicalWidth,ID,Name,Category,LastSeen"
   query="(Category=Display)"

   query = quote(f"{query}", safe=":/?=(),<>@\"'&")
   sass_api_url = quote(f"/api/v2/device/items?fields={fields}&query={query}", safe=":/?=(),<>@&'")
   #sass_api_url = quote(f"/api/v2/computer/fields", safe=":/?=")

   print(YELLOW + "\tDEBUG" + RESET + f"Sassafraz endpoint: {sass_api_url}")
   sass_connection.request(method="GET", url=sass_api_url, headers=headers)
   response = sass_connection.getresponse()

   # Raise exception for non-2xx responses
   if response.status < 200 or response.status >= 300:
      raise Exception(f"HTTP error {response.status}: {response.reason}")

   raw_data = response.read()
   decoded_str = raw_data.decode('iso-8859-1')
   data = json.loads(decoded_str)
   #formatted_data = json.dumps(data, indent=4)
   #print(formatted_data)

   model_matches = 0;

   now = datetime.now()
   timezone = pytz.timezone('America/Los_Angeles')
   now = timezone.localize(now)


   # Pull down Sassafras data.
   for row in data:

      if not 'Model' in row :
         formatted_data = json.dumps(row, indent=4)
         #print("WTF: " + formatted_data)
         continue

      # Strip Manufacturer from Model
      if 'Manufacturer' in row:
          manf = sanitize_manufacturer(row['Manufacturer'])
          row['Manufacturer'] = manf

          model = row['Model']
          model_number = re.sub(rf"^\s*{manf}\s*", "", row['Model'], flags=re.IGNORECASE)

          row['Model Number'] = model_number
      else:
          manf = "Unknown"
          row['Manufacturer'] = manf
          model_number = row['Model']
          row['Model Number'] = model_number

      #if not 'Manufacturer' in row:
      #   formatted_data = json.dumps(row, indent=4)
      #   #print("WTF: " + formatted_data)
      #   continue

      if not row["Category"] == "Display":
         continue;

      if 'SerialNumber' in row:
         sass_displays[row['SerialNumber']] = row

   return sass_displays


def get_sass_computers(form_factor, category_id):

   global sass_connection
   global sass_access_token

   sass_manufacturers = {}
   sass_models = {}
   sass_computers = {}

   models_found = 0

   # Does this manufacturere already exist. 
   headers = {
      "accept": "application/json",
      "Content-Type": "application/json",
      "Authorization": f"Bearer {sass_access_token}"
   }

   '''
   # --------- Show fields in development
   sass_api_url = quote(f"/api/v2/computer/fields", safe=":/?=")
   sass_connection.request(method="GET", url=sass_api_url, headers=headers)
   response = sass_connection.getresponse()

   raw_data = response.read()
   data = json.loads(raw_data)
   formatted_data = json.dumps(data, indent=4)
   print(formatted_data)

   print("-------------------------------------------------\n")
   '''


   fields ="Name,ComputerID,FormFactor,Manufacturer,Model,InService,LastLogin,Status,UserName,OEMSerial,OSFamily,OSVersion"
   query="(LastLogin>=@20240000000000Z)"
   sass_api_url = quote(f"/api/v2/computer/items/?fields={fields}&query={query}", safe=":/?=()<@&")
   print(sass_api_url)
   sass_connection.request(method="GET", url=sass_api_url, headers=headers)
   response = sass_connection.getresponse()

   # Raise exception for non-2xx responses
   if response.status < 200 or response.status >= 300:
      raise Exception(f"HTTP error {response.status}: {response.reason}")

   raw_data = response.read()
   data = json.loads(raw_data)
   formatted_data = json.dumps(data, indent=4)
   # print(formatted_data)

   rows = len(data)
   print(f"rows = {rows}")
 
   for row in data:
      formatted_data = json.dumps(row, indent=4)

      if not 'Model' in row :
         formatted_data = json.dumps(row, indent=4)
         #print("WTF: " + formatted_data)
         continue


      if not 'Manufacturer' in row:
         formatted_data = json.dumps(row, indent=4)
         #print("WTF: " + formatted_data)
         continue

      if not 'FormFactor' in row:
         continue


      if row['FormFactor'] != form_factor:
         continue

      #print("ROW: " + formatted_data)


      manf = sanitize_manufacturer(row['Manufacturer'])
      if manf not in sass_manufacturers:
         sass_manufacturers[manf] = manf

      model = row['Model']

      if model not in sass_models:
         models_found += 1

         print(f"{manf} - {model} \t\t last seen:{row['LastLogin']}\n")
         # sass_models[model] = (manf, category_id)    
         sass_models[model] = (manf,  model,  category_id)

   print(f"Computer Models Found: {models_found}")
   return (sass_manufacturers, sass_models, sass_computers)

def sass_lookup_asset(serial):
   global sassafras_display_models

   if not sassafras_display_models:
      print(f"\n--------------------------------- Loading Sass Assets .. Please Wait ")
      sassafras_display_models = get_sass_displays_serial_model()
      print(f"\n--------------------------------- Loading Assets .. Done! ")

   if serial in sassafras_display_models :
      #formatted_data = json.dumps(sassafras_display_models[serial], indent=4)
      #print(f"Asset {serial} found Sassafras Data:\n {formatted_data}")
 
      return sassafras_display_models[serial]
   else:
      return False


sass_connection = open_sass_connection()
sass_access_token = get_sass_access_token()

