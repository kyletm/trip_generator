'''
schoolCounty.py

Project: United States Trip File Generation - Module 3
Author: Garvey, Marocchini
version date: 9/17/2016
Python 3.5

Purpose: This is the helper module for module3, which assigns each student a proper place of school. This module creates and designs a school County
object that houses all the enrollment data for a particular county and its geographical neighbors. It provides methods to select a county of schooling,
and then a particular school given that county and type of school.

Notes: 
'''

import os
import sys
import random
import bisect
from ..module2 import adjacency
from . import convertToFIPS, module3classdump
from ..utils import core, distance, paths, reading, writing

'------------------------GLOBAL DATA------------------------'
'File Location of School Data'

stateFourYearList = None; stateTwoYearList = None; stateNonDegList = None
stateFourYearDist = None; stateTwoYearDist = None; stateNonDegDist = None

'-----------------------------------------------------------'

'SchoolCounty Object: An object for housing the entire school data for a particular county, and points to its neighbors. '
class schoolAssigner:
    
    # TODO - Fix confusion with State School and complete args
    def __init__(self, fips, unweighted = 1, complete = 1, post_sec_schools = None, centroid = None):
        'Initialize County Geography'
        self.fips = fips
        self.county = adjacency.read_data(fips)
        self.county.set_lat_lon()
        'Create Distributions for:'
        '1.) public schools (nothing right now ... just choosing the closest public school without doing any pre-processing ahead of time)'
        self.elem_public, self.mid_public, self.high_public = read_public_schools(fips)
        if self.mid_public is None: 
            self.mid_public = self.high_public
        self.dist_pub_elem, self.dist_pub_mid, self.dist_pub_high = self.assemble_public_county_dist(unweighted, centroid)
        'CHOOSE THE NEAREST PUBLIC SCHOOL'
        if complete:
            '2.) private school distributions by age demographic within aa partic '
            self.elem_private, self.mid_private, self.high_private = read_private_schools(fips)
            self.dist_priv_elem, self.dist_priv_middle, self.dist_priv_high = self.assemble_private_county_dist()
            '3.) post-secondary education by demographic within a county'
            'DONE ON THE STATE LEVEL'
            self.post_sec_schools = post_sec_schools

    def assemble_public_county_dist(self, unweighted, centroid):
        if unweighted:
            self.dist_pub_elem = [int(school[5]) for school in self.elem_public]
            self.dist_pub_mid = [int(school[5]) for school in self.mid_public]
            self.dist_pub_high = [int(school[5]) for school in self.high_public]
        else:
            if centroid is None:
                raise ValueError('Must have non-null centroid to weight against')
            lat, lon = centroid[0], centroid[1]
            dist_pub_elem = [int(school[5]) 
            / (distance.between_points(lat, lon, float(school[6]), float(school[7])))**2 
            for school in self.elem_public]
            dist_pub_mid = [int(school[5]) 
            / (distance.between_points(lat, lon, float(school[6]), float(school[7])))**2
            for school in self.mid_public]
            dist_pub_high = [int(school[5]) 
            / (distance.between_points(lat, lon, float(school[6]), float(school[7])))**2
            for school in self.high_public]
        return core.cdf(dist_pub_elem), core.cdf(dist_pub_mid), core.cdf(dist_pub_high)

    def assemble_private_county_dist(self):
         self.dist_priv_elem = core.cdf([int(school[7]) for school in self.elem_private])
         self.dist_priv_mid = core.cdf([int(school[7]) for school in self.mid_private])
         self.dist_priv_high = core.cdf([int(school[7]) for school in self.high_private])

    'Select an Individual School For a Student' 
    def select_school_by_type(self, type1, type2, homelat, homelon):
        global noSchoolCount
        assert type2 != 'no'
        x = random.random()
        school = None
        if type2 == 'public':
            school = self.select_public_schools(type1, homelat, homelon)
        elif type2 == 'private':
            # We change the type from private to public if no private
            # schools exist due to a lack of data
            school, type2 = self.select_private_schools(type1, type2, homelat, homelon)
        else:
            if type2 == 'four year':
                idx=bisect.bisect(self.post_sec_schools.bach_or_grad_dist, x)
                school = self.post_sec_schools.bach_or_grad_schools[idx]
            elif type2 == 'two year':
                idx=bisect.bisect(self.post_sec_schools.associates_dist,x)
                school = self.post_sec_schools.associates_schools[idx]
            elif type2 == 'non deg':
                idx=bisect.bisect(self.post_sec_schools.non_degree_dist,x)
                school = self.post_sec_schools.non_degree_schools[idx]
            else:
                raise ValueError('Invalid Type2 for Current Student')
        return school, type2

    def select_public_schools(self, type1, homelat, homelon):
        # Returns the public school, given a school type and a latitude/longitude
        # For the home
        global noSchoolCount
        x=random.random()
        if type1 == 'elem':
           idx=bisect.bisect(self.dist_pub_elem,x)
           try:
               school = self.elem_public[idx]
           except:
               noSchoolCount += 1
               school = select_neighoboring_public_school(self.county.neighbors, 1, homelat, homelon, x)
        elif type1 == 'mid':
           idx=bisect.bisect(self.dist_pub_mid,x)
           try:
               school = self.mid_public[idx]
           except:
               noSchoolCount += 1
               school = select_neighoboring_public_school(self.county.neighbors, 2, homelat, homelon, x)
        elif type1 == 'high':
           idx=bisect.bisect(self.dist_pub_high,x)
           try:
               school = self.high_public[idx]
           except:
               noSchoolCount += 1
               school = select_neighoboring_public_school(self.county.neighbors, 3, homelat, homelon, x)
        else:
            raise ValueError('Invalid Type1 for Current Student')
        return school

    def select_private_schools(self, type1, type2, homelat, homelon):
        # Returns the public school, given a school type and a latitude/longitude
        # For the home. If there are no suitable private schools, a public
        # school is selected.
        x=random.random()
        if type1 == 'elem': 
           if self.dist_priv_elem is None:
               type2 = 'public'
               return self.select_public_schools(type1, homelat, homelon), type2
           idx = bisect.bisect(self.dist_priv_elem,x)
           school = self.elem_private[idx]
        elif type1 == 'mid':
           if self.dist_priv_mid is None:
               type2 = 'public'
               return self.select_public_schools(type1, homelat, homelon), type2
           idx = bisect.bisect(self.dist_priv_middle,x)
           school = self.mid_private[idx]
        elif type1 == 'high':
           if self.dist_priv_high is None:
              type2 = 'public'
              return self.select_public_schools(type1, homelat, homelon), type2
           idx=bisect.bisect(self.dist_priv_high,x)
           school = self.high_private[idx]
        else:
            raise ValueError('Invalid Type1 for Current Student')
        return school, type2



