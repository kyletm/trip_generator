location = "D:/Data/Schools/private schools/"
fname = location + "Private_Schools_09_10_clean.csv"

f = open(fname, 'r')
M_PATH = "D:/Data"
def read_states():
    """ Read in State names, abbreviations, and state codes"""
    censusFileLocation = M_PATH + '/'
    fname = censusFileLocation + 'ListofStates.csv'
    f = open(fname, 'r')
    mydata = []
    [mydata.append(row.split(',')) for row in f]
    return mydata

def get_state_index(state, data):
    for row in data:
        if state == row[1]:
            return row[2].strip('\n')

data = read_states()

schoolCounties = []
schoolObjects = []
count= 0
for row in f:
    if count == 0: count+=1; continue
    splitter = row.split(',')
    index = get_state_index(splitter[1], data)
    if index == None: county = '99999'
    else:county = index + splitter[2]
    
    if county not in schoolCounties:
        schoolCounties.append(county)
        schoolObjects.append([county, [splitter]])
    else:
        index = 0
        for j in schoolCounties:
            if j == county:
                schoolObjects[index][1].append(splitter)
                break
            index+=1
    
import csv
type = 'Private'
for j in schoolObjects:
    f = open(location + 'CountyPrivateSchools/' + str(j[0]) + type + '.csv', 'w+')
    writer = csv.writer(f, delimiter=',', lineterminator='\n')
    for k in j[1]:
        writer.writerow([k[0]] + [k[1]] + [k[2]] + [k[3]] + [k[4]] + [k[5]] + [k[6]] + [k[7].strip('\n')])
        
        