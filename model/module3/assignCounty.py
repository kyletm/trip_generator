'''
assignCounty.py

defines the assignCounty class.
An object of type assignCounty is generated from a input county, and can then assign people living in that input county to particular counties for
for their schooling.

Dependencies: None
Notes:
'''

import sys
import csv
import cdf
import math
import random
import bisect
import module3classdump
import fileReadingModule
import fileWritingModule
import countyAdjacencyReader
from datetime import datetime


'------------------------GLOBAL DATA------------------------'
'File Location of School Data'
schoolDataBase = 'D:/Data/Schools/School Database/'
inputFolder = 'D:/Data/Output/Module2/'
outputFolder = 'D:/Data/Output/Module3/'
'Constants for National Enrollment in Private and Public Schools'
public_school_enrollment_elem_mid = 34637.0
public_school_enrollment_high = 14668.0
private_school_enrollment_elem_mid = 4092.0
private_school_enrollment_high = 1306.0
total = public_school_enrollment_elem_mid + public_school_enrollment_high + private_school_enrollment_elem_mid + private_school_enrollment_high
privtotal = private_school_enrollment_elem_mid + private_school_enrollment_high
pubtotal = public_school_enrollment_elem_mid + public_school_enrollment_high
'-----------------------------------------------------------'


class assignCounty:
    def __init__(self, fips):
        'Initialize County Geography'
        self.fips = fips
        self.county = countyAdjacencyReader.read_data(fips)
        self.county.set_lat_lon()
        self.elemprivate = [] 
        self.midprivate = []
        self.highprivate = []
        self.read_private_schools(fips)
        self.privateElemSeats = 0
        self.privateMiddleSeats = 0
        self.privateHighSeats = 0
        self.get_total_seats()
        self.assignCountyList = []
        self.privateElemCounties = []
        self.privateMiddleCounties = []
        self.privateHighCounties = []


    def assemble_neighborly_dist(self):
         privateSchoolCounties = []
         for j in self.county.neighbors:
             privateSchoolCounties.append(assignCounty(j))
         privateSchoolCounties.append(self)
         validPrivateSchoolCounties = []
         for i in range(3):
             schoolTypeList = []
             for assigncounty in privateSchoolCounties:
                 if i == 0:
                     if assigncounty.privateElemSeats > 0:
                         schoolTypeList.append(assigncounty)
                 elif i == 1:
                     if assigncounty.privateMiddleSeats > 0:
                         schoolTypeList.append(assigncounty)
                 else:
                     if assigncounty.privateHighSeats > 0:
                         schoolTypeList.append(assigncounty)
             validPrivateSchoolCounties.append(schoolTypeList)
         'Create the distributions from the neighbors for the different age demographics.'
         privateElemCounties = []; privateElemNames = []
         privateMiddleCounties = []
         privateHighCounties = []
         homelat, homelon = self.county.get_lat_lon()
         minDistance = sys.maxsize
         for assigncounty in privateSchoolCounties:
             if assigncounty is self:
                 continue
             distanceCounty = distance_between_points(homelat, homelon, (assigncounty.county).lat, (assigncounty.county).lon)
             if distanceCounty == 0:
                 distanceCounty = 1
             if assigncounty.privateElemSeats > 0:
                 privateElemCounties.append(assigncounty.privateElemSeats / (distanceCounty**2)); privateElemNames.append(assigncounty.fips)
             if assigncounty.privateMiddleSeats > 0:
                 privateMiddleCounties.append(assigncounty.privateMiddleSeats / (distanceCounty**2))
             if assigncounty.privateHighSeats > 0:
                 privateHighCounties.append(assigncounty.privateHighSeats / (distanceCounty**2))
             if distanceCounty < minDistance:
                 minDistance = distanceCounty
         if self.privateElemSeats > 0:
             privateElemCounties.append(self.privateElemSeats / (minDistance * 0.75)**2); privateElemNames.append(assigncounty.fips)
         if self.privateMiddleSeats > 0:
             privateMiddleCounties.append(self.privateMiddleSeats / (minDistance * 0.75)**2)
         if self.privateHighSeats > 0:
             privateHighCounties.append(self.privateHighSeats / (minDistance * 0.75)**2)
         self.assignCountyList = validPrivateSchoolCounties
         self.privateElemCounties = cdf.cdf(privateElemCounties)
         self.privateMiddleCounties = cdf.cdf(privateMiddleCounties)
         self.privateHighCounties = cdf.cdf(privateHighCounties)


    'Calculate the Total Enrollment of a County'
    def get_total_seats(self):
        privateElem = 0
        privateMiddle = 0
        privateHigh = 0
        for k in self.elemprivate:
            privateElem += int(k[7])
        for k in self.midprivate:
            privateMiddle += int(k[7])
        for k in self.highprivate:
            privateHigh += int(k[7])
        self.privateElemSeats = privateElem
        self.privateMiddleSeats = privateMiddle
        self.privateHighSeats = privateHigh


    'Initialize Private Schools For County'
    def read_private_schools(self, fips):
        fileLocation = schoolDataBase + 'CountyPrivateSchools/'
        try:
            elem = open(fileLocation + fips + 'Private.csv', 'r+')
            elemprivateschools = csv.reader(elem, delimiter = ',')
        except IOError:
            elem = None
        elemprivate = []; midprivate = []; highprivate = []
        if elem != None:
            for j in elemprivateschools: 
                j[7] = int(j[7])
                if j[6] == '1':
                    elemprivate.append(j)
                if j[6] == '2' or j[6] == '3':
                    highprivate.append(j)
        midprivate = highprivate
        self.elemprivate = elemprivate
        self.midprivate = midprivate
        self.highprivate = highprivate

    def choose_assignCounty(self, type1, type2):
        assert type2 != 'no'
        if type2 == 'four year' or type2 == 'two year' or type2 == 'non deg':
            countyForSchool = 'UNASSIGNED'
        elif type2 == 'public':
            countyForSchool = self.fips
        elif type2 == 'private':
            split = random.random()
            idx = None
            if type1 == 'elem':
                if len(self.privateElemCounties) == 0:
                    return self.fips
                idx = bisect.bisect(self.privateElemCounties, split)
                countyForSchool = (self.assignCountyList[0][idx]).fips
            elif type1 == 'mid':
                if len(self.privateMiddleCounties) == 0:
                    return self.fips
                idx = bisect.bisect(self.privateMiddleCounties, split)
                countyForSchool = (self.assignCountyList[1][idx]).fips
            elif type1 == 'high':
                if len(self.privateHighCounties) == 0:
                    return self.fips
                idx = bisect.bisect(self.privateHighCounties, split)
                countyForSchool = (self.assignCountyList[2][idx]).fips
            else:
                print('FATAL ERROR: INVALID TYPE1 OF PRIVATE SCHOOL STUDENT')
                return None
        else:
            print('FATAL ERROR: INVALID TYPE2 VALUE FOR THE CURRENT STUDENT')
        return countyForSchool