'Initialize Private Schools For County'
def read_private_schools(fips):
     input_path = paths.SCHOOL_DBASE + 'CountyPrivateSchools/'
     elem_private = []
     high_private = []
     try:
         with open(input_path + fips + 'Private.csv') as read:
             elem_private_reader = reading.csv_reader(read)
             for row in elem_private_reader:
                 row[7] = int(row[7])
                 if row[6] == '1':
                     elem_private.append(row)
                 elif row[6] == '2' or row[6] == '3':
                     high_private.append(row)
                 else:
                     raise ValueError('School does not have a code that lies in {1, 2, 3}')
     except IOError:
         # File not found, no data available
         pass
     # We have no data for mid_private, so mid_private = high_private
     return elem_private, high_private, high_private    

'Initialize Public Schools For County'
def read_public_schools(fips):
    elem_file = paths.SCHOOL_DBASE + 'CountyPublicSchools/' +  'Elem/'
    mid_file = paths.SCHOOL_DBASE + 'CountyPublicSchools/' +  'Mid/'
    high_file = paths.SCHOOL_DBASE + 'CountyPublicSchools/' +  'High/'
    elem_public = []
    mid_public = []
    high_public = []
    try:
        with open(elem_file + fips + 'Elem.csv') as read:
            elem_public_reader = reading.csv_reader(read)
            for row in elem_public_reader:
                row[5] = int(row[5])
                elem_public.append(row)
    except IOError:
        # File not found, no data available
        pass
    try:
        with open(mid_file + fips + 'Mid.csv') as read:
            mid_public_reader = reading.csv_reader(read)
            for row in mid_public_reader:
                row[5] = int(row[5])
                mid_public.append(row)
    except IOError:
        # File not found, no data available
        pass
    try:
        with open(high_file + fips + 'High.csv') as read:
            high_public_reader = reading.csv_reader(read)
            for row in high_public_reader:
                row[5] = int(row[5])
                high_public.append(row)
    except IOError:
        # File not found, no data available
        pass
    return elem_public, mid_public, high_public

