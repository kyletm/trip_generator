"""
adjacency.py

Project: United States Trip File Generation - Module 2
Author: Hill, Garvey, Marocchini
version date: 9/17/2016
Python 3.5

Purpose: This set of methods and classes provides operations on counties
(distance between them, accesing unique identifiers) and reads in the
Journey-to-Work Census and formats it for use in module2.py. All of these
functions are helper functions for module2.py which is
the bulk execution of module 2.

Relies on access to the Jouney to Work Census as well as top level
County Data and County Adjacency files in the WorkFlow folder.

Dependencies: None

Note: All of this is either implicitly done in Module2b/2c.py in
Mufti's version, or not done at all. Much of it was not done, or not
modularized. This provides more clear definitions of the functions and
uses of the data needed for the US trip generation project. All of this
is original.

"""

import random
from ..utils import paths, distance

"""
County (Object) Definition:

Name: Alpha name of county (ex: Mercer County)
StateAbbrev: Two Digit Alpha Abbreviation of State of County
Statecode: Two Digit Numeric FIPS code of State of County
fips_code: 5 Digit numeric FIPS code of county
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
class County:
    def __init__(self, name, stateabbrev, statecode, fips_code, countycode):
        self.name = name
        self.stateabbrev = stateabbrev
        self.statecode = fips_code
        self.fips_code = statecode
        self.countycode = countycode
        self.lat = 0
        self.lon = 0
        self.neighbors = []
        self.num = 0
    def add_neighbor(self, county):
        self.neighbors.append(county.fips_code)
    def get_lat_lon(self):
        return self.lat, self.lon
    def get_num(self):
        return self.num
    def set_lat_lon(self):
        self.lat, self.lon = read_counties(self.fips_code)
    def print_county(self):
        print('County name: ' + str(self.name))
        print('State Abbrev and Code: ' + str(self.stateabbrev) +
              ' ' + str(self.statecode))
        print('fips_code: ' + str(self.fips_code))
        print('County Code: ' + str(self.countycode))
        print('Neighbors: ' + str(self.neighbors))
        print('Lat: ' + str(self.lat))
        print('Lon: ' + str(self.lon))


'RETURN LAT LON OF COUNTY BY fips_code - POP/AREA DATA AVAILABLE'
def read_counties(fips_code):
    fname = paths.WORKFLOW_PATH + '/allCounties.csv'
    with open(fname) as file:
        for line in file:
            splitter = line.split(',')
            if splitter[3] == fips_code:
                return splitter[4], splitter[5]

'RETURN COUNTY OBJECT FOR GIVEN FIPS COUNTY CODE, OFTEN OVERKILL'
def read_data(returncode):
    fname = paths.WORKFLOW_PATH + '/county_adjacency.csv'
    with open(fname) as file:
        count = 0
        for line in file:
            count += 1
            condensed = ''.join(line.split())
            splitter = condensed.split(',')
            countyname = splitter[0]
            stateabbrev = splitter[1][0:2]
            fips_code = splitter[1][2:7]
            statecode = splitter[1][2:4]
            countycode = splitter[1][4:7]
            if splitter[2] != '' and count == 1:
                homecounty = County(countyname, stateabbrev, fips_code, statecode, countycode)
                homename = countyname
            elif splitter[2] != '' and count != 1:
                if returncode == homecounty.fips_code:
                    return homecounty
                homecounty = County(countyname, stateabbrev, fips_code, statecode, countycode)
                homename = countyname
                if splitter[1][7:] != countyname:
                    firstneighborcountyname = splitter[1][7:]
                    nstateabbrev = splitter[2][0:2]
                    nfips_code = splitter[2][2:]
                    nstatecode = splitter[2][2:4]
                    ncountycode = splitter[2][4:]
                    firstneighbor = County(firstneighborcountyname, nstateabbrev,
                                           nfips_code, nstatecode, ncountycode)
                    homecounty.add_neighbor(firstneighbor)
            else:
                neighborcounty = County(countyname, stateabbrev, fips_code, statecode, countycode)
                if countyname != homename:
                    homecounty.add_neighbor(neighborcounty)
        return homecounty

'RETURN DISTANCE BETWEEN TWO COUNTIES BY FIPS CODE'
def get_distance(fips1, fips2):
    lat1, lon1 = read_counties(fips1)
    lat2, lon2 = read_counties(fips2)
    return distance.between_points(lat1, lon1, lat2, lon2)

'READ JOURNEY TO WORK CENSUS'
def read_J2W():
    fname = paths.WORKFLOW_PATH + '/J2W.txt'
    with open(fname) as file:
        allJ2W = []
        for line in file:
            allJ2W.append(line)
        return allJ2W[1:]

'GET ALL COUNTY to COUNTY MOVEMENTS FOR GIVEN COUNTY BY FIPS CODE, LIST OF COUNTY-COUNTY [FIPSHOME, FIPSWORK, #]'
def get_movements(fips_code, data):
    array = []
    for _, j in enumerate(data):
        splitter = j.split(',')
        fips = (splitter[0]+splitter[1])
        if fips == fips_code:
            array.append(splitter)
    newarray = []
    for _, j in enumerate(array):
        newarray.append([j[2]+j[3], j[4]])
    return newarray

'GIVEN ARRAY OF ALL MOVEMENTS FROM A COUNTY TO ALL OTHER WORK COUNTIES'
def create_distribution(movearray):
    newarray = []
    for _, j in enumerate(movearray):
        newarray.append([j[1], j[2]])
    return newarray

'JOURNEY TO WORK FLOW OBJECT AND CLASS OPERATIONS'
class J2WDist:

    def __init__(self, array):
        self.flows = array
        self.items = []
        self.vals = []

    'RETURN LIST OF TUPLES OF COMMUTERS AND WORK COUNTY DESTINATION'
    def get_pairs(self):
        return create_distribution(self.flows)

    'GET TWO LISTS OF (# of Workers Commuting), (Work County) TO CREATE DISTRIBUTION'
    def set_items(self):
        items = []
        values = []
        for j in self.flows:
            items.append(j[0])
            values.append(int(j[1]))
        self.items = items
        self.vals = values

    'GET TOTAL NUMBER OF WORKERS COMMUTING FROM A HOME COUNTY'
    def total_workers(self):
        return sum(self.vals)

    'SELECT A WORK COUNTY BY CREATING CDF'
    def select(self):
        variate = random.random() * sum(self.vals)
        cum = 0.0
        count = 0
        for item in self.items:
            cum += self.vals[count]
            if variate < cum:
                self.vals[count] -= 1
                return item
            count += 1
        return item

    'RETURN THE WORK COUNTY GIVEN RESIDENT, GENDER, AGE, HOUSEHOLD TYPE, and TRAVELER TYPE.'
    def get_work_county_fips(self, homefips, hht, tt):
        if tt in [0, 1, 3, 6] or hht in [2, 3, 4, 5, 7]:
            return -1
        elif tt in [2, 4]:
            return homefips
        else:
            val = self.select()
            if val[0] != '0':
                return -2
            if int(val[1]) > 5:
                return -2
            else:
                return val[1:]