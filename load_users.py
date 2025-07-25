#!/usr/bin/env python3
import sys
import http.client
import json
import ssl
import getpass
import requests
import random
import string
import time

RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
RESET = '\033[0m'

# Define password length and character set
passwd_length = 12
passwd_characters = string.ascii_letters + string.digits + string.punctuation  # Letters, digits, punctuation

# Defining certificate related stuff and host of endpoint
certificate_file = '../rsa2048/cdaniel1-dev.ischool.uw.edu.pem'
certificate_secret= getpass.getpass("Enter your Certificate Secret: ")
#host = 'groups.uw.edu'
host = 'api.ischool.uw.edu'

# Defining parts of the HTTP request
#membership_api_base='/group_sws/v3/group/'
membership_api_base='/api/v1/group/membership/direct/'
person_api_base='/api/v1/person/person/'
request_headers = {
    'Content-Type': 'application/json'
}

# Define the client certificate settings for https connection
context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
context.load_cert_chain(certfile=certificate_file, password=certificate_secret)

# Create a connection to submit HTTP requests
connection = http.client.HTTPSConnection(host, port=443, context=context)

with open("it-inventory.access-token","r") as file:
    access_token = file.readline().rstrip()


def load_person_from_netid(netid):

    request_url = person_api_base + netid 
    # Use connection to submit a HTTP POST request
    connection.request(method="GET", url=request_url, headers=request_headers)
    response = connection.getresponse()

    raw_data = response.read()
    data = json.loads(raw_data)

    #formatted_data = json.dumps(data, indent=4)
    #print(formatted_data)

    
    if ('person' in data):
        first_name = data['person']["preferred_first_name"] or data['person']["registered_first_middle_name"]
        last_name = data['person']["preferred_last_name"] or data['person']["registered_surname"]
    else: 
        print(f"NetID is not known [{netid}] - Bail")
        return  {'data': {'display_name': None}}
   
    print(f"Loading: {netid} - {first_name} {last_name}")

    huskyid = False 
    if ('employee' in data):
        huskyid =  data["employee"]["employee_id"]
        email =  data["employee"]["email"]
        title =  data["employee"]["title_1"]


    elif ('student' in data):
        huskyid =  data["student"]["student_number"]
        email =  data["student"]["email"]
        title =  f'{data["student"]["department_1"]} {data["student"]["class"]} student'


    if not email :
       email = f"{netid}@uw.edu"
   


    #formatted_data = json.dumps(data, indent=4)
    #print(formatted_data)


    snipe_headers = {
       "accept": "application/json",
       "Content-Type": "application/json",
       "Authorization": f"Bearer {access_token}"
    }

    snipe_connection = http.client.HTTPSConnection('it-inventory.ischool.uw.edu', port=443, context=context)
    snipe_api_url = f'/api/v1/users?username={netid}&all=true'
    snipe_connection.request(method="GET", url=snipe_api_url, headers=snipe_headers)
    snipe_response = snipe_connection.getresponse()

    snipe_raw_data = snipe_response.read()
    snipe_data = json.loads(snipe_raw_data)
    rows = snipe_data["total"]
    print(f"{netid} Rows {rows}")
    #formatted_data = json.dumps(snipe_data, indent=4)
    #print(formatted_data)

    if (rows == 0 ):
       snipe_api_url = f'/api/v1/users'

       # Generate the password
       password = ''.join(random.choice(passwd_characters) for _ in range(passwd_length))

       if (huskyid):
           payload = json.dumps({ 'username': f'{netid}', 'password':f'{password}', 'password_confirmation':f'{password}', "employee_num": f'{huskyid}', 'activated': True, 'jobtitle':f'{title}', 'email':f'{email}', 'first_name': f'{first_name}',  'last_name': f'{last_name}', 'groups': 4 } )
       else:
           payload = json.dumps({ 'username': f'{netid}', 'password':f'{password}', 'password_confirmation':f'{password}', 'activated': False, 'email':f'{email}', 'first_name': f'{first_name}',  'last_name': f'{last_name}' } )

       snipe_connection.request(method="POST", url=snipe_api_url, body=payload, headers=snipe_headers)
       snipe_response = snipe_connection.getresponse()
       ## print(payload)
       snipe_raw_data = snipe_response.read()
       #print(repr(snipe_raw_data))

    elif (snipe_data["total"] == 1 ):     # If we know this person in Snipe.
       
       id = snipe_data["rows"][0]["id"]
       #print(snipe_data["rows"][0]["id"])
     
       # update our NetID.
       #snipe_api_url = f'https://it-inventory.ischool.uw.edu/api/v1/users/{id}'
       snipe_api_url = f'/api/v1/users/{id}'

       changes = {}
       if (snipe_data["rows"][0]["first_name"] !=  first_name):
           changes['first_name'] = first_name

       if (snipe_data["rows"][0]["last_name"] != last_name):
           changes['last_name'] = last_name

       if (huskyid):
           if (snipe_data["rows"][0]["email"] != email ):
               changes['email'] = email

           if (snipe_data["rows"][0]["jobtitle"] != title ):
               changes['jobtitle'] = title

           if (snipe_data["rows"][0]["employee_num"] != huskyid):
               changes['employee_num'] = huskyid

           if (not snipe_data["rows"][0]["activated"]): # No longer Affiliated
               changes['activated'] = True

       else:
           if ( snipe_data["rows"][0]["activated"]): # No longer Affiliated
              changes['activated'] = False
              changes['jobtitle'] = 'Unaffiliated'
       
       if changes:
          payload = json.dumps(changes)
          snipe_connection.request(method="PATCH", url=snipe_api_url, body=payload, headers=snipe_headers)
          snipe_response = snipe_connection.getresponse()
          #print(payload)

          snipe_raw_data = snipe_response.read()
          print(repr(snipe_raw_data))
          #snipe_data = json.loads(snipe_raw_data)
          #formatted_data = json.dumps(snipe_data, indent=4)
          #print(formatted_data)
       else:
           print(f"{netid} - No Changes .")
    return data


def walk_group(group_name, indent_depth=4):

    request_url = membership_api_base + group_name 
    # Use connection to submit a HTTP POST request
    connection.request(method="GET", url=request_url, headers=request_headers)

    # Print the HTTP response from the IOT service endpoint
    response = connection.getresponse()

    raw_data = response.read()
    data = json.loads(raw_data)
    #formatted_data = json.dumps(data, indent=indent_depth)
    #print(formatted_data)

    grp_data = data["data"]
    for grp_data in data["data"]:
        type = grp_data["type"]
        name = grp_data["name"]

        if type == "group":
            print(RED+(" " * indent_depth) + type + ": " + RESET + name)
            walk_group(name, indent_depth + 4)
        else:
            #data = get_person_from_netid(name)
            data = load_person_from_netid(name)
            person = data["person"]
            print(GREEN+(" " * indent_depth) + 'person' + ": " + RESET + f'{person["display_name"]} ({name})')
            time.sleep(0.5) # Trottle API calls to 120/minute


    print();


walk_group('uw_ischool_staff_core')
walk_group('uw_ischool_faculty_core')
walk_group('uw_ischool_students_inscphd')
walk_group('uw_ischool_employees_research-assistant')
