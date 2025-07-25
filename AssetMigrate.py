import re, random, time, requests, sys, json, html, argparse
import http.client
from http import *
from colorama import * # Some colors to make the CLI seem a bit more lively to less fmailiar users.
import urllib.parse
from sp_asset_funcs import sp_lookup_asset, load_sp_assets, sp_asset_entry
from sassafras_funcs import sass_lookup_asset
from snipe_funcs import load_snipe_asset, checkout_asset_to


QUERY_SNIPE_ASSET_EXISTS_BY_TAG = 0
QUERY_SNIPE_LOCATION_EXISTS = 1
QUERY_OLD_SYSTEM_GET_SERIAL = 2
QUERY_OLD_SYSTEM_GET_MODEL = 3
QUERY_OLD_SYSTEM_GET_MAKE = 4


SnipeHost = "it-inventory"

def parse_args(): # Parse room num from command line
    parser = argparse.ArgumentParser(description='This program is for adding things to SnipeIT. Contact cdaniel1@uw.edu for details.', usage='python3 main.py -b buildingID -r RoomID')
    parser.add_argument('-b', help='Building ID input on command line because SOMEONE kept complaining.', required=True)
    parser.add_argument('-r', help='Room ID input on command line.', required=True)

    returnArgs = parser.parse_args()
    return returnArgs

def queryAPI(data1, data2, mode): # Query API. Mode options passed as string.

    with open(f"{SnipeHost}.access-token","r") as file:
        snipeAccessToken = file.readline().rstrip() # Get access token from file.

    headers = {
            "accept": "application/json",
            "Authorization": "Bearer " + snipeAccessToken,
            "Accept": "application/json"
    }

    if mode == QUERY_SNIPE_ASSET_EXISTS_BY_TAG: # Query for checking if an asset exists.
        assetCheckURL = f"https://{SnipeHost}.ischool.uw.edu/api/v1/hardware/bytag/"
        fullURL = assetCheckURL + urllib.parse.quote(str(data1)) + "?deleted=false" # Build the full URL for the query.
        response = requests.get(fullURL, headers=headers)
        #print (json.dumps(response.json(), indent=4))

        if response.status_code != 200:
            raise Exception((Fore.RED + 'FATAL: API request failure, status code not 200. Exiting program. Request data is as follows.' + str(response.text) + str(response.status_code) + fullURL))

    elif mode ==  QUERY_SNIPE_LOCATION_EXISTS: # Query for checking if a desk (and therefore room) exists.
        assetCheckURL = f"https://{SnipeHost}.ischool.uw.edu/api/v1/locations"
        fullURL = assetCheckURL + "?name=" + (urllib.parse.quote(str(data1))) # Build the full URL for the query.
        response = requests.get(fullURL, headers=headers)

        if response.status_code != 200:
            raise Exception((Fore.RED + 'FATAL: API request failure, status code not 200. Exiting program. Request data is as follows.' + str(response.text) + str(response.status_code) + fullURL))

    elif mode == QUERY_OLD_SYSTEM_GET_SERIAL or QUERY_OLD_SYSTEM_GET_MAKE or QUERY_OLD_SYSTEM_GET_MODEL: # If any modes related to Sass/SharePoint are used, then we can use the same code and just return a different result.
        assetTagQuery = data1
        spAssetInfo = sp_lookup_asset(assetTagQuery)
        if spAssetInfo:
            serialNumberQuery = spAssetInfo['Serial']
            sassAssetInfo = sass_lookup_asset(serialNumberQuery)
            if sassAssetInfo:
                if mode == QUERY_OLD_SYSTEM_GET_SERIAL:
                    response = sassAssetInfo['SerialNumber']
                elif mode == QUERY_OLD_SYSTEM_GET_MODEL:
                    response = sassAssetInfo['Model Number']
                elif mode == QUERY_OLD_SYSTEM_GET_MAKE:
                    response = sassAssetInfo['Manufacturer']
            else:
                if mode == QUERY_OLD_SYSTEM_GET_SERIAL:
                    response = spAssetInfo['Serial']
                elif mode == QUERY_OLD_SYSTEM_GET_MODEL:
                    response = spAssetInfo['Model']
                elif mode == QUERY_OLD_SYSTEM_GET_MAKE:
                    response = spAssetInfo['Brand']

                printColoredError('Warning: Sass API error, nothing was found for this serial number/model/manufacturer. Using sharepoint data instead.')
        else:
            response = '[NO DATA - SP/SASS]'
            printColoredError('SharePoint API error, nothing was found for this assetTag.')
    
    else: # Just in case, to catch if I mess up the code.
        raise TypeError(('function queryAPI: Invalid mode input: ' + str(mode)))

    return response

