'''
module1.py

Project: United States Trip File Generation - Module 1
Author: A.P. Hill Wyrough
version date: 3/15/2014
Python 3.3

Purpose: This is a procedural method to introduce mode split into the model. It reads already processed files by Module 5 and revises all the possible
trip patterns that should qualify for long distance air travel by assigning the resident a originating airport, a destination airport, and a hotel
near his or her end-point destination.

Relies on FAA database. 

Dependencies: None

          '''

'----------PATH DEFINITIONS---------------------'
#rootDrive = 'E'
rootFilePath = 'D:/Data/Output/'
inputFileNameSuffix = 'Module5NN1stRun.csv'
outputFileNameSuffix = 'Module5NN1stRun_MODAL.csv'

#dataDrive = 'E'
dataRoot = 'D:/Data/'
'-----------------------------------------------'
import csv
import math
import random
from datetime import datetime
import classDumpModule5
import countyAdjacencyReader
import bisect
from os import listdir
from os.path import isfile, join
counties = []
stateCode =''
'Read All Airports and Create Distribution Where Land-Area Is Attraction'
'Convert LatLon to Decimal Lat Lon'
def read_airports(stateabbrev):
    global stateCode
    filepath = dataRoot + 'WorkFlow/airports.csv'
    f = open(filepath, 'r+')
    reader = csv.reader(f, delimiter=',')
    stateAirports = []
    weights = []
    for row in reader:
        if row[6] == stateabbrev and row[1] == 'AIRPORT':
            lat = row[22].split('-')
            lon = row[24].split('-')
            realLat = float(lat[0]) + float(lat[1])/60.0 + float(lat[2][0:6])/3600.0
            realLon = -(float(lon[0]) + float(lon[1])/60.0 + float(lon[2][0:6])/3600.0)
            landArea = row[35]
            if landArea == '': landArea = 10
            weights.append(float(landArea))
            stateAirports.append([row[6], row[8], row[11], landArea, str(realLat), str(realLon), classDumpModule5.lookup_name(row[8],stateCode, counties)])
    return stateAirports, weights
          
'Send Traveler to International Destination'
'Return Revised Trip Tour'
def send_to_international(lat, lon, person, stateAirports):
    dist = [float(j[3])/(distance_between_points_normal(lat, lon, j[4], j[5])**2) for j in stateAirports]
    weights = classDumpModule5.cdf(dist)
    split = random.random()
    idx = bisect.bisect(weights, split)
    airport = stateAirports[idx]
    
    'Create Trip Tour'
    person[9] = 'W*'
    person[15] = 'W*'
    person[16] = 'H'
    person[17] = 'N'
    person[18] = airport[2]
    person[21] = airport[4]
    person[22] = airport[5]
    
    person[23] = 'N'
    person[24] = 'W*'
    return person

'Send Traveler to Work on a Plane, return revised trip sequence'
def take_a_plane(person, lat, lon, stateAirports):
    global counties
    global states
    dist = [(float(j[3])**2)/(distance_between_points_normal(lat, lon, j[4], j[5])**2) for j in stateAirports]
    weights = classDumpModule5.cdf(dist)
    split = random.random()
    idx = bisect.bisect(weights, split)
    Firstairport = stateAirports[idx]
    Secondairport = find_destination_airport(person, classDumpModule5.match_code_abbrev(states, person[19][0:2]))
    'Adjust Trips: 1st - to airport, 2nd - airport to work 3rd - other trip 4th - to hotel'
    
    'Change Node 4 to Real Work Place'
    person[31] = 'W'
    person[32] = 'A'
    person[33] = 'O'
    person[34] = person[18]
    person[35] = person[19]
    person[36] = person[20]
    person[37] = person[21]
    person[38] = person[22]
    'Change Node 2 to First Airport'
    person[15] = 'A'
    person[16] = 'H'
    person[17] = 'A'
    person[18] = Firstairport[2]
    person[19] = Firstairport[6]
    person[20] = Firstairport[4]
    person[21] = Firstairport[5]
    person[22] = 'Airport'
    person[9] = 'A'
    'Change Node 3 to Second Airport'
    person[23] = 'A'
    person[24] = 'A'
    person[25] = 'W'
    person[26] = Secondairport[2]
    person[27] = Secondairport[6]
    person[28] = Secondairport[4]
    person[29] = Secondairport[5]
    person[30] = 'Airport'
    'Change Node 5 to Hotel'
    hotels = find_hotels(person[35])
    'Select Hotel'
    dist = [float(j[12]) / (distance_between_points_normal(person[36], person[37], j[15], j[16])**2) for j in hotels]
    weights = classDumpModule5.cdf(dist)
    split = random.random()
    idx = bisect.bisect(weights, split)
    hotel = hotels[idx]
    
    person[39] = 'O'
    person[40] = 'A'
    person[41] = 'N'
    person[42] = hotel[0]
    person[43] = person[35]
    person[44] = hotel[len(hotel) - 2]
    person[45] = hotel[len(hotel) - 1].strip('\n')
    person[46] = '72'
    
    return person
 
