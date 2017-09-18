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
import csv
import random
import bisect
from . import distance, convertToFIPS, module3classdump, fileReadingModule, fileWritingModule, countyAdjacencyReader
from ..utils import core

'------------------------GLOBAL DATA------------------------'
'File Location of School Data'
schoolDataBase = 'D:/Data/Schools/School Database/'
inputFolder = 'D:/Data/Output/Module3/'
outputFolder = 'D:/Data/Output/Module3/'

stateFourYearList = None; stateTwoYearList = None; stateNonDegList = None
stateFourYearDist = None; stateTwoYearDist = None; stateNonDegDist = None

'-----------------------------------------------------------'

'SchoolCounty Object: An object for housing the entire school data for a particular county, and points to its neighbors. '
class schoolAssigner:
    def __init__(self, fips, unweighted = 1, complete = 1):
        'Initialize County Geography'
        self.fips = fips
        self.county = countyAdjacencyReader.read_data(fips)
        self.county.set_lat_lon()
        'Create Distributions for:'
        '1.) public schools (nothing right now ... just choosing the closest public school without doing any pre-processing ahead of time)'
        self.elempublic, self.midpublic, self.highpublic = self.read_public_schools(fips)
        if len(self.midpublic) == 0: self.midpublic = self.highpublic
        self.distPublicElem, self.distPublicMiddle, self.distPublicHigh = self.assemble_publicCounty_dist(unweighted)
        'CHOOSE THE NEAREST PUBLIC SCHOOL'
        if complete:
            '2.) private school distributions by age demographic within aa partic '
            self.elemprivate, self.midprivate, self.highprivate = self.read_private_schools(fips)
            self.distPrivElem, self.distPrivMiddle, self.distPrivHigh = self.assemble_privateCounty_dist()
            '3.) post-secondary education by demographic within a county'
            'DONE ON THE STATE LEVEL'
        

    def assemble_publicCounty_dist(self, unweighted):
        # Note - we perform the cdf calculation on public schools population
        # Without a weighting of distance when there is no need to weight distance
        # Since every school is within the same county
        # Ignores the case where we have someone assigned to a public school
        # That doesn't exist in the county
        distPublicElem = []
        distPublicMiddle = []
        distPublicHigh = []
        if unweighted:
            [distPublicElem.append(int(school[5]))  for school in self.elempublic]
            [distPublicMiddle.append(int(school[5])) for school in self.midpublic]
            [distPublicHigh.append(int(school[5])) for school in self.highpublic]
        else:
            homelat, homelon = unweighted[0],unweighted[1]
            [distPublicElem.append(int(school[5])/(distance.CurvedDistance_between_LonLatPoints(
            homelat, homelon, float(school[6]), float(school[7])))**2)  for school in self.elempublic]
            [distPublicElem.append(int(school[5])/(distance.CurvedDistance_between_LonLatPoints(
            homelat, homelon, float(school[6]), float(school[7])))**2)  for school in self.midpublic]
            [distPublicElem.append(int(school[5])/(distance.CurvedDistance_between_LonLatPoints(
            homelat, homelon, float(school[6]), float(school[7])))**2)  for school in self.highpublic]
        distPublicElem = core.cdf(distPublicElem)
        distPublicMiddle = core.cdf(distPublicMiddle)
        distPublicHigh = core.cdf(distPublicHigh)
        return distPublicElem, distPublicMiddle, distPublicHigh
        



    def assemble_privateCounty_dist(self):
         distPrivElem = []
         distPrivMiddle = []
         distPrivHigh = []
         [distPrivElem.append(int(school[7])) for school in self.elemprivate]
         [distPrivMiddle.append(int(school[7])) for school in self.midprivate]
         [distPrivHigh.append(int(school[7])) for school in self.highprivate]
         distPrivElem = core.cdf(distPrivElem)
         distPrivMiddle = core.cdf(distPrivMiddle)
         distPrivHigh = core.cdf(distPrivHigh)
         return distPrivElem, distPrivMiddle, distPrivHigh


    '''
    def scale_school_employment_to_students(self, statefouryear, statetwoyear, statenodeg):
        countyFourYear, countyTwoYear, countyNonDeg = self.fouryear, self.twoyear, self.nondeg
        countyfouryear_Scale, countytwoyear_Scale, countynodeg_Scale = get_scale_factor(self.fips, self.county.statecode, statefouryear, statetwoyear, statenodeg)
        totalEmployment = []
        [totalEmployment.append(int(j[len(j) - 4])) for j in countyFourYear]
        totalFourEmployment = sum(totalEmployment)
        totalEmployment = []        
        [totalEmployment.append(int(j[len(j) - 4])) for j in countyTwoYear]
        totalTwoEmployment = sum(totalEmployment)
        totalEmployment = []
        [totalEmployment.append(int(j[len(j) - 4])) for j in countyNonDeg]
        totalNonEmployment = sum(totalEmployment)
        count = 0
        fouryearEnrollment = []; twoyearEnrollment = []; nonEnrollment = []
        for j in countyFourYear:
            j[len(j) - 4] = int((float(j[len(j) - 4]) / totalFourEmployment) * countyfouryear_Scale)
            fouryearEnrollment.append(j[len(j) - 4])
            count+=1
        count = 0
        for j in countyTwoYear:
            j[len(j) - 4] = int((float(j[len(j) - 4]) / totalTwoEmployment) * countytwoyear_Scale)
            twoyearEnrollment.append(j[len(j) - 4])
            count+=1
        count = 0
        for j in countyNonDeg:
            j[len(j) - 4] = int((float(j[len(j) - 4]) / totalNonEmployment) * countynodeg_Scale)
            nonEnrollment.append(j[len(j) - 4])
            count+=1
        return fouryearEnrollment, twoyearEnrollment, nonEnrollment
        '''

    'Select an Individual School For a Student' 
    def select_school_by_type(self, type1, type2, homelat, homelon):
        global stateFourYearDist, stateTwoYearDist, stateNonDegDist, someCount
        assert type2 != 'no'
        assert stateFourYearDist != None; assert stateTwoYearDist != None; assert stateNonDegDist != None
        x=random.random()
        school = None
        if type2 == 'public':
            school = self.select_public_schools(type1, homelat, homelon)
        elif type2 == 'private':
            # We change the type from private to public if no private
            # schools exist due to a lack of data
            school, type2 = self.select_private_schools(type1, type2, homelat, homelon)
        else:
            if type2 == 'four year':
                idx=bisect.bisect(stateFourYearDist,x)
                school = stateFourYearList[idx]
            elif type2 == 'two year':
                idx=bisect.bisect(stateTwoYearDist,x)
                school = stateTwoYearList[idx]
            elif type2 == 'non deg':
                idx=bisect.bisect(stateNonDegDist,x)
                school = stateNonDegList[idx]
            else:
                print('FATAL ERROR: INVALID TYPE2 FOR CURRENT STUDENT')
        return school, type2

    def select_public_schools(self, type1, homelat, homelon):
        # Returns the public school, given a school type and a latitude/longitude
        # For the home
        global someCount
        x=random.random()
        if type1 == 'elem':
           idx=bisect.bisect(self.distPublicElem,x)
           try:
               school = self.elempublic[idx]
           except:
               school = select_neighboring_PublicSchool(self.county.neighbors,1,homelat,homelon,x)
        elif type1 == 'mid':
           idx=bisect.bisect(self.distPublicMiddle,x)
           try:
               school = self.midpublic[idx]
           except:
               someCount+=1
               school = select_neighboring_PublicSchool(self.county.neighbors,2,homelat,homelon,x)
        elif type1 == 'high':
           idx=bisect.bisect(self.distPublicHigh,x)
           try:
               school = self.highpublic[idx]
           except:
               someCount+=1
               school = select_neighboring_PublicSchool(self.county.neighbors,3,homelat,homelon,x)
        else:
            print('FATAL ERROR: INVALID TYPE1 FOR CURRENT STUDENT')
        return school

    def select_private_schools(self, type1, type2, homelat, homelon):
        # Returns the public school, given a school type and a latitude/longitude
        # For the home. If there are no suitable private schools, a public
        # school is selected.
        global someCount
        x=random.random()
        if type1 == 'elem': 
           if len(self.distPrivElem) == 0:
               type2 = "public"
               return self.select_public_schools(type1, homelat, homelon), type2
           idx=bisect.bisect(self.distPrivElem,x)
           try:
               school = self.elemprivate[idx]
           except:
               print(self.distPrivElem)
               print(self.fips)
               print(self.elemprivate)
               someCount+=1
               school = 'UNKNOWN'
               print('None detected 4')
               sys.exit()
        elif type1 == 'mid':
           if len(self.distPrivMiddle) == 0:
               type2 = "public"
               return self.select_public_schools(type1, homelat, homelon), type2
           idx=bisect.bisect(self.distPrivMiddle,x)
           try:
               school = self.midprivate[idx]
           except:
               someCount+=1
               school = 'UNKNOWN'
               print('None detected 5')
               sys.exit()
        elif type1 == 'high':
           if len(self.distPrivHigh) == 0:
              type2 = "public"
              return self.select_public_schools(type1, homelat, homelon), type2
           idx=bisect.bisect(self.distPrivHigh,x)
           try:
               school = self.highprivate[idx]
           except:
               someCount+=1
               school = 'UNKNOWN'
               print('None detected 6')
               sys.exit()
        else:
            print('FATAL ERROR: INVALID TYPE1 FOR CURRENT STUDENT')
        return school, type2

    'Initialize Private Schools For County'
    def read_private_schools(self, fips):
         fileLocation = schoolDataBase + 'CountyPrivateSchools/'
         try:
             elem = open(fileLocation + fips + 'Private.csv', 'rU')
             elemprivateschoolReader = csv.reader(elem, delimiter = ',')
             elemprivateschools = []
             [elemprivateschools.append(row) for row in elemprivateschoolReader] 
         except IOError:
             elem = None
         elemprivate = []; highprivate = []
         if elem != None:
             for j in elemprivateschools: 
                 j[7] = int(j[7])
             for row in elemprivateschools:
                 if row[6] == '1':
                     elemprivate.append(row)
                 elif row[6] == '2' or row[6] == '3':
                     highprivate.append(row)
                 else:
                     print('FATAL ERROR: SCHOOL DOES NOT HAVE A CODE VALUE THAT LIES IN THE SET OF VALUES: {1,2,3}')
         #midprivate = highprivate
         return elemprivate, highprivate, highprivate    

    'Initialize Public Schools For County'
    def read_public_schools(self, fips):
        fileLocationElem = schoolDataBase + 'CountyPublicSchools/' +  'Elem/'
        fileLocationMid = schoolDataBase + 'CountyPublicSchools/' +  'Mid/'
        fileLocationHigh = schoolDataBase + 'CountyPublicSchools/' +  'High/'
        try:
            elem = open(fileLocationElem + fips + 'Elem.csv', 'rU')
            elempublicschools = csv.reader(elem, delimiter = ',')
        except IOError:
            elem = None
        try:
            mid = open(fileLocationMid + fips + 'Mid.csv', 'rU')
            midpublicschools = csv.reader(mid, delimiter = ',')
        except IOError:
            mid = None
        try:
            high = open(fileLocationHigh + fips + 'High.csv', 'rU')
            highpublicschools = csv.reader(high, delimiter = ',')
        except IOError:
            high = None
        elempublic = []; midpublic = []; highpublic = []
        if elem != None:
            [elempublic.append(row) for row in elempublicschools]
            for j in elempublic: j[5] = int(j[5])
        if mid != None:
            [midpublic.append(row) for row in midpublicschools]
            for j in midpublic: j[5] = int(j[5])
        if high != None:
            [highpublic.append(row) for row in highpublicschools]
            for j in highpublic: j[5] = int(j[5])
        return elempublic, midpublic, highpublic

