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
import subprocess
import sys
import os
from datetime import datetime
from . import countyAdjacencyReader
from . import industryReader
from . import workplace
from ..utils import reading
from ..utils import writing
from ..utils import paths

#Paths for module 2 input and output
INPUT_PATH = paths.MODULE_PATHS[0]
OUTPUT_PATH = paths.MODULE_PATHS[1]
#Global Variable for Journey to Work Complete Census Data
j2w = []
#Global Variables that contain the indices of certain columns
WORK_COUNTY_FIPS_INDEX = 16
RESIDENCE_COUNTY_FIPS_INDEX = 15

'RETURN THE WORK COUNTY GIVEN RESIDENT, GENDER, AGE, HOUSEHOLD TYPE, and TRAVELER TYPE.'
def get_work_county_fips(homefips, hht, tt):
    global j2wDist
    if tt in [0, 1, 3, 6] or hht in [2, 3, 4, 5, 7]:
        return -1
    elif tt in [2, 4]:
        return homefips
    else:
        val = countyFlowDist.select()
        if val[0] != '0':
            return -2
        if int(val[1]) > 5:
            return -2
        else:
            return val[1:]

'WRITE MODULE 2 OUTPUT HEADERS'
def write_headers_employers(writer):
    writer.writerow(['Residence_State'] + ['County_Code'] + ['Tract_Code'] + ['Block_Code']
                    + ['HH_ID'] + ['HH_TYPE'] + ['Latitude'] + ['Longitude']
                    + ['Person_ID_Number'] + ['Age'] + ['Sex'] + ['Traveler_Type']
                    + ['Income_Bracket'] + ['Income_Amount'] + ['Residence_County']
                    + ['Work_County_FIPS'] + ['Work_Industry'] + ['Employer'] + ['Work_Address']
                    + ['Work_City'] + ['Work_State'] + ['Work_Zip'] + ['Work_County_FIPS_Name']
                    + ['NAISC_Code'] + ['NAISC_Description'] + ['Patron:Employee']
                    + ['Patrons'] + ['Employees'] + ['Work_Lat'] + ['Work_Lon'])

def write_headers_work_counties(writer):
    writer.writerow(['Residence_State'] + ['County_Code'] + ['Tract_Code'] + ['Block_Code']
                    + ['HH_ID'] + ['HH_TYPE'] + ['Latitude'] + ['Longitude']
                    + ['Person_ID_Number'] + ['Age'] + ['Sex'] + ['Traveler_Type']
                    + ['Income_Bracket'] + ['Income_Amount'] + ['Residence_County']
                    + ['Work_County_FIPS'])

def correct_FIPS(fips, is_work_county_fips=False):
    if len(fips) != 5:
        if is_work_county_fips:
            if fips != '-1' and fips != '-2':
                fips = '0' + fips
                if len(fips) != 5:
                    raise ValueError('FIPS does not have a length of'
                                     + 'five after zero was left padded')
        else:
            fips = '0' + fips
            if len(fips) != 5:
                raise ValueError('FIPS does not have a length of'
                                 + 'five after zero was left padded')
    if fips == '15005':
        fips = '15009'
    return fips

