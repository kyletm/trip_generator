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
        stateabbrev (str): 2 Digit Alpha Abbreviation of State of County.
        statecode (str): 2 Digit Numeric FIPS code of State of County.
        fips (str): 5 Digit numeric FIPS code of county.
        countycode (str): 3 Digit numeric FIPS county code.
        lat (float): Latitude point of centroid of county.
        lon (float): Longitutde Point of centroid of county.
        neighbors (list): All bordering counties of county, by 5 digit FIPS code.
        num (int): Number of neighboring counties.
    """
    
    def __init__(self, name, stateabbrev, fips, statecode, countycode):
        """Initializes all county data.
    
        Inputs: 
            See County class docstring.
        """
        self.name = name
        self.stateabbrev = stateabbrev
        self.statecode = statecode
        self.fips = fips
        self.countycode = countycode
        self._lat, self._lon = read_counties(self.fips)
        self.neighbors = []
        self.num = 0
        
    def add_neighbor(self, county):
        """Adds neighboring county to county list.
    
        Inputs: 
            county (County): A county object.
        """
        self.neighbors.append(county.fips)
        
    @property    
    def coords(self):
        """Get lat, lon county centroid tuple.
    
        Returns: 
            lat (float): Latitude point of centroid of county.
            lon (float): Longitutde Point of centroid of county.
        """
        return self._lat, self._lon
        
    def get_num(self):
        """Get number of neighboring counties.
    
        Returns: 
            num (int): Number of neighboring counties.
        """
        return self.num        
        
    def print_county(self):
        """Print county information."""
        print('County name: ' + str(self.name))
        print('State Abbrev and Code: ' + str(self.stateabbrev) +
              ' ' + str(self.statecode))
        print('fips: ' + str(self.fips))
        print('County Code: ' + str(self.countycode))
        print('Neighbors: ' + str(self.neighbors))
        print('Lat: ' + str(self.coords))
        print('Lon: ' + str(self.lon))
        
def read_counties(fips):
    """Get lat, lon county centroid tuple by FIPS code.
    
    Inputs: 
        fips (str): County FIPS code.

    Returns: 
        lat (float): Latitude point of centroid of county.
        lon (float): Longitutde Point of centroid of county.
    """
    fname = paths.WORKFLOW + '/allCounties.csv'
    with open(fname) as file:
        for line in file:
            splitter = line.split(',')
            if splitter[3] == fips:
                return splitter[4], splitter[5]
        
def read_data(fips):
    file_path = paths.WORKFLOW + 'county_adjacency2010.csv'
    with open(file_path) as read:
        reader = reading.csv_reader(read)
        neighbors = []
        for row in reader:
            if row[1] == fips:
                neighbors.append(row)
    neighbor_counties = []
    home_county = None
    for neighbor in neighbors:
        county_name, state_abbrev = neighbor[2].split(', ')
        curr_fips = neighbor[3]
        state_code, county_code = curr_fips[0:2], curr_fips[2:5]
        if neighbor[3] == fips:
            home_county = County(county_name, state_abbrev, curr_fips, state_code, county_code)
        else:
            neighbor_counties.append(County(county_name, state_abbrev, curr_fips, state_code, county_code))
    for neighbor in neighbor_counties:
        home_county.add_neighbor(neighbor)
    return home_county

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
        
def read_j2w():
    """Read Journey to Work Census.
    
    Returns: 
        J2W (list): J2W census data.
    """
    
    j2w_data = dict()
    with open(paths.WORKFLOW + '/J2W.txt') as read:
        reader = reading.csv_reader(read)
        next(reader)
        for row in reader:
            curr_fips = row[0] + row[1]
            if curr_fips not in j2w_data:
                j2w_data[curr_fips] = dict()
            dest_fips = row[2] + row[3]
            movements = int(row[4])
            j2w_data[curr_fips][dest_fips] = movements
    return j2w_data
    
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

    def __init__(self, j2w_data, curr_fips):
        """Initializes all J2W data.
    
        Inputs: 
            See J2WDist class docstring.
        """
        self.movements = j2w_data[curr_fips]
        self.counties, self.workers = self.set_counties()

    def set_counties(self):
        """Set county and worker movement lists for a county."""
        counties = []
        workers = []
        for county, worker in self.movements.items():
            counties.append(county)
            workers.append(worker)
        return counties, workers

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

    def get_work_county_fips(self, home_fips, household_type, traveler_type):
        """Select a work county for a worker to commute to.
        
        Returns:
            county (str): A county FIPS code.
        """
        if traveler_type in (0, 1, 3, 6) or household_type in (2, 3, 4, 5, 7):
            return -1
        elif traveler_type in (2, 4):
            return home_fips
        else:
            county = self.select()
            if county[0] != '0':
                return -2
            if int(county[1]) > 5:
                return -2
            else:
                return county[1:]