'Read Enrollment In State For Post-Secondary Schools by Type'        
def read_post_sec_enrollment(state):
    fileLocation = schoolDataBase + 'stateenrollmentindegrees.csv'
    f = open(fileLocation, 'rU')
    for row in f:
        row = row.split(',')
        if (row[0] == state):
            total = row[3]
            bachelor = row[4]
            graduate = row[5]
            associates = row[6].strip('\n')
            return float(total), float(bachelor)+float(graduate), float(associates), float(row[2])


'Assign Student a Type of School (Private/Public) or (Elem, Mid, High, College) Based on Age/HHT/State'  
def get_school_type(age, gender, hht, homecounty, homestate, privelemmidpop, pubelemmidpop, privhighpop, pubhighpop,
                    fouryear, twoyear, nondeg):
    'Not A Student'
    if hht in [2,3,4,5,7,8] or age<5 or age>24:
        return 'non student', 'no', pubelemmidpop, privelemmidpop, pubhighpop, privhighpop, fouryear, twoyear, nondeg
    elif hht == 6:
        fouryear-=1
        return 'on campus college', 'four year', pubelemmidpop, privelemmidpop, pubhighpop, privhighpop, fouryear, twoyear, nondeg 
    elif hht in [0,1]:
        # 6 to 10 -> ELEMENTARY SCHOOL
        if age < 11:
            type1 = 'elem'
            puborpriv = random.random()
            totalPop = pubelemmidpop + privelemmidpop
            thresh = pubelemmidpop / totalPop
            if puborpriv < thresh: 
                pubelemmidpop-=1
                type2 = 'public'
            else:
                privelemmidpop-=1 
                type2 = 'private'
        # 11 to 13 -> MIDDLE SCHOOL
        elif age < 14:
            type1 = 'mid'
            puborpriv = random.random()
            totalPop = pubelemmidpop + privelemmidpop
            thresh = pubelemmidpop / totalPop
            if puborpriv < thresh: 
                pubelemmidpop-=1
                type2 = 'public'
            else:
                privelemmidpop-=1 
                type2 = 'private'
        # 14 - 18ish -> HIGH SCHOOL (SOME 18's IN COLLEGE)
        elif age < 19:
            split = random.random()
            'Account for 18 Year Olds Who Are In College (approx 1/3)'
            if age != 18 or split < 0.35:
                type1 = 'high'
            elif age == 18 and split > 0.35: 
                type1 = 'college'; 
                fouryearprop = fouryear / (fouryear +twoyear + nondeg)
                split = random.random()
                if split < fouryearprop:
                    type2 = 'four year'
                    fouryear-=1
                else:
                    type2 = 'two year'
                    twoyear-=1
            else:
                type1 = 'high'
            if type1 == 'high':
                puborpriv = random.random()
                totalPop = pubhighpop + privhighpop
                thresh = pubhighpop / totalPop
                if puborpriv < thresh: 
                    pubhighpop-=1
                    type2 = 'public'
                else:
                    privhighpop-=1 
                    type2 = 'private'
        elif age >= 19:
            type1 = 'college'
            split = random.random()
            fouryearprop = fouryear/(fouryear +twoyear + nondeg)
            twoyearprop = twoyear/(fouryear + twoyear + nondeg)
            nonprop = 1.0 - fouryearprop - twoyearprop
            weights = cdf.cdf([fouryearprop, twoyearprop, nonprop])
            names = ['four year', 'two year', 'non deg']
            idx=bisect.bisect(weights,split)
            type2 = names[idx]
            if idx == 0: fouryear-=1
            elif idx == 1: twoyear-=1
            else: nondeg-=1
        return type1, type2, pubelemmidpop, privelemmidpop, pubhighpop, privhighpop, fouryear, twoyear, nondeg