def assign_to_work_counties(file_name):
    global j2w
    global countyFlowDist
    j2w = countyAdjacencyReader.read_J2W()
    menemp, womemp, meninco, wominco = industryReader.read_employment_income_by_industry()
    start_time = datetime.now()
    print(file_name + " started at: " + str(start_time))
    with open(INPUT_PATH + file_name + 'Module1NN2ndRun.csv') as read, \
    open(OUTPUT_PATH + file_name + 'Module2NN_work_county.csv', 'w+') as write:
        reader = reading.csv_reader(read)
        writer = writing.csv_writer(write)
        write_headers_work_counties(writer)
        count = 0
        trailing_FIPS = ''
        next(reader)
        for row in reader:
            #Get County FIPS Code
            fips = row[0]+row[1]
            fips = correct_FIPS(fips)
            if fips != trailing_FIPS:
                print('Iterating through county identified by the number: ' + fips)
                trailing_FIPS = fips
                #Initialize New County J2W Distribution
                array = countyAdjacencyReader.get_movements(trailing_FIPS, j2w)
                countyFlowDist = countyAdjacencyReader.j2wDist(array)
                it, vals = countyFlowDist.get_items()
            #If Distribution is Exhausted, Rebuild From Scratch (not ideal, but
            #assumptions were made to distribution of TT that are not right
            #FAIL SAFE: SHOULD NOT HAPPEN
            if countyFlowDist.total_workers() == 0:
                array = countyAdjacencyReader.get_movements(trailing_FIPS, j2w)
                countyFlowDist = countyAdjacencyReader.j2wDist(array)
                it, vals = countyFlowDist.get_items()
            hht = int(row[5])
            tt = int(row[11])
            work_county_fips = str(get_work_county_fips(fips, hht, tt))
            work_county_fips = correct_FIPS(work_county_fips, is_work_county_fips=True)
            writer.writerow(row + [fips] + [work_county_fips])
            count += 1
            if count % 1000000 == 0:
                print(str(count) + ' residents done')
                print('Time Elapsed: ' + str(datetime.now() - start_time))
        print(str(count) + ' residents done')
        print(file_name + " took this much time: " + str(datetime.now()-start_time))

def separate_workers_non_workers(file_name):
    with open(OUTPUT_PATH + file_name + 'Module2NN_work_county.csv') as read, \
    open(OUTPUT_PATH + file_name + 'Module2NN_work_county_work.csv', 'w+') as write_work, \
    open(OUTPUT_PATH + file_name + 'Module2NN_work_county_non_work.csv', 'w+') as write_non_work:
        reader = reading.csv_reader(read)
        writer_work = writing.csv_writer(write_work)
        writer_non_work = writing.csv_writer(write_non_work)
        write_headers_work_counties(writer_work)
        write_headers_employers(writer_non_work)
        count_work = 0
        count_non_work = 0
        total_count = 0
        next(reader)
        for person in reader:
            if person[15] == '-1':
                work_industry = '-1'
                employer = ['Non-Worker'] + ['NA' for i in range(0, 16)]
                writer_non_work.writerow(person + [work_industry] + [employer[0]] + [employer[1]]
                                         + [employer[2]] + [employer[3]] + [employer[4]]
                                         + [employer[5]] + [employer[9]] + [employer[10]]
                                         + [employer[11]] + [employer[12]] + [employer[13]]
                                         + [employer[15]] + [employer[16]])
                count_non_work += 1
            else:
                writer_work.writerow(person)
                count_work += 1
            total_count += 1
            if total_count % 1000000 == 0:
                print('Number of Workers parsed: ' +  str(total_count))

        print('number of Work: ' + str(count_work))
        print('number of NonWork: ' + str(count_non_work))
        print('Work + NonWork: ' + str(total_count))

def sort_by_input_column(input_path, input_file_termination, sort_column,
                       output_path, output_file_termination):
    base_module_path = os.path.dirname(os.path.realpath(__file__))
    script_path = base_module_path + '/' + 'sort_by_input_column.r'
    subprocess.call(["C:/R/R-3.3.1/bin/Rscript.exe", script_path,
                     input_path, input_file_termination, sort_column,
                     output_path, output_file_termination])

