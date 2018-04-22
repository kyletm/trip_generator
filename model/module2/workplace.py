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

DEPENDENCIES: industry.py; adjacency.py

NOTE: This is all original work, none of these methods are taken from
Mufti's Module 2, as they are performed entirely in a new fashion.
"""

import random
import bisect
import collections
from . import industry, adjacency
from ..utils import core

class WorkingCounty:
    """Employment and Patronage data encapsulation for a given county.  
    
    Attributes:    
        data (list): List of all employers associated with county.
        county (County): County object for a FIPS code.
        industries (list): Each element is a list of employers for a specific
            NAISC industry code given by create_industry_lists indust_dict. Each employer
            is also a list, detailing specific geographic and demographic information
            about the employer.
        patrons (list): Each element is a list detailing the number of employees/patrons
            employed by an employer within each NAISC industry code.
        patrons_cdf (list): Each element is a list detailing the CDF of employees/patrons
            employed by an employer within each NAISC industry code.
        
    """    

    def __init__(self, fips):
        self.fips = fips
        self.data = industry.read_county_employment(fips)
        self.county = adjacency.read_data(fips)
        self.industries = self.create_industry_lists()
        self.patrons, self.patrons_cdf = self.create_industry_distributions()

    def print_county(self):
        """Print County object."""
        self.county.print_county()

    def create_industry_lists(self):
        """Partition Employers/Patrons into NAISC Industries
        
        Returns:
            industries (list): Each element is a list of employers for a specific
                NAISC industry code given by create_industry_lists indust_dict. Each employer
                is also a list, detailing specific geographic and demographic information
                about the employer.
        """
        # TODO - Fix this once I've figured out what to do with
        # dictionary lookalike in dist_index_to_code, industry.py
        industries = []
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
        industries = [value for value in indust_dict.values()]
        return industries

    def create_industry_distributions(self):
        """Create distributions for each NAISC Industry category

        Returns:        
            patrons (list): Each element is a list detailing the number of 
                employees/patrons employed by an employer within each 
                NAISC industry code.
            patrons_cdf (list): Each element is a list detailing the CDF of 
                employees/patrons employed by an employer within each
                NAISC industry code.
        """
        all_patrons = []
        all_patrons_cdf = []
        for naisc_division in self.industries:
            patrons = []
            patrons_percentage = []
            patrons_cdf = []
            for employer in naisc_division:
                tot_employees = int(employer[13][0:].strip("'"))
                if tot_employees > 0:
                    all_patrons.append(tot_employees)
            total_spots = sum(all_patrons)
            if total_spots > 0:
                patrons_percentage = [float(s)/(total_spots) for s in all_patrons]
            else:
                patrons_percentage = []
            patrons_cdf = core.cdf(patrons_percentage)
            all_patrons.append(patrons)
            all_patrons_cdf.append(patrons_cdf)
        return all_patrons, all_patrons_cdf

    def draw_from_industry_distribution(self, index):
        """Select an Employer from a given industry in this workingCounty
        
        Inputs: 
            index (int): Index corresponding to NAISC industry category.
        
        Returns: 
            idx (int): Index corresponding to employer within NAISC industry category.
        """
        draw_cdf = self.patrons_cdf[index]
        if len(draw_cdf) == 0:
            print(self.spots_cdf)
            print(self.spots)
            print(index)
            print(self.spots[index])
            print(self.spots_cdf[index])
            raise ValueError('CDF has no elements')
        idx = bisect.bisect(draw_cdf, random.random())
        return idx

    'Selection of Industry and Employer for a Particular Resident, Given Work County and Demographic Data'
    def select_industry_and_employer(self, work_county, gender, income, inc_emp):
        """Select an Employer from a given industry in this WorkingCounty.
        
        Inputs: 
            work_county (str): FIPS code for a county.
            gender (int): 0 for Female, 1 for Male.
            income (float): Worker's income.
            inc_emp (IncomeEmployment): County level income and employment data.
        
        Returns: 
            indust (str): 2 Digit NAISC Industry Code.
            indust_idx (int): Index of this NAISC Industry Code in index list.
            employer (list): Information about selected employer.
        """
        no_employers_present = []
        for naisc_industry in self.patrons:
            if len(naisc_industry) == 0:
                no_employers_present.append(True)
            else:
                no_employers_present.append(False)
        if self.fips == '02282':
            print(no_employers_present)
            print(self.spots[9])
            print(self.spots_cdf[9])
        indust, indust_index = industry.get_work_industry(work_county, gender,
                                                          income, inc_emp, no_employers_present)
        if self.fips == '02282':
            print(indust_index, indust)
        employer_index = self.draw_from_industry_distribution(indust_index)
        return indust, indust_index, self.industries[indust_index][employer_index]

def _convert_code_to_indust(code):
    """Convert NAISC code to industry abbrevation.
    
    Used for mapping multiple NAISC codes to a broader industry categorization.    
    
    Inputs: 
        code (int): NAISC industry code.
    
    Returns: 
        indust (str): Broader industry abbrevation.
    """
    if code in (31, 32, 33):
        indust = 'man'
    elif code in (44, 45):
        indust = 'rtr'
    elif code in (48, 49):
        indust = 'tra'
    else:
        indust = 'otr'
    return indust
