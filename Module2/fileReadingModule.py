'''
fileReadingModule.py

Module for Generating Different ways to Read in Different Types of Files 
'''
import csv

def returnCSVReader(CSVfilePath):
	f = open(CSVfilePath, 'rU')
	return (csv.reader(f, delimiter=','))