def printColoredError(message): # Error text styling.
    errorJokeTypes = ['PEBKAC', 'ID-10-t', 'invalidInput', 'biologicalProcessorFailure', '43-dd-1t04', 'iqMustNotBeNegative', 'notEnoughSkill', 'couldNotFindErrorMessage', 'probablyMicrosoft\\\'sFault', 'somethingWentWrongButWeWillNotTellYouWhat', 'OOPS']
def printSystemMessage(message): # System message text styling.
    scrollText(('\n' + Fore.BLUE + '[System] ') + Fore.CYAN + message)

def scrollText(text):
    fun = True
    if fun == True:
        for c in text:
            sys.stdout.write(c)
            sys.stdout.flush()
            time.sleep(0.001)




def serialModel(data): # This function gets information from Sass and SharePoint.

    # Query the API, and store the text results in a dict even if they are "none".
    printSystemMessage("Please wait, loading data from APIs...")
    serialQuery = queryAPI(data, 'dummy', QUERY_OLD_SYSTEM_GET_SERIAL)
    modelQuery = queryAPI(data, 'dummy', QUERY_OLD_SYSTEM_GET_MODEL)
    makeQuery = queryAPI(data, 'dummy', QUERY_OLD_SYSTEM_GET_MAKE)

    # Before storing in dict, we do need to extract the results from the query. This is not needed right now, but I will leave the logic here in case we need it later.
    serialQueryResult = re.match(r"(.*)", serialQuery)
    modelQueryResult = re.match(r"(.*)", modelQuery)
    makeQueryResult = re.match(r"(.*)", makeQuery)

    # Store the results in a query dict.
    smmQueryResults = {
        'serial' : serialQueryResult.group(1), 
        'model'  : modelQueryResult.group(1),
        'make'   : makeQueryResult.group(1)
    }

    printSystemMessage('Data retreived from APIs!') # This is just communicating to user that we got the data, then prints what it found.
    printSystemMessage('automatedSerial: ' + Fore.MAGENTA + smmQueryResults['serial'])
    printSystemMessage('automatedModel: ' + Fore.MAGENTA + smmQueryResults['model'])
    printSystemMessage('automatedMake: ' + Fore.MAGENTA + smmQueryResults['make'])

    userDataEdits = smmQueryResults # Initially set the user edited values to be the automated data.

    printSystemMessage((Fore.YELLOW + "Would you like to edit any of this information? Type \"edit\" if you would like to edit something. Otherwise, press <ENTER>."))
    quitSN = input('\n' + Fore.BLUE + "[Interface] " + Fore.LIGHTGREEN_EX + "Edit or quit? " + Fore.LIGHTBLUE_EX)
    if quitSN == "edit": # Asking the user if they want to edit the data
        userWantsToStopEditing = False
        while userWantsToStopEditing == False:
            printSystemMessage((Fore.YELLOW + "Which information would you like to edit? " + Fore.CYAN + "Enter \"serial\" if you want to edit the serial number, \"model\" if you want to edit the model, or \"make\" if you want to edit the make."))
            userEditChoice = input('\n' + Fore.BLUE + "[Interface] " + Fore.LIGHTGREEN_EX + "Which value would you like to edit? " + Fore.LIGHTBLUE_EX)
            # modify code to eventually ask for what they want to edit individually instead of typing everything
            if userEditChoice == 'serial':
                userInputSerial = input(Fore.BLUE + "[Interface] " + Fore.LIGHTGREEN_EX + "Input new serial number: " + Fore.LIGHTBLUE_EX)
                userDataEdits.update({
                'serial' : userInputSerial
            })
                printSystemMessage('New serial set: ' + Fore.MAGENTA + userInputSerial)
            
            elif userEditChoice == 'model':
                userInputModel = input(Fore.BLUE + "[Interface] " + Fore.LIGHTGREEN_EX + "Input new model: " + Fore.LIGHTBLUE_EX)
                userDataEdits.update({
                'model' : userInputModel
            })
                printSystemMessage('New model set: ' + Fore.MAGENTA + userInputModel)

            elif userEditChoice == 'make': 
                userInputMake = input(Fore.BLUE + "[Interface] " + Fore.LIGHTGREEN_EX + "Input new make: " + Fore.LIGHTBLUE_EX)
                userDataEdits.update({
                'make' :userInputMake
            })
                printSystemMessage('New make set: ' + Fore.MAGENTA + userInputMake)
            
            else:
                printColoredError("Invalid editing  mode choice.")
            
            printSystemMessage('< > Current data < >')
            printSystemMessage('Serial: ' + Fore.MAGENTA + userDataEdits['serial'])
            printSystemMessage('Model: ' + Fore.MAGENTA + userDataEdits['model'])
            printSystemMessage('Make: ' + Fore.MAGENTA + userDataEdits['make'])
            printSystemMessage((Fore.YELLOW + "Would you like to edit any of this information further? Type \"edit\" if you would like to continue editing, or press <ENTER> to exit editing and push your changes."))
            userStillEditing = input('\n' + Fore.BLUE + "[Interface] " + Fore.LIGHTGREEN_EX + "Continue editing? " + Fore.LIGHTBLUE_EX)
            if userStillEditing != 'edit':
                userWantsToStopEditing = True
            else:
                printSystemMessage('Continuing editing.')
                time.sleep(0.1)
    else:
        serial, model, make, isValidSerialModel = None, None, None, False
        

    isValidSerialModel = True # PLACEHOLDER FOR LOGIC TO CHECK IF SERIAL MODEL VALID

    return userDataEdits['serial'], userDataEdits['model'], userDataEdits['make'], isValidSerialModel



