

schoolCounties = []
schoolObjects = []

location = "D:/Data/Schools/Public Schools/"
type = "High"
filename = location + "Public Schools_2011_" + type + ".csv"

f = open(filename, 'r')

count = 0

for row in f:
    if count == 0: count+=1; continue
    splitter = row.split(',')
    county = splitter[2]
    
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
for j in schoolObjects:
    f = open(location + 'CountyPublicSchools/' + type + '/'+ str(j[0]) + type + '.csv', 'w+')
    writer = csv.writer(f, delimiter=',', lineterminator='\n')
    for k in j[1]:
        writer.writerow([k[0]] + [k[1]] + [k[2]] + [k[3]] + [k[4]] + [k[5]] + [k[6]] + [k[7]] + [k[8]] + [k[9]] + [k[10].strip('\n')])

                