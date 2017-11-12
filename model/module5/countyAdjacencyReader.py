'METHODOLOGY FOR THE HANDLING OF COUNTY OBJECTS, COUNTY LEVEL DATA, JOURNEY TO WORK (COUNTY TO COUNTY)'
'CALCULATING DISTANCE BETWEEN TWO COUNTIES'

"""
countyAdjacencyReader.py

Project: United States Trip File Generation - Module 2
Author: Garvey, Hill, Marocchini
version date: 
Python 3.5

Purpose: This set of methods and classes provides operations on counties (distance between them, accesing unique identifiers)
and reads in the Journey-to-Work Census and formats it for use in employeePatronageReader.py. All of these functions are helper
functions for employeePatronageReader.py which is the bulk execution of module 2.

Relies on access to the Jouney to Work Census as well as top level County Data and County Adjacency files in the WorkFlow folder.

Dependencies: None

Note: All of this is either implicitly done in Module2b/2c.py in Mufti's version, or not done at all. Much of it was not done, or not
modularized. This provides more clear definitions of the functions and uses of the data needed for the US trip generation project. All of
this is original.

"""

"""
County (Object) Definition:

Name: Alpha name of county (ex: Mercer County)
StateAbbrev: Two Digit Alpha Abbreviation of State of County
Statecode: Two Digit Numeric FIPS code of State of County
Fipscode: 5 Digit numeric FIPS code of county
Countycode: 3 Digit numeric FIPS county code
Lat: Latitude point of centroid of county
Lon: Longitutde Point of Centroid of county
Neighbors: All bordering counties of county, by 5 digit FIPS code
Num: Number of neighboring counties

Functions:

add_neighbor: add a neighbor to county by neighbor FIPS code
get_lat_lon: retrieve latitude and longitude point of county
get_num: retrieve number of neighbors
set_lat_lon: set the two points for a county and store (read_counties)
print_county: print all elements of county
"""

import math
import random

class County: 
    def __init__(self, name, stateabbrev, statecode, fipscode, countycode):
        self.name = name
        self.stateabbrev = stateabbrev
        self.statecode = fipscode
        self.fipscode = statecode
        self.countycode = countycode
        self.lat = 0
        self.lon = 0
        self.neighbors = []
        self.num = 0
        self.distanceMatrix = []
    def add_neighbor(self, county):
        self.neighbors.append(county.fipscode)   
    def get_lat_lon(self):
        return self.lat, self.lon
    def get_num(self):
        return self.num
    def set_lat_lon(self):
        self.lat, self.lon = read_counties(self.fipscode)
    def print_county(self):
        print('County name: ' + str(self.name))
        print('State Abbrev and Code: ' + str(self.stateabbrev) + ' ' + str(self.statecode))
        print('FipsCode: ' + str(self.fipscode))
        print('County Code: ' + str(self.countycode))
        print('Neighbors: ' + str(self.neighbors))
        print('Lat: ' + str(self.lat))
        print('Lon: ' + str(self.lon))
        
        
'RETURN LAT LON OF COUNTY BY FIPSCODE - POP/AREA DATA AVAILABLE'    
def read_counties(fipscode):
    'MAIN PATH ON MY COMPUTER TOWARDS FILES OF USE'
    M_PATH = 'D:/Data/Workflow'
    fname = M_PATH + '/allCounties.csv'
    f = open(fname, 'r')
    for line in f:
        splitter = line.split(',')
        if (splitter[3] == fipscode):
            return splitter[4], splitter[5]
        
