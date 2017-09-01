'''
Module for reading different types of files. 
'''

import csv
import json

def csv_reader(file_obj):
    return csv.reader(file_obj, delimiter = ',', lineterminator='\n')
    
def file_reader(file_obj):
    return file_obj.read().splitlines()
    
def json_reader(file_obj):
    return json.load(file_obj)