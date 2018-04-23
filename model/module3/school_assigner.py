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
import random
import bisect
import os.path as path
from scipy import spatial
from ..module2 import adjacency
from ..utils import core, distance, paths, reading, writing

global neighboringCount
neighboringCount = 0

class SchoolAssigner:
    """Holds all school data for a county and points to its neighbors.

    Attributes:
        fips (str):  5 digit FIPS code of student's residence county.
        county (County): Geographic information about the county associated 
            with the FIPS as well as all neighboring counties.
        public_schools (dict): Dictionary with keys for each public school type
            (elementary, middle, high), where each key maps to a list with
            elements containing information about a school of that
            type associated with the FIPS code. List contains every known
            school that we have data for with that county. The index of
            the school in each list maps to the corresponding CDF in public_cdfs,
            and vice versa.
        public_dists (dict): Dictionary with keys for each public school type
            (elementary, middle, high), where each key maps to a dictionary
            with two keys. The first key, 'tree', maps to a KDTree that
            contains the Cartesian transformed coordinates of every school
            in public_schools. The second key, 'cart_to_idx', maps to a 
            dictionary that maps the Cartesian transformed coordinates
            of every school to the school's index in public_schools.
        private_schools (dict): Dictionary with keys for each public school type
            (elementary, middle, high), where each key maps to a list with
            elements containing a CDF of all of the schools of that type
            with respect to the number of students enrolled in the school.
            The index of each CDF element in each list maps to a school in
            public_schools (for identification) and vice versa.
        private_cdfs (dict): Same style as public_schools, but with
            private school types instead.
        post_sec_schools (dict): Dictionary with keys for each post-secondary
            school type (bachelor/grad, associates, non-degree), where
            each key maps to a list with elements containing information
            about a school of that type associated with the state code.
            List contains every known school that we have data for.
            The index of the school in each list maps to the corresponding
            CDF in post_sec_cdfs, and vice versa.
        post_sec_cdfs (dict): Dictionary with keys for each public school type
            (elementary, middle, high), where each key maps to a list with
            elements containing a CDF of all of the schools of that type
            with respect to the number of students enrolled in the school.
            The index of each CDF element in each list maps to a school in
            public_schools (for identification) and vice versa.
    """

    # TODO - Fix confusion with State School and complete args
    def __init__(self, fips, state_abbrev):
        """Initializes School Assigner schools and distributions.

        Inputs:
            fips (str):  5 digit FIPS code of student's residence county.
            state_abbrev (str): 2 character state abbreviation.
        """
        self.fips = fips
        self.county = adjacency.read_data(fips)
        self.public_schools = read_public_schools(fips)
        self.public_dists = assemble_public_dist(self.public_schools)
        self.private_schools = read_private_schools(fips)
        self.private_cdfs = assemble_private_dist(self.private_schools)
        self.post_sec_schools = read_post_sec_schools(self.county.neighbors, state_abbrev)
        self.post_sec_cdfs = assemble_post_sec_dist(self.post_sec_schools, *self.county.coords)

    def select_school_by_type(self, type1, type2, homelat, homelon):
        """Selects school for a student based on demographic attributes.

        Inputs:
            type1 (str): The division of school that the student has been
                assigned to. Can be any of "elem", "mid", "high", "college".
            type2 (str): The type of school that the student has been assigned
                to. Can be any of "public", "private", "bach_or_grad",
                "associates", "non_degree". Public/Private refers to primary
                and secondary education, while the various types of graduate
                programs refer to post-secondary education.
            homelat, homelon (float): The latitude and longitude of the student's
                assigned home address.

        Returns:
            school (list): Student's school of assignment.
            type2 (str): Student's type2 assignment.
        """
        assert type2 != 'no'
        if type2 == 'public':
            school = self.select_public_schools(type1, homelat, homelon)
        elif type2 == 'private':
            school, type2 = self.select_private_schools(type1, type2, homelat, homelon)
        else:
            school = self.select_post_sec_schools(type2)
        return school, type2

    def select_public_schools(self, type1, homelat, homelon):
        """Selects nearest public school to a student from their home.

        If there are no public schools available for assignment, public
        schools from all neighboring counties are used instead and the
        nearest public school from these counties is used. KDTree used to
        find the nearest public school.

        Inputs:
            type1 (str): The division of school that the student has been
                assigned to. Can be any of "elem", "mid", "high", "college".
            homelat, homelon (float): The latitude and longitude of the student's
                assigned home address.

        Returns:
            school (list): Student's school of assignment.
        """
        global neighboringCount
        if type1 not in ('elem', 'mid', 'high'):
            raise ValueError('Invalid Type1 for Current Student')
        else:
            if self.public_dists[type1]['tree'] is not None:
                x, y, z = distance.to_cart(homelat, homelon)
                _, data_ind = self.public_dists[type1]['tree'].query([x, y, z])
                school_cart_pos = tuple(self.public_dists[type1]['tree'].data[data_ind])
                school_idx = self.public_dists[type1]['cart_to_idx'][school_cart_pos]
                school = self.public_schools[type1][school_idx]
            else:
                school = select_neighboring_public_school(self.county.neighbors, type1, homelat, homelon)
                neighboringCount += 1
        return school

    def select_private_schools(self, type1, type2, homelat, homelon):
        """Selects private school for a student based on demographic attributes.

        If there are no private schools available for assignment, the student's
        type2 assignment is changed to public and a public school is selected.

        Inputs:
            type1 (str): The division of school that the student has been
                assigned to. Can be any of "elem", "mid", "high", "college".
            type2 (str): The type of school that the student has been assigned
                to. Can be any of "public", "private", "bach_or_grad",
                "associates", "non_degree". Public/Private refers to primary
                and secondary education, while the various types of graduate
                programs refer to post-secondary education.
            homelat, homelon (float): The latitude and longitude of the student's
                assigned home address.

        Returns:
            school (list): Student's school of assignment.
            type2 (str): Student's type2 assignment.
        """
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
        """Selects post-secondary school for a student based on demographic attributes.

        Inputs:
            type2 (str): The type of school that the student has been assigned
                to. Can be any of "public", "private", "bach_or_grad",
                "associates", "non_degree". Public/Private refers to primary
                and secondary education, while the various types of graduate
                programs refer to post-secondary education.

        Returns:
            school (list): Student's school of assignment.
        """
        rand_split = random.random()
        if type2 not in ('bach_or_grad', 'associates', 'non_degree'):
            raise ValueError('Invalid Type2 for Current Student')
        else:
            idx = bisect.bisect(self.post_sec_cdfs[type2], rand_split)
            school = self.post_sec_schools[type2][idx]
        return school

