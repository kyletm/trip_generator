'''
Project: United States Trip File Generation - Module 3
Author: Garvey, Marocchini
version date: 9/17/2016
Python 3.5

Purpose: This is the helper module for module3, which assigns each
student a proper place of school. This module creates and designs a school County
object that houses all the enrollment data for a particular county and its
geographical neighbors. It provides methods to select a county of schooling,
and then a particular school given that county and type of school.

Notes:
'''

import os
import sys
import random
import bisect
from ..module2 import adjacency
from ..utils import core, distance, paths, reading, writing

'SchoolCounty Object: An object for housing the entire school data for a particular county, and points to its neighbors. '
class SchoolAssigner:
    """Holds all school data for a county and points to its neighbors.

    """    
    
    # TODO - Fix confusion with State School and complete args
    def __init__(self, fips, unweighted=1, complete=1, post_sec_schools=None, centroid=None):
        'Initialize County Geography'
        self.fips = fips
        self.county = adjacency.read_data(fips)
        self.county.set_lat_lon()
        'Create Distributions for:'
        '1.) public schools (nothing right now ... '
        'just choosing the closest public school without doing any pre-processing ahead of time)'
        self.public_schools = read_public_schools(fips)
        self.assemble_public_county_dist(unweighted, centroid)
        'CHOOSE THE NEAREST PUBLIC SCHOOL'
        if complete:
            '2.) private school distributions by age demographic within aa partic '
            self.private_schools = read_private_schools(fips)
            self.assemble_private_county_dist()
            '3.) post-secondary education by demographic within a county'
            'DONE ON THE STATE LEVEL'
            self.post_sec_schools = post_sec_schools.post_sec_schools
            self.post_sec_cdfs = post_sec_schools.post_sec_cdfs

    def assemble_public_county_dist(self, unweighted, centroid):
        self.public_cdfs = {'elem': [], 'mid': [], 'high': []}
        if unweighted:
            for school_type in self.public_cdfs:
                self.public_cdfs[school_type] = [int(school[5]) for school 
                                                 in self.public_schools[school_type]]
        else:
            if centroid is None:
                raise ValueError('Must have non-null centroid to weight against')
            lat, lon = centroid[0], centroid[1]
            for school_type in self.public_cdfs:
                # TODO - Maybe restructure this to look a bit nicer...?
                self.public_cdfs[school_type] = [int(school[5])
                                                 / (distance.between_points(lat, lon,
                                                                            float(school[6]),
                                                                            float(school[7])))**2 for school
                                                                            in self.public_schools[school_type]]
        for school_type in self.public_cdfs:
            self.public_cdfs[school_type] = core.cdf(self.public_cdfs[school_type])

    def assemble_private_county_dist(self):
        self.private_cdfs = {'elem': [], 'mid': [], 'high': []}
        for school_type in self.private_cdfs:
            self.private_cdfs[school_type] = core.cdf([int(school[7]) for school 
                                                       in self.private_schools[school_type]])

    'Select an Individual School For a Student'
    def select_school_by_type(self, type1, type2, homelat, homelon):
        global noSchoolCount
        assert type2 != 'no'
        school = None
        if type2 == 'public':
            school = self.select_public_schools(type1, homelat, homelon)
        elif type2 == 'private':
            # We change the type from private to public if no private
            # schools exist due to a lack of data
            school, type2 = self.select_private_schools(type1, type2, homelat, homelon)
        else:
            school = self.select_post_sec_schools(type2)
        return school, type2

    def select_public_schools(self, type1, homelat, homelon):
        # Returns the public school, given a school type and a latitude/longitude
        # For the home
        global noSchoolCount
        rand_split = random.random()
        if type1 not in ('elem', 'mid', 'high'):
            raise ValueError('Invalid Type1 for Current Student')
        else:
            idx = bisect.bisect(self.public_cdfs[type1], rand_split)
            try:
                school = self.public_schools[type1][idx]
            except IndexError:
                noSchoolCount += 1
                school = select_neighboring_public_school(self.county.neighbors, type1, homelat, homelon, rand_split)
        return school

    def select_private_schools(self, type1, type2, homelat, homelon):
        # Returns the private school, given a school type and a latitude/longitude
        # for the home. If there are no suitable private schools, a public
        # school is selected.
        rand_split = random.random()
        if type1 not in ('elem', 'mid', 'high'):
            raise ValueError('Invalid Type1 for Current Student')
        else:
            if not self.private_schools[type1]:
                type2 = 'public'
                return self.select_public_schools(type1, homelat, homelon), type2
            else:
                idx = bisect.bisect(self.private_cdfs[type1], rand_split)
                school = self.private_schools[type1][idx]
        return school, type2
        
    def select_post_sec_schools(self, type2):
        rand_split = random.random()
        if type2 not in ('bach_or_grad', 'associates', 'non_degree'):
            raise ValueError('Invalid Type2 for Current Student')
        else:
            idx = bisect.bisect(self.post_sec_cdfs[type2], rand_split)
            school = self.post_sec_schools[type2][idx]
        return school

'Initialize Private Schools For County'
def read_private_schools(fips):
    input_path = paths.SCHOOL_DBASE + 'CountyPrivateSchools/'
    schools = {'elem': [], 'mid': [], 'high': []}
    try:
        with open(input_path + fips + 'Private.csv') as read:
            reader = reading.csv_reader(read)
            for row in reader:
                row[7] = int(row[7])
                if row[6] == '1':
                    schools['elem'].append(row)
                elif row[6] == '2' or row[6] == '3':
                    schools['mid'].append(row)
                    schools['high'].append(row)
                else:
                    raise ValueError('School does not have a code that lies in {1, 2, 3}')
    except IOError:
        # File not found, no data available
        pass
    return schools

