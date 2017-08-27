'OBJECTIVE: SPLIT STATE WIDE EMP/PAT FILES INTO COUNTY FIPS LABELED FILES FOR ALL OF UNITED STATES'
'READ IN A STATE FILE, CONVERT ZIP CODE TO COUNTY FIPS CODE, CACHE, WRITE TO FILE'

M_PATH = 'D:/Data/ZipCodes/'
O_PATH = 'D:/Data/Employment/CountyEmployeeFiles/'
F_PATH = 'D:/Data/WorkFlow/'
E_PATH = 'D:/Data/Employment/Employee Patronage Data/'
N_PATH = 'D:/Data/Employment/CountyEmployeeFiles/'

zipdata = []
namedata = []

import csv
from module2 import py
from datetime import datetime


def match_abbrev_code(states, abbrev):
    for i, j in enumerate(states):
        splitter = j.split(',')
        if splitter[1] == abbrev:
            return splitter[2]

'Read in Zip to County FIPS Dictionary'
def read_zip_dict():
    zipFileLocation = M_PATH
    fname = zipFileLocation + 'zipCountyDictionary.csv'
    lines = open(fname).read().splitlines()
    return lines

'Read in Emp/Pat File'
def read_employee_file(state):
    empFileLocation = E_PATH
    fname = empFileLocation + 'epfile_' + state + '.csv'
    f = open(fname, 'r')
    empData = []; count = 0
    for line in f:
        if count == 0:
            count += 1
            continue
        empData.append(line.split(","))
    return empData

'Return FIPS County code for a given zip code'
def lookup_zip(zipcode):
    global zipdata
    if len(zipcode) < 5:
        zipcode = '0' + zipcode
    for j in zipdata:
        if j[0:5] == (zipcode):
            return j[6:12]
    return None
    
'Read in County Name to FIPS Code Data'
def read_counties():
    global namedata
    fname = F_PATH + '/allCounties.csv'
    f = open(fname, 'r')
    namedata = []
    for line in f:
        splitter = line.split(',')
        namedata.append([splitter[3], splitter[6].split(' ')])
    return namedata  
    
'Match County Name from EMP file to County Name in FIPS Related Data'
def lookup_name(countyname, code):
    global namedata
    for j in namedata:

        countyname = countyname.strip('"')
        splitter = countyname.split(' ')

        if (splitter[0] == j[1][0]) and (len(splitter) == 1):
            if (j[0][0:2] == code):
                return j[0]
        elif (splitter[0] == j[1][0]) and (splitter[1] == j[1][1]) and (len(splitter)==2):
            if (j[0][0:2] == code):
                return j[0]
        elif (len(j[1]) == 3) and (len(splitter) > 2):
            if (splitter[0] == j[1][0]) and (splitter[1] == j[1][1]) and (splitter[2] == j[1][2]):
                if (j[0][0:2] == code):   
                    return j[0]
        elif (len(j[1]) > 3) and (len(splitter) > 1):
            if (splitter[0] == j[1][0]) and (splitter[1] == j[1][1]):
                if (j[0][0:2] == code):
                    return j[0]
    
    
'Read in state employement file, parse it into county files'
def rewrite_state(state): 
    global namedata 
    global zipdata 
    global allStates
    # Removed code?
    allStates = module2.py.read_states()
    code = match_abbrev_code(allStates, state)
    zipdata = read_zip_dict()
    data = read_employee_file(state)
    namedata = read_counties()
    fipslist = []
    fipsdata = []
    count = 0
    startTime = datetime.now()
    print(state + " started at " + str(datetime.now())
          + " duration: " + str(datetime.now()-startTime))
    
    'Iterate Over Rows of Emp File'
    for j in data:
        'Look Up county name to get fips code'
        if j[5] == 'NA':  
            if (j[2] == 'Hoonah') or (j[2] == 'HOONAH') or (j[2] == 'ANGOON') or (j[2] == 'Angoon')  or (j[2] == 'PELICAN') or (j[2] == 'TENAKEE SPRINGS'): rowfips = '02105'        
            elif (j[2] == 'Petersburg') or (j[2] == 'PETERSBURG') or (j[2] == 'KAKE') or (j[2] == 'PORT ALEXANDER'): rowfips = '02195';
            elif (j[2] == 'KLAWOCK') or (j[2] == 'THORNE BAY') or (j[2] == 'METLAKATLA') or (j[2] == 'COFFMAN COVE') or (j[2] == 'CRAIG'): rowfips = '02198'
            elif (j[2] == 'HYDABURG') or (j[2] == 'POINT BAKER'): rowfips = '02198'
            elif (j[2] == 'GUSTAVUS') or (j[2] == 'ELFIN COVE'): rowfips = '02105'
            elif (j[2] == 'SKAWGAY') or (j[2] == 'SKAGWAY'): rowfips = '02230'
            elif (j[2] == 'WRANGELL'): rowfips = '02275'
            else: 
                print(j)
                break
#                rowfips = (lookup_zip(j[4]))
        else:
            rowfips = lookup_name(j[5], code)
        if rowfips == None: print(j); break
        if rowfips not in fipslist:
            fipslist.append(rowfips)
            fipsdata.append([count, rowfips, []])
        count+=1
        
        for k,p in enumerate(fipslist):
            if p == rowfips:
                index = k
                break
        fipsdata[index][2].append(j)
    
    print(state + " is writing after this much time: " + str(datetime.now()-startTime))
    'Write FIPSDATA to Files'
    for j in fipsdata:
        'Open File or Create it'
        path = N_PATH + state + '/'
        f = open(path + str(j[1]) + '_' + state + '_EmpPatFile.csv', 'w+')
        storeWriter = csv.writer(f, delimiter= ',', lineterminator='\n')
        for k in j[2]:
            storeWriter.writerow([k[0].strip('"')] + [k[1].strip('"')] + [k[2].strip('"')] + [k[3].strip('"')] +
                                 [k[4].strip('"')] + [k[5].strip('"')] + [k[6].strip('"')] + [k[7].strip('"')] +
                                 [k[8].strip('"')] + [k[9].strip('"')] + [k[10].strip('"')] + [k[11].strip('"')] +
                                 [k[12].strip('"')] +[k[14].strip('"')] + [k[16].strip('"')] + [k[19].strip('"')] + [k[20].strip('"').strip('\n')]) 
    print(state + " took this much time: " + str(datetime.now()-startTime))
            
    