def read_private_schools(fips):
    """Reads all private schools for a county.

    Some counties do not have private schools of a specific type1 type
    (e.g. elementary private schools). If this happens, we leave the school
    type1 key in schools empty.

    Inputs:
        fips (str): 5 digit FIPS code of student's residence county.

    Returns:
        schools (dict): Dictionary with keys for each private school type
            ('elem', 'mid', 'high'), where each key maps to a list with
            elements containing information about a school of that
            type associated with the FIPS code. The keys for this dictionary
            correspond to all valid type1 assignments for the 'private' type2
            assignment.
    """
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
                    raise ValueError('School does not have a code in (1, 2, 3)')
    except IOError:
        # File not found, no data available
        pass
    return schools

def read_public_schools(fips, school_types=None):
    """Reads all public schools for a county.

    Some counties do not have public schools of a specific type1 type
    (e.g. elementary private schools). If this happens, we leave the school
    type1 key in schools empty. Some counties also classify public middle schools
    and public high schools as the same. If there are no schools classified
    as middle schools in a county, we assume that they are classified
    as high school type public schools and use all high schools as middle
    schools for seleciton purposes.

    Inputs:
        fips (str): 5 digit FIPS code of student's residence county.

    Returns:
        schools (dict): Dictionary with keys for each public school type
            ('elem', 'mid', 'high'), where each key maps to a list with
            elements containing information about a school of that
            type associated with the FIPS code. The keys for this dictionary
            correspond to all valid type1 assignments for the 'public' type2
            assignment.
    """
    if school_types is None:
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