'Initialize Post Secondary Schools for county'
def read_post_sec_schools_for_state(state, stateAbbrev):
    stateFolderLocation = schoolDataBase + 'PostSecSchoolsByCounty/' + stateAbbrev + '/'
    allStateNonDegSchools = []; allStateTwoYearSchools = []; allStateFourYearSchools = []
    for fileName in os.listdir(stateFolderLocation):
        fileName = stateFolderLocation + fileName
        if fileName.endswith('CommunityCollege.csv'):
            twoyearschools = fileReadingModule.returnCSVReader(fileName)
            for row in twoyearschools: allStateTwoYearSchools.append(row)
        elif fileName.endswith('University.csv'):
            fouryearschools = fileReadingModule.returnCSVReader(fileName)
            for row in fouryearschools: allStateFourYearSchools.append(row)
        elif fileName.endswith('NonDegree.csv'):
            nondegschools = fileReadingModule.returnCSVReader(fileName)
            for row in nondegschools: allStateNonDegSchools.append(row)
        else:
            'Do nothing for a non-csv file'
    return allStateFourYearSchools, allStateTwoYearSchools, allStateNonDegSchools

'Use employment at Universities as a proxy for school attendance'
def assemble_postsec_dist(fourYearSchools, twoYearSchools, nonDegSchools):
    fourYearEmployment = []
    twoYearEmployment = []
    nonDegEmployment = []
    [fourYearEmployment.append(int(j[len(j) - 4])) for j in fourYearSchools]
    [twoYearEmployment.append(int(j[len(j) - 4])) for j in twoYearSchools]
    [nonDegEmployment.append(int(j[len(j) - 4])) for j in nonDegSchools]
    fouryearDist = []
    twoyearDist = []
    nonDegreeDist = []
    fouryearDist = core.cdf(fourYearEmployment)
    twoyearDist = core.cdf(twoYearEmployment)
    nonDegreeDist = core.cdf(nonDegEmployment)
    return fouryearDist, twoyearDist, nonDegreeDist 