def find_destination_airport(person, destinationCounty):
    destinationState = destinationCounty[0:2]
    destinationAirports, weights = read_airports(destinationState)
    dist = [float(j[3]) / (distance_between_points_normal(person[20], person[21], j[4], j[5])**2) for j in destinationAirports]
    weights = classDumpModule5.cdf(dist)
    split = random.random()
    idx = bisect.bisect(weights, split)
    airport = destinationAirports[idx]
    return airport

def find_hotels(fips):
    countyObject = countyAdjacencyReader.read_data(fips)
    allHotels = []
    # Handle neighborless counties, e.g. Hawaii
    if not countyObject.neighbors:
        hotels, stores = get_hotels(fips)
        [allHotels.append(j) for j in hotels]
        return allHotels
    else:
        for j in countyObject.neighbors:
            hotels, stores = get_hotels(j)
            [allHotels.append(j) for j in hotels]
        return allHotels
 
'Return List of Hotels and Stores in FIPS County'
def get_hotels(fips):
    if len(fips) == 4:
        fips = '0' + str(fips)
    if fips == '15005': 
        split = random.random(); 
        if split > 0.5: fips = '15003'
        else: fips = '15007'
    states = classDumpModule5.read_states()
    abbrev = classDumpModule5.match_code_abbrev(states, fips[0:2])
    filepath = dataRoot + 'Employment/CountyEmployeeFiles/' + abbrev + '/' + fips + '_' + abbrev + '_EmpPatFile.csv'
    f = open(filepath, 'r+')
    reader = csv.reader(f, delimiter=',')
    stores = []; hotels = []
    for row in reader:
        code = row[8][0:2]
        if code == '72' or code == '62':
            stores.append(row)
        if row[8][0:4] == '7211':
            hotels.append(row)
    return hotels, stores
   
def distance_between_points_normal(lat1, lon1, lat2, lon2):
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
    if distance == 0:
        distance = 0.1
    return distance  
    
def file_len(fname):
    with open('D:/Data/Output/Module5/' + fname) as f:
        for i, l in enumerate(f):
            pass
    return i + 1
    
def executive1(state, stateabbrev):
    mypath = 'D:/Data/Output/Module5/' + state
    onlyfiles = [f for f in listdir(mypath) if isfile(join(mypath, f))]
    filesOfInterest = [f for f in onlyfiles if state in f]
    totalCount = 0
    filesSplit = [f.split('_') for f in filesOfInterest]
    for f in filesSplit:
        print(f[1])
        executive(f[0],stateabbrev,f[1])
    
    
def executive(state, stateabbrev, county):
    global counties
    global stateCode
    global states
    stateCode = county[0:2]
    states = classDumpModule5.read_states()
    'Module 5 Input Path'
    fileLocation = rootFilePath + 'Module5/' + state + '/' + state + '_' + county + '_' +  inputFileNameSuffix
    'Module 5 MODAL Output Path'
    outputLocation = rootFilePath + 'Module5MODE/' + state + '_' + county + '_' + outputFileNameSuffix
    startTime = datetime.now()
    'Open File'
    f = open(fileLocation, 'r')
    reader = csv.reader(f, delimiter=',')
    out = open(outputLocation, 'w+', encoding='utf8')
    personWriter = csv.writer(out, delimiter=',', lineterminator='\n')
    counties = classDumpModule5.read_counties()
    stateAirports, weights = read_airports(stateabbrev)
    count = -1
    pCount = 0
    
    for p in reader:
        if count == -1: personWriter.writerow(p); count+=1; continue
        if 'Activity Pattern' in p[6]:
            continue
        if p[6] == '-5': 
            lat = (p[12])
            lon = (p[13])
            newP = send_to_international(lat, lon, p, stateAirports); 
            personWriter.writerow(newP)
        elif p[9] == 'W':
            if len(p[19]) == 4:
                p[19] = '0' + p[19]
            lat = (p[12])
            lon = (p[13])
            workLat = float(p[20])
            workLon = float(p[21])
            distanceFirstTrip = distance_between_points_normal(lat, lon, workLat, workLon)
            
            if distanceFirstTrip > 200.0:
                newP = take_a_plane(p, lat, lon, stateAirports)
                personWriter.writerow(newP)
        else:
            personWriter.writerow(p)
        pCount+=1
        if pCount % 10000 == 0:
            print(str(pCount) + ' Residents Completed and taken this much time: ' + str(datetime.now()-startTime))
    
    print(state + " " + county + " took this much time: " + str(datetime.now()-startTime))
#executive1('Texas','TX')
executive('Texas','TX','48021')