
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

'Constants for National Enrollment in Private and Public Schools'
PUBLIC_SCHOOL_ENROLLMENT_ELEM_MID = 34637.0
PUBLIC_SCHOOL_ENROLLMENT_HIGH = 14668.0
PRIVATE_SCHOOL_ENROLLMENT_ELEM_MID = 4092.0
PRIVATE_SCHOOL_ENROLLMENT_HIGH = 1306.0
'-----------------------------------------------------------'


class AssignCounty:
    def __init__(self, fips):
        'Initialize County Geography'
        self.fips = fips
        self.county = adjacency.read_data(fips)
        self.county.set_lat_lon()
        self.priv_elem = []
        self.priv_mid = []
        self.priv_high = []
        self.read_private_schools(fips)
        self.priv_elem_seats = 0
        self.priv_mid_seats = 0
        self.priv_high_seats = 0
        self.get_total_seats()
        self.assignable_counties = []
        self.priv_elem_counties = []
        self.priv_mid_counties = []
        self.priv_high_counties = []

    def assemble_neighborly_dist(self):
        private_school_counties = []
        for fips in self.county.neighbors:
            private_school_counties.append(AssignCounty(fips))
        private_school_counties.append(self)
        # Create the distributions from the neighbors for the different age demographics
        self.get_valid_private_counties(private_school_counties)
        self.generate_county_cdfs(private_school_counties)

    def generate_county_cdfs(self, private_school_counties):
        homelat, homelon = self.county.get_lat_lon()
        min_distance = sys.maxsize
        for assign_county in private_school_counties:
            if assign_county is self:
                continue
            county_distance = distance.between_points(homelat, homelon,
                                                      assign_county.county.lat,
                                                      assign_county.county.lon)
            if county_distance == 0:
                county_distance = 1
            if assign_county.priv_elem_seats > 0:
                self.priv_elem_counties.append(assign_county.priv_elem_seats / (county_distance**2))
            if assign_county.priv_mid_seats > 0:
                self.priv_mid_counties.append(assign_county.priv_mid_seats / (county_distance**2))
            if assign_county.priv_high_seats > 0:
                self.priv_high_counties.append(assign_county.priv_high_seats / (county_distance**2))
            if county_distance < min_distance:
                min_distance = county_distance
        if self.priv_elem_seats > 0:
            self.priv_elem_counties.append(self.priv_elem_seats / (min_distance * 0.75)**2)
        if self.priv_mid_seats > 0:
            self.priv_mid_counties.append(self.priv_mid_seats / (min_distance * 0.75)**2)
        if self.priv_high_seats > 0:
            self.priv_high_counties.append(self.priv_high_seats / (min_distance * 0.75)**2)
        self.priv_elem_counties = core.cdf(self.priv_elem_counties)
        self.priv_mid_counties = core.cdf(self.priv_mid_counties)
        self.priv_high_counties = core.cdf(self.priv_high_counties)

    def get_valid_private_counties(self, private_school_counties):
        for school_type in ['elem', 'mid', 'high']:
            school_type = []
            for assign_county in private_school_counties:
                if school_type == 'elem':
                    if assign_county.priv_elem_seats > 0:
                        school_type.append(assign_county)
                elif school_type == 'mid':
                    if assign_county.priv_mid_seats > 0:
                        school_type.append(assign_county)
                else:
                    if assign_county.priv_high_seats > 0:
                        school_type.append(assign_county)
            self.assignable_counties.append(school_type)

    'Calculate the Total Enrollment of a County'
    def get_total_seats(self):
        for k in self.priv_elem:
            self.priv_elem_seats += int(k[7])
        for k in self.priv_mid:
            self.priv_mid_seats += int(k[7])
        for k in self.priv_high:
            self.priv_high_seats += int(k[7])

    'Initialize Private Schools For County'
    def read_private_schools(self, fips):
        path = paths.SCHOOL_DBASE + 'CountyPrivateSchools/'
        try:
            elem = open(path + fips + 'Private.csv')
            elem_private_schools = reading.csv_reader(elem)
        except IOError:
            # Data does not exist, we can't do anything about this
            pass
        else:
            for row in elem_private_schools:
                row[7] = int(row[7])
                if row[6] == '1':
                    self.priv_elem.append(row)
                if row[6] == '2' or row[6] == '3':
                    self.priv_mid.append(row)
                    self.priv_high.append(row)

    def choose_school_county(self, type1, type2):
        assert type2 != 'no'
        if type2 in ('four year', 'two year', 'non deg'):
            school_county = 'UNASSIGNED'
        elif type2 == 'public':
            school_county = self.fips
        elif type2 == 'private':
            split = random.random()
            idx = None
            if type1 == 'elem':
                if not self.priv_elem_counties:
                    return self.fips
                idx = bisect.bisect(self.priv_elem_counties, split)
                school_county = (self.assignable_counties[0][idx]).fips
            elif type1 == 'mid':
                if not self.priv_mid_counties:
                    return self.fips
                idx = bisect.bisect(self.priv_mid_counties, split)
                school_county = (self.assignable_counties[1][idx]).fips
            elif type1 == 'high':
                if not self.priv_high_counties:
                    return self.fips
                idx = bisect.bisect(self.priv_high_counties, split)
                school_county = (self.assignable_counties[2][idx]).fips
            else:
                raise ValueError('Invalid Type1 Value for Private School Student')
        else:
            raise ValueError('Invalid Type2 Value for Current Student')
        return school_county


