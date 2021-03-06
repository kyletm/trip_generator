'''
module2.py

Project: United States Trip File Generation - Module 2
Author: Hill, Garvey, Marocchini
version date: 9/17/2016
Python 3.5

Purpose: This is the executive function for Task 2 (Module 2) that assigns a work place to every
eligible worker. It reads in a state residence file and iterates over every resident.

Notes: The structure is inspired by Hill Wyrough's Module 2. The supporting modules
were originally written by Hill Wyrough, and were debugged in order to correctly
and efficiently process large state files (TX, CA).

'''
import sys
import os
from datetime import datetime
from . import adjacency, industry, workplace
from ..utils import reading, writing, paths, core

#Paths for module 2 input and output
INPUT_PATH = paths.MODULES[0]
OUTPUT_PATH = paths.MODULES[1]
#Global Variables that contain the indices of certain columns
WORK_COUNTY_FIPS_INDEX = 16
RESIDENCE_COUNTY_FIPS_INDEX = 15
RESIDENCE_COUNTY_INDEX = 14

def write_headers_employers(writer):
    """Writes 'Module2NN_work_county_non_work.csv' file type headers.

    Inputs:
        writer (csv.writer): CSV writer object.
    """
    writer.writerow(['Residence_State'] + ['County_Code'] + ['Tract_Code'] + ['Block_Code']
                    + ['HH_ID'] + ['HH_TYPE'] + ['Latitude'] + ['Longitude']
                    + ['Person_ID_Number'] + ['Age'] + ['Sex'] + ['Traveler_Type']
                    + ['Income_Bracket'] + ['Income_Amount'] + ['Residence_County']
                    + ['Work_County_FIPS'] + ['Work_Industry'] + ['Employer'] + ['Work_Address']
                    + ['Work_City'] + ['Work_State'] + ['Work_Zip'] + ['Work_County_FIPS_Name']
                    + ['NAISC_Code'] + ['NAISC_Description'] + ['Patron:Employee']
                    + ['Patrons'] + ['Employees'] + ['Work_Lat'] + ['Work_Lon'])

def write_headers_work_counties(writer):
    """Writes 'Module2NN_work_county_work.csv' and 'Module2NN_work_county.csv' file type headers.

    Inputs:
        writer (csv.writer): CSV writer object.
    """
    writer.writerow(['Residence_State'] + ['County_Code'] + ['Tract_Code'] + ['Block_Code']
                    + ['HH_ID'] + ['HH_TYPE'] + ['Latitude'] + ['Longitude']
                    + ['Person_ID_Number'] + ['Age'] + ['Sex'] + ['Traveler_Type']
                    + ['Income_Bracket'] + ['Income_Amount'] + ['Residence_County']
                    + ['Work_County_FIPS'])

def assign_to_work_counties(state_name):
    """Assigns all workers to a work county.

    Inputs:
        state_name (str): Name of state being processed.
    """
    j2w = adjacency.read_j2w()
    start_time = datetime.now()
    print(state_name + " started at: " + str(start_time))
    with open(INPUT_PATH + state_name + 'Module1NN2ndRun.csv') as read, \
    open(OUTPUT_PATH + state_name + 'Module2NN_work_county.csv', 'w+') as write:
        reader = reading.csv_reader(read)
        writer = writing.csv_writer(write)
        write_headers_work_counties(writer)
        trailing_fips = ''
        next(reader)
        for count, row in enumerate(reader):
            #Get County FIPS Code
            fips = row[0] + row[1]
            fips = core.correct_FIPS(fips)
            if fips != trailing_fips:
                print('Iterating through county identified by FIPS: ' + fips)
                trailing_fips = fips
                #Initialize New County J2W Distribution
                county_flow_dist = adjacency.J2WDist(j2w, trailing_fips)
            #If Distribution is Exhausted, Rebuild From Scratch (not ideal, but
            #assumptions were made to distribution of traveler_type that are not right)
            #FAIL SAFE: SHOULD NOT HAPPEN
            if county_flow_dist.total_workers() == 0:
                county_flow_dist = adjacency.J2WDist(j2w, trailing_fips)
            household_type = int(row[5])
            traveler_type = int(row[11])
            work_county_fips = str(county_flow_dist.get_work_county_fips(fips, household_type, traveler_type))
            work_county_fips = core.correct_FIPS(work_county_fips, is_work_county_fips=True)
            writer.writerow(row + [fips] + [work_county_fips])
            if count % 1000000 == 0:
                print(str(count) + ' residents done')
                print('Time Elapsed: ' + str(datetime.now() - start_time))
        print(str(count) + ' residents done')
        print(state_name + " took this much time: " + str(datetime.now()-start_time))