'''
'Scale State Enrollment in Types of Post-Sec Schools by County Population'
'To Obtain County Enrollment in Different Programs'
def get_scale_factor(fips, state, statefouryear, statetwoyear, statenodeg):
    statecounties = []
    C_PATH = '/Users/matthewgarvey/Desktop/Data/WorkFlow'
    fname = C_PATH + '/allCounties.txt'
    f = open(fname, 'rU')
    totalStatePop = 0.0
    countyPop = []
    weights = []
    for line in f:
        splitter = line.split(',')
        'In State'
        if (splitter[1] == state):
            if splitter[3] not in statecounties:
                statecounties.append(splitter[3])
                totalStatePop+=float(splitter[7])
                countyPop.append([splitter[3], splitter[7]])
    for j in countyPop:
        weights.append([j[0], float(j[1])/totalStatePop])
        if j[0] == fips:
            req = (weights.pop())
    countyfouryear = req[1]*statefouryear
    countytwoyear = req[1]*statetwoyear
    countynodeg = req[1]*statenodeg
    return countyfouryear, countytwoyear, countynodeg
'''


'Return the index of the best public school'
def _Nearest_PublicSchool(homelat, homelon, listPublicSchools, returnDist = 0):
    closestSchool = None
    minDistance = sys.maxsize
    for publicSchool in listPublicSchools:
        newDistance = distance.CurvedDistance_between_LonLatPoints(homelat, homelon, float(publicSchool[6]), float(publicSchool[7]))
        if newDistance < minDistance:
            closestSchool = publicSchool
            minDistance = newDistance
    if returnDist:
        return closestSchool, minDistance
    return closestSchool


