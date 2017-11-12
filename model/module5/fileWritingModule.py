'''
fileWritingModule.py

Module for Generating Different ways to Write to Different Types of Files 
'''


import csv



def returnCSVWriter(CSVfilePath):
	f = open(CSVfilePath, 'w+')
	return (csv.writer(f, delimiter=',', lineterminator='\n'))


	

