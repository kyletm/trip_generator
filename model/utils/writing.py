'''
Module for writing different types of files.
'''

import csv

def csv_writer(file_obj):
    return csv.writer(file_obj, delimiter=',', lineterminator='\n')
    