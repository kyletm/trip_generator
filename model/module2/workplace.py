"""
workPlaceHelper.py

Project: United States Trip File Generation - Module 2
Author: Hill, Garvey, Marocchini
version date: 9/17/16
Python 3.5

PURPOSE: This set of methods and classes provides operations enabling
 the selection of a work place for a worker. It reads in employment files
for a particular county, creates lists of employers by industry, and
provides classes for creating distributions and selecting employers.

Relies on access to Emp Pat Files For All States and All counties

DEPENDENCIES: industry.py; countyAdjacencyReader.py

NOTE: This is all original work, none of these methods are taken from
Mufti's Module 2, as they are performed entirely in a new fashion.
"""

import random
import bisect
import collections
from . import industry, countyAdjacencyReader

'Working County Object - To Hold All Emp-Pat Data For a Given County'
class WorkingCounty:

    'Initialize with FIPS'

    def __init__(self, fips):
        self.data = industry.read_county_employment(fips)
        self.county = countyAdjacencyReader.read_data(fips)
        self.county.set_lat_lon()
        self.lat, self.lon = self.county.get_lat_lon()
        self.industries = []
        self.create_industry_lists()
        self.spots = []
        self.spots_cdf = []
        self.create_industry_distributions()

    'Print County For Testing Purposes'
    def print_county(self):
        self.county.print_county()

    'Partition Employers/Patrons into Industries'
    def create_industry_lists(self):
        indust_dict = collections.OrderedDict([(11, []), (21, []), (23, []), ('man', []),
                                               (42, []), ('rtr', []), ('tra', []), (22, []),
                                               (51, []), (52, []), (53, []), (54, []),
                                               (55, []), (56, []), (61, []), (62, []),
                                               (71, []), (72, []), (81, []), (92, [])])
        for j in self.data:
            if j[9][0:2] == 'NA':
                code = 99
            else:
                code = int(j[9][0:2])
            if code not in indust_dict.keys():
                code = _convert_code_to_indust(code)
            if code not in indust_dict.keys():
                continue
            indust_dict[code].append(j)
        self.industries = [value for value in indust_dict.values()]

    'Create Distributions For Each Industry'
    def create_industry_distributions(self):
        all_spots = []
        all_spots_cdf = []
        for j in self.industries:
            spots = []
            spots_percentage = []
            spots_cdf = []
            for k in j:
                spots.append(int(k[13][0:].strip("'")))
            total_spots = sum(spots)
            if total_spots > 0:
                spots_percentage = [float(s)/(total_spots) for s in spots]
            else:
                spots_percentage = []
            spots_cdf = industry.cdf(spots_percentage)
            all_spots.append(spots)
            all_spots_cdf.append(spots_cdf)
        self.spots = all_spots
        self.spots_cdf = all_spots_cdf

    'Select an Employer from a given industry in this workingCounty'
    def draw_from_industry_distribution(self, index):
        'Get List of # of Workers, Calculate Distance From Home to all Employers'
        draw_cdf = self.spots_cdf[index]
        if len(draw_cdf) == 0:
            raise ValueError('CDF has no elements')
        'Draw From CDF and get a Row Pointer of the Employer'
        idx = bisect.bisect(draw_cdf, random.random())
        'Return Row Pointer/Index'
        return idx

    'Selection of Industry and Employer for a Particular Resident, Given Work County and Demographic Data'
    def select_industry_and_employer(self, work_county, gender, income,
                                     menemp, womemp, meninco, wominco):
        markers = []
        for j in self.spots:
            if len(j) == 0:
                markers.append(True)
            else:
                markers.append(False)
        indust, indust_index = industry.get_work_industry(work_county, gender,
                                                                 income, menemp,
                                                                 womemp, meninco,
                                                                 wominco, markers)
        employer_index = self.draw_from_industry_distribution(indust_index)
        return indust, indust_index, self.industries[indust_index][employer_index]

def _convert_code_to_indust(code):
    if code in [31, 32, 33]:
        indust = 'man'
    elif code in [44, 45]:
        indust = 'rtr'
    elif code in [48, 49]:
        indust = 'tra'
    else:
        indust = 'otr'
    return indust
