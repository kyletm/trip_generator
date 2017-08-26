'OBJECTIVE: READ IN ZIP CODE TO COUNTY FIPS AND CREATE A FILE WITH MATCHING DICTIONARY'
'ONLY NEEDED ONE TIME PRODUCES MATCHING DICTIONARY'

'''
zipCodeReader.py

Project: United States Trip File Generation - Module 2
Author: Wyrough, Garvey, Marocchini
version date: 3/15/2014
Python 3.3

Purpose: Read in zip code to county fips matching dictionary and create an operable matching dictionary
for use as fail-safe when numeric matching of counties is not available. This is not used by an functions,
it is a one time script to create a file from 10 separate files relating zip codes to fips county codes. The file
is used in py.py

Dependencies: None

Notes: This code is original and was deemed necessary because Mufti's solution of hardcoding in unique
identifies for counties was not applicable at a larger scale.
'''

import module2
import csv

M_PATH = "D:/Data"

'Match State Name to Abbreviation'
def match_abbrev_code(states, abbrev):
    for i, j in enumerate(states):
        splitter = j.split(',')
        if splitter[1] == abbrev:
            return splitter[2]
        
'READ IN ASSOCIATED STATE ABBREVIATIONS WITH STATE FIPS CODES'
'*********NEEDED ONLY ONE TIME TO CREATE A MASTER FILE*******'
def read_zips():
    states = module2.read_states()
    zipFileLocation = M_PATH + '/ZipCodes/'
    fname = zipFileLocation + 'zipcty1.txt'
    hname = zipFileLocation + 'zipCountyDictionary.csv'
    h = open(hname, 'w+')
    personWriter = csv.writer(h, delimiter= ',', lineterminator = '\n')
    f = open(fname, 'r')
    trailingzip = '00000'
    for row in f:
        zipcode = row[0:5]
        if (zipcode != trailingzip):
            statecode = match_abbrev_code(states, row[23:25])
            if (statecode == None):
                continue
            countycode = row[25:28]
            fips = statecode + countycode
            personWriter.writerow([zipcode] + [fips])
            trailingzip = zipcode
            
    f.close()
    fname = zipFileLocation + 'zipcty4.txt'
    print(fname)
    f = open(fname, 'r')
    for row in f:
        zipcode = row[0:5]
        if (zipcode != trailingzip):
            statecode = match_abbrev_code(states, row[23:25])
            if (statecode == None):
                continue
            countycode = row[25:28]
            fips = statecode + countycode
            personWriter.writerow([zipcode] + [fips])
            trailingzip = zipcode
    f.close()
    fname = zipFileLocation + 'zipcty5.txt'
    print(fname)
    f = open(fname, 'r')
    for row in f:
        zipcode = row[0:5]
        if (zipcode != trailingzip):
            statecode = match_abbrev_code(states, row[23:25])
            if (statecode == None):
                continue
            countycode = row[25:28]
            fips = statecode + countycode
            personWriter.writerow([zipcode] + [fips])
            trailingzip = zipcode
    f.close()
    fname = zipFileLocation + 'zipcty6.txt'
    print(fname)
    f = open(fname, 'r')
    for row in f:
        zipcode = row[0:5]
        if (zipcode != trailingzip):
            statecode = match_abbrev_code(states, row[23:25])
            if (statecode == None):
                continue
            countycode = row[25:28]
            fips = statecode + countycode
            personWriter.writerow([zipcode] + [fips])
            trailingzip = zipcode
    f.close()
    fname = zipFileLocation + 'zipcty7.txt'
    print(fname)
    f = open(fname, 'r')
    for row in f:
        zipcode = row[0:5]
        if (zipcode != trailingzip):
            statecode = match_abbrev_code(states, row[23:25])
            if (statecode == None):
                continue
            countycode = row[25:28]
            fips = statecode + countycode
            personWriter.writerow([zipcode] + [fips])
            trailingzip = zipcode
    f.close()
    fname = zipFileLocation + 'zipcty8.txt'
    print(fname)
    f = open(fname, 'r')
    for row in f:
        zipcode = row[0:5]
        if (zipcode != trailingzip):
            statecode = match_abbrev_code(states, row[23:25])
            if (statecode == None):
                continue
            countycode = row[25:28]
            fips = statecode + countycode
            personWriter.writerow([zipcode] + [fips])
            trailingzip = zipcode
    f.close()
    fname = zipFileLocation + 'zipcty9.txt'
    print(fname)
    f = open(fname, 'r')
    for row in f:
        zipcode = row[0:5]
        if (zipcode != trailingzip):
            statecode = match_abbrev_code(states, row[23:25])
            if (statecode == None):
                continue
            countycode = row[25:28]
            fips = statecode + countycode
            personWriter.writerow([zipcode] + [fips])
            trailingzip = zipcode
    f.close()
    fname = zipFileLocation + 'zipcty10.txt'
    print(fname)
    f = open(fname, 'r')
    for row in f:
        zipcode = row[0:5]
        if (zipcode != trailingzip):
            statecode = match_abbrev_code(states, row[23:25])
            if (statecode == None):
                continue
            countycode = row[25:28]
            fips = statecode + countycode
            personWriter.writerow([zipcode] + [fips])
            trailingzip = zipcode
    f.close()
    h.close()
    return []