def read_post_sec_schools(fips, state_abbrev):
    """Reads all post-secondary schools for a county.

    Inputs:
        fips (list): Elements are all adjacent counties to current county, 
            each denoted by a 5 digit FIPS code.
        state_abbrev (str): 2 character state abbreviation.

    Returns:
        post_sec_schools (dict): Dictionary with keys for each post-secondary
            school type (bachelor/grad, associates, non-degree), where
            each key maps to a list with elements containing information
            about a school of that type associated with the state code.
            List contains every known school that we have data for.
            The index of the school in each list maps to the corresponding
            CDF in post_sec_cdfs, and vice versa.
    """
    school_path = paths.SCHOOL_DBASE + 'PostSecSchoolsByCounty/' + state_abbrev + '/'
    post_sec_schools = {'bach_or_grad': [], 'associates': [], 'non_degree': []}
    for fips_code in fips:
        county_files = [f for f in os.listdir(school_path) if path.isfile(path.join(school_path, f))
                        and fips_code in f]
        for file in county_files:
            if file.endswith('CommunityCollege.csv'):
                _read_school_file(school_path + file, 'associates', post_sec_schools)
            elif file.endswith('University.csv'):
                _read_school_file(school_path + file, 'bach_or_grad', post_sec_schools)
            elif file.endswith('NonDegree.csv'):
                _read_school_file(school_path + file, 'non_degree', post_sec_schools)
    return post_sec_schools

def assemble_public_dist(public_schools):
    """Generates KDTree of public schools to find nearest school.

    Inputs:
        public_schools (dict): Dictionary with keys for each public school type
            (elementary, middle, high), where each key maps to a list with
            elements containing information about a school of that
            type associated with the FIPS code. List contains every known
            school that we have data for with that county. The index of
            the school in each list maps to the corresponding CDF in public_cdfs,
            and vice versa.
    Returns:
        public_dists (dict): Dictionary with keys for each public school type
            (elementary, middle, high), where each key maps to a dictionary
            with two keys. The first key, 'tree', maps to a KDTree that
            contains the Cartesian transformed coordinates of every school
            in public_schools. The second key, 'cart_to_idx', maps to a 
            dictionary that maps the Cartesian transformed coordinates
            of every school to the school's index in public_schools.
    """
    public_dist = {'elem': {'tree': None, 'cart_to_idx': None},
                   'mid':  {'tree': None, 'cart_to_idx': None},
                   'high': {'tree': None, 'cart_to_idx': None}}
    for school_type in public_dist:
        cart_to_idx = dict()
        data = []
        for idx, school in enumerate(public_schools[school_type]):
            x, y, z = distance.to_cart(float(school[6]), float(school[7]))
            cart_to_idx[(x, y, z)] = idx
            data.append([x, y, z])
        if data:
            tree = spatial.KDTree(data)
            public_dist[school_type]['tree'] = tree
            public_dist[school_type]['cart_to_idx'] = cart_to_idx
    return public_dist