'Initialize Public Schools For County'
def read_public_schools(fips):
    school_types = ['Elem', 'Mid', 'High']
    schools = {'elem': [], 'mid': [], 'high': []}
    base_file = paths.SCHOOL_DBASE + 'CountyPublicSchools/'
    for school_type in school_types:
        try:
            with open(base_file + school_type + '/' + fips + school_type + '.csv') as read:
                reader = reading.csv_reader(read)
                for row in reader:
                    row[5] = int(row[5])
                    schools[school_type.lower()].append(row)
        except IOError:
            # File not found, no data available
            pass
    # No middle schools recorded - assume they are mixed with high schools
    if not schools['mid']:
        schools['mid'] = schools['high']
    return schools

class StateSchoolAssigner:

    def __init__(self, state_abbrev):
        self.post_sec_schools = read_post_sec_schools(state_abbrev)
        self.assemble_post_sec_dist()

    'Use employment at Universities as a proxy for school attendance'
    def assemble_post_sec_dist(self):
        self.post_sec_cdfs = {'bach_or_grad': [], 'associates': [], 'non_degree': []}
        for school_type in self.post_sec_cdfs:
            self.post_sec_cdfs[school_type] = core.cdf([int(row[-4]) for row 
                                                        in self.post_sec_schools[school_type]])

'Initialize Post Secondary Schools for county'
def read_post_sec_schools(state_abbrev):
    school_path = paths.SCHOOL_DBASE + 'PostSecSchoolsByCounty/' + state_abbrev + '/'
    post_sec_schools = {'bach_or_grad': [], 'associates': [], 'non_degree': []}
    for file_name in os.listdir(school_path):
        file = school_path + file_name
        if file.endswith('CommunityCollege.csv'):
            read_school_file(file, 'associates', post_sec_schools)
        elif file.endswith('University.csv'):
            read_school_file(file, 'bach_or_grad', post_sec_schools)
        elif file.endswith('NonDegree.csv'):
            read_school_file(file, 'non_degree', post_sec_schools)
    return post_sec_schools

def read_school_file(file_name, school_type, post_sec_schools):
    with open(file_name) as read:
        reader = reading.csv_reader(read)
        for row in reader:
            post_sec_schools[school_type].append(row)

'Return the index of the best public school'
# TODO - Consider replacing this with KdTree - unsure if this is called enough
# to warrant it...
# TODO - This code segment isn't used anymore - ask Kornhauser about
# changing methodology to use it in the future...
def _nearest_public_school(homelat, homelon, schools, return_dist=0):
    closest_school = None
    min_dist = sys.maxsize
    for school in schools:
        curr_dist = distance.between_points(homelat, homelon, float(school[6]), float(school[7]))
        if curr_dist < min_dist:
            closest_school = school
            min_dist = curr_dist
    if return_dist:
        return closest_school, min_dist
    return closest_school

def select_neighboring_public_school(counties, school_type, lat, lon, rand_split):
    school_weights = []
    schools = []
    for fips in counties:
        school_county = SchoolAssigner(fips, unweighted=1, complete=0, centroid=(lat, lon))
        school_weights.append(school_county.public_cdfs[school_type])
        schools.append(school_county.public_schools[school_type])
    combined = [weight for sublist in school_weights for weight in sublist]
    schools = [school for sublist in schools for school in sublist]
    dist = core.cdf(combined)
    idx = bisect.bisect(dist, rand_split)
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
    assert school != None
    if school == 'UNKNOWN':
        raise ValueError('Unknown school detected')
    if type2 == 'public':
        writer.writerow(person + [school[1]] + [school[0]] + [school[3]] + [school[6]] + [school[7]])
    elif type2 == 'private':
        writer.writerow(person + [school[3]] + [school[1]] + [school[0]] + [school[4]] + [school[5]])
    elif school != 'UNKNOWN':
        writer.writerow(person + [school[5]] + [school[3]] + [school[0]] + [school[15]] + [school[16]])


def main(state):
    input_path = paths.MODULES[2] + state + 'Module3NN_AssignedSchoolCounty_SortedSchoolCounty.csv'
    output_path = paths.MODULES[2] + state + 'Module3NN_AssignedSchool.csv'
    with open(input_path) as read, open(output_path, 'w') as write:
        reader = reading.csv_reader(read)
        writer = writing.csv_writer(write)
        next(reader)
        write_headers(writer)
        states = core.read_states()
        state_abbrev = core.match_name_abbrev(states, state)
        global noSchoolCount
        state_schools = StateSchoolAssigner(state_abbrev)
        trailing_fips = ''
        trailing_assigner = None
        count_index = 0
        noSchoolCount = 0
        for person in reader:
            if person[30] != 'UNASSIGNED' and person[30] != 'NA':
                school_county = core.correct_FIPS(person[30])
            type1 = person[31]
            type2 = person[32]
            homelat = float(person[6])
            homelon = float(person[7])
            if trailing_fips != school_county:
                trailing_fips = school_county
                trailing_assigner = SchoolAssigner(school_county, post_sec_schools=state_schools)
            school = None
            if type2 == 'no':
                write_non_student(writer, person)
            else:
                school, type2 = trailing_assigner.select_school_by_type(type1, type2, homelat, homelon)
                write_school_by_type(writer, person, school, type2)
            count_index += 1
            if count_index % 1000000 == 0:
                print('Number of people assigned schools in the state ' + state + ': ' + str(count_index))
        print('Finished assigning residents in '+ state + ' to schools. Total number of residents processed: ' + str(count_index))
        print('No school assignments: ' + str(noSchoolCount))