'ASSIGN WORK INDUSTRY AND WORK PLACE TO WORKERS SORTED BY WORK COUNTY'
def assign_workers_to_employers(file_name):
    menemp, womemp, meninco, wominco = industryReader.read_employment_income_by_industry()
    start_time = datetime.now()
    with open(OUTPUT_PATH + file_name + 'Module2NN_sorted_work_county.csv') as read, \
    open(OUTPUT_PATH + file_name + 'Module2NN_assigned_employer.csv', 'w+') as write:
        reader = reading.csv_reader(read)
        writer = writing.csv_writer(write)
        write_headers_employers(writer)
        #Assign Workers to places of Work by using the FIPS codes
        count = 0
        trailing_county = ''
        current_working_county = ''
        next(reader)
        for person in reader:
            work_county_fips = str(person[15])
            work_county_fips = correct_FIPS(work_county_fips, is_work_county_fips=True)
            if work_county_fips == '-2':
                work_industry = '-2'
                employer = ['International Destination for Work'] + ['NA' for i in range(0, 16)]
            else:
                gender = int(person[10])
                income = float(person[13])
                if trailing_county != work_county_fips:
                    current_working_county = workplace.WorkingCounty(work_county_fips)
                    trailing_county = work_county_fips
                work_industry, index, employer = current_working_county.select_industry_and_employer(work_county_fips,
                                                                   gender, income, menemp, womemp, meninco, wominco)
            writer.writerow(person + [work_industry] + [employer[0]] + [employer[1]]
                            + [employer[2]] + [employer[3]] + [employer[4]] + [employer[5]]
                            + [employer[9]] + [employer[10]] + [employer[11]] + [employer[12]]
                            + [employer[13]] + [employer[15]] + [employer[16]])
            count += 1
            if count % 10000 == 0:
                print(str(count) + 'Working residents done')
                print('Time Elapsed: ' + str(datetime.now() - start_time))
        print(file_name + " took this much time: " + str(datetime.now()-start_time))

def merge_sorted_files(file_name_1, file_name_2, output_file, column_sort):
    'Write all of the Non-Workers to the output file:'
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
            value_file_1 = _obtain_value(curr_person_file_1)
            value_file_2 = _obtain_value(curr_person_file_2)
            if value_file_1 < value_file_2:
                writer.writerow(curr_person_file_1)
                curr_person_file_1 = next(reader_file_1, None)
            else:
                writer.writerow(curr_person_file_2)
                curr_person_file_2 = next(reader_file_2, None)

def _obtain_value(curr_person):
    if curr_person is None:
        return sys.maxsize
    else:
        return int(float(curr_person[14]))

def main_script(state_name):
    start_time = datetime.now()
    print('Assigning workers in input file to Work Counties')
    assign_to_work_counties(state_name)
    print('Separating Workers from Non-Workers for this input file')
    separate_workers_non_workers(state_name)
    print('sorting the Workers who work in one input File by Working County')
    input_file = state_name + 'Module2NN_work_county_work.csv'
    output_file = state_name + 'Module2NN_sorted_work_county.csv'
    sort_by_input_column(OUTPUT_PATH, input_file, str(WORK_COUNTY_FIPS_INDEX), OUTPUT_PATH, output_file)
    print('Assigning Workers in one input File to Employers')
    assign_workers_to_employers(state_name)
    print('Sorting the Workers Assigned to Employers in one input file by Residence County')
    input_file = state_name + 'Module2NN_assigned_employer.csv'
    output_file = state_name + 'Module2NN_assigned_employer_sorted_residence_county.csv'
    sort_by_input_column(OUTPUT_PATH, input_file, str(RESIDENCE_COUNTY_FIPS_INDEX), OUTPUT_PATH, output_file)
    print('Merging the two files sorted by Residence County into one file that is also sorted by Residence County')
    state_name_1 = OUTPUT_PATH + state_name + 'Module2NN_work_county_non_work.csv'
    state_name_2 = OUTPUT_PATH + state_name + 'Module2NN_assigned_employer_sorted_residence_county.csv'
    output_file = OUTPUT_PATH + state_name + 'Module2NN_AllWorkersEmployed_SortedResidenceCounty.csv'
    merge_sorted_files(state_name_1, state_name_2, output_file, 'Residence_County')
    print('Total Time to process the input file: ' + str(datetime.now() - start_time))