'Read State Enrollment in Schools, Scaled Using Past Data'
def read_state_lowerSchool_enrollment(state):
    fileLocation = schoolDataBase + 'statehighelemmidenrollment.csv'
    f = open(fileLocation, 'rU')
    for row in f:
        row = row.split(',')
        row = [row[x].strip('"') for x in range(0,(len(row)))]
        if row[0].strip('.').strip(' ') == state:
            statetotalenrollment2009 = float(row[8].strip('\n').strip('"'))
            statetotalenrollment2006 = float(row[1].strip('"'))
            statetotalenrollment2007 = float(row[4].strip('"'))
            statehighenrollment2006 = float(row[3].strip('"'))
            stateelemmidenrollment2006 = float(row[2].strip('"'))
            statehighenrollment2007 = float(row[6].strip('"'))
            stateelemmidenrollment2007 = float(row[5].strip('"'))
            prop1 = statehighenrollment2006 / statetotalenrollment2006
            prop2 = statehighenrollment2007 / statetotalenrollment2007
            projected2009high = ((prop1+prop2)/2.0) * statetotalenrollment2009
            prop1 = stateelemmidenrollment2006 / statetotalenrollment2006
            prop2 = stateelemmidenrollment2007 / statetotalenrollment2007
            projected2009elemmid = ((prop1+prop2)/2.0) * statetotalenrollment2009
            return projected2009high, projected2009elemmid


def scale_public_and_private(projHigh, projElemMid):
    # NATIONAL NUMBERS TO BE SCALED TO STATE LEVEL NUMBERS
    elemmidtotal  = private_school_enrollment_elem_mid + public_school_enrollment_elem_mid 
    hightotal =  public_school_enrollment_high + private_school_enrollment_high
    # PROJECTED STATE LEVEL NUMBERS FOR ENROLLMENT IN ALL SCHOOLS
    prop1 = private_school_enrollment_elem_mid / elemmidtotal
    prop2 = public_school_enrollment_elem_mid / elemmidtotal
    projectedPrivElemMid = prop1 * projElemMid
    projectedPublElemMid = prop2 * projElemMid
    prop1 = private_school_enrollment_high / hightotal
    prop2 = public_school_enrollment_high / hightotal
    projectedPrivHigh = prop1 * projHigh
    projectedPublHigh = prop2 * projHigh
    return projectedPrivElemMid, projectedPublElemMid, projectedPrivHigh, projectedPublHigh