def separate_workers_non_workers(state_name):
    """Separate workers from non workers in order to assign employer.

    Inputs:
        state_name (str): Name of state being processed.
    """
    with open(OUTPUT_PATH + state_name + 'Module2NN_work_county.csv') as read, \
    open(OUTPUT_PATH + state_name + 'Module2NN_work_county_work.csv', 'w+') as write_work, \
    open(OUTPUT_PATH + state_name + 'Module2NN_work_county_non_work.csv', 'w+') as write_non_work:
        reader = reading.csv_reader(read)
        writer_work = writing.csv_writer(write_work)
        writer_non_work = writing.csv_writer(write_non_work)
        write_headers_work_counties(writer_work)
        write_headers_employers(writer_non_work)
        count_work = 0
        count_non_work = 0
        next(reader)
        for count, row in enumerate(reader):
            if row[15] == '-1':
                work_industry = '-1'
                employer = ['Non-Worker'] + ['NA' for i in range(0, 16)]
                writer_non_work.writerow(row + [work_industry] + employer[:6] 
                                         + employer[9:14] + employer[15:17])
                count_non_work += 1
            else:
                writer_work.writerow(row)
                count_work += 1
            if count % 1000000 == 0:
                print('Number of Workers parsed: ' +  str(count))

        print('number of Work: ' + str(count_work))
        print('number of NonWork: ' + str(count_non_work))
        print('Work + NonWork: ' + str(count))

def assign_workers_to_employers(state_name):
    """Assign work industry and work place to workers sorted by work county.

    Inputs:
        state_name (str): Name of state being processed.
    """
    inc_emp = industry.read_employment_income_by_industry()
    start_time = datetime.now()
    with open(OUTPUT_PATH + state_name + 'Module2NN_sorted_work_county.csv') as read, \
    open(OUTPUT_PATH + state_name + 'Module2NN_assigned_employer.csv', 'w+') as write:
        reader = reading.csv_reader(read)
        writer = writing.csv_writer(write)
        write_headers_employers(writer)
        trailing_county = ''
        current_county = ''
        next(reader)
        for count, row in enumerate(reader):
            work_county_fips = str(row[15])
            work_county_fips = core.correct_FIPS(work_county_fips, is_work_county_fips=True)
            if work_county_fips == '-2':
                work_industry = '-2'
                employer = ['International Destination for Work'] + ['NA' for i in range(0, 16)]
            else:
                gender = int(row[10])
                income = float(row[13])
                if trailing_county != work_county_fips:
                    current_county = workplace.WorkingCounty(work_county_fips)
                    trailing_county = work_county_fips
                work_industry, index, employer = current_county.select_industry_and_employer(work_county_fips,
                                                                                             gender, income, inc_emp)
            writer.writerow(row + [work_industry] + employer[:6] 
                            + employer[9:14] + employer[15:17])
            if count % 10000 == 0:
                print(str(count) + ' Working residents done')
                print('Time Elapsed: ' + str(datetime.now() - start_time))
        print(state_name + " took this much time: " + str(datetime.now()-start_time))

