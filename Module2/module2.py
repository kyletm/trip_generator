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
from datetime import datetime
import countyAdjacencyReader
import industryReader
import workPlaceHelper
import fileReadingModule
import fileWritingModule
import subprocess
import sys

'MAIN PATH ON MY COMPUTER TOWARDS MODULE1 OUTPUT'
O_PATH = "D:/Data/Output/Module1/"
M_PATH = "D:/Data"
inputPath = "D:/Data/Output/Module1/"
outputPath = "D:/Data/Output/Module2/"
'Global Variable for Journey to Work Complete Census Data'
j2w = []
'Global Variables that contain the indices of certain Columns'
WorkCounty_Index = 16
ResidenceCounty_Index = 15
'RETURN THE WORK COUNTY GIVEN RESIDENT, GENDER, AGE, HOUSEHOLD TYPE, and TRAVELER TYPE.'
def get_work_county(homefips, hht, tt):
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

'READ IN ASSOCIATED STATE ABBREVIATIONS WITH STATE FIPS CODES'
def read_states():
    stateFileLocation = M_PATH + '/'
    fname = stateFileLocation + 'ListofStates.csv'
    lines = open(fname).read().splitlines()
    return lines

'WRITE MODULE 2 OUTPUT HEADERS'
def write_headers_employers(pW):
    pW.writerow(['Residence_State'] + ['County_Code'] + ['Tract_Code'] + ['Block_Code']
                + ['HH_ID'] + ['HH_TYPE'] + ['Latitude'] + ['Longitude']
                + ['Person_ID_Number'] + ['Age'] + ['Sex'] + ['Traveler_Type']
                + ['Income_Bracket'] + ['Income_Amount'] + ['Residence_County']
                + ['Work_County'] + ['Work_Industry'] + ['Employer'] + ['Work_Address']
                + ['Work_City'] + ['Work_State'] + ['Work_Zip'] + ['Work_County_Name']
                + ['NAISC_Code'] + ['NAISC_Description'] + ['Patron:Employee']
                + ['Patrons'] + ['Employees'] + ['Work_Lat'] + ['Work_Lon'])

def write_headers_work_counties(pW):
    pW.writerow(['Residence_State'] + ['County_Code'] + ['Tract_Code'] + ['Block_Code']
                + ['HH_ID'] + ['HH_TYPE'] + ['Latitude'] + ['Longitude']
                + ['Person_ID_Number'] + ['Age'] + ['Sex'] + ['Traveler_Type']
                + ['Income_Bracket'] + ['Income_Amount'] + ['Residence_County']
                + ['Work_County'])

def assign_to_work_counties(fileName):
    global j2w
    global countyFlowDist
    'Read In J2W and Employment by Income by Industry'
    j2w = countyAdjacencyReader.read_J2W()
    menemp, womemp, meninco, wominco = industryReader.read_employment_income_by_industry()
    'Begin Progress Reporting Initialization'
    startTime = datetime.now()
    print(fileName + " started at: " + str(startTime))
    'OPEN INPUT AND OUTPUT FILES'
    reader = fileReadingModule.returnCSVReader(inputPath + fileName 
                                              + 'Module1NN2ndRun.csv')
    person_writer = fileWritingModule.returnCSVWriter(outputPath 
                                                      + str(fileName 
                                                            + 'Module2NN_WorkCounty.csv'))
    write_headers_work_counties(person_writer)
     ############ RUN ###################
    'ITERATE OVER ALL RESIDENTS WITHIN STATE'
    count = 0 
    trailing_FIPS = ''
    for row in reader:
        'Skip First Row'
        if count == 0:
            count += 1
            continue
        'ASSIGN WORK COUNTY----------------------------------------------------------------'
        'Get County Fips Code'
        fips = row[0]+row[1];
        if len(fips) != 5:
            fips = '0' + fips
            if len(fips) != 5:
                    print('ERROR: RESIDENCE COUNTY DOES NOT HAVE A' 
                          + 'LENGTH OF FIVE AFTER THE ZERO WAS ADDED')
        'Track County Code Through State File'
        if fips == '15005':
            fips = '15009'
        if fips != trailing_FIPS:
            print('Iterating through county identified by the number: ' + fips)
            trailing_FIPS = fips
            'Initialize New County J2W Distribution'
            array = countyAdjacencyReader.get_movements(trailing_FIPS, j2w)
            countyFlowDist = countyAdjacencyReader.j2wDist(array)
            it, vals = countyFlowDist.get_items()
        'If Distribution is Exhausted, Rebuild From Scratch (not ideal, but'
        'assumptions were made to distribution of TT that are not right'
        'FAIL SAFE: SHOULD NOT HAPPEN'
        if countyFlowDist.total_workers() == 0:
            array = countyAdjacencyReader.get_movements(trailing_FIPS, j2w)
            countyFlowDist = countyAdjacencyReader.j2wDist(array)
            it, vals = countyFlowDist.get_items()
        'Get Gender, Age, HHT, TT, Income, HomeLat, HomeLon'
        hht = int(row[5])
        tt = int(row[11])
        workCounty = str(get_work_county(fips, hht, tt))
        if len(workCounty) != 5 and workCounty != '-1' and workCounty != '-2':
                workCounty = '0' + workCounty
                if len(workCounty) != 5:
                    print('ERROR111: WORK COUNTY DOES NOT HAVE A LENGTH OF FIVE AFTER THE ZERO WAS ADDED')
        person_writer.writerow(row + [fips] + [workCounty])
        'PROGRESS REPORTING-------------------------------------------------------------------------'
        count += 1
        if count % 1000000 == 0:
            print(str(count) + ' residents done')
            print('Time Elapsed: ' + str(datetime.now() - startTime))
    print(str(count) + ' residents done')
    print(fileName + " took this much time: " + str(datetime.now()-startTime))