def checkAsset(): # Check if our asset is valid and usable

    assetTagInOldSystem = False # Replace with asset tag getting logic.
    # ASSET TAGS WILL USE PREVIOUSLY GOTTEN DESK ID TO FIGURE OUT IF ITEM IS IN DATABASE AT ONCE

    isValidTag = False
    assetTag = input('\n' + Fore.BLUE + "[Interface] " + Fore.LIGHTGREEN_EX + "Input asset tag: " + Fore.LIGHTBLUE_EX)
    assetID = False
    
    isAssetTagValidCheck = re.match(r"^[0-9]{8}$", assetTag) # Handle errors, ensuring that asset tag is exactly 8 digits.
    if not isAssetTagValidCheck:
        printColoredError('assetTag input is not in a valid format. A valid assetTag should be a string of eight digits.')
        isValidTag = False
        assetTagInSnipe = False
    else:
        apiResponse = queryAPI(assetTag, "dummyData", QUERY_SNIPE_ASSET_EXISTS_BY_TAG) # Get an API query for if that asset tag exists.
        apiErrorCheck = re.match(r".*Asset does not exist.*", apiResponse.text) # Check if any of the dict has the right error. If so, then asset has not been found in system, so set that value to true. Otherwise, assume it has been found.

        
        if apiErrorCheck is None:
           # print (f"apiErrorCheck is None - assetTagInSnipe is True: {apiResponse.text}: {apiErrorCheck}")
            assetTagInSnipe = True
        else:
           # print (f"apiErrorCheck is None - assetTagInSnipe is False {apiResponse.text}: {apiErrorCheck}")
            assetTagInSnipe = False
        
    
        if assetTagInSnipe == True:
            responseJSON = apiResponse.json()
            assetID = responseJSON['id']
            printSystemMessage("Asset found in old system! Need to Update Location.")
            isValidTag = True

        else: # If we cannot find the asset tag in SnipeIT, then query Sharepoint/Sass.
            printSystemMessage('Asset tag not found in SnipeIT system. Querying Sharepoint and sass...')
            a, b, c, d = serialModel(assetTag)
            # eventually update desk
            isValidTag = True
            return assetTag, isValidTag, assetID, a, b, c


    return assetTag, isValidTag, assetID, None, None, None
    