def select_neighboring_PublicSchool(listCounties,schoolType, lat, lon, x):
    schoolWeights = []; schools = []
    for fips in listCounties:
        schoolCounty = schoolAssigner(fips, unweighted = [lat, lon], complete = 0)
        if schoolType == 1:
            schoolWeights.append(schoolCounty.distPublicElem); schools.append(schoolCounty.elempublic)
        elif schoolType == 2:
            schoolWeights.append(schoolCounty.distPublicMiddle); schools.append(schoolCounty.midpublic)
        else:
            schoolWeights.append(schoolCounty.distPublicHigh); schools.append(schoolCounty.highpublic)
    combined = sum(schoolWeights,[])
    schools = sum(schools,[])
    dist = core.cdf(combined)
    #print(dist)
    #print(len(schools))
    #print(len(dist))
    idx = bisect.bisect(dist,x)
    #print(idx)
    return schools[idx]

def writeHeaders(pW):
    pW.writerow(['Residence_State'] + ['County_Code'] + ['Tract_Code'] + ['Block_Code'] + ['HH_ID'] + ['HH_TYPE'] + ['Latitude'] + ['Longitude'] 
                + ['Person_ID_Number'] + ['Age'] + ['Sex'] + ['Traveler_Type'] + ['Income_Bracket']
                + ['Income_Amount'] + ['Residence_County'] + ['Work_County'] + ['Work_Industry'] + ['Employer'] + ['Work_Address'] + ['Work_City'] + ['Work_State'] 
                + ['Work_Zip'] + ['Work_County_Name'] + ['NAISC_Code'] + ['NAISC_Description'] + ['Patron:Employee'] + ['Patrons'] + ['Employees'] + ['Work_Lat'] + ['Work_Lon'] 
                + ['School_County'] + ['Type1'] + ['Type2'] + ['School_County_Name'] + ['School_State'] + ['School_Name'] + ['School_Lat'] + ['School_Lon'])