class StateSchoolPop:

    def __init__(self, state):
        self.school_pop = {'private': {'elem': 0, 'mid' : 0, 'high': 0},
                           'public': {'elem': 0, 'mid' : 0, 'high': 0},
                           'postsec': {'four year': 0, 'two year': 0, 'non deg': 0},
                           'postsectotal': 0}
        self.primary_sec_enrollment(state)
        self.post_sec_enrollment(state)
        self.scale_public_and_private()

    'Read Enrollment In State For Post-Secondary Schools by Type'
    def post_sec_enrollment(self, state):
        input_file = paths.SCHOOL_DBASE + 'stateenrollmentindegrees.csv'
        with open(input_file) as read:
            post_sec_enrollment = reading.csv_reader(read)
            for row in post_sec_enrollment:
                if row[0] == state:
                    self.school_pop['postsec']['non deg'] = float(row[2])
                    self.school_pop['postsectotal'] = float(row[3])
                    self.school_pop['postsec']['four year'] = float(row[4]) + float(row[5])
                    self.school_pop['postsec']['two year'] = float(row[6])

    'Read State Enrollment in Schools, Scaled Using Past Data'
    def primary_sec_enrollment(self, state):
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
                    self.high = ((prop1+prop2)/2) * statetotalenrollment2009
                    prop1 = stateelemmidenrollment2006 / statetotalenrollment2006
                    prop2 = stateelemmidenrollment2007 / statetotalenrollment2007
                    self.ele_mid = ((prop1+prop2)/2) * statetotalenrollment2009

    def scale_public_and_private(self):
        # NATIONAL NUMBERS TO BE SCALED TO STATE LEVEL NUMBERS
        elemmidtotal = PRIVATE_SCHOOL_ENROLLMENT_ELEM_MID + PUBLIC_SCHOOL_ENROLLMENT_ELEM_MID
        hightotal = PUBLIC_SCHOOL_ENROLLMENT_HIGH + PRIVATE_SCHOOL_ENROLLMENT_HIGH
        # PROJECTED STATE LEVEL NUMBERS FOR ENROLLMENT IN ALL SCHOOLS
        prop1 = PRIVATE_SCHOOL_ENROLLMENT_ELEM_MID / elemmidtotal
        prop2 = PUBLIC_SCHOOL_ENROLLMENT_ELEM_MID / elemmidtotal
        self.school_pop['private']['elem'] = prop1 * self.ele_mid
        self.school_pop['private']['mid'] = prop1 * self.ele_mid
        self.school_pop['public']['elem'] = prop2 * self.ele_mid
        self.school_pop['public']['mid'] = prop2 * self.ele_mid
        prop1 = PRIVATE_SCHOOL_ENROLLMENT_HIGH / hightotal
        prop2 = PUBLIC_SCHOOL_ENROLLMENT_HIGH / hightotal
        self.school_pop['private']['high'] = prop1 * self.high
        self.school_pop['public']['high'] = prop2 * self.high

    'Assign Student a Type of School (Private/Public) or (Elem, Mid, High, College) Based on Age/HHT/State'
    def get_school_type(self, age, household_type):
        # Not a student
        if household_type in (2, 3, 4, 5, 7, 8) or age < 5 or age > 24:
            return 'non student', 'no'
        elif household_type == 6:
            self.school_pop['postsec']['four year'] -= 1
            return 'on campus college', 'four year'
        elif household_type in (0, 1):
            # 6 to 10 -> ELEMENTARY SCHOOL
            if age < 11:
                type1 = 'elem'
                type2 = self.pub_or_priv(type1)
            # 11 to 13 -> MIDDLE SCHOOL
            elif age < 14:
                type1 = 'mid'
                type2 = self.pub_or_priv(type1)
            # 14 - 18ish -> HIGH SCHOOL (SOME 18's IN COLLEGE)
            elif age < 19:
                type1, type2 = self.college_or_high(age)
            elif age >= 19:
                type1, type2 = self.college()
            return type1, type2

    def college(self):
        type1 = 'college'
        split = random.random()
        bachgradprop = self.school_pop['postsec']['four year'] / self.school_pop['postsectotal']
        associatesprop = self.school_pop['postsec']['two year'] / self.school_pop['postsectotal']
        nondegreeprop = 1.0 - bachgradprop - associatesprop
        weights = core.cdf([bachgradprop, associatesprop, nondegreeprop])
        idx = bisect.bisect(weights, split)
        college_types = ['four year', 'two year', 'non deg']
        type2 = college_types[idx]
        self.school_pop['postsec'][type2] -= 1
        return type1, type2

    def college_or_high(self, age):
        split = random.random()
        # Account for 18 Year Olds Who Are In College (approx 1/3)
        if age != 18 or split < 0.35:
            type1 = 'high'
        elif age == 18 and split > 0.35:
            type1 = 'college'
            bachgradprop = self.school_pop['postsec']['four year'] / self.school_pop['postsectotal']
            split = random.random()
            type2 = 'four year' if split < bachgradprop else 'two year'
            self.school_pop['postsec'][type2] -= 1
        else:
            type1 = 'high'
        if type1 == 'high':
            type2 = self.pub_or_priv(type1)
        return type1, type2

    def pub_or_priv(self, type1):
        puborpriv = random.random()
        total_pop = self.school_pop['public'][type1] + self.school_pop['private'][type1]
        thresh = self.school_pop['public'][type1] / total_pop
        type2 = 'public' if puborpriv < thresh else 'private'
        self.school_pop[type2][type1] -= 1
        return type2