def merge_sorted_files(file_name_1, file_name_2, output_file, column_sort):
    """Merge two files by sorted column.

    Used to merge workers and non-workers by residing county.

    Inputs:
        file_name_1 (str): First file to be merged.
        file_name_2 (str): Second file to be merged.
        output_file (str): Output that first and second files are merged to.
        column_sort (int): Column to sort files by.
    """
    with open(file_name_1) as read_1, open(file_name_2) as read_2, \
    open(output_file, 'w+') as write:
        reader_file_1 = reading.csv_reader(read_1)
        reader_file_2 = reading.csv_reader(read_2)
        writer = writing.csv_writer(write)
        write_headers_employers(writer)
        next(reader_file_1)
        next(reader_file_2)
        curr_person_file_1 = next(reader_file_1, None)
        curr_person_file_2 = next(reader_file_2, None)
        while((curr_person_file_1 != None) or (curr_person_file_2 != None)):
            fips_file_1 = _get_fips_code(curr_person_file_1, column_sort)
            fips_file_2 = _get_fips_code(curr_person_file_2, column_sort)
            if fips_file_1 < fips_file_2:
                writer.writerow(curr_person_file_1)
                curr_person_file_1 = next(reader_file_1, None)
            else:
                writer.writerow(curr_person_file_2)
                curr_person_file_2 = next(reader_file_2, None)

def _get_fips_code(curr_person, fips_index):
    """Returns FIPS code from person row.

    Used to merge workers and non-workers by residing county.

    Inputs:
        curr_person (list): Row of a file detailing a person's info.
        fips_index (int): Index of FIPs code in file row.

    Returns:
        fips_code (int): Cast of FIPS code as an integer.
    """
    if curr_person is None:
        return sys.maxsize
    else:
        return int(float(curr_person[fips_index]))

def main(state_name):
    """Process a state in Module 2.

    Inputs:
        state_name (str): Name of state being processed.
    """
    start_time = datetime.now()
    print('Assigning workers in input file to work counties')
    assign_to_work_counties(state_name)
    print('Separating workers from non-workers for this input file')
    separate_workers_non_workers(state_name)
    os.remove(OUTPUT_PATH + state_name + 'Module2NN_work_county.csv')
    print('Sorting the workers who work in one input file by working county')
    input_file = state_name + 'Module2NN_work_county_work.csv'
    output_file = state_name + 'Module2NN_sorted_work_county.csv'
    core.sort_by_input_column(OUTPUT_PATH, input_file, str(WORK_COUNTY_FIPS_INDEX), OUTPUT_PATH, output_file)
    print('Assigning workers in one input file to employers')
    assign_workers_to_employers(state_name)
    os.remove(OUTPUT_PATH + input_file)
    os.remove(OUTPUT_PATH + output_file)
    print('Sorting workers assigned to employers in one input file by residence county')
    input_file = state_name + 'Module2NN_assigned_employer.csv'
    output_file = state_name + 'Module2NN_assigned_employer_sorted_residence_county.csv'
    core.sort_by_input_column(OUTPUT_PATH, input_file, str(RESIDENCE_COUNTY_FIPS_INDEX), OUTPUT_PATH, output_file)
    print('Merging the two files sorted by residence county into one file that is also sorted by residence county')
    os.remove(OUTPUT_PATH + input_file)
    state_name_1 = OUTPUT_PATH + state_name + 'Module2NN_work_county_non_work.csv'
    state_name_2 = OUTPUT_PATH + state_name + 'Module2NN_assigned_employer_sorted_residence_county.csv'
    output_file = OUTPUT_PATH + state_name + 'Module2NN_AllWorkersEmployed_SortedResidenceCounty.csv'
    merge_sorted_files(state_name_1, state_name_2, output_file, RESIDENCE_COUNTY_INDEX)
    print('Total time to process the input file: ' + str(datetime.now() - start_time))
    os.remove(state_name_1)
    os.remove(state_name_2)
