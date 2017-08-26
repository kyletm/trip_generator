'''
Module for generating different ways to write to different types of files. 
'''

import csv

def csv_writer(CSVfilePath):
	f = open(CSVfilePath, 'w+')
	return csv.writer(f, delimiter=',', lineterminator='\n')


	