def writer_headers(writer):
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
    start_time = datetime.now()
    print(state + " started at: " + str(start_time))
    # Gather state enrollment data
    school_pops = StateSchoolPop(state)
    input_file = paths.MODULES[1] + state + 'Module2NN_AllWorkersEmployed_SortedResidenceCounty.csv'
    output_file = paths.MODULES[2] + state + 'Module3NN_AssignedSchoolCounty.csv'
    with open(input_file) as read, open(output_file, 'w+') as write:
        reader = reading.csv_reader(read)
        writer = writing.csv_writer(write)
        writer_headers(writer)
        next(reader)
        unassigned_count = 0
        student_count = 0
        pop_count = 0
        trailing_fips = ''
        for person in reader:
            if len(person) != 30:
                print(person)
                raise ValueError('Possible missing data for person')
            fips = person[14]
            age = int(person[9])
            household_type = int(person[5])
            if len(fips) != 5:
                curr_county = '0'+ fips
                if len(curr_county) != 5:
                    raise ValueError('County FIPS code is not 5 digits')
            else:
                curr_county = fips
            if curr_county != trailing_fips:
                trailing_fips = curr_county
                print('Assigning people who live in county "' + curr_county + '" to school counties')
                assign_county = AssignCounty(curr_county)
                assign_county.assemble_neighborly_dist()
            type1, type2 = school_pops.get_school_type(age, household_type)
            if type1 == 'non student':
                schoolcounty = 'NA'
                unassigned_count += 1
            else:
                schoolcounty = assign_county.choose_school_county(type1, type2)
                student_count += 1
            writer.writerow(person + [schoolcounty] + [type1] + [type2])
            pop_count += 1
            if pop_count % 1000000 == 0:
                print('Have printed out a total of ' + str(pop_count) + ' people')

    print('student_count: ' + str(student_count))
    print('unassigned_count: ' + str(unassigned_count))
    print('pop: ' + str(pop_count))













