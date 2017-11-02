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


import csv
from datetime import datetime
import random
import bisect
import sys
'----------PATH DEFINITIONS---------------------'
#rootDrive = 'E'
rootFilePath = 'D:/Data/Output/'
inputFileNameSuffix = 'Module3NN_AssignedSchool.csv'
outputFileNameSuffix = 'Module4NN2ndRun.csv'

#dataDrive = 'E'
dataRoot = 'D:/Data/'
'-----------------------------------------------'

def read_states():
      M_PATH = "D:/Data"
      stateFileLocation = M_PATH + '/'
      fname = stateFileLocation + 'ListofStates.csv'
      lines = open(fname).read().splitlines()
      return lines
      
def readActivityPatternDistributions():
    fileLocation = dataRoot + '/Trip Distributions and Times/' + 'TripTypeDistributions.csv'
    f = open(fileLocation, 'r+')
    zero = []; one = []; two = []; three = []; four = []; five = []; six = []
    allDistributions = [zero, one, two, three, four, five, six]
    for row in f:
        splitter = row.split(',')
        count = 0
        for j in splitter:
            allDistributions[count].append(float(j.strip('\n'))); count+=1
    f.close()
    return(allDistributions)

def constructMassiveDict():
    fileLocation = dataRoot + 'Schools/' + 'us_states.csv'
    f = open(fileLocation, 'r+')
    stateAbbrevs = []; countyDicts = []
    for row in f:
        splitter = row.split(',')
        someCountyDict = createCountyDict(splitter[2].rstrip())
        stateAbbrevs.append(splitter[2].rstrip())
        countyDicts.append(someCountyDict)
    massiveDict = dict(zip(stateAbbrevs,countyDicts))
    return massiveDict

# Deprecated
#def getStateAbbrev(state):
#    fileLocation = dataRoot + 'Schools/' + 'us_states.csv'
#    f = open(fileLocation, 'r+')
#    for row in f:
#        splitter = row.split(',')
#        if state == splitter[1]:
#            print(splitter[2])
#            return splitter[2].rstrip()

def createCountyDict(abbrev):
    fileLocation = dataRoot + 'Schools/' + 'countyfips.csv'
    f = open(fileLocation, 'r+')
    counties = []; countycodes = []
    for row in f:
        splitter = row.split(',')
        if splitter[0] == abbrev:
            if abbrev == 'DC':
                counties.append(splitter[3])
                countycodes.append(splitter[1]+splitter[2])
            if abbrev == 'AK':
                if 'Census Area' in splitter[3]:
                    counties.append(splitter[3].partition(' Census Area')[0])
                    countycodes.append(splitter[1]+splitter[2])
                elif 'Borough' in splitter[3]:
                    if 'City and Borough' in splitter[3]:
                        counties.append(splitter[3].partition(' City and Borough')[0])
                        countycodes.append(splitter[1]+splitter[2])
                    else:
                        counties.append(splitter[3].partition(' Borough')[0])
                        countycodes.append(splitter[1]+splitter[2])
                elif 'Municipality' in splitter[3]:
                    counties.append(splitter[3].partition(' Municipality')[0])
                    countycodes.append(splitter[1]+splitter[2])
            if abbrev == 'FL':
                if 'DeSoto' in splitter[3]:
                    counties.append('De Soto')
                    countycodes.append(splitter[1]+splitter[2])
                else:
                    counties.append(splitter[3].partition(' County')[0])
                    countycodes.append(splitter[1]+splitter[2])
            if abbrev == 'GA':
                if 'DeKalb' in splitter[3]:
                    counties.append('De Kalb')
                    countycodes.append(splitter[1]+splitter[2])
                else:
                    counties.append(splitter[3].partition(' County')[0])
                    countycodes.append(splitter[1]+splitter[2])
            if abbrev == 'MD':
                if 'Baltimore City' in splitter[3]:
                    counties.append('Baltimore City')
                    countycodes.append(splitter[1]+splitter[2])
                else:
                    counties.append(splitter[3].partition(' County')[0])
                    countycodes.append(splitter[1]+splitter[2])
            if abbrev == 'LA':
                if 'Parish' in splitter[3]:
                    counties.append(splitter[3].partition(' Parish')[0])
                    countycodes.append(splitter[1]+splitter[2])
                else:
                    counties.append(splitter[3].partition(' County')[0])
                    countycodes.append(splitter[1]+splitter[2])
            if abbrev == 'VA':
                if 'City' in splitter[3]:
                    counties.append(splitter[3])
                    countycodes.append(splitter[1]+splitter[2])
                else:
                    counties.append(splitter[3].partition(' County')[0])
                    countycodes.append(splitter[1]+splitter[2])
            else:
                counties.append(splitter[3].partition(' County')[0])
                countycodes.append(splitter[1]+splitter[2])
    f.close()
    collegeDict = dict(zip(counties, countycodes))
    return collegeDict