def separate_workers_non_workers(fileName):
    startTime = datetime.now()
    reader = fileReadingModule.returnCSVReader(outputPath + fileName + 'Module2NN_WorkCounty.csv')
    person_writer_work = fileWritingModule.returnCSVWriter(outputPath + fileName + 'Module2NN_WorkCounty_Work.csv')
    person_writer_non_work = fileWritingModule.returnCSVWriter(outputPath + fileName + 'Module2NN_WorkCounty_NonWork.csv')
    write_headers_work_counties(person_writer_work)
    write_headers_employers(person_writer_non_work)
    count_Work = 0
    count_NonWork = 0
    total_Count = 0
    header = next(reader, None)
    for person in reader:
        if person[15] == '-1':
            workIndustry = '-1'
            employer = ['Non-Worker'] + ['NA']+['NA']+['NA']+['NA']+['NA']+['NA']+['NA']+['NA']+['NA']+['NA']+['NA']+['NA']+['NA']+['NA']+['NA']+['NA']
            person_writer_non_work.writerow(person + [workIndustry] + [employer[0]] + [employer[1]]
                                 + [employer[2]] + [employer[3]] + [employer[4]] + [employer[5]]
                                 + [employer[9]] + [employer[10]] + [employer[11]] + [employer[12]]
                                 + [employer[13]] + [employer[15]] + [employer[16]])
            count_NonWork += 1
        else:
            person_writer_work.writerow(person)
            count_Work += 1
        total_Count += 1
        if total_Count % 1000000 == 0:
            print('Number of Workers parsed: ' +  str(total_Count))

    print('number of Work: ' + str(count_Work))
    print('number of NonWork: ' + str(count_NonWork))
    print('Work + NonWork: ' + str(total_Count))

def sort_by_input_column(input_path, input_file_termination, sort_column,
                       output_path, output_file_termination):
    scriptPath = "C:/Users/Kyle/Documents/Rscript_SortByInputColumn.R"
    subprocess.call(["C:/R/R-3.3.1/bin/Rscript.exe", scriptPath,
                     inputPath, input_file_termination, sort_column,
                     outputPath, output_file_termination])

def assign_workers_to_employers(fileName):
    menemp, womemp, meninco, wominco = industryReader.read_employment_income_by_industry()
    'ASSIGN WORK INDUSTRY AND WORK PLACE TO WORKERS SORTED BY WORK COUNTY----------------------------'
    startTime = datetime.now()
    reader_Work = fileReadingModule.returnCSVReader(outputPath + fileName + 'Module2NN_SortedWorkCounty.csv')
    person_writer = fileWritingModule.returnCSVWriter(outputPath + fileName + 'Module2NN_AssignedEmployer.csv')
    'Write the header to the output file:'
    write_headers_employers(person_writer)
    'Assign Workers to places of Work by using the fips codes:'
    count = 0; trailingCounty = ''; currentWorkingCountyObject = ''
    for person in reader_Work:
        if count == 0:
            count += 1
            continue
        workCounty = str(person[15])
        if (workCounty == '15005'):
            workCounty = '15009'
        if len(workCounty) != 5 and workCounty != '-1' and workCounty != '-2':
                workCounty = str('0' + workCounty)
                if len(workCounty) != 5:
                    print('ERROR: WORK COUNTY DOES NOT HAVE A LENGTH OF FIVE AFTER THE ZERO WAS ADDED')
        if (workCounty == '-2'):
            workIndustry = '-2'
            employer = ['International Destination for Work'] + ['NA']+['NA']+['NA']+['NA']+['NA']+['NA']+['NA']+['NA']+['NA']+['NA']+['NA']+['NA']+['NA']+['NA']+['NA']+['NA']
        else:
            gender = int(person[10])
            income = float(person[13])
            if trailingCounty != workCounty:
                #print('workcounty',workCounty)
                currentWorkingCountyObject = workPlaceHelper.workingCounty(workCounty)
                trailingCounty = workCounty
            workIndustry, index, employer = currentWorkingCountyObject.select_industry_and_employer(workCounty,
                                                               gender, income, menemp, womemp, meninco, wominco)
        person_writer.writerow(person + [workIndustry] + [employer[0]] + [employer[1]]
                                 + [employer[2]] + [employer[3]] + [employer[4]] + [employer[5]]
                                 + [employer[9]] + [employer[10]] + [employer[11]] + [employer[12]]
                                 + [employer[13]] + [employer[15]] + [employer[16]])
        count +=1
        if count % 10000 == 0:
            print(str(count) + 'Working residents done')
            print('Time Elapsed: ' + str(datetime.now() - startTime))
    'Output the runtime statistics of this function call:'
    print(fileName + " took this much time: " + str(datetime.now()-startTime))

