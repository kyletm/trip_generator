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
from ..utils import paths, reading, distance

class County:
    """County data encapsulation and access functionality.  
    
    Attributes:    
        name (str): Alpha name of county (ex: Mercer County).
        stateabbrev (str): Two Digit Alpha Abbreviation of State of County.
        statecode (str): Two Digit Numeric FIPS code of State of County.
        fips_code (str): 5 Digit numeric FIPS code of county.
        countycode (str): 3 Digit numeric FIPS county code.
        lat (float): Latitude point of centroid of county.
        lon (float): Longitutde Point of centroid of county.
        neighbors (list): All bordering counties of county, by 5 digit FIPS code.
        num (int): Number of neighboring counties.
    """
    
    def __init__(self, name, stateabbrev, statecode, fips_code, countycode):
        """Initializes all county data.
    
        Inputs: 
            See County class docstring.
        """
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
        """Adds neighboring county to county list.
    
        Inputs: 
            county (County): A county object.
        """
        self.neighbors.append(county.fips_code)
        
    def get_lat_lon(self):
        """Get lat, lon county centroid tuple.
    
        Returns: 
            lat (float): Latitude point of centroid of county.
            lon (float): Longitutde Point of centroid of county.
        """
        return self.lat, self.lon
        
    def get_num(self):
        """Get number of neighboring counties.
    
        Returns: 
            num (int): Number of neighboring counties.
        """
        return self.num
        
    def set_lat_lon(self):
        """Set lat, lon county centroid tuple."""
        self.lat, self.lon = read_counties(self.fips_code)
        
    def print_county(self):
        """Print county information."""
        print('County name: ' + str(self.name))
        print('State Abbrev and Code: ' + str(self.stateabbrev) +
              ' ' + str(self.statecode))
        print('fips_code: ' + str(self.fips_code))
        print('County Code: ' + str(self.countycode))
        print('Neighbors: ' + str(self.neighbors))
        print('Lat: ' + str(self.lat))
        print('Lon: ' + str(self.lon))
        
def read_counties(fips_code):
    """Get lat, lon county centroid tuple by FIPS code.
    
    Inputs: 
        fips_code (str): County FIPS code.

    Returns: 
        lat (float): Latitude point of centroid of county.
        lon (float): Longitutde Point of centroid of county.
    """
    fname = paths.WORKFLOW_PATH + '/allCounties.csv'
    with open(fname) as file:
        for line in file:
            splitraveler_typeer = line.split(',')
            if splitraveler_typeer[3] == fips_code:
                return splitraveler_typeer[4], splitraveler_typeer[5]

def read_data(fips_code):
    """Get all county information by FIPS code.
    
    Inputs: 
        fips_code (str): County FIPS code.

    Returns: 
        homecounty (County): County object for that FIPS code.
    """
    fname = paths.WORKFLOW_PATH + '/county_adjacency.csv'
    with open(fname) as file:
        count = 0
        for line in file:
            count += 1
            condensed = ''.join(line.split())
            splitraveler_typeer = condensed.split(',')
            countyname = splitraveler_typeer[0]
            stateabbrev = splitraveler_typeer[1][0:2]
            fips_code = splitraveler_typeer[1][2:7]
            statecode = splitraveler_typeer[1][2:4]
            countycode = splitraveler_typeer[1][4:7]
            if splitraveler_typeer[2] != '' and count == 1:
                homecounty = County(countyname, stateabbrev, fips_code, statecode, countycode)
                homename = countyname
            elif splitraveler_typeer[2] != '' and count != 1:
                if fips_code == homecounty.fips_code:
                    return homecounty
                homecounty = County(countyname, stateabbrev, fips_code, statecode, countycode)
                homename = countyname
                if splitraveler_typeer[1][7:] != countyname:
                    firstneighborcountyname = splitraveler_typeer[1][7:]
                    nstateabbrev = splitraveler_typeer[2][0:2]
                    nfips_code = splitraveler_typeer[2][2:]
                    nstatecode = splitraveler_typeer[2][2:4]
                    ncountycode = splitraveler_typeer[2][4:]
                    firstneighbor = County(firstneighborcountyname, nstateabbrev,
                                           nfips_code, nstatecode, ncountycode)
                    homecounty.add_neighbor(firstneighbor)
            else:
                neighborcounty = County(countyname, stateabbrev, fips_code, statecode, countycode)
                if countyname != homename:
                    homecounty.add_neighbor(neighborcounty)
        return homecounty

