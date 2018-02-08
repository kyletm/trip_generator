import math
import random
'----------PATH DEFINITIONS---------------------'
#rootDrive = 'E'
rootFilePath = 'D:/Data/Output/'
inputFileNameSuffix = 'Module4NN2ndRun.csv'
outputFileNameSuffix = 'Module5NN1stRun.csv'

#dataDrive = 'E'
dataRoot = 'D:/Data/'
'-----------------------------------------------'
'Read in County Name to FIPS Code Data'
def read_counties():
    fname = dataRoot + '/WorkFlow/allCounties.csv'
    namedata = []
    with open(fname) as f:
        for line in f:
            splitter = line.split(',')
            namedata.append([splitter[3], splitter[6].split(' ')])
    return namedata  

'Match County Name from EMP file to County Name in FIPS Related Data'
def lookup_name(countyname, code, namedata):
    for j in namedata:

        countyname = countyname.strip('"')
        splitter = countyname.split(' ')
        #print(code)
        #print('countyname',countyname)
        #print('splitter',splitter)
        #print('splitter 0',splitter[0])
        if (splitter[0] == j[1][0]) and (len(splitter) == 1):
            if len(j[0]) == 4:
                j[0] = '0' + j[0]
            if (j[0][0:2] == code):
                return j[0]
        elif (splitter[0] == j[1][0]) and (splitter[1] == j[1][1]) and (len(splitter)==2):
            if len(j[0]) == 4:
                j[0] = '0' + j[0]
            if (j[0][0:2] == code):
                return j[0]
        elif (len(j[1]) == 3) and (len(splitter) > 2):
            if (splitter[0] == j[1][0]) and (splitter[1] == j[1][1]) and (splitter[2] == j[1][2]):
                if len(j[0]) == 4:
                    j[0] = '0' + j[0]
                if (j[0][0:2] == code):   
                    return j[0]
        elif (len(j[1]) > 3) and (len(splitter) > 1):
            if (splitter[0] == j[1][0]) and (splitter[1] == j[1][1]):
                if len(j[0]) == 4:
                    j[0] = '0' + j[0]
                if (j[0][0:2] == code):
                    return j[0]


'Create Cumulative Distribution'
def cdf(weights):
    total=sum(weights); result=[]; cumsum=0
    if total == 0:
        return random.randint(0, len(weights) - 1)
    for w in weights:
        cumsum+=w
        result.append(cumsum/total)
    return result

'RETURN MILES BETWEEN LATITUDE AND LONGITUDE POINTS '
def distance_between_points_normal(lat1, lon1, lat2, lon2):
    if lat1 == lat2 and lon1 == lon2:
        return 10000000
    degrees_to_radians = math.pi/180.0
    phi1 = (90.0 - float(lat1))*degrees_to_radians
    try:
        phi2 = (90.0 - float(lat2))*degrees_to_radians
    except ValueError:
        return 1000
    theta1 = float(lon1)*degrees_to_radians
    theta2 = float(lon2)*degrees_to_radians
    cos = (math.sin(phi1)*math.sin(phi2)*math.cos(theta1 - theta2) + 
           math.cos(phi1)*math.cos(phi2))
    arc = math.acos(cos)
    distance =  arc * 3963.167
    # Prevents close trips from dominating?
    if distance < 0.5:
        return 10000.0
    else:
        return distance

'RETURN MILES BETWEEN LATITUDE AND LONGITUDE POINTS '
def distance_between_points_w2w(lat1, lon1, lat2, lon2):
    if lat1 == lat2 and lon1 == lon2:
        return 10000000
    degrees_to_radians = math.pi/180.0
    phi1 = (90.0 - float(lat1))*degrees_to_radians
    phi2 = (90.0 - float(lat2))*degrees_to_radians
    theta1 = float(lon1)*degrees_to_radians
    theta2 = float(lon2)*degrees_to_radians
    cos = (math.sin(phi1)*math.sin(phi2)*math.cos(theta1 - theta2) + 
           math.cos(phi1)*math.cos(phi2))
    arc = math.acos(cos)
    distance =  arc * 3963.167
    # Prevents far trips from dominatng?
    if distance > 5:
        return 100000.0
    else:
        return distance
        

'Match State Code to State Abbrev'
def match_code_abbrev(states, code):
    for i, j in enumerate(states):
        splitter = j.split(',')
        if splitter[2] == code:
            return splitter[1]

'READ IN ASCIATED STATE ABBREVIATIONS WITH STATE FIPS CODES'
def read_states():
    stateFileLocation = dataRoot
    fname = stateFileLocation + 'ListofStates.csv'
    with open(fname) as f:
        lines = f.read().splitlines()
    return lines