'RETURN COUNTY OBJECT FOR GIVEN FIPS COUNTY CODE, OFTEN OVERKILL'       
def read_data(returncode):
    'MAIN PATH ON MY COMPUTER TOWARDS FILES OF USE'
    M_PATH = 'D:/Data/Workflow'
    fname = M_PATH + '/county_adjacency.csv'
    f = open(fname, 'rU')
    count = 0
    list1 = []
    printcount = 0
    for line in f:
        count += 1
        condensed = (''.join(line.split()))
        splitter = condensed.split(',')
        countyname = splitter[0]
        stateabbrev = splitter[1][0:2]
        fipscode = splitter[1][2:7]
        statecode = splitter[1][2:4]
        countycode = splitter[1][4:7]
        if (splitter[2] != '') and (count == 1):
            homecounty = County(countyname, stateabbrev, fipscode, statecode, countycode)
            list1.append(homecounty.fipscode)
            homename = countyname
        elif (splitter[2] != '') and (count != 1):
            if (returncode == homecounty.fipscode): return homecounty
            homecounty = County(countyname, stateabbrev, fipscode, statecode, countycode)
            list1.append(homecounty.fipscode)
            homename = countyname
            if (splitter[1][7:] != countyname):
                firstneighborcountyname = splitter[1][7:]
                nstateabbrev = splitter[2][0:2]
                nfipscode = splitter[2][2:]
                nstatecode = splitter[2][2:4]
                ncountycode = splitter[2][4:]
                firstneighbor = County(firstneighborcountyname, nstateabbrev, nfipscode, nstatecode, ncountycode)
                homecounty.add_neighbor(firstneighbor)
        else:
            neighborcounty = County(countyname, stateabbrev, fipscode, statecode, countycode)
            if (countyname != homename):
                homecounty.add_neighbor(neighborcounty)
    return homecounty

'RETURN MILES BETWEEN LATITUDE AND LONGITUDE POINTS '
def distance_between_counties(lat1, lon1, lat2, lon2):
    #degrees_to_radians = math.pi/180.0
    #phi1 = (90.0 - float(lat1))*degrees_to_radians
    #phi2 = (90.0 - float(lat2))*degrees_to_radians
    #theta1 = float(lon1)*degrees_to_radians
    #theta2 = float(lon2)*degrees_to_radians
    #cos = (math.sin(phi1)*math.sin(phi2)*math.cos(theta1 - theta2) + 
    #       math.cos(phi1)*math.cos(phi2))
    #arc = math.acos(cos)
    return ((float(lat1) - float(lat2))**2 + (float(lon1) - float(lon2))**2)
    #return arc * 5000
'RETURN DISTANCE BETWEEN TWO COUNTIES BY FIPS CODE'
def get_distance(fips1, fips2):
    lat1, lon1 = read_counties(fips1)
    lat2, lon2 = read_counties(fips2)
    dist = distance_between_counties(lat1, lon1, lat2, lon2)
    return dist

'READ JOURNEY TO WORK CENSUS'
def read_J2W():
    'MAIN PATH ON MY COMPUTER TOWARDS FILES OF USE'
    M_PATH = 'C:/Data/Workflow'
    fname = M_PATH + '/J2W.txt'
    f = open(fname, 'rU')
    allJ2W = []
    for line in f:
        allJ2W.append(line)
    return allJ2W[1:]

'GET ALL COUNTY to COUNTY MOVEMENTS FOR GIVEN COUNTY BY FIPS CODE, LIST OF COUNTY-COUNTY [FIPSHOME, FIPSWORK, #]'
def get_movements(fipscode, data):
    array = []
    for i, j in enumerate(data):
        splitter = j.split(',')
        fips = (splitter[0]+splitter[1])
        if (fips == fipscode):
            array.append(splitter)
    newarray = []
    for i, j in enumerate(array):
        newarray.append([j[2]+j[3], j[4]])
    return newarray

'GIVEN ARRAY OF ALL MOVEMENTS FROM A COUNTY, GENERATE A DISTRIBUTION WHEREBY'
def create_distribution(movearray):
    newarray = []
    for i, j in enumerate(movearray):
        newarray.append([j[1], j[2]])
    return newarray

'JOURNEY TO WORK FLOW OBJECT AND CLASS OPERATIONS'       
class j2wDist:
    def __init__(self, array):
        self.flows = array
        self.items = []
        self.vals = []
    def get_pairs(self):
        return create_distribution(self.flows)
    def get_items(self):
        items = []
        values = []
        for j in self.flows:
            items.append(j[0])
            values.append(int(j[1]))
        self.items = items
        self.vals = values
        return items, values
    def total_workers(self):
        return sum(self.vals)
    def select(self):
        variate = random.random() * sum(self.vals)
        cum = 0.0
        count = 0
        for it in self.items:
            cum += self.vals[count]
            if variate < cum:
                self.vals[count]-=1
                return it
            count += 1
        return it

#test = read_data('15003')
#test.print_county()
#stlouis = read_data('29510')
#stlouis.print_county()
#for j in stlouis.neighbors:
#    print(get_distance(j, stlouis.fipscode))