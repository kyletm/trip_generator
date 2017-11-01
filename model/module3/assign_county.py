
'''
assign_county.py

defines the AssignCounty class.
An object of type AssignCounty is generated from a input county, and 
can then assign people living in that input county to particular counties
for their schooling.

Dependencies: None
Notes:
'''

import sys
import random
import bisect
from datetime import datetime
from ..module2 import adjacency
from ..utils import reading, writing, paths, core, distance

# Constants for National Enrollment in Private and Public Schools
PUBLIC_SCHOOL_ENROLLMENT_ELEM_MID = 34637.0
PUBLIC_SCHOOL_ENROLLMENT_HIGH = 14668.0
PRIVATE_SCHOOL_ENROLLMENT_ELEM_MID = 4092.0
PRIVATE_SCHOOL_ENROLLMENT_HIGH = 1306.0

class AssignCounty:
    """Assigns students to a county of schooling based on demographic info.
    
    For public schools, students are assigned to their own county (excluding
    extenuating circumstances, e.g. no public schools in a county). For 
    private schools, students are assigned to their county or neighboring
    counties based on information about county distance and school enrollment.
    For post-secondary schools, assignment is done statewide.
    
    Attributes:
        fips (str):  5 Digit numeric FIPS code of county.
        county (County): County styled object with geographic information
            about the county associated with the FIPS and all neighboring counties.
        schools (dict): Dictionary with keys for each private school type
            (elementary, middle, high), where each key maps to a list with
            elements containing information about a school of that
            type associated with the FIPS code. List contains every known
            school that we have data for with that county. The index of
            the school in each list maps to the corresponding CDF in county_cdfs,
            and vice versa.
        seats (dict): Dictionary with keys for each private school type
            (elementary, middle, high), where each key maps to an integer 
            detailing the number of enrolled students of that school type
            in the county associated with the FIPS code.
        assignable_counties (dict): Dictionary with keys for each private 
            school type (elementary, middle, high), where each key maps 
            to a list with elements as AssignCounties. Each AssignCounty
            is guaranteed to have at least one seat in a private school 
            of the key type it is associated with.
        county_cdfs (dict): Dictionary with keys for each public school type
            (elementary, middle, high), where each key maps to a list with
            elements containing a CDF of all of the schools of that type. The
            CDF is generated based on the number of seats of that school type
            and different measures of the distance. The index of each CDF 
            element in each list maps to a school in schools (for 
            identification) of that school type and vice versa.
    """
    
    def __init__(self, fips):
        """Initializes AssignCounty data.

        Note that the actual data reading and CDF generation process is
        done by assemble_neighborly_dist() - we hold off on doing this
        processing as we construct AssignCounties in assemble_neighborly_
        dist() and if we called it in the constructor, we would generate
        data for all of the U.S. every time we created an AssignCounty.
        
        Inputs:
            fips (str): 5 Digit numeric FIPS code of a county.
        """
        self.fips = fips
        self.county = adjacency.read_data(fips)
        self.county.set_lat_lon()
        self.schools = read_private_schools(self.fips)
        self.seats = self.get_total_seats()
        self.assignable_counties = {'elem': [], 'mid': [], 'high': []}
        self.county_cdfs = {'elem': [], 'mid': [], 'high': []}

    def assemble_neighborly_dist(self):
        """Reads in seat data for neighboring counties and generates CDFs."""
        private_school_counties = []
        for fips in self.county.neighbors:
            private_school_counties.append(AssignCounty(fips))
        private_school_counties.append(self)
        # Create the distributions from the neighbors for the different age demographics
        self.get_valid_private_counties(private_school_counties)
        self.generate_county_cdfs(private_school_counties)

    def generate_county_cdfs(self, private_school_counties):
        """Generates county CDFs for all private school types.
        
        Inputs:
            private_school_counties (list): Each element is a neighboring
                AssignCounty to the current county.
        """
        homelat, homelon = self.county.get_lat_lon()
        min_distance = sys.maxsize
        for assign_county in private_school_counties:
            if assign_county is self:
                continue
            county_distance = distance.between_points(homelat, homelon,
                                                      assign_county.county.lat,
                                                      assign_county.county.lon)
            if county_distance == 0:
                raise ValueError('Counties have zero distance, yet are different counties')
            for school_type in assign_county.seats:
                if assign_county.seats[school_type] > 0:
                    self.county_cdfs[school_type].append(assign_county.seats[school_type] / county_distance**2)
            if county_distance < min_distance:
                min_distance = county_distance
        for school_type in self.seats:
            if self.seats[school_type] > 0:
                self.county_cdfs[school_type].append(self.seats[school_type] / (min_distance * 0.75)**2)
        for school_type in self.county_cdfs:
            self.county_cdfs[school_type] = core.cdf(self.county_cdfs[school_type])

    def get_valid_private_counties(self, private_school_counties):
        """Determines all assignable counties from neighboring counties.
        
        Inputs:
            private_school_counties (list): Each element is a neighboring
                AssignCounty to the current county.
        """
        for school_type in self.assignable_counties:
            for assign_county in private_school_counties:
                if assign_county.seats[school_type] > 0:
                        self.assignable_counties[school_type].append(assign_county)

    def get_total_seats(self):
        """Determines total seat enrollment of all private school types.

        Returns:
            seats (dict): Dictionary with keys for each private school type
                (elementary, middle, high), where each key maps to an integer 
                detailing the number of enrolled students of that school type
                in the county associated with the FIPS code.
        """
        seats = {'elem': 0, 'mid': 0, 'high': 0}
        for school_type in self.schools:
            for school in self.schools[school_type]:
                seats[school_type] += int(school[7])
        return seats

    def choose_school_county(self, type1, type2):
        """Selects school county based on school division and school type.
        
        Inputs:
            type1 (str): The division of school that the student has been
                assigned to. Can be any of "elem", "mid", "high", "college".
            type2 (str): The type of school that the student has been assigned
                to. Can be any of "public", "private", "bach_or_grad",
                "associates", "non_degree". Public/Private refers to primary
                and secondary education, while the various types of graduate
                programs refer to post-secondary education.
        
        Returns:
            school_county (str): Assigned county for school, represented
                as a 5 Digit FIPS code.
        """
        assert type2 != 'no'
        if type2 in ('bach_or_grad', 'associates', 'non_degree'):
            school_county = 'UNASSIGNED'
        elif type2 == 'public':
            school_county = self.fips
        elif type2 == 'private':
            split = random.random()
            if type1 not in ('elem', 'mid', 'high'):
                raise ValueError('Invalid Type1 Value for Private School Student')
            else:
                if not self.county_cdfs[type1]:
                    return self.fips
                else:
                    idx = bisect.bisect(self.county_cdfs[type1], split)
                    school_county = self.assignable_counties[type1][idx].fips
            school_county = core.correct_FIPS(school_county)
        else:
            raise ValueError('Invalid Type2 Value for Current Student')
        return school_county