'Initialize Post Secondary Schools for county'
def read_post_sec_schools(state, state_abbrev):
    school_path = paths.SCHOOL_DBASE + 'PostSecSchoolsByCounty/' + state_abbrev + '/'
    non_degree_schools = []; associates_schools = []; bach_or_grad_schools = []
    for file_name in os.listdir(school_path):
        file = school_path + file_name
        if file.endswith('CommunityCollege.csv'):
            read_school_file(file, associates_schools)
        elif file.endswith('University.csv'):
            read_school_file(file, bach_or_grad_schools)
        elif file.endswith('NonDegree.csv'):
            read_school_file(file, non_degree_schools)
    return bach_or_grad_schools, associates_schools, non_degree_schools

def read_school_file(file_name, school_type):
    with open(file_name) as read:
        reader = reading.csv_reader(read)
        for row in reader: 
            school_type.append(row)

class StateSchoolAssigner:
    
    def __init__(self, state, state_abbrev):
        bach_or_grad, associates, non_degree = read_post_sec_schools(state, state_abbrev)
        self.bach_or_grad_schools = bach_or_grad
        self.associates_schools = associates
        self.non_degree_schools = non_degree
        self.assemble_post_sec_dist()
        
    'Use employment at Universities as a proxy for school attendance'
    def assemble_post_sec_dist(self):
        bach_or_grad_employment = [int(row[-4]) for row in self.bach_or_grad_schools]
        associates_employment = [int(row[-4]) for row in self.associates_schools]
        non_degree_employment = [int(row[-4]) for row in self.non_degree_schools]
        self.bach_or_grad_dist = core.cdf(bach_or_grad_employment)
        self.associates_dist = core.cdf(associates_employment)
        self.non_degree_dist = core.cdf(non_degree_employment) 

'Return the index of the best public school'
def _Nearest_PublicSchool(homelat, homelon, listPublicSchools, returnDist = 0):
    closestSchool = None
    minDistance = sys.maxsize
    for publicSchool in listPublicSchools:
        newDistance = distance.between_points(homelat, homelon, float(publicSchool[6]), float(publicSchool[7]))
        if newDistance < minDistance:
            closestSchool = publicSchool
            minDistance = newDistance
    if returnDist:
        return closestSchool, minDistance
    else:
        return closestSchool


def select_neighoboring_public_school(listCounties, schoolType, lat, lon, x):
    schoolWeights = []; schools = []
    for fips in listCounties:
        schoolCounty = schoolAssigner(fips, unweighted = 1, complete = 0, centroid = (lat, lon))
        if schoolType == 1:
            schoolWeights.append(schoolCounty.dist_pub_elem)
            schools.append(schoolCounty.elem_public)
        elif schoolType == 2:
            schoolWeights.append(schoolCounty.dist_pub_mid)
            schools.append(schoolCounty.mid_public)
        else:
            schoolWeights.append(schoolCounty.dist_pub_high)
            schools.append(schoolCounty.high_public)
    combined = sum(schoolWeights,[])
    schools = sum(schools,[])
    dist = core.cdf(combined)
    idx = bisect.bisect(dist,x)
    return schools[idx]