def checkDesk():
    
    isValidDesk = False
    deskID = None
    args = parse_args()

    desk = input('\n' + Fore.BLUE + "[Interface] " + Fore.LIGHTGREEN_EX + "Input desk number/ID: " + Fore.LIGHTBLUE_EX)
    if desk == 'reload':
        sp_asset_entry = {}

    deskFull = (str(args.b) + " " + str(args.r) + "-" + desk)
    #isDeskIDValidCheck = re.match(r"^([A-Z]+\s[0-9]+[A-Z]+-[0-9]+)|([A-Z]+\s[0-9]+[A-Z]+)$", desk)
    isDeskIDValidCheck = re.match(r"^([A-Z]+\s[0-9]+[A-Z]*-[0-9]+|[A-Z]+\s[0-9]+[A-Z]*)$", deskFull)

    
    if not isDeskIDValidCheck: # Input validation.
        printColoredError(('desk \'' + deskFull + '\' is not a valid desk. A desk should be something like \"[BUILDING_ID] [ID_NUM][ID_LETTERS]-[ID_NUM]\"'))
        isValidDesk = False
        deskID = None
    else:
        deskIDSystemCheck = queryAPI(deskFull, 'dummyData', 1) # Query location API.
        doesDeskNotExist = re.match(r"\"total\":.0", deskIDSystemCheck.text) # Check if the desk does not exist by checking total matched.
        if not doesDeskNotExist:
            deskIDNotInSystem = False
            isValidDesk = True
            printSystemMessage('deskID found in system!')

            responseJSON = deskIDSystemCheck.json()
            formattedData = json.dumps(responseJSON, indent=4)
            try:
                deskID = responseJSON['rows'][0]['id']    
            except IndexError:
                printColoredError('deskID \'' + str(deskFull) + '\' not found! Debug: JSON returned no data.')
                isValidDesk = False
                deskIDNotInSystem = True
        else:
            deskIDNotInSystem = True
            isValidDesk = False
    
            printColoredError('desk not found in system. Please try again.')

    return deskFull, deskID, isValidDesk



def checkSnipeForModel(model, assetTag):
    offset = 0
    endpoint =  f"/api/v1/models?limit=50&offset={offset}"
    endpointFull = endpoint + f"&search={model}"
    snipeAPIURL = urllib.parse.quote(endpointFull, safe=":/?=&")

    modelID = False
    
    with open(f"{SnipeHost}.access-token","r") as file:
        snipeAccessToken = file.readline().rstrip()
    headers = {
         "accept": "application/json",
         "Content-Type": "application/json",
         "Authorization": f"Bearer {snipeAccessToken}"
      }
    snipeKnowsAboutModel = False

    snipeHTTPConnection = http.client.HTTPSConnection(f"{SnipeHost}.ischool.uw.edu", port=443)
    snipeHTTPConnection.request(method="GET", url=snipeAPIURL, headers=headers)
    response = snipeHTTPConnection.getresponse()

    rawData = response.read()
    data = json.loads(rawData)
    formattedData = json.dumps(data, indent=4)
    snipeHTTPConnection.close()
    if not 'rows' in data:
        printSystemMessage(f'Snipe does not know about model {model}')
        snipeKnowsAboutModel = False
    else:
        for row in data['rows']:
            model_num = html.unescape(row['model_number'])
            printSystemMessage(f'Comparing sass/sp model:{model} with SnipeIT model:{model_num}')

            patternString = ('.*' + model + '$')
            patternComp = re.compile(patternString)
            isFoundInSystem = re.match(patternComp, model_num)

            if isFoundInSystem:
                #logic for we found something
                snipeKnowsAboutModel = True
                modelID = row['id']
            else:
                snipeKnowsAboutModel = False
    
    return snipeKnowsAboutModel, modelID