def read_private_schools(fips):
    """Reads in private school data for a county

    Inputs:
        fips (str): 5 Digit FIPS code for a county.
        
    Returns:
        schools (dict): Dictionary with keys for each private school type
            (elementary, middle, high), where each key maps to a list with
            elements containing information about a school of that
            type associated with the FIPS code. List contains every known
            school that we have data for with that county.
    """
    schools = {'elem': [], 'mid': [], 'high': []}
    path = paths.SCHOOL_DBASE + 'CountyPrivateSchools/'
    try:
        elem = open(path + fips + 'Private.csv')
        reader = reading.csv_reader(elem)
    except IOError:
        # Data does not exist, we can't do anything about this
        pass
    else:
        for row in reader:
            if row[6] == '1':
                schools['elem'].append(row)
            if row[6] == '2' or row[6] == '3':
                schools['mid'].append(row)
                schools['high'].append(row)
    return schools

class AssignType:
    """Assigns school division and school type for a student.
    
    Division and type is generated based on scaled school population 
    estimates for each division and type on a state-wide level.
    
    Attributes:
        school_pop (dict): Details the total school enrollment on a statewide
            level by division, then type. Each key refers to a specific school
            division, and maps to a dictionary of types, each of which maps
            to an integer detailing the state-wide enrollment for that division
            and type.
    """
    
    def __init__(self, state):
        """Constructs all data needed for AssignType.
        
        Inputs:
            state (str): State name, without spaces.
        """
        self.school_pop = {'private': {'elem': 0, 'mid' : 0, 'high': 0},
                           'public': {'elem': 0, 'mid' : 0, 'high': 0},
                           'postsec': {'bach_or_grad': 0, 'associates': 0, 'non_degree': 0}}
        ele_mid_prop, high_prop = self.primary_sec_enrollment(state)
        self.post_sec_enrollment(state)
        self.scale_public_and_private(ele_mid_prop, high_prop)

    def post_sec_enrollment(self, state):
        """Reads in state post-secondary enrollment data by type.
        
        Inputs:
            state (str): State name, without spaces.
        """
        input_file = paths.SCHOOL_DBASE + 'stateenrollmentindegrees.csv'
        with open(input_file) as read:
            post_sec_enrollment = reading.csv_reader(read)
            for row in post_sec_enrollment:
                if row[0] == state:
                    self.school_pop['postsec']['non_degree'] = float(row[2])
                    self.school_pop['postsec']['bach_or_grad'] = float(row[4]) + float(row[5])
                    self.school_pop['postsec']['associates'] = float(row[6])

    def primary_sec_enrollment(self, state):
        """Generates estimates of primary and secondary enrollment.
        
        Inputs:
            state (str): State name, without spaces.
        
        Returns:
            ele_mid_prop (float): Scaled proportion of total enrollment 
                of 2010 state enrollment for elementary and middle school 
                type schools, for both public and private divisions.
            high_prop (float): Scaled proportion of total enrollment 
                of 2010 state enrollment for high school type schools,
                for both public and private divisions.
        """
        # TODO - Might want to update data - we shouldn't need to estimate
        # this as it probably exists somewhere in census by now...
        input_file = paths.SCHOOL_DBASE + 'statehighelemmidenrollment.csv'
        with open(input_file) as read:
            primary_sec_enrollment = reading.csv_reader(read)
            for row in primary_sec_enrollment:
                if row[0].strip('.').strip(' ') == state:
                    statetotalenrollment2009 = float(row[8])
                    statetotalenrollment2006 = float(row[1])
                    statetotalenrollment2007 = float(row[4])
                    statehighenrollment2006 = float(row[3])
                    stateelemmidenrollment2006 = float(row[2])
                    statehighenrollment2007 = float(row[6])
                    stateelemmidenrollment2007 = float(row[5])
                    prop1 = statehighenrollment2006 / statetotalenrollment2006
                    prop2 = statehighenrollment2007 / statetotalenrollment2007
                    high_prop = ((prop1+prop2)/2) * statetotalenrollment2009
                    prop1 = stateelemmidenrollment2006 / statetotalenrollment2006
                    prop2 = stateelemmidenrollment2007 / statetotalenrollment2007
                    ele_mid_prop = ((prop1+prop2)/2) * statetotalenrollment2009
        return ele_mid_prop, high_prop
        
    def scale_public_and_private(self, ele_mid_prop, high_prop):
        """Scales public and private enrollment data to generate state estimates.
        
        Inputs:
            ele_mid_prop (float): Scaled proportion of total enrollment 
                of 2010 state enrollment for elementary and middle school 
                type schools, for both public and private divisions.
            high_prop (float): Scaled proportion of total enrollment 
                of 2010 state enrollment for high school type schools,
                for both public and private divisions.
        """
        # TODO - Might want to update data - we shouldn't need to estimate
        # this as it probably exists somewhere in census by now...
        elemmidtotal = PRIVATE_SCHOOL_ENROLLMENT_ELEM_MID + PUBLIC_SCHOOL_ENROLLMENT_ELEM_MID
        hightotal = PUBLIC_SCHOOL_ENROLLMENT_HIGH + PRIVATE_SCHOOL_ENROLLMENT_HIGH
        prop1 = PRIVATE_SCHOOL_ENROLLMENT_ELEM_MID / elemmidtotal
        prop2 = PUBLIC_SCHOOL_ENROLLMENT_ELEM_MID / elemmidtotal
        self.school_pop['private']['elem'] = prop1 * ele_mid_prop
        self.school_pop['private']['mid'] = prop1 * ele_mid_prop
        self.school_pop['public']['elem'] = prop2 * ele_mid_prop
        self.school_pop['public']['mid'] = prop2 * ele_mid_prop
        prop1 = PRIVATE_SCHOOL_ENROLLMENT_HIGH / hightotal
        prop2 = PUBLIC_SCHOOL_ENROLLMENT_HIGH / hightotal
        self.school_pop['private']['high'] = prop1 * high_prop
        self.school_pop['public']['high'] = prop2 * high_prop

    def get_school_type(self, age, household_type):
        """Assigns a type and division of school based on student Age/HHT/State.
        
        Inputs:
            age (int): Student age.
            household_type (int): Student household type.
            
        Returns:
            type1 (str): The division of school that the student has been
                assigned to. Can be any of "elem", "mid", "high", "college".
            type2 (str): The type of school that the student has been assigned
                to. Can be any of "public", "private", "bach_or_grad",
                "associates", "non_degree". Public/Private refers to primary
                and secondary education, while the various types of graduate
                programs refer to post-secondary education.
        """
        if household_type in (2, 3, 4, 5, 7, 8) or age < 5 or age > 24:
            return 'non student', 'no'
        elif household_type == 6:
            self.school_pop['postsec']['bach_or_grad'] -= 1
            return 'on campus college', 'bach_or_grad'
        elif household_type in (0, 1):
            # 6 to 10 -> ELEMENTARY SCHOOL
            if age < 11:
                type1 = 'elem'
                type2 = self.pub_or_priv(type1)
            # 11 to 13 -> MIDDLE SCHOOL
            elif age < 14:
                type1 = 'mid'
                type2 = self.pub_or_priv(type1)
            # 14 - 18ish -> HIGH SCHOOL OR COLLEGE (SOME 18's IN COLLEGE)
            elif age < 19:
                type1, type2 = self.college_or_high(age)
            elif age >= 19:
                type1 = 'college'
                type2 = self.college()
            return type1, type2

    def college(self):
        """Determines the type of post-secondary school a student goes to.
            
        Returns:
            type2 (str): The type of school that the student has been assigned
                to. Can be any of "bach_or_grad", "associates", "non_degree"
        """
        split = random.random()
        post_sec_total = sum(self.school_pop['postsec'].values())
        bachgradprop = self.school_pop['postsec']['bach_or_grad'] / post_sec_total
        associatesprop = self.school_pop['postsec']['associates'] / post_sec_total
        nondegreeprop = 1.0 - bachgradprop - associatesprop
        weights = core.cdf([bachgradprop, associatesprop, nondegreeprop])
        idx = bisect.bisect(weights, split)
        college_types = ['bach_or_grad', 'associates', 'non_degree']
        type2 = college_types[idx]
        self.school_pop['postsec'][type2] -= 1
        return type2

    def college_or_high(self, age):
        """Determines college or high school division and type assignment
        
        Used to deal with teenage students eligible for college or high school.   
            
        Returns:
            type1 (str): The division of school that the student has been
                assigned to. Can be any of "elem", "mid", "high", "college".
            type2 (str): The type of school that the student has been assigned
                to. Can be any of "public", "private", "bach_or_grad",
                "associates", "non_degree". Public/Private refers to primary
                and secondary education, while the various types of graduate
                programs refer to post-secondary education.
        """
        split = random.random()
        # Account for 18 Year Olds Who Are In College (approx 1/3)
        if age != 18 or split < 0.35:
            type1 = 'high'
        elif age == 18 and split > 0.35:
            type1 = 'college'
            post_sec_total = sum(self.school_pop['postsec'].values())
            bachgradprop = self.school_pop['postsec']['bach_or_grad'] / post_sec_total
            split = random.random()
            type2 = 'bach_or_grad' if split < bachgradprop else 'associates'
            self.school_pop['postsec'][type2] -= 1
        else:
            type1 = 'high'
        if type1 == 'high':
            type2 = self.pub_or_priv(type1)
        return type1, type2

    def pub_or_priv(self, type1):
        """Public or private type assignment
        
        Returns:
            type2 (str): The type of school that the student has been assigned
                to. Can be any of "public", "private". Public/Private 
                refers to primary and secondary education.
        """
        puborpriv = random.random()
        total_pop = self.school_pop['public'][type1] + self.school_pop['private'][type1]
        thresh = self.school_pop['public'][type1] / total_pop
        type2 = 'public' if puborpriv < thresh else 'private'
        self.school_pop[type2][type1] -= 1
        return type2


