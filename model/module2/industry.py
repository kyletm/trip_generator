"""
industryReader.py

Project: United States Trip File Generation - Module 2
Author: A.P. matthewgarvey Wyrough
version date: 3/23/14
Python 3.3f

PURPOSE: This set of methods and classes provides operations enabling the
selection of an industry of work for a particular worker. It used by
workplace.py. It reads in the ACS Industry Participation by Sex by
Median Income and prepares that dataset for operations, extracting the
 relevant information.

Relies on access to the ACS Industry data.

DEPENDENCIES: None

Note: None of this code is taken from Mufti's Module 2 Synthesizer
which performs all of these tasks in an entirely different way.

"""
import random
import bisect
from ..utils import paths, reading

def match_code_abbrev(states, code):
    for state_row in states:
        splitter = state_row.split(',')
        if splitter[2] == code:
            return splitter[1]
    return None

'Match the state name to a state abbreviation'
def match_name_abbrev(states, state):
    for state_row in states:
        splitter = state_row.split(',')
        if splitter[0] == str(state):
            return splitter[1]
    return None

'Read in County Employment/Patronage File and Return List of All Locations in that county'
def read_county_employment(fips):
    with open(paths.MAIN_DRIVE + 'ListOfStates.csv') as state_file:
        states = reading.file_reader(state_file)
    code = fips[0:2]
    abbrev = match_code_abbrev(states, code)
    file_path = paths.COUNTY_PATH + abbrev + '/' + fips + '_' + abbrev + '_EmpPatFile.csv'
    with open(file_path) as file:
        return list(reading.csv_reader(file))

'Create Distribution of Work Industries Within A County'
def read_county_industries(county_data):
    iset = []
    ind = []
    #Create Key, Value Pairs for Industry Codes and Frequency of Industry Workers
    for j in county_data:
        #Extract 2 Digit NAISC Code
        industry = j[9][2:4]
        if industry == 'NA':
            industry = '99'
        if industry not in ind:
            ind.append(industry)
            iset.append([industry, 0])
        #Increment Weight of Industry by Number of Employees There
        for k in iset:
            if k[0] == industry:
                k[1] += int(j[12][2:].strip("'"))
    return iset

'Draw at Random An Industry From Weighted List, Return Industry Code, New Distribution, Number of Work Spots Left'
def select_industry(industry_dist):
    keys = []
    vals = []
    for industry in industry_dist:
        keys.append(industry[0])
        vals.append(industry[1])
    variate = random.random() * sum(vals)
    cum = 0.0
    for industry in industry_dist:
        cum += industry[1]
        if variate < cum:
            industry[1] = int(industry[1])-1
            return industry[0], industry_dist, sum(vals)-1
    return industry, industry_dist, sum(vals)-1

'Returns NAISC Code Corresponding to Index of Distribution'
def dist_index_to_naisc_code(index):
    indextocode = [(0, 11), (1, 21), (2, 23), (3, 31), (4, 42), (5, 44),
                   (6, 48), (7, 22), (8, 51), (9, 52), (10, 53), (11, 54),
                   (12, 55), (13, 56), (14, 61), (15, 62), (16, 71), (17, 72),
                   (18, 81), (19, 92)]
    return str(indextocode[index][1])

'Read in and create 4 lists of employment and income by gender by industry for each county'
def read_employment_income_by_industry():
    with open(paths.EMPLOYMENT_PATH + 'SexByIndustryByCounty_MOD.csv') as empl_file:
        reader = reading.csv_reader(empl_file)
        next(reader)
        menempdata = []; womempdata = []
        menincodata = []; womincodata = []
        for row in reader:
            menemp = []; womemp = []
            meninco = []; wominco = []
            #Create Men Employment By Industry, Women Employment, Men Median Income By Industry, Women Med Income
            menemp.append(row[0]); menemp.append(row[1]); menemp.append(row[2])
            womemp.append(row[0]); womemp.append(row[1]); womemp.append(row[2])
            meninco.append(row[0]); meninco.append(row[1]); meninco.append(row[2])
            wominco.append(row[0]); wominco.append(row[1]); wominco.append(row[2])
            for j in range(29, 101, 12):
                total = float(row[j-2])
                menemp.append(float(row[j]) * total / 100.0)
                womemp.append(float(row[j+2]) * total / 100.0)
                meninco.append(float(row[j+6]))
                wominco.append(float(row[j+8]))
            for j in [113, 125, 137, 161, 173, 197, 209, 221, 245, 257, 281, 293, 305, 317]:
                total = float(row[j-2])
                menemp.append(float(row[j]) * total / 100.0)
                womemp.append(float(row[j+2]) * total / 100.0)
                meninco.append(float(row[j+6]))
                wominco.append(float(row[j+8]))
            menempdata.append(menemp)
            womempdata.append(womemp)
            menincodata.append(meninco)
            womincodata.append(wominco)
        return menempdata, womempdata, menincodata, womincodata

'Create CDF of Weighted List For Given Distribution'
def cdf(weights):
    total = sum(weights)
    result = []
    cumsum = 0
    for w in weights:
        cumsum += w
        result.append(cumsum/total)
    return result

def get_work_industry(workcounty, gender, income, menempdata, womempdata,
                      menincodata, womincodata, markers):
    #Non-Worker
    if workcounty == '-1':
        return -1, -1
    #International Worker
    if workcounty == '-2':
        return -2, -2
    #Normal In-Country Worker
    count = 0
    for j in menempdata:
        if workcounty == j[1]:
            index = count
            break
        count += 1
    #Grab Distributions According to Gender of Worker'
    if gender == 0:
        empdata = womempdata[index][3:]
        incdata = womincodata[index][3:]
    else:
        empdata = menempdata[index][3:]
        incdata = menincodata[index][3:]
    #Zero Out Industries If No Employers Exist Within Actual Employment Data
    count = 0
    for j in markers:
        if markers[count]:
            empdata[count] = 0.0
            incdata[count] = 200000
        count += 1
    #Create distribution
    incdata[:] = [(x - income)**2 for x in incdata]
    try:
        draw_list = [x / y for x, y in zip(empdata, incdata)]
    except:
        #Issue where income is equal to x - rare, but possible
        #Overcome it by perturbing income
        incdata[:] = [(x - (income+0.01))**2 for x in incdata]
        draw_list = [x / y for x, y in zip(empdata, incdata)]
    weights = cdf(draw_list)
    x = random.random()
    idx = bisect.bisect(weights, x)
    #Get Industry Code
    industry = dist_index_to_naisc_code(idx)
    return industry, idx