def sendDataToSnipe(assetTag, serial, name, model_id, note):


    # send data to snipe, and CREATE a new asset 
    # return the newly created assetID to the user, thats it
    # testing - only use stuff on 4th floor for bogus IDs
    # something like MGH 420A-1, 30188414
    # use load_snipe_asset logic or smth after to load the new asset data

    with open(f"{SnipeHost}.access-token","r") as file:
        snipeAccessToken = file.readline().rstrip() # Get access token from file.

    headers = {
            "accept": "application/json",
            "Authorization": "Bearer " + snipeAccessToken,
            "Accept": "application/json",
            "content-type": "application/json"
    }

    # stupid piece of crap wont work
    snipeURL = urllib.parse.quote(f"/api/v1/hardware/byserial/{serial}", safe=":/?=")

    snipeConnection2 = http.client.HTTPSConnection(f"{SnipeHost}.ischool.uw.edu", port=443)

    snipeConnection2.request(method="GET", url=snipeURL, headers=headers)

    snipeResponse = snipeConnection2.getresponse()

    '''
    snipeHTTPConnection = http.client.HTTPSConnection(f"{SnipeHost}.ischool.uw.edu", port=443)
    snipeHTTPConnection.request(method="GET", url=snipeAPIURL, headers=headers)
    response = snipeHTTPConnection.getresponse()

    rawData = response.read()
    '''
    
    
    rawData = snipeResponse.read()
    data = json.loads(rawData)
 

    if 'messages' in data: 
        if re.match( 'Asset does not exist', data['messages'] ): # check to make sure asset does not exist because we do not want to overwrite existing assets.
            newSnipeURL = urllib.parse.quote(f"/api/v1/hardware", safe=":/?=")

            payload = json.dumps({ # The data to add to SnipeIT.
                'name': name, 
                'asset_tag': assetTag, 
                'status_id': 5, 
                'model_id': model_id, 
                'serial': serial,
                'notes': note } )
            
            snipeConnection2.request(method="POST", url=newSnipeURL, body=payload, headers=headers) # Sending the new information to SnipeIT.
            newSnipeResponse = snipeConnection2.getresponse()

            snipeReturnRawData = newSnipeResponse.read()
            returnCode = newSnipeResponse.getcode()
            
            data2 = json.loads(snipeReturnRawData)
     #       printSystemMessage('debug: ' + str(data2))

        else:
            raise Exception('Unexpected SnipeIT response: ' + str(snipeReturnRawData))
    else:
        raise Exception('Asset already exists in SnipeIT even though we checked for that beforehand, if you are seeing this then something went horribly wrong.')
    
    return data2['payload']['id'] #return the NEW assetID to the user



def checkoutAssetToDesk(assetID, deskID):
    # Once the item is in SnipeIT, we check it out to a desk using the AssetID. 
    
    with open(f"{SnipeHost}.access-token","r") as file:
        snipeAccessToken = file.readline().rstrip() # Get access token from file.

    headers = { # Setup headers.
            "accept": "application/json",
            "Authorization": "Bearer " + snipeAccessToken,
            "Content-Type": "application/json"
    }

    snipeURL = urllib.parse.quote(f"/api/v1/hardware/{assetID}/checkout", safe=":/?=") # Setup URL.

    snipeConnection = http.client.HTTPSConnection(f"{SnipeHost}.ischool.uw.edu", port=443) # Establish SnipeIT connection.

    payloadDict = { # The payload is simply where we are checking out the asset to.
        'checkout_to_type' : 'location',
        'assigned_location' : deskID
    }
    payload = json.dumps(payloadDict)

    snipeConnection.request(method="POST", url=snipeURL, body=payload, headers=headers) # Send a checkout request to SnipeIT.

    snipeResponse = snipeConnection.getresponse()
    snipeRawData = snipeResponse.read()
    snipeReturnCode = snipeResponse.getcode()
    data = json.loads(snipeRawData)