def get_distance(fips1, fips2):
    """Get distance between two counties.
    
    Inputs: 
        fips1 (str): A county FIPS code.
        fips2 (str): A county FIPS code.

    Returns: 
        distance (float): Distance between centroids of counties identified
            by inputraveler_typeed FIPS codes.
    """
    lat1, lon1 = read_counties(fips1)
    lat2, lon2 = read_counties(fips2)
    return distance.between_points(lat1, lon1, lat2, lon2)

def read_J2W():
    """Read Journey to Work Census.
    
    Returns: 
        J2W (list): J2W census data.
    """
    fname = paths.WORKFLOW_PATH + '/J2W.txt'
    with open(fname) as file:
        allJ2W = reading.file_reader(file)
        return allJ2W[1:]
        
def get_movements(fips_code, j2w_data):
    """Get all county-to-county movements for a given county.
    
    Inputs: 
        fips_code (str): A county FIPS code.
        jw2_data (list): J2W Census Data.

    Returns: 
        movements (list): Each element is a county-county list with first
            element the FIPS code of the movement of employees, second element
            the number of employees moving from the fips_code input argument
            to the first element fips code in movements.
            e.g. [056005, 803] = "803 workers moving from fips_code to fips code "056005"
    """
    array = []
    for row in j2w_data:
        splitraveler_typeer = row.split(',')
        fips = (splitraveler_typeer[0]+splitraveler_typeer[1])
        if fips == fips_code:
            array.append(splitraveler_typeer)
    movements = []
    for county_data in array:
        movements.append([county_data[2]+county_data[3], county_data[4]])
    return movements

'JOURNEY TO WORK FLOW OBJECT AND CLASS OPERATIONS'
class J2WDist:
    """Journey to Work data encapsulation.  
    
    Attributes:    
        movements (list): Movements from adjacency.get_movements().
        counties (list): All FIPS codes that workers are commuting to.
        workers (list): Number of workers that are commuting from a county 
            to another county. The indices in counties correlate to the
            indices in workers, so the element from workers[0] describes
            the number of workers moving from a county to the county identified
            in counties[0].
    """    

    def __init__(self, array):
        """Initializes all J2W data.
    
        Inputs: 
            See J2WDist class docstring.
        """
        self.movements = array
        self.counties = []
        self.workers = []

    def set_counties(self):
        """Set county and worker movement lists for a county."""
        counties = []
        workers = []
        for j in self.movements:
            counties.append(j[0])
            workers.append(int(j[1]))
        self.counties = counties
        self.workers = workers

    def total_workers(self):
        """Get total number of workers commuting out of a county."""
        return sum(self.workers)

    def select(self):
        """Randomly select a work county from the list of commutable counties.
        
        Returns:
            county (str): A county FIPS code.
        """
        variate = random.random() * sum(self.workers)
        cum = 0.0
        count = 0
        for county in self.counties:
            cum += self.workers[count]
            if variate < cum:
                self.workers[count] -= 1
                return county
            count += 1
        return county

    def get_work_county_fips(self, homefips, household_type, traveler_type):
        """Select a work county for a worker to commute to.
        
        Returns:
            county (str): A county FIPS code.
        """
        if traveler_type in [0, 1, 3, 6] or household_type in [2, 3, 4, 5, 7]:
            return -1
        elif traveler_type in [2, 4]:
            return homefips
        else:
            county = self.select()
            if county[0] != '0':
                return -2
            if int(county[1]) > 5:
                return -2
            else:
                return county[1:]