def merge_sorted_files(fileName1, fileName2, outputFile, columnSort):
    'Write all of the Non-Workers to the output file:'
    reader_File1 = fileReadingModule.returnCSVReader(fileName1)
    reader_File2 = fileReadingModule.returnCSVReader(fileName2)
    person_writer = fileWritingModule.returnCSVWriter(outputFile)
    write_headers_employers(person_writer)
    header = next(reader_File1)
    header = next(reader_File2)
    index = 0
    for columnName in header:
        if columnName == columnSort:
            sortIndex = index
            break
        index += 1
    currPerson_File1 = next(reader_File1, None)
    currPerson_File2 = next(reader_File2, None)
    while((currPerson_File1 != None) or (currPerson_File2 != None)):
        value_File1 = _obtainValue(currPerson_File1)
        value_File2 = _obtainValue(currPerson_File2)
        if value_File1 < value_File2:
            person_writer.writerow(currPerson_File1)
            currPerson_File1 = next(reader_File1, None)
        else:
            person_writer.writerow(currPerson_File2)
            currPerson_File2 = next(reader_File2, None)


def _obtainValue(currPerson):
    if currPerson == None:
        return sys.maxsize
    else:
        return int(float(currPerson[14]))

def mainScript(state_name):
      startTime = datetime.now()
      print('Assigning workers in input file to Work Counties')
      assign_to_work_counties(state_name)
      print('Separating Workers from Non-Workers for this input File')
      separate_workers_non_workers(state_name)
      print('sorting the Workers who work in one input File by Working County')
      inputTermination = state_name + 'Module2NN_WorkCounty_Work.csv'
      outputFileTermination = state_name + 'Module2NN_SortedWorkCounty.csv'
      sort_by_input_column(outputPath, inputTermination, str(WorkCounty_Index), outputPath, outputFileTermination)
      print('Assigning Workers in one input File to Employers')
      assign_workers_to_employers(state_name)
      print('Sorting the Workers Assigned to Employers in one input File by Residence_County')
      inputFileTermination = state_name + 'Module2NN_AssignedEmployer.csv'
      outputFileTermination = state_name + 'Module2NN_AssignedEmployer_SortedResidenceCounty.csv'
      sort_by_input_column(outputPath, inputFileTermination, str(ResidenceCounty_Index), outputPath, outputFileTermination)
      print('Merging the two files sorted by residence county into one File that is also sorted by Residence County')
      state_name_1 = outputPath + state_name + 'Module2NN_WorkCounty_NonWork.csv'
      state_name_2 = outputPath + state_name + 'Module2NN_AssignedEmployer_SortedResidenceCounty.csv'
      outputFile = outputPath + state_name + 'Module2NN_AllWorkersEmployed_SortedResidenceCounty.csv'
      merge_sorted_files(state_name_1, state_name_2, outputFile, 'Residence_County')
      print('Total Time to process the input File: ' + str(datetime.now() - startTime))

def module2runner():
    count = 1
    states = read_states()
    for state in states:
        print(count)
        if state.split(',')[0].replace(" ","") != "NewYork" and ny != True:
            continue
        if state.split(',')[0].replace(" ","") == "NewYork":
            ny = True
        if state.split(',')[0].replace(" ","") != "NewYork" and ny == True:
            mainScript(state.split(',')[0].replace(" ",""))
        count += 1

exec('mainScript(sys.argv[1])')
#cProfile.run('exec("module2runner()")') #sys.argv[1]