def main():

    # Check if desk is valid, if it is not repeat the query to the user.
    desk, deskID, isValidDesk = checkDesk()
    while isValidDesk != True:
        desk, deskID, isValidDesk = checkDesk()
    printSystemMessage('Desk & ID Set: ' + Fore.MAGENTA + desk + ", " + f"{deskID}")

    # Enter the snipe loop.
    snipeUserLoop = True
    while snipeUserLoop == True:

        # Check if asset tag is valid.
        assetTagInput, isValidTag, assetID, serial, model, make = checkAsset() 
        while isValidTag != True:
            assetTagInput, isValidTag, assetID, serial, model, make = checkAsset()


        if assetID: # If we find the asset in SnipeIT, just check it out.
            printSystemMessage('Asset found in SnipeIT! Checking out asset to indicated desk.')
            checkoutAssetToDesk(assetID, deskID)
            '''
            printSystemMessage('Asset Number: ' + Fore.MAGENTA + assetTagInput)
            printSystemMessage('Serial: ' + Fore.MAGENTA + serial)
            printSystemMessage('Model: ' + Fore.MAGENTA + model)
            printSystemMessage('Make: ' + Fore.MAGENTA + make)
            '''
            printSystemMessage('deskID: ' + Fore.MAGENTA + str(deskID))
            snipeUserLoop = False
            continue

        printSystemMessage('Checking to see if SnipeIT has this model in the database...')
        modelInSnipe, modelID = checkSnipeForModel(model, assetTagInput)

        if modelInSnipe != True: # If SnipeIT does not have the model, allow the user to re-enter any details.
            printColoredError(('Model number/ID \'' + model +  '\' not found in SnipeIT.'))
            printSystemMessage(('Would you like to re-enter the data in case you got it wrong?'))
            doesUserWantToRetryData = input('\n' + Fore.BLUE + "[Interface] " + Fore.LIGHTGREEN_EX + "Press <ENTER> to skip, or type \"retry\" to re-enter the data." + Fore.LIGHTBLUE_EX)
            if doesUserWantToRetryData == 'retry':
                printSystemMessage('Retrying asset data entry...')
                snipeUserLoop = True
            else:
                snipeUserLoop = False # If the user does not change anything, then tell them that the asset could not be found.
                printSystemMessage('Skipping data re-entry. ')
                printSystemMessage('Asset Number: ' + Fore.MAGENTA + assetTagInput)
                printSystemMessage('Serial: ' + Fore.MAGENTA + serial)
                printSystemMessage('Model: ' + Fore.MAGENTA + model)
                printSystemMessage('Make: ' + Fore.MAGENTA + make)
                printColoredError('This asset will not be added to Snipe. ' + Fore.RED + 'No model with this name found in system!')
                continue

        
        elif modelInSnipe == True: # If the model is found in SnipeIT, then exit the loop. Then we add the asset with a new ID, and check it out to the user indicated desk.
                snipeUserLoop = False
                printSystemMessage('Model found in SnipeIT!')
                
                printSystemMessage('Asset Number: ' + Fore.MAGENTA + assetTagInput)
                printSystemMessage('Serial: ' + Fore.MAGENTA + serial)
                printSystemMessage('Model: ' + Fore.MAGENTA + model)
                printSystemMessage('Make: ' + Fore.MAGENTA + make)

                printSystemMessage('Adding this asset to SnipeIT...')
                assetID = sendDataToSnipe(assetTagInput, serial, f"Display - {make} {model}", modelID, "") 
                # Since we are only going to be auditing displays, that means we can just hardcode this and always change later

                printSystemMessage("Asset added.")
                printSystemMessage('SnipeIT asset ID set: ' + Fore.MAGENTA + str(assetID))
                printSystemMessage('Checking out asset to selected desk...')
                checkoutAssetToDesk(assetID, deskID)
                printSystemMessage('Checked out asset to desk: ' + Fore.MAGENTA + str(deskID))
                printSystemMessage("Looping program. Remember, if you want to select a different room please restart the program.")
        else:
            raise Exception ("lmao how did this boolean become not one")

def argsCheck():
    args = parse_args()
    commandLineInputValidationCheckBuilding = re.match(r"^([A-Z]|[a-z]){3}?", str(args.b))
    commandLineInputValidationCheckRoom = re.match(r"([0-9]*+[A-Z]|[0-9]*+)", str(args.r))

    try:
        gorp2 = commandLineInputValidationCheckBuilding.group(1)
        gorp = commandLineInputValidationCheckRoom.group(1)
    except IndexError:
        raise Exception("COMMAND LINE INPUTS INVALID. DOES PROBLEM EXIST BETWEEN KEYBOARD AND CHAIR? PROBABLY.")
        return False
    else:
        printSystemMessage('Command line inputs valid. Calling SharePoint login...')
        return True

# Lets preload our assets so as to improve code flow.
if argsCheck() == True:
    load_sp_assets()
else:
    sys.exit()

while 1 == 1:
    main()