'Create Cumulative Distribution'
def cdf(weights):
    total=sum(weights); result=[]; cumsum=0
    for w in weights:
        cumsum+=w
        result.append(cumsum/total)
    return result
            
def assignActivityPattern(travelerType, allDistributions, person):
    'Revise Traveler Type, In the event of no school assigned (incredibly fringe population < 0.001%)'
    if person[len(person) - 3] == 'NA' and (travelerType == 3 or travelerType == 4 or travelerType == 2 or travelerType == 1):
        travelerType = 6
    dist = allDistributions[travelerType]
    weights = cdf(dist)
    split = random.random()
    idx = bisect.bisect(weights, split)
    return idx

'WRITE MODULE 2 OUTPUT HEADERS'
def writeHeaders(pW):
    pW.writerow(['Residence State'] + ['County Code'] + ['Tract Code'] + ['Block Code'] + ['HH ID'] + ['HH TYPE'] + ['Latitude'] + ['Longitude'] 
                + ['Person ID Number'] + ['Age'] + ['Sex'] + ['Traveler Type'] + ['Income Bracket']
                + ['Income Amount'] + ['Work County'] + ['Work Industry'] + ['Employer'] + ['Work Address'] + ['Work City'] + ['Work State'] 
                + ['Work Zip'] + ['Work County Name'] + ['NAISC Code'] + ['NAISC Description'] + ['Patron:Employee'] + ['Patrons'] + ['Employees'] + ['Work Lat'] + ['Work Lon'] 
                + ['School Name'] + ['School County'] + ['SchoolLat'] + ['SchoolLon'] + ['Activity Pattern'])

def executive(state):
    'Module 3 Input Path'
    fileLocation = rootFilePath + 'Module3/' + state + inputFileNameSuffix
    'Module 4 Output Path'
    outputLocation = rootFilePath + 'Module4/' + state + outputFileNameSuffix
    'Begin Reporting'
    startTime = datetime.now()
    print(state + " started at: " + str(startTime))
    
    'Open State File'
    f = open(fileLocation, 'r')
    personReader = csv.reader(f, delimiter=',')
    out = open(outputLocation, 'w+', encoding='utf8')
    personWriter = csv.writer(out, delimiter=',', lineterminator='\n')
    writeHeaders(personWriter)
    count = -1
    'Read Distributions'
    distributions = readActivityPatternDistributions()
    'Assign Every Resident a Tour Type AND Write Start of Trip File'
    unknownCount = 0
    weirdCount = 0
    problemCount = 0
    massiveDict = constructMassiveDict()
    for person in personReader:
        if count == -1: count+=1; continue
        count +=1
        'Assign Activity Pattern from Revised Traveler Type'
        travelerType = int(person[11])
        schoolCountyCode = person[30]
        schoolCountyName = person[33]
        if 'Radford' in schoolCountyName:
            schoolCountyName = 'Radford City'
        schoolAbbrev = person[34]
        if schoolCountyCode == 'UNASSIGNED':
            countyDict = massiveDict.get(schoolAbbrev)
            person[30] = countyDict.get(schoolCountyName)
            unknownCount += 1
        if travelerType == 5 and person[15] == '-2':
            activityIndex = '-5'
            weirdCount +=1
        else:
            activityIndex = assignActivityPattern(travelerType, distributions, person)
        # Deals with issues where students are assigned invalid county
        # By removing them from the dataset - note, this should only be a small
        # amount of the population.
        if person[30] == None and person[33] == 'NA' and person[34] != 'NA':
            problemCount +=1
            print('FIPS Issue found - no County Provided, skipping.')
            print('COUNT',count)
            continue
        else:
            personWriter.writerow(person + [activityIndex])
        if count % 1000000 == 0:
            print(str(count) + ' Residents Completed')
    f.close()
    out.close()  
    print(str(count) + ' of all Residents in ' + state + ' have been processed')
    print(state + " took this much time: " + str(datetime.now()-startTime))
    print('FIPS MISSING/ABLE TO FIX',unknownCount)
    print('INTERNATIONAL',weirdCount)
    print('FIPS MISSING/UNABLE TO FIX',problemCount)


def module4runner():
    count = 1
    states = read_states()
    for state in states:
        print(state)
        executive(state.split(',')[0].replace(" ",""))
        
#exec('module4runner()')   
exec('executive(sys.argv[1])')        