'RETURN MILES BETWEEN LATITUDE AND LONGITUDE POINTS '
def distance_between_points(lat1, lon1, lat2, lon2):
    degrees_to_radians = math.pi/180.0
    phi1 = (90.0 - float(lat1))*degrees_to_radians
    phi2 = (90.0 - float(lat2))*degrees_to_radians
    theta1 = float(lon1)*degrees_to_radians
    theta2 = float(lon2)*degrees_to_radians
    cos = (math.sin(phi1)*math.sin(phi2)*math.cos(theta1 - theta2) + 
           math.cos(phi1)*math.cos(phi2))
    arc = math.acos(cos)
    return arc * 3963.167


def writeHeaders(pW):
    pW.writerow(['Residence_State'] + ['County_Code'] + ['Tract_Code'] + ['Block_Csode'] + ['HH_ID'] + ['HH_TYPE'] + ['Latitude'] + ['Longitude'] 
                + ['Person_ID_Number'] + ['Age'] + ['Sex'] + ['Traveler_Type'] + ['Income_Bracket']
                + ['Income_Amount'] + ['Residence_County'] + ['Work_County'] + ['Work_Industry'] + ['Employer'] + ['Work_Address'] + ['Work_City'] + ['Work_State'] 
                + ['Work_Zip'] + ['Work_County_Name'] + ['NAISC_Code'] + ['NAISC_Description'] + ['Patron:Employee'] + ['Patrons'] + ['Employees'] + ['Work_Lat'] + ['Work_Lon'] 
                + ['School_County'] + ['Type1'] + ['Type2'])


def executive(state):
    startTime = datetime.now()
    print(state + " started at: " + str(startTime))
    'Gather State Enrollment Data'
    statehigh, stateelemmid = read_state_lowerSchool_enrollment(state)
    privEleMidPop, pubEleMidPop, privHighPop, pubHighPop = scale_public_and_private(statehigh, stateelemmid)
    totalcollege, bachormore, assoc, non = read_post_sec_enrollment(state)
    '------------------------------RUN------------------------------'
    terminationInput = 'Module2NN_AllWorkersEmployed_SortedResidenceCounty.csv'
    terminationOutput = 'Module3NN_AssignedSchoolCounty.csv'
    personReader = fileReadingModule.returnCSVReader(inputFolder + state + terminationInput)
    personWriter = fileWritingModule.returnCSVWriter(outputFolder + state + terminationOutput)
    writeHeaders(personWriter)
    specCount = 0
    studentCount = 0
    count = 0
    trailingFIPS = ''
    for person in personReader:
        if count == 0: 
            count+=1
            continue
        'Gather Personal Data of Resident'
        if len(person) != 30: print(person); print(count); print(person); continue
        homeState = person[0]; homeCounty = person[1]; residenceCounty = person[14]; workCounty = person[15];
        age = int(person[9]); gender = int(person[10]); hht = int(person[5])
        homelat = float(person[6]); homelon = float(person[7])
        if len(residenceCounty) != 5:
            newCounty = '0'+ residenceCounty
            if(len(newCounty) != 5):
                print("FATAL SYSTEM ERROR: COUNTY IS NOT CORRECT")
        else:
            newCounty = residenceCounty
        if newCounty != trailingFIPS:
            trailingFIPS = newCounty
            print('Assigning people who live in county "' + newCounty + '" to school counties'); #print(newCounty)
            assigncounty = assignCounty(newCounty)
            assigncounty.assemble_neighborly_dist()
#            print('for every county neighboring the current county: print out the number of students that go to private school in that given county:')
#            for county in assigncounty.assignCountyList:
#                print('county/privateSchoolSeats: ' + str(county.fips) + '/' + str(county.privateElemSeats))
        'Get School Type'
        type1, type2, pubEleMidPop, privEleMidPop, pubHighPop, privHighPop, bachormore, assoc, non = get_school_type(age, gender, hht, homeCounty, homeState,privEleMidPop, pubEleMidPop, privHighPop, pubHighPop, bachormore, assoc, non)
        if type1 == 'non student':
            schoolcounty = 'NA'
            specCount += 1
        else:
            schoolcounty = assigncounty.choose_assignCounty(type1, type2)
            studentCount += 1
        personWriter.writerow(person + [schoolcounty] + [type1] + [type2])
        count += 1
        if count % 1000000 == 0:
            print('Have printed out a total of ' + str(count) + ' people')

    print('students: ' + str(studentCount))
    print('unassigned: ' + str(specCount))
    print('pop: ' + str(count))
