def writeNonStudent(pW, person):
    pW.writerow(person + ['NA'] + ['NA'] + ['NA'] + ['NA'] +  ['NA'] + ['NA'] + ['NA'])

def write_school_by_type(personWriter, person, school, type2):
    #print('PERSON:' + ', '.join(map(str, person)))
    #print('school:' + ', '.join(map(str, school)))
    global someCount
    assert type2 != 'no'
    try:
        assert school != None
    except:
        someCount += 1
        school = 'UNKNOWN'
        sys.exit()
    if school == 'UNKNOWN':
        personWriter.writerow(person + ['UNKNOWN'] + ['UNKNOWN'] + ['UNKNOWN'] + ['UNKNOWN'] + ['UNKNOWN'])
    if school != 'UNKNOWN' and type2 == 'public':
        try:
            personWriter.writerow(person + [school[1]] + [school[0]] + [school[3]] + [school[6]] + [school[7]])
        except:
            print('ERRORWRITESCHOOL: ' + school)
            print(school == 'UNKNOWN')
            sys.exit()
    elif school != 'UNKNOWN' and type2 == 'private':
        try:
            personWriter.writerow(person + [school[3]] + [school[1]] + [school[0]] + [school[4]] + [school[5]])
        except:
            print('ERRORWRITESCHOOL: ' + school)  
            sys.exit()
    elif school != 'UNKNOWN':
        personWriter.writerow(person + [school[5]] + [school[3]] + [school[0]] + [school[15]] + [school[16]])


def executive(state):
    inputPath = inputFolder + state + 'Module3NN_AssignedSchoolCounty_SortedSchoolCounty.csv'
    outputPath = outputFolder + state + 'Module3NN_AssignedSchool.csv'
    personReader = fileReadingModule.returnCSVReader(inputPath)
    personWriter = fileWritingModule.returnCSVWriter(outputPath)
    writeHeaders(personWriter)
    states = module3classdump.read_states()
    stateAbbrev = module3classdump.match_name_abbrev(states, state); print(stateAbbrev)
    global stateFourYearList, stateTwoYearList, stateNonDegList
    global stateFourYearDist, stateTwoYearDist, stateNonDegDist, someCount
    stateFourYearList, stateTwoYearList, stateNonDegList = read_post_sec_schools_for_state(state, stateAbbrev)
    stateFourYearDist, stateTwoYearDist, stateNonDegDist = assemble_postsec_dist(stateFourYearList, stateTwoYearList, stateNonDegList)
    trailingFips = ''
    trailingAssigner = None
    count = -1; countindex = 0; someCount = 0
    for person in personReader:
        if count == -1:
            count += 1; countindex +=1
            continue
        schoolCounty = convertToFIPS.convertToFIPS(person[30])
        type1 = person[31]
        type2 = person[32]
        homelat = float(person[6])
        homelon = float(person[7])
        if trailingFips != schoolCounty:
            trailingFips = schoolCounty
            trailingAssigner = schoolAssigner(schoolCounty)
        school = None
        if type2 == 'no':
            writeNonStudent(personWriter, person)
        else:
            school, type2 = trailingAssigner.select_school_by_type(type1, type2, homelat, homelon)
            write_school_by_type(personWriter, person, school, type2)
        count += 1; countindex +=1;
        if count % 1000000 == 0:
            print('Number of people assigned schools in the state ' + state + ': ' + str(count))
    print('Finished assigning residents in '+ state + ' to schools. Total number of residents processed: ' + str(count)); print(someCount)