def assemble_private_dist(private_schools):
    """Generates CDFs for all private schools in a county.
    
    Inputs:
        private_schools (dict): Dictionary with keys for each public school type
            (elementary, middle, high), where each key maps to a list with
            elements containing a CDF of all of the schools of that type
            with respect to the number of students enrolled in the school.
            The index of each CDF element in each list maps to a school in
            public_schools (for identification) and vice versa.
    Returns:
        private_cdfs (dict): Dictionary with keys for each private school type
            (elementary, middle, high), where each key maps to a list with
            elements containing a CDF of all of the schools of that type
            with respect to the number of students enrolled in the school.
            The index of each CDF element in each list maps to a school in
            private_schools (for identification) and vice versa.                
    """
    private_cdfs = {'elem': [], 'mid': [], 'high': []}
    for school_type in private_cdfs:
        private_cdfs[school_type] = core.cdf([int(school[7]) for school
                                              in private_schools[school_type]])
    return private_cdfs

def assemble_post_sec_dist(post_sec_schools, county_lat, county_lon):
    """Generates CDFs for all post-secondary schools in a state.

    Note that employment at post-secondary insitutions is used as a
    proxy for school attendance. This is a reasonable assumption as
    faculty and staff size at a school is positively correlated with
    student enrollment and all post-secondary schools are being compared
    based on this metric.
    
    Returns:
        post_sec_cdfs (dict): Dictionary with keys for each public school type
            (elementary, middle, high), where each key maps to a list with
            elements containing a CDF of all of the schools of that type
            with respect to the number of students enrolled in the school.
            The index of each CDF element in each list maps to a school in
            public_schools (for identification) and vice versa.
    """
    post_sec_cdfs = {'bach_or_grad': [], 'associates': [], 'non_degree': []}
    for school_type in post_sec_cdfs:
        post_sec_cdfs[school_type] = core.cdf([int(school[-4])
                                               / (distance.between_points(county_lat,
                                                                          county_lon,
                                                                          float(school[-2]),
                                                                          float(school[-1])))**2
                                               for school
                                               in post_sec_schools[school_type]])
    return post_sec_cdfs
    
def _read_school_file(file_name, school_type, post_sec_schools):
    """Helper function for read_post_sec_schools() for file reading.

    Inputs:
        file_name (str): Path to school file .csv data.
        school_type (str): Type2 designation for post-secondary school.
        post_sec_schools (dict): See read_post_sec_schools()
    """
    with open(file_name) as read:
        reader = reading.csv_reader(read)
        for row in reader:
            post_sec_schools[school_type].append(row)

def select_neighboring_public_school(counties, school_type, lat, lon):
    """Selects public schools from all neighboring counties of a county.

    Inputs:
        counties (list): FIPS code of all neighboring counties of a county.
        school_type (str): Type1 designation for public schools.
        lat, lon (float): Home latitude and longitude to weight school CDFs
            against in the CDF generation process.
    Returns:
        school (list): Student's school of assignment.
    """
    schools = {'elem': [], 'mid': [], 'high': []}
    for fips in counties:
        neighbor_schools = read_public_schools(fips, school_types = [school_type.title()])
        for key, value in schools.items():
            value.extend(neighbor_schools[key])
    # No schools of school type in all counties - try to find any school type
    if not schools[school_type]:
        for fips in counties:
            neighbor_schools = read_public_schools(fips)
            for key, value in schools.items():
                school_type = key
                value.extend(neighbor_schools[key])
    public_dists = assemble_public_dist(schools)
    x, y, z = distance.to_cart(lat, lon)
    _, data_ind = public_dists[school_type]['tree'].query([x, y, z])
    school_cart_pos = tuple(public_dists[school_type]['tree'].data[data_ind])
    school_idx = public_dists[school_type]['cart_to_idx'][school_cart_pos]
    school = schools[school_type][school_idx]
    return school

