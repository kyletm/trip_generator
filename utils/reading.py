'''
Module for generating different ways to read in different types of files. 
'''

import csv

def csv_reader(file_path):
	f = open(file_path)
	return csv.reader(f, delimiter = ',')




