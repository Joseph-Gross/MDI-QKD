import requests
import numpy as np
from urllib.request import urlopen
from requests.models import PreparedRequest
from lxml import html
import re
import time

# User Parameters
integrationTimeValue = 1000 # Integration time in ms, min = 100, max = 10000
pauseTimeValue = 1 # Pause time for motion in s
url = 'http://169.254.69.140:8080/?'

# Accessible parameters
diodeCurrent = "ild"
motor1 = "pm1"
motor2 = "pm2"
integrationTime = "int"
countRate = "cnt"
moterRef = "mref"

def quED_Access(url, action, param, reply = 0, value = []):
    
    """
    Function that accesses QED via an ethernet connection
    Inputs:
        url - IP adddress of instrument (find in settings)
        action - 'set' or 'get'
        param - the parameter to set or get (see below)
        reply - gives response output text, default false, true to debug
        value - value to pass in, default is empty
    Outputs:
        finalData.response.text - raw string response from instrument
        finalData.name - name of channel measured
        finalData.data - data from measured channel
    """
    
    class finalData:
        pass
    
    # For reading values out
    if (value == []):
        params = {'action':action,'param':param}
        req = PreparedRequest()
        req.prepare_url(url, params)
        response = requests.get(req.url)
    
    # For setting values
    else:
        params = {'action':action,'param':param,'value':value}
        req = PreparedRequest()
        req.prepare_url(url, params)
        response = requests.get(req.url)
    
#     if reply == 1:
#         if action == 'set':
#             print(response.text.split("<body>")[1].split("</body>")[0])
#         else:
#             print(response.text)
    
    # For case where we measure count data
    if param == 'cnt':
        rawArray = response.text.split('<br>')
        truncArray = rawArray[2:-2] 
        numElem = len(truncArray)
        dataArray = np.zeros(numElem)
        labelArray  = ['0' for i in range(numElem)]

        for elem in range(numElem-1):
            extractLine = truncArray[elem].split(':')
            labelArray[elem] = (extractLine[0])
            dataArray[elem] = int(extractLine[1])

        finalData.name = labelArray
        finalData.data = dataArray
    
    finalData.response = response
    return finalData


HALF_WAVE_PLATE = 'pm2'
POLARIZER = 'pm1'
COUNT = 'cnt'
INTEGRATION_TIME = 'int'

def reset_setup():
        # Rotate Alice's HWP
        output = quED_Access(url, 'set', HALF_WAVE_PLATE, reply = 1, value = [0])
        # Rotate Bob's HWP
        output = quED_Access(url, 'set', POLARIZER, reply = 1, value = [0])


def QKD_exp(alice_angles, bob_angles, int_time, det_index, num_trials):
    
    assert len(alice_angles) == len(bob_angles), "Incorrect input - Bob and Alice do not match"

    detector_vals = []
    
    # Change the integration time
    output = quED_Access(url, 'set', INTEGRATION_TIME, reply = 1, value = [int_time])
    
    for ind in range(len(alice_angles)):
        ## Preparaing both Alice's and Bob's polarization bases
        alice_angle = alice_angles[ind]
        bob_angle = bob_angles[ind]
        
        print("---------------------")
        print(f"Alice: {alice_angle}")
        print(f"Bob: {bob_angle}")
        
        # Rotate Alice's HWP
        output = quED_Access(url, 'set', HALF_WAVE_PLATE, reply = 1, value = [alice_angle])
        # Rotate Bob's HWP
        output = quED_Access(url, 'set', POLARIZER, reply = 1, value = [bob_angle])
        temp_vals = []
        time.sleep(3)
        for k in range(num_trials):
            # Grab coincidence counts between detector X and Y
            output = quED_Access(url, 'get', COUNT, reply = 0)
            counts = output.data[det_index]
            temp_vals.append(counts)

        detector_vals.append(np.mean(temp_vals))

    return detector_vals