def write_headers(writer):
    writer.writerow(['Residence_State'] + ['County_Code'] + ['Tract_Code'] 
                    + ['Block_Code'] + ['HH_ID'] + ['HH_TYPE'] + ['Latitude']
                    + ['Longitude'] + ['Person_ID_Number'] + ['Age'] + ['Sex'] 
                    + ['Traveler_Type'] + ['Income_Bracket'] + ['Income_Amount'] 
                    + ['Residence_County'] + ['Work_County'] + ['Work_Industry'] 
                    + ['Employer'] + ['Work_Address'] + ['Work_City'] + ['Work_State'] 
                    + ['Work_Zip'] + ['Work_County_Name'] + ['NAISC_Code'] 
                    + ['NAISC_Description'] + ['Patron:Employee'] + ['Patrons'] 
                    + ['Employees'] + ['Work_Lat'] + ['Work_Lon'] + ['School_County'] 
                    + ['Type1'] + ['Type2'] + ['School_County_Name'] + ['School_State']
                    + ['School_Name'] + ['School_Lat'] + ['School_Lon'])


def write_non_student(writer, person):
    writer.writerow(person + ['NA'] + ['NA'] + ['NA'] + ['NA'] 
                    +  ['NA'] + ['NA'] + ['NA'])

def write_school_by_type(writer, person, school, type2):
    assert type2 != 'no'
    try:
        assert school != None
    except:
        raise ValueError('None-type school detected')
    if school == 'UNKNOWN':
        raise ValueError('Unknown school detected')
    if type2 == 'public':
        writer.writerow(person + [school[1]] + [school[0]] + [school[3]] + [school[6]] + [school[7]])
    elif type2 == 'private':
        writer.writerow(person + [school[3]] + [school[1]] + [school[0]] + [school[4]] + [school[5]])
    elif school != 'UNKNOWN':
        writer.writerow(person + [school[5]] + [school[3]] + [school[0]] + [school[15]] + [school[16]])


def executive(state):
    input_path = paths.MODULES[2] + state + 'Module3NN_AssignedSchoolCounty_SortedSchoolCounty.csv'
    output_path = paths.MODULES[2] + state + 'Module3NN_AssignedSchool.csv'
    with open(input_path) as read, open(output_path, 'w') as write:
        reader = reading.csv_reader(read)
        writer = writing.csv_writer(write)
        next(reader)
        write_headers(writer)
        states = module3classdump.read_states()
        state_abbrev = module3classdump.match_name_abbrev(states, state)
        print(state_abbrev)
        global noSchoolCount
        state_schools = StateSchoolAssigner(state, state_abbrev)
        trailingFips = ''
        trailingAssigner = None
        count_index = 0  
        noSchoolCount = 0
        for person in reader:
            schoolCounty = convertToFIPS.convertToFIPS(person[30])
            type1 = person[31]
            type2 = person[32]
            homelat = float(person[6])
            homelon = float(person[7])
            if trailingFips != schoolCounty:
                trailingFips = schoolCounty
                trailingAssigner = schoolAssigner(schoolCounty, post_sec_schools = state_schools)
            school = None
            if type2 == 'no':
                write_non_student(writer, person)
            else:
                school, type2 = trailingAssigner.select_school_by_type(type1, type2, homelat, homelon)
                write_school_by_type(writer, person, school, type2)
            count_index +=1;
            if count_index % 1000000 == 0:
                print('Number of people assigned schools in the state ' + state + ': ' + str(count_index))
        print('Finished assigning residents in '+ state + ' to schools. Total number of residents processed: ' + str(count_index))
        print('No school assignments: ' + noSchoolCount)