def writer_headers(writer):
    """Writes headers for assign_county output file"""
    writer.writerow(['Residence_State'] + ['County_Code'] + ['Tract_Code'] + ['Block_Code']
                    + ['HH_ID'] + ['HH_TYPE'] + ['Latitude'] + ['Longitude']
                    + ['Person_ID_Number'] + ['Age'] + ['Sex'] + ['Traveler_Type']
                    + ['Income_Bracket'] + ['Income_Amount'] + ['Residence_County']
                    + ['Work_County'] + ['Work_Industry'] + ['Employer'] + ['Work_Address']
                    + ['Work_City'] + ['Work_State'] + ['Work_Zip'] + ['Work_County_Name']
                    + ['NAISC_Code'] + ['NAISC_Description'] + ['Patron:Employee'] + ['Patrons']
                    + ['Employees'] + ['Work_Lat'] + ['Work_Lon'] + ['School_County']
                    + ['Type1'] + ['Type2'])


def main(state):
    """Assigns all eligible students to specific counties for school.

    Inputs:
        state (str): Alphabetical state name with no spaces.
    """
    start_time = datetime.now()
    print(state + " started at: " + str(start_time))
    type_assigner = AssignType(state)
    input_file = paths.MODULES[1] + state + 'Module2NN_AllWorkersEmployed_SortedResidenceCounty.csv'
    output_file = paths.MODULES[2] + state + 'Module3NN_AssignedSchoolCounty.csv'
    with open(input_file) as read, open(output_file, 'w+') as write:
        reader = reading.csv_reader(read)
        writer = writing.csv_writer(write)
        writer_headers(writer)
        next(reader)
        non_student_count = 0
        student_count = 0
        pop_count = 0
        trailing_fips = ''
        for person in reader:
            if len(person) != 30:
                print(person)
                raise ValueError('Possible missing data for person')
            curr_county = core.correct_FIPS(person[14])
            age = int(person[9])
            household_type = int(person[5])
            if curr_county != trailing_fips:
                trailing_fips = curr_county
                print('Assigning people who live in county "' + curr_county + '" to school counties')
                assign_county = AssignCounty(curr_county)
                assign_county.assemble_neighborly_dist()
            type1, type2 = type_assigner.get_school_type(age, household_type)
            if type1 == 'non student':
                school_county = 'NA'
                non_student_count += 1
            else:
                school_county = assign_county.choose_school_county(type1, type2)
                student_count += 1
            writer.writerow(person + [school_county] + [type1] + [type2])
            pop_count += 1
            if pop_count % 1000000 == 0:
                print('Have printed out a total of ' + str(pop_count) + ' people')

    print('student_count: ' + str(student_count))
    print('non_student_count: ' + str(non_student_count))
    print('pop: ' + str(pop_count))