def write_headers(writer):
    """Writes headers for Module3 output file."""
    writer.writerow(['Residence_State'] + ['County_Code'] + ['Tract_Code']
                    + ['Block_Code'] + ['HH_ID'] + ['HH_TYPE'] + ['Latitude']
                    + ['Longitude'] + ['row_ID_Number'] + ['Age'] + ['Sex']
                    + ['Traveler_Type'] + ['Income_Bracket'] + ['Income_Amount']
                    + ['Residence_County'] + ['Work_County'] + ['Work_Industry']
                    + ['Employer'] + ['Work_Address'] + ['Work_City'] + ['Work_State']
                    + ['Work_Zip'] + ['Work_County_Name'] + ['NAISC_Code']
                    + ['NAISC_Description'] + ['Patron:Employee'] + ['Patrons']
                    + ['Employees'] + ['Work_Lat'] + ['Work_Lon'] + ['School_County']
                    + ['Type1'] + ['Type2'] + ['School_County_Name'] + ['School_State']
                    + ['School_Name'] + ['School_Lat'] + ['School_Lon'] + ['GC_Distance'])


def write_non_student(writer, row):
    """Writes data for non-students in Module3 output file.

    Inputs:
        writer (csv.writer): Module3 csv writer.
        row (list): Data describing a row.
    """
    writer.writerow(row + ['NA'] + ['NA'] + ['NA'] + ['NA'] + ['NA'])

def write_school_by_type(writer, row, school, type2):
    """Writes data for students in Module3 output file.

    Inputs:
        writer (csv.writer): Module3 csv writer.
        row (list): Data describing a student.
        school (list): Student's assigned school.
        type2 (str): The type of school that the student has been assigned
            to. Can be any of "public", "private", "bach_or_grad",
            "associates", "non_degree". Public/Private refers to primary
            and secondary education, while the various types of graduate
            programs refer to post-secondary education.
    """
    assert type2 != 'no'
    assert school != None
    if school == 'UNKNOWN':
        raise ValueError('Unknown school detected')
    if type2 == 'public':
        writer.writerow(row + [school[1]] + [school[0]] + [school[3]] + [school[6]] + [school[7]])
    elif type2 == 'private':
        writer.writerow(row + [school[3]] + [school[1]] + [school[0]] + [school[4]] + [school[5]])
    elif school != 'UNKNOWN':
        writer.writerow(row + [school[5]] + [school[3]] + [school[0]] + [school[15]] + [school[16]])


def main(state):
    """Assigns all valid students with county assignments to schools.

    Assumes that initial school county assignment file is sorted by school
    county in order to reduce the number of times county-wide distributions
    are created for schools in a county. Poor performance is guaranteed if
    this is not true.

    Inputs:
        state (str): State name, no spaces (e.g. Wyoming, NorthCarolina, DC).
    """
    global neighboringCount
    input_path = paths.MODULES[2] + state + 'Module3NN_AssignedSchoolCounty_SortedSchoolCounty.csv'
    output_path = paths.MODULES[2] + state + 'Module3NN_AssignedSchool.csv'
    with open(input_path) as read, open(output_path, 'w') as write:
        reader = reading.csv_reader(read)
        writer = writing.csv_writer(write)
        next(reader)
        write_headers(writer)
        states = core.read_states(spaces=False)
        state_abbrev = core.match_name_abbrev(states, state)
        trailing_fips = ''
        for count, row in enumerate(reader):
            if row[30] != 'UNASSIGNED' and row[30] != 'NA':
                school_county = core.correct_FIPS(row[30])
            type1 = row[31]
            type2 = row[32]
            homelat = float(row[6])
            homelon = float(row[7])
            if trailing_fips != school_county:
                trailing_fips = school_county
                trailing_assigner = SchoolAssigner(school_county, state_abbrev)
            school = None
            if type2 == 'no':
                write_non_student(writer, row)
            else:
                school, type2 = trailing_assigner.select_school_by_type(type1, type2, homelat, homelon)
                write_school_by_type(writer, row, school, type2)
            if count % 1000000 == 0:
                print('Number of people assigned schools in the state ' + state + ': ' + str(count))
                print('neighboring county ' + str(neighboringCount))
        print('Finished assigning residents in '+ state + ' to schools. Total number of residents processed: ' + str(count))
