"""
workPlaceHelper.py

Project: United States Trip File Generation - Module 2
Author: Hill, Garvey, Marocchini
version date: 9/17/16
Python 3.5

PURPOSE: This set of methods and classes provides operations enabling the selection of a work place for a worker. It reads in employment files
for a particular county, creates lists of employers by industry, and provides classes for creating distributions and selecting employers. 

Relies on access to Emp Pat Files For All States and All counties

DEPENDENCIES: industryReader.py; countyAdjacencyReader.py

NOTE: This is all original work, none of these methods are taken from Mufti's Module 2, as they are performed entirely in a new fashion.
"""

""" Initialize a work county and return the entire object """
import industryReader
import countyAdjacencyReader
import random
import bisect
import math

'Working County Object - To Hold All Emp-Pat Data For a Given County'
class workingCounty:
    'Initialize with FIPS'
    def __init__(self, fips):
        self.data = industryReader.read_county_employment(fips)
        self.county = countyAdjacencyReader.read_data(fips)
        self.county.set_lat_lon()
        self.lat, self.lon = self.county.get_lat_lon()
        self.industries = []
        self.create_industryLists()
        self.spots = []
        self.spotsCDF = []
        self.create_industry_distributions()
    'Print County For Testing Purposes'
    def printCounty(self):
        self.county.print_county()
    'Partition Employers/Patrons into Industries'
    def create_industryLists(self):
        agr = []; mqo = []; con = []; man = []; wtr = []; rtr = []
        tra = []; uti = []; inf = []; fin = []; rer = []; pro = []
        mgt = []; adm = []; edu = []; hea = []; art = []; aco = []
        otr = []; pub = []
        for j in self.data:
            if j[9][0:2] == 'NA' : code = 99
            else: code = int(j[9][0:2])
            if (code == 11): agr.append(j)
            elif (code == 21): mqo.append(j)
            elif (code == 23): con.append(j)
            elif (code in [31, 32, 33]): man.append(j)
            elif (code == 42): wtr.append(j)
            elif (code in [44, 45]): rtr.append(j)
            elif (code in [48, 49]): tra.append(j)
            elif (code == 22): uti.append(j)
            elif (code == 51): inf.append(j)
            elif (code == 52): fin.append(j)
            elif (code == 53): rer.append(j)
            elif (code == 54): pro.append(j)
            elif (code == 55): mgt.append(j)
            elif (code == 56): adm.append(j)
            elif (code == 61): edu.append(j)
            elif (code == 62): hea.append(j)
            elif (code == 71): art.append(j)
            elif (code == 72): aco.append(j)
            elif (code == 81): otr.append(j)
            elif (code == 92): pub.append(j)
            else: otr.append(j)
        self.industries = [agr, mqo, con, man, wtr, rtr, tra, uti,
                           inf, fin, rer, pro, mgt, adm, edu, hea,
                           art, aco, otr, pub]     
        return
    
    'Create Distributions For Each Industry'
    def create_industry_distributions(self):
        allSpots = []
        allSpotsCDF = []
        for j in self.industries:
            spots = []
            spotsPercentage = []
            spotsCDF = []
            for k in j:
                spots.append(int(k[13][0:].strip("'")))
            totalSpots = sum(spots)
            if totalSpots > 0:
                spotsPercentage = [float(s)/(totalSpots) for s in spots]
            else:
                spotsPercentage = []
            spotsCDF = industryReader.cdf(spotsPercentage)
            allSpots.append(spots)
            allSpotsCDF.append(spotsCDF)
        self.spots = allSpots
        self.spotsCDF = allSpotsCDF
    
    'Select an Employer from a given industry in this workingCounty'
    def draw_from_industry_distribution(self, index):
        'Get List of # of Workers, Calculate Distance From Home to all Employers'
        drawCDF = self.spotsCDF[index]
        if len(drawCDF) == 0: print('ERROR')
        'Draw From CDF and get a Row Pointer of the Employer'
        x=random.random()
        idx=bisect.bisect(drawCDF,x)
        'Return Row Pointer/Index'
        return idx
    
    'Selection of Industry and Employer for a Particular Resident, Given Work County and Demographic Data'
    def select_industry_and_employer(self, wC, gender, income, menemp, womemp, meninco, wominco):
        markers = []
        for j in (self.spots):
            if len(j) == 0: 
                markers.append(True)
            else: 
                markers.append(False)
        indust, industIndex = industryReader.get_work_industryA(wC, gender, income, menemp, womemp, meninco, wominco, markers)
        employerIndex = self.draw_from_industry_distribution(industIndex)
        return indust, industIndex, self.industries[industIndex][employerIndex]


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


'''
def weight_my_list(drawList):
    normFactor = sum(drawList)
    weightedlist =  [x/normFactor for x in drawList]
    return weightedlist
'''

'''
def spots_to_distances(dist, spots, lat, lon):
    'Get List of # of Workers, Calculate Distance From Home to all Employers'
    'Calculate Pre-Normalized Weighted List (# of workers / Dij^2) for all employers j in county i'
    drawList = [float(s)/(distance_between_points(lat, lon, j[2] , j[3])**2) for s, j in zip(spots, dist)]
    return drawList
'''

