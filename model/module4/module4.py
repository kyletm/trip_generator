'''
module4.py

Project: United States Trip File Generation
Author: A.P. Hill Wyrough
version date: 3/15/2014
Python 3.3

PURPOSE: Assign Each Resident an Activity Pattern
INPUTS: Activity Pattern Distributions
DEPENDENCIES: None
'''
import random
import bisect
from datetime import datetime
from ..utils import core, paths, reading, writing

def read_activity_pattern_dists():
    """Creates dictionary mapping traveler type to weight distribution.

    Returns:
        distribution (dict): Each key is a traveler type, that
            maps to a list, where each element maps to the probability
            that a traveler type is assigned an activity pattern, with the
            activity tour being the index of the element in the list
            (e.g. distributions[0][4] refers to the probability that a
            traveler type 0 is assigned to activity pattern 4).
    """
    file_path = paths.TRIP_DISTS + 'TripTypeDistributions.csv'
    with open(file_path) as read:
        reader = reading.csv_reader(read)
        distributions = {0: [], 1: [], 2: [], 3: [], 4: [], 5: [], 6: []}
        for row in reader:
            for index, weight in enumerate(row):
                distributions[index].append(float(weight))
    return distributions

def assign_activity_pattern(traveler_type, distributions, person):
    """Assigns activity pattern based on traveler type to a person.

    Inputs:
        traveler_type (int): Person's traveler type.
        distributions (dict): Each key is a traveler type, that
            maps to a list, where each element maps to the probability
            that a traveler type is assigned an activity pattern, with the
            activity tour being the index of the element in the list.
        person (list): Information about a person from input file.

    Returns:
        activity_pattern (str): The assigned activity_pattern for a person.
    """
    # revise traveler type, in the event of no school assigned
    # (incredibly fringe population < 0.001%)
    if person[-3] == 'NA':
        if traveler_type == 3 or traveler_type == 4 or traveler_type == 2 or traveler_type == 1:
            traveler_type = 6
    if traveler_type == 5 and person[15] == '-2':
            return '-5'
    dist = distributions[traveler_type]
    weights = core.cdf(dist)
    split = random.random()
    return bisect.bisect(weights, split)

def writeHeaders(writer):
    """Writes headers for Module 4 output."""
    writer.writerow(['Residence State'] + ['County Code'] + ['Tract Code']
                    + ['Block Code'] + ['HH ID'] + ['HH TYPE'] + ['Latitude']
                    + ['Longitude'] + ['Person ID Number'] + ['Age'] + ['Sex']
                    + ['Traveler Type'] + ['Income Bracket'] + ['Income Amount']
                    + ['Work County'] + ['Work Industry'] + ['Employer']
                    + ['Work Address'] + ['Work City'] + ['Work State'] + ['Work Zip']
                    + ['Work County Name'] + ['NAISC Code'] + ['NAISC Description']
                    + ['Patron:Employee'] + ['Patrons'] + ['Employees']
                    + ['Work Lat'] + ['Work Lon'] + ['School Name'] + ['School County']
                    + ['SchoolLat'] + ['SchoolLon'] + ['Activity Pattern'])

def fix_missing_school_fips(state_county_dict, person):
    """Fixes school FIPS codes that are unassigned.

    Inputs:
        state_county_dict (dict): Each key is a state abbrevation, that
            maps to another dictionary with every county for that state,
            with key as county name and value county FIPS code.
        person (list): Information about a person from input file.

    Returns:
        activity_pattern (str): The assigned activity_pattern for a person.
    """
    school_county_name = person[33]
    school_abbrev = person[34]
    county_dict = state_county_dict.get(school_abbrev)
    person[30] = county_dict.get(school_county_name)

def main(state):
    """Assigns all persons a traveler type.

    Inputs:
        state (str): Alphabetical state name with no spaces.
    """
    input_path = paths.MODULES[2] + state + 'Module3NN_AssignedSchool.csv'
    output_path = paths.MODULES[3] + state + 'Module4NN2ndRun.csv'
    start_time = datetime.now()
    print(state + " started at: " + str(start_time))
    with open(input_path) as read, open(output_path, 'w+') as write:
        reader = reading.csv_reader(read)
        writer = writing.csv_writer(write)
        next(reader)
        write_headers(writer)
        distributions = read_activity_pattern_dists()
        count = 0
        school_fixes = 0
        school_issue = 0
        state_county_dict = core.state_county_dict()
        for person in reader:
            count += 1
            traveler_type = int(person[11])
            school_county_code = person[30]
            school_county_name = person[33]
            # TODO - Refactor this out to core.county_dict()...
            if 'Radford' in school_county_name:
                school_county_name = 'Radford City'
            if school_county_code == 'UNASSIGNED':
                fix_missing_school_fips(state_county_dict, person)
                school_fixes += 1
            else:
                activity_index = assign_activity_pattern(traveler_type, distributions, person)
            if person[30] is None and person[33] == 'NA' and person[34] != 'NA':
                school_issue += 1
                print('FIPS Issue found - no County Provided, skipping.')
                print('Row number', count)
                continue
            else:
                writer.writerow(person + [activity_index])
            if count % 1000000 == 0:
                print(str(count) + ' Residents Completed')

    print(str(count) + ' of all Residents in ' + state + ' have been processed')
    print(state + " took this much time: " + str(datetime.now()-start_time))
    print('FIPS MISSING/ABLE TO FIX', school_fixes)
    print('FIPS MISSING/UNABLE TO FIX', school_issue)
